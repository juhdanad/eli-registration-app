from django.urls import path
from django.contrib.auth.views import LogoutView

from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("login/", views.LoginView.as_view(), name="login"),
    path(
        "register-visitor/",
        views.RegisterVisitorView.as_view(),
        name="register-visitor",
    ),
    path(
        "register-client/",
        views.RegisterClientView.as_view(),
        name="register-client",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "password-change/", views.PasswordChangeView.as_view(), name="password-change"
    ),
    path("register-orcid/", views.RegisterOrcidView.as_view(), name="register-orcid"),
    path(
        "administration/users/", views.AdminUserList.as_view(), name="admin-user-list"
    ),
    path(
        "administration/users/<int:id>/edit/",
        views.AdminUserEditView.as_view(),
        name="admin-user-edit",
    ),
    path(
        "administration/users/<int:id>/details/",
        views.AdminUserDetailsView.as_view(),
        name="admin-user-details",
    ),
    path(
        "profile/",
        views.UserProfileView.as_view(),
        name="user-profile",
    ),
    path(
        "profile/edit/",
        views.UserProfileEditView.as_view(),
        name="user-profile-edit",
    ),
]
