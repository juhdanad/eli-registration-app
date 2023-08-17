from django import forms
from .models import UserData, RegistrationType, UserType
from django.contrib.auth.forms import UserCreationForm


class VisitorRegistrationForm(UserCreationForm, forms.ModelForm):
    class Meta:
        model = UserData
        fields = ["email", "name", "phone_number"]
        widgets = {
            "password": forms.PasswordInput,
        }

    def clean(self):
        self.instance.user_type = UserType.VISITOR
        self.instance.registration_type = RegistrationType.VISITOR
        return super().clean()


class ClientRegistrationForm(UserCreationForm, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].required = True
        self.fields["country_of_origin"].required = True

    class Meta:
        model = UserData
        fields = [
            "email",
            "name",
            "phone_number",
            "company",
            "country_of_origin",
        ]
        widgets = {
            "password": forms.PasswordInput,
        }

    def clean(self):
        self.instance.user_type = UserType.CLIENT
        self.instance.registration_type = RegistrationType.CLIENT
        return super().clean()


class VisitorProfileEditForm(forms.ModelForm):
    """Form for editing own profile information."""

    class Meta:
        model = UserData
        fields = ["email", "name", "phone_number"]


class ClientProfileEditForm(forms.ModelForm):
    """Form for editing own profile information."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].required = True
        self.fields["country_of_origin"].required = True

    class Meta:
        model = UserData
        fields = [
            "email",
            "name",
            "phone_number",
            "company",
            "country_of_origin",
        ]


class VisitorEditForm(forms.ModelForm):
    """This is the form for admins."""

    class Meta:
        model = UserData
        fields = [
            "orcid_id_comment",
            "name_comment",
            "email_comment",
            "phone_number_comment",
        ]
        widgets = {
            "orcid_id_comment": forms.Textarea(attrs={"rows": 2}),
            "name_comment": forms.Textarea(attrs={"rows": 2}),
            "email_comment": forms.Textarea(attrs={"rows": 2}),
            "phone_number_comment": forms.Textarea(attrs={"rows": 2}),
        }


class ClientEditForm(forms.ModelForm):
    """This is the form for admins."""

    class Meta:
        model = UserData
        fields = [
            "name_comment",
            "email_comment",
            "phone_number_comment",
            "company_comment",
            "country_of_origin_comment",
        ]
        widgets = {
            "name_comment": forms.Textarea(attrs={"rows": 2}),
            "email_comment": forms.Textarea(attrs={"rows": 2}),
            "phone_number_comment": forms.Textarea(attrs={"rows": 2}),
            "company_comment": forms.Textarea(attrs={"rows": 2}),
            "country_of_origin_comment": forms.Textarea(attrs={"rows": 2}),
        }
