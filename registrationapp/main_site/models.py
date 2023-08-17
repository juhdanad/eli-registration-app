from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.core.mail import send_mail
from django.db import transaction


class UserType(models.TextChoices):
    ADMIN = "admin", "Admin"
    VISITOR = "visitor", "Visitor"
    CLIENT = "client", "Client"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user: models.Model = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(force_insert=True)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("user_type", UserType.ADMIN)

        if extra_fields.get("is_admin") is not True:
            raise ValueError("Superuser must have is_admin=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        "email address",
        unique=True,
        error_messages={
            "unique": "A user with that email already exists.",
        },
    )

    is_admin = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    @property
    def is_staff(self):
        return self.is_admin

    user_type = models.CharField(
        max_length=255,
        choices=UserType.choices,
    )

    @property
    def user_type_as_enum(self):
        return UserType(self.user_type)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(user_type__in=UserType.values),
                name="user_type_check",
            ),
        ]

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def __str__(self):
        return self.email


class RegistrationType(models.TextChoices):
    VISITOR = "visitor", "Visitor"
    CLIENT = "client", "Client"


class RegistrationState(models.TextChoices):
    INITIAL = "initial", "Initial registration"
    ADMIN_REQUESTED_MODIFY = "admin_requested_modify", "Admin requested modifications"
    WAITING_FOR_APPROVAL = "waiting_for_approval", "Waiting for approval"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class UserData(User):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        parent_link=True,
    )
    registration_type = models.CharField(
        max_length=255,
        choices=RegistrationType.choices,
    )

    @property
    def registration_type_as_enum(self):
        return RegistrationType(self.registration_type)

    registration_state = models.CharField(
        max_length=255,
        choices=RegistrationState.choices,
        default=RegistrationState.INITIAL,
    )

    @property
    def registration_state_as_enum(self):
        return RegistrationState(self.registration_state)

    orcid_id = models.CharField(max_length=255, blank=True, default="")
    orcid_id_comment = models.TextField(blank=True, default="")
    name = models.CharField(max_length=255)
    name_comment = models.TextField(blank=True, default="")
    email_comment = models.TextField(blank=True, default="")
    phone_number = models.CharField(max_length=255)
    phone_number_comment = models.TextField(blank=True, default="")
    company = models.CharField(max_length=255, blank=True, default="")
    company_comment = models.TextField(blank=True, default="")
    country_of_origin = models.CharField(max_length=255, blank=True, default="")
    country_of_origin_comment = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(registration_type__in=RegistrationType.values),
                name="registration_type_check",
            ),
            models.CheckConstraint(
                check=models.Q(registration_state__in=RegistrationState.values),
                name="registration_state_check",
            ),
            models.CheckConstraint(
                check=(~models.Q(registration_type=RegistrationType.VISITOR))
                | (
                    models.Q(
                        company="",
                        company_comment="",
                        country_of_origin="",
                        country_of_origin_comment="",
                    )
                ),
                name="visitor_allowed_fields_check",
            ),
            models.CheckConstraint(
                check=(~models.Q(registration_type=RegistrationType.CLIENT))
                | (
                    models.Q(
                        ~models.Q(company=""),
                        ~models.Q(country_of_origin=""),
                        orcid_id="",
                        orcid_id_comment="",
                    )
                ),
                name="client_allowed_fields_check",
            ),
        ]

    def is_editable_by_admin(self):
        return self.registration_state in [
            RegistrationState.INITIAL,
            RegistrationState.WAITING_FOR_APPROVAL,
        ]

    def is_editable_by_user(self):
        return self.registration_state in [
            RegistrationState.ADMIN_REQUESTED_MODIFY,
            RegistrationState.APPROVED,
        ]
