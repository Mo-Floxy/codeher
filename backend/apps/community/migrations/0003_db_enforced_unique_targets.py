"""Turn the conditional unique indexes into ones MySQL and TiDB actually create.

MySQL 8 and TiDB do not support a partial (conditional) unique index: Django reports
``models.W036`` and then skips the DDL entirely. Every "one row per user, target and
kind" guarantee in this app therefore lived only in Python on those servers, and the
write paths assume otherwise — ``toggle_engagement()`` and ``create_report()`` both
rely on an ``IntegrityError`` to collapse a double click, so a race used to insert two
rows and the denormalised counters then published "2 likes" for one.

The replacement is a stored generated column holding the row's target as one
comparable value (``'post:12'``), plus a *plain* unique index over it. The column is
NULL when no target is set, and a unique index never compares NULLs, which reproduces
the old ``condition=`` exactly.
"""

from django.conf import settings
from django.db import migrations, models
from django.db.models import F, Value
from django.db.models.functions import Cast, Concat

# Pure helper, no models — see apps/core/db_guard.py for why this import is safe here.
from apps.core.db_guard import guard_against_duplicates


def target_ref(*field_names):
    """`'post:12'` for whichever foreign key is populated; NULL when none is.

    Mirrors `apps.community.models._target_ref`. CASE rather than COALESCE because
    Django renders a nullable `Concat` argument as `COALESCE(x, '')` on SQLite but not
    on MySQL, which would give the two servers different uniqueness keys.
    """
    return models.Case(
        *(
            models.When(
                **{f"{name}__isnull": False},
                then=Concat(
                    models.Value(f"{name}:"),
                    Cast(F(name), models.CharField(max_length=20)),
                    output_field=models.CharField(max_length=32),
                ),
            )
            for name in field_names
        ),
        default=Value(None, output_field=models.CharField(max_length=32)),
        output_field=models.CharField(max_length=32),
    )



class Migration(migrations.Migration):
    dependencies = [
        ("community", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # On MySQL/TiDB these six were never created, so dropping them is a no-op there.
        migrations.RemoveConstraint(model_name="engagement", name="uniq_post_engagement"),
        migrations.RemoveConstraint(model_name="engagement", name="uniq_project_engagement"),
        migrations.RemoveConstraint(model_name="engagement", name="uniq_comment_engagement"),
        migrations.RemoveConstraint(model_name="report", name="uniq_post_report"),
        migrations.RemoveConstraint(model_name="report", name="uniq_comment_report"),
        migrations.RemoveConstraint(model_name="report", name="uniq_project_report"),
        migrations.AddField(
            model_name="engagement",
            name="target_ref",
            field=models.GeneratedField(
                db_persist=False,
                expression=target_ref("post", "project", "comment"),
                output_field=models.CharField(max_length=32),
            ),
        ),
        migrations.AddField(
            model_name="report",
            name="target_ref",
            field=models.GeneratedField(
                db_persist=False,
                expression=target_ref("post", "comment", "project"),
                output_field=models.CharField(max_length=32),
            ),
        ),
        migrations.RunPython(
            guard_against_duplicates("community", "engagement", ("user", "kind"), "target_ref", "uniq_engagement_target"),
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            guard_against_duplicates(
                "community", "report", ("created_by", "target_type"), "target_ref", "uniq_report_target"
            ),
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="engagement",
            constraint=models.UniqueConstraint(
                fields=("user", "kind", "target_ref"), name="uniq_engagement_target"
            ),
        ),
        migrations.AddConstraint(
            model_name="report",
            constraint=models.UniqueConstraint(
                fields=("created_by", "target_type", "target_ref"), name="uniq_report_target"
            ),
        ),
    ]
