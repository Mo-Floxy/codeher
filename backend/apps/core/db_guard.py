"""Shared migration helpers for building unique indexes over tables that may already
hold duplicates.

Migrations normally must not import application code, because app code moves under them.
This module is the exception: it is pure, touches no models, and is versioned alongside
the schema it guards, so a migration can state "index these columns" once instead of
carrying three copies of the same duplicate search.
"""

import os

DEDUPE_OVERRIDE = "CODEHER_ALLOW_DEDUPE"


def duplicate_ids(model, key_fields, ref_field):
    """Ids of every row repeating an earlier row's unique key, oldest kept.

    Grouping in Python rather than SQL keeps this identical on SQLite, MySQL and TiDB,
    where NULL handling in ``GROUP BY`` differs. Rows with a NULL reference are exempt
    from the index, so they are exempt here too.
    """
    rows = (
        model.objects.exclude(**{f"{ref_field}__isnull": True})
        .order_by("created_at", "id")
        .values_list("id", *key_fields, ref_field)
    )
    seen, duplicates = set(), []
    for row in rows:
        key = row[1:]
        if key in seen:
            duplicates.append(row[0])
        else:
            seen.add(key)
    return duplicates


def guard_against_duplicates(app_label, model_name, key_fields, ref_field, constraint):
    """Return a RunPython callable that refuses to index over duplicates.

    Deleting rows is destructive, so the default is to stop and report. Setting
    ``CODEHER_ALLOW_DEDUPE=1`` keeps the oldest row of each group, which is the one the
    denormalised counters were already computed from.
    """

    def operation(apps, schema_editor):
        model = apps.get_model(app_label, model_name)
        duplicates = duplicate_ids(model, key_fields, ref_field)
        if not duplicates:
            return
        if os.environ.get(DEDUPE_OVERRIDE) != "1":
            raise RuntimeError(
                f"Cannot create {constraint}: {len(duplicates)} duplicate {model_name} row(s) exist "
                f"(ids {', '.join(str(pk) for pk in duplicates[:20])}). Inspect them, then re-run with "
                f"{DEDUPE_OVERRIDE}=1 to keep the oldest row of each group."
            )
        model.objects.filter(id__in=duplicates).delete()

    return operation
