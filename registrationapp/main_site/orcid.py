from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
import requests
import logging

logger = logging.getLogger()


def find_orcid_email(orcid_email_data):
    """
    Returns the primary email address from the ORCID record's "email" field,
    or any email if the primary is not available.
    """
    for entry in orcid_email_data:
        if entry["primary"]:
            return entry["email"]
    if len(orcid_email_data) > 0:
        return orcid_email_data[0]["email"]
    return None


class PublicOrcidData:
    """
    Public data requested from ORCID. This is stored in the user's session.
    """

    def __init__(self, orcid: str, name: str, email: str | None) -> None:
        self.orcid = orcid
        self.name = name
        self.email = email

    @staticmethod
    def from_session(session: SessionBase):
        orcid = session.get("orcid")
        orcid_name = session.get("orcid_name")
        orcid_email = session.get("orcid_email")
        if orcid is None or orcid_name is None:
            return None
        return PublicOrcidData(orcid, orcid_name, orcid_email)

    @staticmethod
    def delete_from_session(session: SessionBase):
        session.pop("orcid", None)
        session.pop("orcid_name", None)
        session.pop("orcid_email", None)

    def save_to_session(self, session: SessionBase):
        session["orcid"] = self.orcid
        session["orcid_name"] = self.name
        session["orcid_email"] = self.email


def request_public_orcid_data(orcid_id: str):
    """
    Calls the public ORCID endpoint to request user data.
    """
    res = requests.get(
        f"{settings.ORCID_PUBLIC_API_URL}/v3.0/{orcid_id}/person",
        headers={"Accept": "application/json"},
    ).json()
    name = (
        f'{res["name"]["given-names"]["value"]} {res["name"]["family-name"]["value"]}'
    )
    email = find_orcid_email(res["emails"]["email"])
    return PublicOrcidData(orcid_id, name, email)


class OrcidToken:
    """
    A Bearer token for an ORCID record.
    """

    def __init__(self, orcid: str, token: str) -> None:
        self.orcid = orcid
        self.token = token


def exchange_token(code: str):
    """
    After the user has given ORCID permission to the application,
    the ORCID server responds with a one-time code. This function
    exchanges that code for a permanent token.
    """
    result: dict = requests.post(
        f"{settings.ORCID_URL}/oauth/token",
        headers={"Accept": "application/json"},
        data={
            "client_id": settings.ORCID_CLIENT_ID,
            "client_secret": settings.ORCID_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.ORCID_REDIRECT_URI,
        },
    ).json()
    error = result.get("error")
    error_description = result.get("error_description")
    if error is not None:
        logger.error(
            "Error during ORCID exchange_token: %s, %s", error, error_description
        )
    orcid = result.get("orcid")
    token = result.get("access_token")
    if orcid is None or token is None:
        return None
    return OrcidToken(orcid, token)


def get_orcid_oauth_url():
    """Returns the URL with which the user can authenticate itself in ORCID."""
    return f"{settings.ORCID_URL}/oauth/authorize?client_id={settings.ORCID_CLIENT_ID}&response_type=code&scope=/authenticate&redirect_uri={settings.ORCID_REDIRECT_URI}"
