"""Keep "one live mentorship request per pair" true on MySQL and TiDB.

The old constraint needed a condition (``status__in=["pending", "accepted"]``) so that
closed requests stay historical, and conditional unique indexes are not created on those
servers. ``live_flag`` is 1 while the request is pending or accepted and NULL after it,
which lets a plain unique index hold the same promise.
"""

from django.conf import settings
from django.db import migrations, models

# Pure helper, no models — see apps/core/db_guard.py for why this import is safe here.
from apps.core.db_guard import guard_against_duplicates

LIVE_STATUSES = ["pending", "accepted"]


class Migration(migrations.Migration):
    dependencies = [
        ("mentorship", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(model_name="mentorshiprequest", name="uniq_live_mentorship_request"),
        migrations.AddField(
            model_name="mentorshiprequest",
            name="live_flag",
            field=models.GeneratedField(
                db_persist=True,
                expression=models.Case(
                    models.When(status__in=LIVE_STATUSES, then=models.Value(1)),
                    default=models.Value(None, output_field=models.SmallIntegerField()),
                    output_field=models.SmallIntegerField(),
                ),
                output_field=models.SmallIntegerField(),
            ),
        ),
        migrations.RunPython(
            guard_against_duplicates(
                "mentorship",
                "mentorshiprequest",
                ("learner", "mentor"),
                "live_flag",
                "uniq_live_mentorship_request",
            ),
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="mentorshiprequest",
            constraint=models.UniqueConstraint(
                fields=("learner", "mentor", "live_flag"), name="uniq_live_mentorship_request"
            ),
        ),
    ]
