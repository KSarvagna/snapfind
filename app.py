import os
import base64
from email.message import EmailMessage

import streamlit as st

from google import genai
from google.genai import types
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE, SUMMARY_PROMPT


# -----------------------------
# GEMINI
# -----------------------------

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

MODEL_NAME = "gemini-3.5-flash"


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


# -----------------------------
# GMAIL
# -----------------------------

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


@st.cache_resource
def get_gmail_service():

    creds = None

    # Use existing login if available
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    # Login if needed
    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        # Save login for future use
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build(
        "gmail",
        "v1",
        credentials=creds
    )


# -----------------------------
# SEND EMAIL
# -----------------------------

def send_email(to_email, user_name, summary):

    try:

        message = EmailMessage()

        message["To"] = to_email
        message["Subject"] = "🔎 Your SnapFind Shopping Summary"

        message.set_content(
            f"""Hi {user_name}! 👋

Here is your SnapFind shopping summary:

{summary}

Thanks for using SnapFind! 🔎

Snap it. Find it. Compare it.
"""
        )

        encoded_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        body = {
            "raw": encoded_message
        }

        service = get_gmail_service()

        result = service.users().messages().send(
            userId="me",
            body=body
        ).execute()

        return True, result.get("id")

    except Exception as error:

        return False, str(error)


# -----------------------------
# GEMINI CHAT
# -----------------------------

def render_message(message):

    with st.chat_message(message["role"]):

        if message["kind"] == "text":
            st.write(message["content"])

        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):

    st.session_state.messages.append(
        {
            "role": role,
            "kind": kind,
            "content": content
        }
    )

    render_message(
        st.session_state.messages[-1]
    )


def ask_gemini(parts):

    try:

        return st.session_state.chat.send_message(
            parts
        ).text

    except Exception as error:

        return f"Sorry, something went wrong: {error}"


# -----------------------------
# ONBOARDING
# -----------------------------

if "onboarded" not in st.session_state:

    st.title("🔎 SnapFind")

    st.caption(
        "Snap it. Find it. Compare it."
    )

    with st.form("onboarding_form"):

        name = st.text_input(
            "Your name"
        )

        email = st.text_input(
            "Email address",
            placeholder="you@gmail.com",
            help="We'll send your SnapFind shopping summary here."
        )

        submitted = st.form_submit_button(
            "Let's explore!!"
        )

    if submitted:

        if not name.strip() or not email.strip():

            st.warning(
                "Please enter your name and email."
            )

        else:

            st.session_state.name = name.strip()

            st.session_state.email = email.strip()

            # Start Gemini chat
            st.session_state.chat = gemini_client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT
                ),
            )

            st.session_state.messages = []

            st.session_state.onboarded = True

            st.rerun()

    st.stop()


# -----------------------------
# HEADER
# -----------------------------

header_col, button_col = st.columns(
    [5, 2],
    vertical_alignment="center"
)


with header_col:

    st.title("🔎 SnapFind")


with button_col:

    send_disabled = (
        len(st.session_state.messages) <= 1
    )

    if st.button(
        "📧 Send to Gmail",
        disabled=send_disabled
    ):

        with st.spinner(
            "Summarizing your discovery..."
        ):

            summary = ask_gemini(
                [SUMMARY_PROMPT]
            )

            success, info = send_email(
                st.session_state.email,
                st.session_state.name,
                summary
            )

            if success:

                st.success(
                    "Sent! Check your Gmail 📧"
                )

            else:

                st.error(
                    f"Couldn't send the email: {info}"
                )


# -----------------------------
# USER INFO
# -----------------------------

st.caption(
    f"🔐 Logged in as {st.session_state.name} "
    f"— summaries go to {st.session_state.email}"
)


# -----------------------------
# CHAT HISTORY
# -----------------------------

if not st.session_state.messages:

    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE
    )

else:

    for message in st.session_state.messages:

        render_message(message)


# -----------------------------
# CHAT INPUT
# -----------------------------

user_input = st.chat_input(
    "Ask a question, or attach a photo",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)


if user_input:

    photo = (
        user_input.files[0]
        if user_input.files
        else None
    )

    text = user_input.text

    parts = []


    # IMAGE
    if photo is not None:

        photo_bytes = photo.getvalue()

        add_message(
            "user",
            "image",
            photo_bytes
        )

        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type
            )
        )


    # TEXT
    if text:

        add_message(
            "user",
            "text",
            text
        )

        parts.append(text)


    # IMAGE ONLY
    elif photo is not None:

        parts.append(
            """
            Analyze this product image.

            Identify what product is shown, including:

            - brand
            - product type
            - model
            - color
            - material
            - style
            - visible identifying features

            Tell me whether you can confidently identify
            the product or only provide a likely match.

            Do not invent information.
            """
        )


        # GEMINI RESPONSE
    with st.spinner(
        "🔎 Analyzing your product..."
    ):

        answer = ask_gemini(parts)


    add_message(
        "assistant",
        "text",
        answer
    )

    st.rerun()


