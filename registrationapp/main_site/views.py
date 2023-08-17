from typing import Any, Dict
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import BadRequest, ObjectDoesNotExist, PermissionDenied
from django.forms.forms import BaseForm
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import resolve_url, redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView, DetailView, TemplateView, FormView, View
from django.views.generic.list import ListView
from urllib.parse import urlencode
import requests
from .forms import (
    VisitorRegistrationForm,
    ClientRegistrationForm,
    VisitorProfileEditForm,
    ClientProfileEditForm,
    VisitorEditForm,
    ClientEditForm,
)
from .mail import (
    send_registration_initiated_email,
    send_registration_state_change_email,
)
from .models import UserData, RegistrationState, RegistrationType
from . import orcid


def get_home_url(user):
    if user.is_authenticated:
        if user.is_admin:
            return resolve_url("admin-user-list")
        else:
            return resolve_url("user-profile")
    return resolve_url("home")


class AnonymousUserRequiredMixin:
    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(get_home_url(request.user))
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(AccessMixin):
    permission_denied_message = "Only admins are permitted to use this function!"

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class UserDataRequiredMixin(AccessMixin):
    permission_denied_message = (
        "Only registering users are permitted to use this function!"
    )

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        has_userdata = False
        try:
            if request.user.is_authenticated and request.user.userdata:
                has_userdata = True
        except ObjectDoesNotExist:
            pass
        if not has_userdata:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class PermissionDeniedWithRedirect(PermissionDenied):
    def __init__(self, redirect: str, message: str, *args: object):
        super().__init__(*args)
        self.redirect = redirect
        self.message = message


class PermissionDeniedWithRedirectMixin:
    def dispatch(self, request: HttpRequest, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDeniedWithRedirect as ex:
            messages.error(request, ex.message)
            return redirect(ex.redirect)


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = "Bearer " + self.token
        return r


class HomeView(AnonymousUserRequiredMixin, TemplateView):
    template_name = "main_site/home.html"


class LoginView(auth_views.LoginView):
    template_name = "main_site/login.html"

    def get_default_redirect_url(self):
        if self.next_page:
            return resolve_url(self.next_page)
        return get_home_url(self.request.user)


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "main_site/password_change.html"

    def get_success_url(self):
        return get_home_url(self.request.user)

    def form_valid(self, form) -> HttpResponse:
        result = super().form_valid(form)
        messages.success(self.request, "Password changed successfully!")
        return result

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            user_home_url=get_home_url(self.request.user), **kwargs
        )


class RegisterVisitorView(FormView):
    template_name = "main_site/register_visitor.html"
    form_class = VisitorRegistrationForm
    success_url = reverse_lazy("login")
    action: str | None
    orcid_data: orcid.PublicOrcidData | None

    def setup(self, request: HttpRequest, *args, **kwargs):
        self.orcid_data = orcid.PublicOrcidData.from_session(request.session)
        return super().setup(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs):
        self.action = request.POST.get("action")
        if self.action == "remove_orcid":
            orcid.PublicOrcidData.delete_from_session(request.session)
            self.orcid_data = None
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: ClientRegistrationForm) -> HttpResponse:
        if self.action != "register":
            return self.render_to_response(self.get_context_data(form=form))
        if self.orcid_data is not None:
            form.instance.orcid_id = self.orcid_data.orcid
        user_data = form.save()
        orcid.PublicOrcidData.delete_from_session(self.request.session)
        self.orcid_data = None
        messages.success(self.request, "The account has been created successfully!")
        send_registration_initiated_email(user_data)
        return super().form_valid(form)

    def get_form(self, form_class=None) -> BaseForm:
        form = super().get_form(form_class)
        if self.orcid_data is not None:
            form.fields["email"].initial = self.orcid_data.email
            form.fields["name"].initial = self.orcid_data.name
        return form

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            orcid_data=self.orcid_data,
            orcid_login_url=orcid.get_orcid_oauth_url(),
            **kwargs,
        )


class RegisterClientView(FormView):
    template_name = "main_site/register_client.html"
    form_class = ClientRegistrationForm
    success_url = reverse_lazy("login")

    def form_valid(self, form: ClientRegistrationForm) -> HttpResponse:
        user_data = form.save()
        messages.success(self.request, "The account has been created successfully!")
        send_registration_initiated_email(user_data)
        return super().form_valid(form)


class RegisterOrcidView(View):
    def get(self, request: HttpRequest, *args, **kwargs):
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


