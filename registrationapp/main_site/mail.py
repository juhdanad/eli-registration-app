from django.core.mail import send_mail
from django.template.loader import render_to_string
import logging
from .models import UserData, RegistrationState

logger = logging.getLogger()


def send_noncritical_mail(*args, **kwargs):
    """
    Used for sending emails where failure should not generate
    an internal server error for users.
    Email errors are logged instead.
    """
    try:
        send_mail(*args, **kwargs)
    except OSError as e:
        logger.error(f"Error during sending email: {e}")


def send_registration_state_change_email(user: UserData):
    context = {"user_data": user}
    send_noncritical_mail(
        render_to_string(
            "main_site/email/user_registration_state_changed.subject.txt",
            context,
        ),
        render_to_string(
            "main_site/email/user_registration_state_changed.txt",
            context,
        ),
        from_email=None,
        recipient_list=[user.email],
    )


def send_registration_initiated_email(user: UserData):
    context = {"user_data": user}
    send_noncritical_mail(
        render_to_string(
            "main_site/email/user_registration_initiated.subject.txt",
            context,
        ),
        render_to_string(
            "main_site/email/user_registration_initiated.txt",
            context,
        ),
        from_email=None,
        recipient_list=[user.email],
    )
