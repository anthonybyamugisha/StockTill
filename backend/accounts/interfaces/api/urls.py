from django.urls import path

from accounts.interfaces.api.views import (
    CurrentUserView,
    LoginView,
    LogoutView,
    UserDetailView,
    UserListCreateView,
)

urlpatterns = [
    path("users/", UserListCreateView.as_view(), name="user-list-create"),
    path("users/<uuid:user_id>/", UserDetailView.as_view(), name="user-detail"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
]
