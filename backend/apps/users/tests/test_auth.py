"""Account, session, profile and permission behaviour.

Unlike the app-scoped suites, these run against the project URLconf so the real
``/api/`` prefixes, the swapped user model and the shared permission classes are
all under test together.

The helper is deliberately named ``api`` rather than ``client``: pytest-django
already owns a ``client`` fixture, and shadowing it produces a confusing
"Client object is not callable" failure.
"""

import re

import pytest
from django.contrib import admin as django_admin
from django.core import mail
from django.test import RequestFactory
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import Profile, User

pytestmark = pytest.mark.django_db

PASSWORD = "CodeHer!Test2026"


def make_user(name="ada", role="learner", password=PASSWORD, **extra):
    return User.objects.create_user(
        email=f"{name}@example.com", username=name, password=password, display_name=name.title(), role=role, **extra
    )


def api(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def register(payload_overrides=None):
    payload = {
        "email": "newbie@example.com",
        "username": "newbie",
        "display_name": "New Bie",
        "password": PASSWORD,
        "password2": PASSWORD,
    }
    payload.update(payload_overrides or {})
    return api().post("/api/auth/register/", payload, format="json")


class TestRegistration:
    def test_creates_account_tokens_and_profile(self):
        response = register()
        assert response.status_code == 201, response.data
        body = response.json()
        assert body["user"]["email"] == "newbie@example.com"
        assert body["user"]["role"] == "learner"
        assert body["access"] and body["refresh"]

        user = User.objects.get(email="newbie@example.com")
        # The gamification/visibility row must exist at creation, not on first read.
        assert Profile.objects.filter(user=user).exists()

    def test_password_is_hashed_never_stored_as_text(self):
        register()
        user = User.objects.get(email="newbie@example.com")
        assert PASSWORD not in user.password
        assert user.password.startswith("pbkdf2_")
        assert user.check_password(PASSWORD)

    def test_email_is_normalised_and_must_be_unique(self):
        make_user("ada")
        response = register({"email": "ADA@EXAMPLE.COM", "username": "someoneelse"})
        assert response.status_code == 400
        assert "email" in response.data
        assert User.objects.filter(email="ada@example.com").count() == 1

    def test_username_must_be_unique(self):
        make_user("ada")
        response = register({"email": "other@example.com", "username": "ada"})
        assert response.status_code == 400
        assert "username" in response.data

    def test_mismatched_confirmation_is_rejected(self):
        response = register({"password2": "Different!Pass2026"})
        assert response.status_code == 400
        assert "password2" in response.data

    @pytest.mark.parametrize("weak", ["short1!", "12345678", "password"], ids=["too-short", "all-numeric", "common"])
    def test_django_password_validators_apply_to_registration(self, weak):
        response = register({"password": weak, "password2": weak})
        assert response.status_code == 400
        assert "password" in str(response.data)

    def test_registration_tokens_authenticate_immediately(self):
        token = register().json()["access"]
        me = api().get("/api/auth/me/", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["user"]["email"] == "newbie@example.com"


class TestLogin:
    def test_returns_user_and_tokens(self):
        make_user("ada")
        response = api().post("/api/auth/login/", {"email": "ada@example.com", "password": PASSWORD}, format="json")
        assert response.status_code == 200
        assert response.json()["user"]["username"] == "ada"
        assert response.json()["access"]

    def test_wrong_password_is_401(self):
        make_user("ada")
        response = api().post(
            "/api/auth/login/", {"email": "ada@example.com", "password": "NotThePassword1!"}, format="json"
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_deactivated_account_cannot_sign_in(self):
        inactive = make_user("ghost")
        inactive.is_active = False
        inactive.save(update_fields=["is_active"])
        response = api().post("/api/auth/login/", {"email": "ghost@example.com", "password": PASSWORD}, format="json")
        assert response.status_code == 401

    def test_email_is_matched_case_insensitively(self):
        make_user("ada")
        response = api().post("/api/auth/login/", {"email": "Ada@Example.com", "password": PASSWORD}, format="json")
        assert response.status_code == 200


class TestSession:
    def test_refresh_exchanges_a_refresh_token_for_a_new_access(self):
        user = make_user("ada")
        refresh = str(RefreshToken.for_user(user))
        response = api().post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")
        assert response.status_code == 200
        replay = api().get("/api/auth/me/", headers={"Authorization": f"Bearer {response.json()['access']}"})
        assert replay.status_code == 200

    def test_logout_blacklists_the_refresh_token(self):
        user = make_user("ada")
        token = RefreshToken.for_user(user)
        response = api(user).post("/api/auth/logout/", {"refresh": str(token)}, format="json")
        assert response.status_code == 205
        replay = api().post("/api/auth/token/refresh/", {"refresh": str(token)}, format="json")
        assert replay.status_code == 401

    def test_protected_endpoints_refuse_anonymous_callers(self):
        for path in ["/api/auth/me/", "/api/users/me/profile/", "/api/users/"]:
            assert api().get(path).status_code == 401, path


class TestPasswordReset:
    def test_known_address_receives_a_working_link(self):
        make_user("ada")
        response = api().post("/api/auth/password/forgot/", {"email": "ada@example.com"}, format="json")
        assert response.status_code == 200
        assert len(mail.outbox) == 1

        link = re.search(r"reset-password\?uid=([^&]+)&token=([^\s]+)", mail.outbox[0].body)
        assert link, mail.outbox[0].body
        uid, token = link.group(1), link.group(2)

        reset = api().post(
            "/api/auth/password/reset/",
            {"uid": uid, "token": token, "new_password": "Fresh!Pass2026", "new_password2": "Fresh!Pass2026"},
            format="json",
        )
        assert reset.status_code == 200, reset.data

        user = User.objects.get(email="ada@example.com")
        assert user.check_password("Fresh!Pass2026")
        old_password = api().post("/api/auth/login/", {"email": "ada@example.com", "password": PASSWORD}, format="json")
        assert old_password.status_code == 401

    def test_unknown_address_is_answered_like_a_known_one_without_sending_mail(self):
        make_user("ada")
        unknown = api().post("/api/auth/password/forgot/", {"email": "nobody@example.com"}, format="json")
        known = api().post("/api/auth/password/forgot/", {"email": "ada@example.com"}, format="json")
        assert unknown.status_code == known.status_code == 200
        assert unknown.json()["detail"] == known.json()["detail"]
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["ada@example.com"]

    def test_a_broken_mail_server_does_not_reveal_that_the_address_exists(self, monkeypatch):
        """The guarantee the view advertises has to survive an SMTP outage.

        Deploys run with DEBUG=False and no EMAIL_HOST until one is chosen, so the
        mail backend points at localhost:587 and every send fails. If that returned
        an error status, a caller could tell "no such account" from "account exists"
        with two requests, so both answers must be identical.
        """

        def boom(*args, **kwargs):
            raise OSError("smtp unreachable")

        make_user("ada")
        monkeypatch.setattr("apps.users.views.send_mail", boom)
        unknown = api().post("/api/auth/password/forgot/", {"email": "nobody@example.com"}, format="json")
        known = api().post("/api/auth/password/forgot/", {"email": "ada@example.com"}, format="json")
        assert unknown.status_code == known.status_code == 200
        assert unknown.json() == known.json()
        assert len(mail.outbox) == 0

    def test_tampered_token_is_rejected(self):
        user = make_user("ada")
        token = str(RefreshToken.for_user(user))  # a real JWT, but not a password-reset token
        response = api().post(
            "/api/auth/password/reset/",
            {"uid": str(user.pk), "token": token, "new_password": "Fresh!Pass2026", "new_password2": "Fresh!Pass2026"},
            format="json",
        )
        assert response.status_code == 400
        user.refresh_from_db()
        assert user.check_password(PASSWORD)

    def test_mismatch_and_weak_new_passwords_are_rejected(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = make_user("ada")
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        mismatch = api().post(
            "/api/auth/password/reset/",
            {"uid": uid, "token": token, "new_password": "Fresh!Pass2026", "new_password2": "Other!Pass2026"},
            format="json",
        )
        assert mismatch.status_code == 400

        weak = api().post(
            "/api/auth/password/reset/",
            {"uid": uid, "token": token, "new_password": "12345678", "new_password2": "12345678"},
            format="json",
        )
        assert weak.status_code == 400
        user.refresh_from_db()
        assert user.check_password(PASSWORD)


class TestProfile:
    def test_owner_edits_are_persisted_and_returned(self):
        user = make_user("ada")
        response = api(user).patch(
            "/api/users/me/profile/",
            {
                "headline": "Frontend learner",
                "bio": "Six weeks into React.",
                "interests": ["react", "css"],
                "skill_level": "intermediate",
                "learning_technologies": ["javascript"],
            },
            format="json",
        )
        assert response.status_code == 200, response.data
        user.profile.refresh_from_db()
        assert user.profile.headline == "Frontend learner"
        assert user.profile.interests == ["react", "css"]
        assert user.profile.skill_level == "intermediate"

    def test_gamification_fields_are_read_only_through_the_profile_api(self):
        user = make_user("ada")
        response = api(user).patch("/api/users/me/profile/", {"total_xp": 99999, "level": 40}, format="json")
        assert response.status_code == 200
        user.profile.refresh_from_db()
        assert (user.profile.total_xp, user.profile.level) == (0, 1)

    def test_visibility_flags_are_enforced_server_side(self):
        owner = make_user("ada")
        profile = owner.profile
        profile.show_email = False
        profile.show_badges = False
        profile.show_streak = False
        profile.save()

        api(owner).patch(
            "/api/users/me/profile/", {"is_profile_public": True}, format="json"
        )
        mine = api(owner).get(f"/api/users/{owner.pk}/").json()
        assert mine["email"] == "ada@example.com"
        assert mine["badge_count"] == 0
        assert mine["is_self"] is True

        stranger = api(make_user("nia")).get(f"/api/users/{owner.pk}/").json()
        assert stranger["email"] is None
        assert stranger["badge_count"] is None
        assert stranger["current_streak"] is None

    def test_private_profile_hides_everything_but_identity_from_others(self):
        owner = make_user("ada")
        owner.profile.is_profile_public = False
        owner.profile.save(update_fields=["is_profile_public"])
        body = api(make_user("nia")).get(f"/api/users/{owner.pk}/").json()
        assert set(body) <= {"id", "user_id", "username", "display_name", "avatar_url", "joined_at", "is_private"}

    def test_badge_list_follows_the_same_flag(self):
        owner = make_user("ada")
        owner.profile.show_badges = False
        owner.profile.save(update_fields=["show_badges"])
        stranger = api(make_user("nia")).get(f"/api/users/{owner.pk}/badges/").json()
        assert stranger == {"badges": [], "count": 0, "hidden": True}
        assert api(owner).get(f"/api/users/{owner.pk}/badges/").json()["hidden"] is False

    def test_display_name_change_persists(self):
        user = make_user("ada")
        response = api(user).patch("/api/auth/me/", {"display_name": "Ada L."}, format="json")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.display_name == "Ada L."

    def test_changing_email_requires_reverification(self):
        user = make_user("ada")
        response = api(user).patch("/api/auth/me/", {"email": "ada2@example.com"}, format="json")
        assert response.status_code == 200, response.data
        user.refresh_from_db()
        assert user.email == "ada2@example.com"
        assert user.is_email_verified is False

    def test_another_members_email_is_refused_not_a_500(self):
        make_user("nia")
        response = api(make_user("ada")).patch("/api/auth/me/", {"email": "NIA@example.com"}, format="json")
        assert response.status_code == 400
        assert "email" in response.data


class TestFollowAndDirectory:
    def test_follow_is_a_toggle_and_not_open_to_yourself(self):
        ada, nia = make_user("ada"), make_user("nia")
        client = api(ada)
        assert client.post(f"/api/users/{nia.pk}/follow/", {}, format="json").json()["following"] is True
        assert client.post(f"/api/users/{nia.pk}/follow/", {}, format="json").json()["following"] is False
        assert client.post(f"/api/users/{ada.pk}/follow/", {}, format="json").status_code == 400

    def test_directory_ranks_by_real_xp_and_searches(self):
        ada, nia = make_user("ada"), make_user("nia")
        nia.profile.total_xp = 500
        nia.profile.save(update_fields=["total_xp"])
        client = api(ada)
        assert client.get("/api/users/").json()["results"][0]["username"] == "nia"
        assert [row["username"] for row in client.get("/api/users/?search=ad").json()["results"]] == ["ada"]

    def test_anonymous_callers_cannot_list_members(self):
        assert api().get("/api/users/").status_code == 401


class TestRolePermissions:
    def test_learner_cannot_change_roles(self):
        target = make_user("nia")
        response = api(make_user("ada")).patch(f"/api/users/{target.pk}/role/", {"role": "admin"}, format="json")
        assert response.status_code == 403
        target.refresh_from_db()
        assert target.role == "learner"

    def test_admin_can_change_role_and_bad_role_is_rejected(self):
        admin = User.objects.create_superuser(email="root@example.com", username="root", password=PASSWORD)
        target = make_user("nia")
        client = api(admin)
        assert client.patch(f"/api/users/{target.pk}/role/", {"role": "mentor"}, format="json").status_code == 200
        target.refresh_from_db()
        assert target.role == "mentor"
        assert client.patch(f"/api/users/{target.pk}/role/", {"role": "wizard"}, format="json").status_code == 400
        assert client.patch(f"/api/users/{target.pk}/role/", {"is_active": False}, format="json").status_code == 200
        target.refresh_from_db()
        assert target.is_active is False

    def test_superuser_gets_the_admin_role_and_a_profile(self):
        admin = User.objects.create_superuser(email="root@example.com", username="root", password=PASSWORD)
        assert admin.role == "admin" and admin.is_staff and admin.is_admin
        assert Profile.objects.filter(user=admin).exists()


class TestDjangoAdminAccount:
    def test_users_created_in_the_admin_get_a_profile_row(self):
        """The admin's creation form saves through ModelForm, bypassing UserManager."""
        from apps.users.admin import CustomUserAdmin, UserCreationForm

        admin = User.objects.create_superuser(email="root@example.com", username="root", password=PASSWORD)
        request = RequestFactory().post("/django-admin/auth/user/add/")
        request.user = admin

        form = UserCreationForm(
            data={
                "email": "managed@example.com",
                "username": "managed",
                "display_name": "Managed",
                "role": "learner",
                "password1": PASSWORD,
                "password2": PASSWORD,
            }
        )
        assert form.is_valid(), form.errors

        created = form.save(commit=False)
        CustomUserAdmin(User, django_admin.site).save_model(request, created, form, change=False)

        assert Profile.objects.filter(user=created).exists()
        assert created.check_password(PASSWORD)
