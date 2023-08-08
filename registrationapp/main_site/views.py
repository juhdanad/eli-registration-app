from django.shortcuts import render
from django.http import HttpResponse
from django.core.mail import send_mail
from .forms import LoginForm


def index(request):
    context = {"form": LoginForm()}
    return render(request, "main_site/index.html", context)


def mail(request):
    send_mail(
        "Test subject",
        "Test message.",
        "admin@localhost",
        ["test@example.com"],
        fail_silently=False,
    )
    return HttpResponse("Hello, world! Sent email.")
