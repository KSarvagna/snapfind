import os
import base64
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def get_gmail_service():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def send_email(service):

    message = EmailMessage()

    message["To"] = "saisarvagnak@gmail.com"
    message["Subject"] = "SnapFind Gmail Test"

    message.set_content(
        """Hello! 👋

This is a test email from SnapFind.

Gmail integration is working! 🔎
"""
    )

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    send_message = {
        "raw": encoded_message
    }

    service.users().messages().send(
        userId="me",
        body=send_message
    ).execute()

    print("✅ Email sent successfully!")


service = get_gmail_service()
send_email(service)