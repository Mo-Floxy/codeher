"""Database-level uniqueness for engagement and report rows.

These constraints used to carry a `condition=`, which MySQL and TiDB drop in silence
(models.W036), so on the deployment database nothing stopped a double click from writing
two likes. They are now plain unique indexes over the generated `target_ref` column.

Everything here writes through the ORM rather than `apps.community.services`, because the
services have their own pre-checks — these tests are about what the schema guarantees if
two requests arrive at the same instant.
"""

import pytest
from django.db import IntegrityError, transaction

from apps.community.models import Comment, Engagement, Post, Report
from apps.users.models import User

pytestmark = pytest.mark.django_db

# A post and a comment deliberately share this primary key: an index that forgot the
# table prefix would treat them as the same target.
SHARED_ID = 9001


def make_user(name):
    return User.objects.create_user(
        email=f"{name}@example.com", username=name, password="Str0ngPass!", display_name=name.title()
    )


@pytest.fixture
def user(db):
    return make_user("ada")


@pytest.fixture
def other_user(db):
    return make_user("nia")


@pytest.fixture
def post(user):
    return Post.objects.create(id=SHARED_ID, user=user, type="discussion", title="Topic", body="Body", status="published")


@pytest.fixture
def comment(post, other_user):
    return Comment.objects.create(id=SHARED_ID, post=post, user=other_user, body="Reply")


def refs_for(user):
    return sorted(Engagement.objects.filter(user=user).values_list("target_ref", flat=True))


def test_second_like_on_the_same_post_is_rejected_by_the_database(user, post):
    Engagement.objects.create(user=user, post=post, kind="like")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Engagement.objects.create(user=user, post=post, kind="like")

    assert Engagement.objects.count() == 1


def test_like_and_bookmark_on_one_post_are_both_kept(user, post):
    Engagement.objects.create(user=user, post=post, kind="like")
    Engagement.objects.create(user=user, post=post, kind="bookmark")

    assert refs_for(user) == ["post:9001", "post:9001"]


def test_targets_are_distinguished_by_table_not_only_by_id(user, post, comment):
    """Post 9001 and comment 9001 are different things, and both likes must survive."""
    Engagement.objects.create(user=user, post=post, kind="like")
    Engagement.objects.create(user=user, comment=comment, kind="like")

    assert post.pk == comment.pk
    assert refs_for(user) == ["comment:9001", "post:9001"]


def test_two_members_may_like_the_same_post(user, other_user, post):
    Engagement.objects.create(user=user, post=post, kind="like")
    Engagement.objects.create(user=other_user, post=post, kind="like")

    assert Engagement.objects.count() == 2


def test_duplicate_report_of_the_same_target_is_rejected(user, post):
    Report.objects.create(created_by=user, target_type="post", post=post, reason="spam")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Report.objects.create(created_by=user, target_type="post", post=post, reason="harassment")

    assert Report.objects.count() == 1


def test_reports_across_tables_with_equal_ids_coexist(user, post, comment):
    Report.objects.create(created_by=user, target_type="post", post=post, reason="spam")
    Report.objects.create(created_by=user, target_type="comment", comment=comment, reason="spam")

    assert sorted(Report.objects.values_list("target_ref", flat=True)) == ["comment:9001", "post:9001"]


def test_report_clean_rejects_a_target_that_is_not_the_one_named(user, post, comment):
    from django.core.exceptions import ValidationError

    # The check constraint that would normally stop this is not enforced on MySQL 5.7
    # family servers, so Report.clean carries the same rule.
    mismatched = Report(created_by=user, target_type="post", comment=comment, reason="spam")
    with pytest.raises(ValidationError):
        mismatched.clean()

    empty = Report(created_by=user, target_type="post", reason="spam")
    with pytest.raises(ValidationError):
        empty.clean()
