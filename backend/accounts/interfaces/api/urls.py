from django.urls import path

from accounts.interfaces.api.views import (
    AuditLogView,
    ChangePasswordView,
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
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("audit-log/", AuditLogView.as_view(), name="audit-log"),
]
