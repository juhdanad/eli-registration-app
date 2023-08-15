from django.shortcuts import render, resolve_url, redirect
from django.http import HttpResponse
from django.core.mail import send_mail
from .forms import (
    BasicUserRegistrationForm,
    VisitorRegistrationForm,
    ClientRegistrationForm,
)
from django.contrib.auth.views import LoginView
from .models import User, UserData
from django.contrib import messages
from django.conf import settings
from django.http import HttpRequest
import requests
from . import orcid


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = "Bearer " + self.token
        return r


def home(request: HttpRequest):
    return render(request, "main_site/home.html")


def mail(request):
    send_mail(
        "Test subject",
        "Test message.",
        "admin@localhost",
        ["test@example.com"],
        fail_silently=False,
    )
    return HttpResponse("Hello, world! Sent email.")


class MainSiteLoginView(LoginView):
    def get_default_redirect_url(self):
        """Return the default redirect URL."""
        if self.next_page:
            return resolve_url(self.next_page)
        elif self.request.user.is_staff:
            return resolve_url("admin-list")
        else:
            return resolve_url("user-view")


def visitor_registration(request: HttpRequest):
    user_form = BasicUserRegistrationForm(request.POST or None)
    visitor_form = VisitorRegistrationForm(request.POST or None)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "register" and user_form.is_valid() and visitor_form.is_valid():
            user_data: UserData = visitor_form.save(commit=False)
            orcid_data = orcid.PublicOrcidData.from_session(request.session)
            if orcid_data is not None:
                user_data.orcid_id = orcid_data.orcid
            User.objects.create_with_userdata(
                user_form.cleaned_data["email"],
                user_form.cleaned_data["password"],
                user_data=user_data,
            )
            orcid.PublicOrcidData.delete_from_session(request.session)
            messages.success(request, "The account has been created successfully!")
            return redirect("login")
        if action == "remove_orcid":
            orcid.PublicOrcidData.delete_from_session(request.session)
    # reload ORCID data because it could just have been deleted
    orcid_data = orcid.PublicOrcidData.from_session(request.session)
    if orcid_data is not None:
        user_form.fields["email"].initial = orcid_data.email
        visitor_form.fields["name"].initial = orcid_data.name
    return render(
        request,
        "main_site/register_visitor.html",
        {
            "user_form": user_form,
            "visitor_form": visitor_form,
            "orcid_data": orcid_data,
            "orcid_login_url": orcid.get_orcid_oauth_url(),
        },
    )


def client_registration(request: HttpRequest):
    user_form = BasicUserRegistrationForm(request.POST or None)
    client_form = ClientRegistrationForm(request.POST or None)

    if request.method == "POST":
        if user_form.is_valid() and client_form.is_valid():
            user_data = client_form.save(commit=False)
            User.objects.create_with_userdata(
                user_form.cleaned_data["email"],
                user_form.cleaned_data["password"],
                user_data=user_data,
            )
            messages.success(request, "The account has been created successfully!")
            return redirect("login")
    return render(
        request,
        "main_site/register_client.html",
        {"user_form": user_form, "client_form": client_form},
    )


def orcid_registration(request: HttpRequest):
    code = request.GET.get("code")
    token = None
    if code is not None:
        token = orcid.exchange_token(code)
    if token is None:
        messages.error(request, "Could not authorize the ORCID login!")
    else:
        data = orcid.request_public_orcid_data(token.orcid)
        data.save_to_session(request.session)
    return redirect("register-visitor")
