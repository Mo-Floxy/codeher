"""Report which schema guarantees MySQL and TiDB actually create.

A conditional unique index is not an error on those servers — Django emits
`models.W036` and then skips the DDL, so the database ends up with no constraint at all
while every test written against SQLite still passes. That is how CodeHer's engagement,
report, notification-dedupe and live-mentorship rules nearly reached production
unenforced, so the check is worth running in CI.

    .venv/Scripts/python.exe scripts/check_mysql_compatibility.py

Exits non-zero when a constraint would be skipped.
"""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import django

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DB_ENGINE", "sqlite")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.apps import apps  # noqa: E402
from django.db.models.constraints import CheckConstraint  # noqa: E402

# What Django's MySQL backend reports for TiDB, which announces itself as MySQL 8.0.11.
# supports_partial_indexes is the one that silently drops conditional unique indexes.
# supports_table_check_constraints is False here on purpose: TiDB v6.3+ does enforce CHECK
# rules, but Django only emits them for a server claiming 8.0.16 or newer, and TiDB's
# compatibility banner says 8.0.11 — so the DDL is skipped even though the cluster could
# have taken it. That gap is tolerated and reported, not failed on; see CHECK_GAP below.
TIDB_CONNECTION = SimpleNamespace(
    display_name="MySQL/TiDB",
    features=SimpleNamespace(
        supports_partial_indexes=False,
        supports_table_check_constraints=False,
        supports_expression_indexes=False,
        supports_covering_indexes=True,
        supports_deferrable_unique_constraints=False,
        supports_nulls_distinct_unique_constraints=False,
    ),
)

CHECK_GAP = (
    "CHECK constraints are skipped because TiDB self-reports MySQL 8.0.11 and Django only "
    "emits them from 8.0.16. The rules are enforced in application code instead; the "
    "cluster would accept them, so a RunSQL migration is the way to reclaim them."
)


def constraint_warnings(constraint, model):
    """The W036-style warnings Django would raise for this constraint on TiDB.

    The name to call is not stable across versions: 5.2 checks constraints through the
    private `_check()`, Django 6 exposed it as `check()` — and on CheckConstraint `check`
    is also the deprecated alias for the condition Q object, which is not callable in the
    way this needs. So take the first attribute that is actually a bound method, and say so
    loudly if none is, rather than inventing the warnings here.
    """
    for attribute in ("_check", "check"):
        candidate = getattr(constraint, attribute, None)
        if callable(candidate):
            return list(candidate(model, TIDB_CONNECTION))
    raise RuntimeError(
        f"{type(constraint).__name__} exposes no callable check method; this reporter is "
        "out of step with the installed Django and would otherwise report nothing."
    )


def skipped_constraints():
    features = TIDB_CONNECTION.features
    for model in apps.get_models():
        for constraint in model._meta.constraints:
            for warning in constraint_warnings(constraint, model):
                if warning.id in {"models.W036", "models.W027", "models.W047"}:
                    yield model, constraint, warning
    # Meta.unique_together cannot carry a condition, but a conditional Index is skipped
    # by the same rule.
    for model in apps.get_models():
        for index in model._meta.indexes:
            if getattr(index, "condition", None) and not features.supports_partial_indexes:
                yield model, index, SimpleNamespace(
                    id="models.W036", msg=f"Index {index.name} carries a condition and would be skipped."
                )


def main():
    # A unique rule that never reaches the schema is a data-integrity bug, so it fails the
    # build. A CHECK rule does not: it is a known, documented difference, and failing on it
    # would only train everyone to pass --no-verify.
    findings = list(skipped_constraints())
    fatal = [f for f in findings if not isinstance(f[1], CheckConstraint)]
    tolerated = [f for f in findings if isinstance(f[1], CheckConstraint)]

    for model, constraint, warning in fatal:
        print(f"{model._meta.label}.{constraint.name}: [{warning.id}] {warning.msg}")
    if fatal:
        print(
            f"\n{len(fatal)} object(s) would be silently skipped. Replace each condition with a "
            "stored generated column plus a plain unique index - see "
            "apps/community/migrations/0003_db_enforced_unique_targets.py."
        )
        return 1

    for model, constraint, warning in tolerated:
        print(f"{model._meta.label}.{constraint.name}: [{warning.id}] {warning.msg} (tolerated)")
    if tolerated:
        print(f"\n{len(tolerated)} CHECK constraint(s) will not be created on TiDB.\n{CHECK_GAP}")

    print("OK: every unique constraint and index in the schema is created on MySQL/TiDB.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
