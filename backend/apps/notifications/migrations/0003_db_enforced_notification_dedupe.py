"""Make notification dedupe enforceable on MySQL and TiDB.

``uniq_notification_dedupe`` carried ``condition=~Q(dedupe_key="")``, which neither
server creates (models.W036). ``notify()`` therefore had no database backstop: two
concurrent writes for the same event produced two inbox rows, and a re-edited comment
could spam a recipient. ``dedupe_ref`` is the key when one is set and NULL when it is
blank, so a plain unique index expresses the same rule.
"""

from django.conf import settings
from django.db import migrations, models

# Pure helper, no models — see apps/core/db_guard.py for why this import is safe here.
from apps.core.db_guard import guard_against_duplicates


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(model_name="notification", name="uniq_notification_dedupe"),
        migrations.AddField(
            model_name="notification",
            name="dedupe_ref",
            field=models.GeneratedField(
                db_persist=False,
                expression=models.Case(
                    models.When(
                        dedupe_key="",
                        then=models.Value(None, output_field=models.CharField(max_length=120)),
                    ),
                    default=models.F("dedupe_key"),
                    output_field=models.CharField(max_length=120),
                ),
                output_field=models.CharField(max_length=120),
            ),
        ),
        migrations.RunPython(
            guard_against_duplicates(
                "notifications", "notification", ("recipient", "kind"), "dedupe_ref", "uniq_notification_dedupe_ref"
            ),
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.UniqueConstraint(
                fields=("recipient", "kind", "dedupe_ref"), name="uniq_notification_dedupe_ref"
            ),
        ),
    ]
