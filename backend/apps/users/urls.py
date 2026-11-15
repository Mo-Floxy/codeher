from django.urls import path

from apps.users import views

urlpatterns = [
    path("me/profile/", views.MyProfileView.as_view(), name="my-profile"),
    path("", views.UserDirectoryView.as_view(), name="user-directory"),
    path("<int:pk>/", views.PublicUserView.as_view(), name="public-profile"),
    path("<int:pk>/badges/", views.UserBadgesView.as_view(), name="user-badges"),
    path("<int:pk>/follow/", views.UserFollowView.as_view(), name="user-follow"),
    path("<int:pk>/role/", views.AdminRoleUpdateView.as_view(), name="admin-user-role"),
]
