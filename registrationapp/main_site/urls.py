from django.urls import path
from django.contrib.auth.views import LogoutView

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("mail/", views.mail, name="mail"),
    path("login/", views.MainSiteLoginView.as_view(), name="login"),
    path(
        "register-visitor/",
        views.visitor_registration,
        name="register-visitor",
    ),
    path(
        "register-client/",
        views.client_registration,
        name="register-client",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register-orcid/", views.orcid_registration, name="register-orcid"),
]