class AdminUserList(AdminRequiredMixin, ListView):
    template_name = "main_site/admin_list.html"
    paginate_by = 3
    query_filters: dict

    def get_queryset(self):
        self.query_filters = {}
        filter = UserData.objects.all().order_by("-user_id")
        state_filter = self.request.GET.get("registration_state")
        if state_filter is not None:
            if state_filter not in RegistrationState:
                raise BadRequest(f"Invalid registration_state: {state_filter}")
            state = RegistrationState(state_filter)
            self.query_filters["registration_state"] = state
            filter = filter.filter(registration_state=state)
        page = self.request.GET.get("page")
        if page is not None:
            self.query_filters["page"] = int(page)
        return filter

    def get_registration_state_filters(self):
        current_registration_state = self.query_filters.get("registration_state")
        filters_copy = dict(self.query_filters)
        # remove current registration state and reset pagination
        filters_copy.pop("registration_state", None)
        filters_copy.pop("page", None)
        # add option to remove filter
        registration_state_urls = [
            {
                "label": "All",
                "url": f"?{urlencode(filters_copy)}",
                "active": current_registration_state is None,
            }
        ]
        # add option for all registration states
        for state in RegistrationState:
            filters_copy["registration_state"] = state
            registration_state_urls.append(
                {
                    "label": state.label,
                    "url": f"?{urlencode(filters_copy)}",
                    "active": current_registration_state == state,
                }
            )
        return registration_state_urls

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            query_filters_url=f"?{urlencode(self.query_filters)}",
            registration_state_filters=self.get_registration_state_filters(),
            **kwargs,
        )


class AdminUserEditView(
    AdminRequiredMixin, PermissionDeniedWithRedirectMixin, UpdateView
):
    success_url = reverse_lazy("admin-user-list")
    queryset = UserData.objects.select_related("user")
    template_name = "main_site/admin_user_edit.html"
    pk_url_kwarg = "id"
    context_object_name = "user_data"

    def get_object(self, queryset=None):
        object: UserData = super().get_object(queryset)
        if not object.is_editable_by_admin():
            raise PermissionDeniedWithRedirect(
                resolve_url("admin-user-details", id=self.kwargs["id"]),
                "You do not have permission to edit the profile!",
            )
        return object

    def get_form_class(self):
        match self.object.registration_type:
            case RegistrationType.VISITOR:
                return VisitorEditForm
            case RegistrationType.CLIENT:
                return ClientEditForm
        raise Exception("Unknown registration type!")

    def form_valid(self, form):
        match self.request.POST.get("action"):
            case "approve":
                self.object.registration_state = RegistrationState.APPROVED
            case "request_modify":
                self.object.registration_state = (
                    RegistrationState.ADMIN_REQUESTED_MODIFY
                )
            case "reject":
                self.object.registration_state = RegistrationState.REJECTED
            case _:
                raise BadRequest()
        result = super().form_valid(form)
        send_registration_state_change_email(self.object)
        messages.success(self.request, "The account has been saved successfully!")
        return result


class AdminUserDetailsView(AdminRequiredMixin, DetailView):
    queryset = UserData.objects.select_related("user")
    template_name = "main_site/admin_user_details.html"
    pk_url_kwarg = "id"
    context_object_name = "user_data"


class UserProfileView(UserDataRequiredMixin, TemplateView):
    template_name = "main_site/user_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user.userdata
        return context


class UserProfileEditView(
    UserDataRequiredMixin, PermissionDeniedWithRedirectMixin, UpdateView
):
    success_url = reverse_lazy("user-profile")
    template_name = "main_site/user_profile_edit.html"
    context_object_name = "user_data"

    def get_object(self):
        user_data: UserData = self.request.user.userdata
        if not user_data.is_editable_by_user():
            raise PermissionDeniedWithRedirect(
                "user-profile",
                "You do not have permission to edit the profile!",
            )
        return user_data

    def get_form_class(self):
        match self.object.registration_type:
            case RegistrationType.VISITOR:
                return VisitorProfileEditForm
            case RegistrationType.CLIENT:
                return ClientProfileEditForm
        raise Exception("Unknown registration type!")

    def form_valid(self, form):
        self.object.registration_state = RegistrationState.WAITING_FOR_APPROVAL
        result = super().form_valid(form)
        send_registration_state_change_email(self.object)
        messages.success(self.request, "The account has been saved successfully!")
        return result
