from django import forms
from .models import UserData, User, RegistrationType


class BasicUserRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "password"]
        widgets = {
            "password": forms.PasswordInput,
        }

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email address is already registered.")
        return email


class VisitorRegistrationForm(forms.ModelForm):
    class Meta:
        model = UserData
        fields = ["name", "phone_number"]

    def clean(self):
        self.instance.registration_type = RegistrationType.VISITOR
        return super().clean()


class ClientRegistrationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].required = True
        self.fields["country_of_origin"].required = True

    class Meta:
        model = UserData
        fields = ["name", "phone_number", "company", "country_of_origin"]

    def clean(self):
        self.instance.registration_type = RegistrationType.CLIENT
        return super().clean()
