"""One live mentorship request per pair, enforced by the schema.

`uniq_live_mentorship_request` used to be conditional on the status, which MySQL and TiDB
drop (models.W036); `live_flag` is 1 while a request is pending or accepted and NULL
afterwards, so a plain unique index now holds the line. Closed history stays intact.
"""

import pytest
from django.db import IntegrityError, transaction

from apps.mentorship.models import MentorshipRequest
from apps.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def learner(db):
    return User.objects.create_user(
        email="ada@example.com", username="ada", password="Str0ngPass!", display_name="Ada"
    )


@pytest.fixture
def mentor(db):
    return User.objects.create_user(
        email="grace@example.com", username="grace", password="Str0ngPass!", display_name="Grace"
    )


def make_request(learner, mentor, status=MentorshipRequest.STATUS_PENDING):
    return MentorshipRequest.objects.create(
        learner=learner, mentor=mentor, goal="Ship a first Django app", message="Please help.", status=status
    )


def test_second_live_request_for_the_same_pair_is_rejected(learner, mentor):
    make_request(learner, mentor)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            make_request(learner, mentor)

    assert MentorshipRequest.objects.count() == 1


def test_accepted_request_still_blocks_a_new_pending_one(learner, mentor):
    make_request(learner, mentor, status=MentorshipRequest.STATUS_ACCEPTED)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            make_request(learner, mentor)


def test_a_closed_request_frees_the_pair_and_keeps_history(learner, mentor):
    closed = make_request(learner, mentor, status=MentorshipRequest.STATUS_PENDING)
    closed.status = MentorshipRequest.STATUS_DECLINED
    closed.save(update_fields=["status", "updated_at"])

    again = make_request(learner, mentor)

    assert MentorshipRequest.objects.count() == 2
    assert again.live_flag == 1
    assert closed.live_flag is None


def test_requests_for_different_partners_are_independent(learner, mentor, db):
    third = User.objects.create_user(
        email="mei@example.com", username="mei", password="Str0ngPass!", display_name="Mei"
    )
    make_request(learner, mentor)
    make_request(learner, third)
    make_request(third, mentor)

    assert MentorshipRequest.objects.count() == 3


def test_self_request_is_refused_by_clean(learner):
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        MentorshipRequest(learner=learner, mentor=learner, goal="x", message="y").full_clean()
