from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

from apps.users.models import Follow, Profile

User = get_user_model()


class UserCreationForm(BaseUserCreationForm):
    # USERNAME_FIELD is email; the stock creation form is bound to a username identifier.
    # Meta.model must target the swapped custom user explicitly.
    class Meta:
        model = User
        fields = ("email", "username", "display_name", "role")


class UserChangeForm(BaseUserChangeForm):
    class Meta:
        model = User
        fields = ("email", "username", "display_name", "role")


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    verbose_name_plural = "profile"


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    inlines = [ProfileInline]

    list_display = ("email", "username", "display_name", "role", "is_staff", "is_active", "is_email_verified",
                    "date_joined")
    list_filter = ("role", "is_staff", "is_active", "is_email_verified", "groups")
    search_fields = ("email", "username", "display_name")
    ordering = ("-date_joined",)
    readonly_fields = ("last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "username", "display_name", "role", "password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "username", "display_name", "role", "password1", "password2")}),
        ("Permissions", {"classes": ("collapse",), "fields": ("is_active", "is_staff", "is_superuser",
                                                              "groups", "user_permissions")}),
    )
    filter_horizontal = ("groups", "user_permissions")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # The admin creation form saves through ModelForm, so UserManager.create_user
        # — the only place a Profile row is normally made — never runs. Without this,
        # an admin-added account has no gamification or visibility row at all.
        Profile.objects.get_or_create(user=obj)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user_email", "skill_level", "total_xp", "level", "current_streak", "is_profile_public")
    list_filter = ("skill_level", "is_profile_public", "show_email", "show_projects")
    search_fields = ("user__email", "user__display_name", "headline", "bio", "country")
    list_select_related = ("user",)
    ordering = ("-total_xp",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="user", ordering="user__email")
    def user_email(self, obj):
        return obj.user.email


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower_email", "following_email", "created_at")
    search_fields = ("follower__email", "following__email")
    list_select_related = ("follower", "following")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="follower", ordering="follower__email")
    def follower_email(self, obj):
        return obj.follower.email

    @admin.display(description="following", ordering="following__email")
    def following_email(self, obj):
        return obj.following.email
