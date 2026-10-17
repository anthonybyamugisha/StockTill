from django.urls import path

from accounts.interfaces.api.views import UserListCreateView

urlpatterns = [
    path("users/", UserListCreateView.as_view(), name="user-list-create"),
]
