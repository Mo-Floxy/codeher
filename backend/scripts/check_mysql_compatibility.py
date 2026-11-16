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

# What Django's MySQL backend reports for TiDB, which announces itself as MySQL 8.0.11.
# supports_table_check_constraints stays True (MySQL 8.0.16+ and TiDB 6.3+ both enforce
# CHECK), supports_partial_indexes is the one that silently drops unique indexes.
TIDB_CONNECTION = SimpleNamespace(
    display_name="MySQL/TiDB",
    features=SimpleNamespace(
        supports_partial_indexes=False,
        supports_table_check_constraints=True,
        supports_expression_indexes=False,
        supports_covering_indexes=True,
        supports_deferrable_unique_constraints=False,
        supports_nulls_distinct_unique_constraints=False,
    ),
)


def skipped_constraints():
    features = TIDB_CONNECTION.features
    for model in apps.get_models():
        for constraint in model._meta.constraints:
            for warning in constraint.check(model, TIDB_CONNECTION):
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
    findings = list(skipped_constraints())
    if not findings:
        print("OK: every unique constraint and index in the schema is created on MySQL/TiDB.")
        return 0
    for model, constraint, warning in findings:
        print(f"{model._meta.label}.{constraint.name}: [{warning.id}] {warning.msg}")
    print(
        f"\n{len(findings)} object(s) would be silently skipped. Replace each condition with a "
        "stored generated column plus a plain unique index - see "
        "apps/community/migrations/0003_db_enforced_unique_targets.py."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
