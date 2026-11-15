from rest_framework.permissions import SAFE_METHODS, BasePermission


def role_of(user):
    if not user or not user.is_authenticated:
        return "anonymous"
    return getattr(user, "role", "learner")


class IsAdmin(BasePermission):
    """Platform administrators only."""

    message = "Administrator access is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (role_of(user) == "admin" or user.is_staff))


class IsMentor(BasePermission):
    message = "Mentor access is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and role_of(user) in {"mentor", "admin"})


class IsAuthenticatedOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or (
            request.user and request.user.is_authenticated and not request.user.is_anonymous
        )


class IsOwnerOrAdmin(BasePermission):
    """Object-level check: `user`/`owner`/`author` field names are all honoured."""

    message = "You can modify only your own content."

    OWNER_FIELDS = ("user", "owner", "author", "member")

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if role_of(user) == "admin" or user.is_staff:
            return True
        for field in self.OWNER_FIELDS:
            owner = getattr(obj, field, None)
            if owner is not None and owner == user:
                return True
        return False


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
