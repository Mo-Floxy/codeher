"""Account, session and profile endpoints."""

import logging

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView

from apps.achievements.models import UserAchievement
from apps.community.services import toggle_follow
from apps.core.permissions import IsAdmin
from apps.users.models import Follow, User
from apps.users.serializers import (
    ForgotPasswordSerializer,
    LoginSerializer,
    MePatchSerializer,
    ProfileSerializer,
    PublicProfileSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserSerializer,
)

logger = logging.getLogger("apps.users")


def tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class EarnedBadgeSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="achievement.code")
    title = serializers.CharField(source="achievement.title")
    description = serializers.CharField(source="achievement.description")
    icon = serializers.CharField(source="achievement.icon")
    color = serializers.CharField(source="achievement.color")
    category = serializers.CharField(source="achievement.category")
    xp_reward = serializers.IntegerField(source="achievement.xp_reward")

    class Meta:
        model = UserAchievement
        fields = ["code", "title", "description", "icon", "color", "category", "xp_reward", "earned_at"]


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.save()
        except IntegrityError:
            raise ValidationError({"email": "That email is already registered."})
        return Response(
            {"user": UserSerializer(user).data, **tokens_for(user)},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response({"user": UserSerializer(user).data, **tokens_for(user)})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw = request.data.get("refresh")
        if raw:
            try:
                RefreshToken(raw).blacklist()
            except TokenError:
                # The session is dropped either way; a stale token is not an error for the caller.
                logger.info("Logout received an unusable refresh token")
        return Response({"detail": "Signed out."}, status=status.HTTP_205_RESET_CONTENT)


class TokenRefreshView(BaseTokenRefreshView):
    permission_classes = [AllowAny]


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "user": UserSerializer(request.user).data,
                "profile": ProfileSerializer(request.user.profile, context={"request": request}).data,
            }
        )

    def patch(self, request):
        serializer = MePatchSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(request.user, field, value)
        if "email" in serializer.validated_data:
            request.user.is_email_verified = False
        request.user.save()
        return Response(UserSerializer(request.user).data)


class ForgotPasswordView(APIView):
    """Answers the same way for unknown addresses so accounts cannot be enumerated.

    Development uses the console mail backend, so the reset link is also returned in
    the body — an honest fallback for an unconfigured mail server, not a fake success.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=serializer.validated_data["email"], is_active=True).first()

        detail = "If that address has an account, a reset link is on its way."
        if user is None:
            return Response({"detail": detail})

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"{settings.FRONTEND_ORIGIN.rstrip('/')}/reset-password?uid={uid}&token={token}"

        try:
            send_mail(
                subject="Reset your CodeHer password",
                message=(
                    "Use this link to choose a new password.\n\n"
                    f"{reset_url}\n\n"
                    "If you did not request this, sign in and review your security settings."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Password reset email could not be sent")
            return Response(
                {
                    "detail": "The mail server is unavailable — set EMAIL_HOST in backend/.env to send reset links.",
                    "mail_configured": False,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payload = {"detail": detail, "mail_configured": True}
        if settings.DEBUG and "console" in settings.EMAIL_BACKEND:
            payload.update(
                {
                    "mail_configured": False,
                    "reset_url": reset_url,
                    "uid": uid,
                    "token": token,
                    "detail": "No mail server is configured in development, so the reset link is returned here.",
                }
            )
        return Response(payload)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            uid = int(urlsafe_base64_decode(data["uid"]))
        except (ValueError, TypeError, OverflowError):
            uid = None

        user = User.objects.filter(pk=uid).first() if uid else None
        if user is None or not default_token_generator.check_token(user, data["token"]):
            return Response(
                {"detail": "That reset link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(data["new_password"], user)
        except DjangoValidationError as exc:
            raise ValidationError({"new_password": list(exc.messages)})

        user.set_password(data["new_password"])
        user.save(update_fields=["password"])
        logger.info("Password reset completed for user %s", user.pk)
        return Response({"detail": "Your password has been reset. Sign in with the new one."})


class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(ProfileSerializer(request.user.profile, context={"request": request}).data)

    def patch(self, request):
        profile = request.user.profile
        serializer = ProfileSerializer(profile, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request):
        return self.patch(request)


class PublicUserView(APIView):
    """Public member profile — the owner's visibility flags are honoured here."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk, is_active=True)
        return Response(PublicProfileSerializer(user.profile, context={"request": request}).data)


class UserBadgesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk, is_active=True)
        profile = user.profile
        viewer = request.user
        is_self = bool(viewer.is_authenticated and viewer.pk == pk)
        is_admin = bool(getattr(viewer, "is_admin", False))

        if not profile.show_badges and not (is_self or is_admin):
            return Response({"badges": [], "count": 0, "hidden": True})

        awards = UserAchievement.objects.filter(user=user).select_related("achievement")
        return Response({"badges": EarnedBadgeSerializer(awards, many=True).data, "count": awards.count(), "hidden": False})


class UserFollowView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk, is_active=True)
        try:
            result = toggle_follow(request.user, target)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        followers = Follow.objects.filter(following=target).count()
        return Response({"following": result["following"], "followers_count": followers})


class UserDirectoryView(APIView):
    """Member search used by the community pages, ranked by real XP."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.filter(is_active=True).select_related("profile").order_by("-profile__total_xp")
        term = request.query_params.get("search", "").strip()
        if term:
            users = users.filter(display_name__icontains=term) | users.filter(username__icontains=term)
        users = list(users[:48])
        payload = PublicProfileSerializer(users, many=True, context={"request": request}).data
        return Response({"count": len(payload), "results": payload})


class AdminRoleUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        errors = {}
        if "role" in request.data and request.data["role"] not in dict(User.ROLE_CHOICES):
            errors["role"] = "Unsupported role."
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        for field in ("role", "is_active", "display_name"):
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()
        return Response(UserSerializer(user).data)
