import base64
import hashlib
import hmac
import secrets
import time
from email.message import EmailMessage
from urllib.parse import urlencode
from urllib.request import Request as URLRequest
from urllib.request import urlopen

import streamlit as st

from google import genai
from google.genai import types
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE, SUMMARY_PROMPT


# =========================================================
# GEMINI
# =========================================================

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

MODEL_NAME = "gemini-3.5-flash"


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


def ask_gemini(parts):
    """
    Send a message to Gemini with retry handling
    for temporary 503 errors.
    """

    for attempt in range(4):

        try:

            response = st.session_state.chat.send_message(parts)

            if response and response.text:
                return response.text

            return "Sorry, Gemini returned an empty response."

        except Exception as error:

            error_message = str(error)

            if "503" in error_message or "UNAVAILABLE" in error_message:

                if attempt < 3:

                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue

                return (
                    "Sorry, Gemini is temporarily busy right now. "
                    "Please try again in a moment."
                )

            return f"Gemini error: {error_message}"

    return "Sorry, Gemini is temporarily unavailable."


# =========================================================
# GMAIL OAUTH
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]

# Local development redirect URI
REDIRECT_URI = "http://localhost:8501"

GOOGLE_AUTH_URL = (
    "https://accounts.google.com/o/oauth2/v2/auth"
)

GOOGLE_TOKEN_URL = (
    "https://oauth2.googleapis.com/token"
)


def load_google_client():
    """
    Load Google Web OAuth credentials from Streamlit Secrets.

    This keeps the client ID and client secret out of GitHub.
    """

    client_id = st.secrets["GOOGLE_CLIENT_ID"]

    client_secret = st.secrets["GOOGLE_CLIENT_SECRET"]

    return client_id, client_secret


def create_oauth_state():
    """
    Create a signed OAuth state value.

    The state protects the OAuth flow against CSRF attacks.
    """

    _, client_secret = load_google_client()

    nonce = secrets.token_urlsafe(32)

    signature = hmac.new(
        client_secret.encode("utf-8"),
        nonce.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return f"{nonce}.{signature}"


def verify_oauth_state(state):
    """
    Verify the signed OAuth state returned by Google.
    """

    if not state or "." not in state:
        return False

    nonce, signature = state.split(".", 1)

    _, client_secret = load_google_client()

    expected_signature = hmac.new(
        client_secret.encode("utf-8"),
        nonce.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        signature,
        expected_signature
    )


def create_google_authorization_url():
    """
    Create Google's OAuth authorization URL.
    """

    client_id, _ = load_google_client()

    state = create_oauth_state()

    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "state": state,
    }

    authorization_url = (
        GOOGLE_AUTH_URL
        + "?"
        + urlencode(params)
    )

    return authorization_url


def exchange_code_for_credentials(code):
    """
    Exchange Google's authorization code
    for access and refresh tokens.
    """

    client_id, client_secret = load_google_client()

    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    encoded_data = urlencode(data).encode("utf-8")

    request = URLRequest(
        GOOGLE_TOKEN_URL,
        data=encoded_data,
        method="POST",
        headers={
            "Content-Type":
                "application/x-www-form-urlencoded"
        },
    )

    with urlopen(request, timeout=30) as response:

        token_data = response.read().decode("utf-8")

    import json

    token_data = json.loads(token_data)

    if "error" in token_data:

        raise ValueError(
            token_data.get(
                "error_description",
                token_data["error"]
            )
        )

    if "access_token" not in token_data:

        raise ValueError(
            "Google did not return an access token."
        )

    credentials = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=GOOGLE_TOKEN_URL,
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )

    return credentials


def get_gmail_service():
    """
    Return an authenticated Gmail API service.
    """

    credentials = st.session_state.get(
        "gmail_credentials"
    )

    if credentials is None:
        return None

    try:

        if (
            credentials.expired
            and credentials.refresh_token
        ):

            credentials.refresh(Request())

            st.session_state.gmail_credentials = (
                credentials
            )

        return build(
            "gmail",
            "v1",
            credentials=credentials
        )

    except Exception:

        return None


# =========================================================
# SEND EMAIL
# =========================================================

def send_email(to_email, user_name, summary):

    try:

        service = get_gmail_service()

        if service is None:

            return (
                False,
                "Please connect your Gmail account first."
            )

        message = EmailMessage()

        message["To"] = to_email

        message["Subject"] = (
            "🔎 Your SnapFind Shopping Summary"
        )

        message.set_content(
            f"""Hi {user_name}! 👋

Here is your SnapFind shopping summary:

{summary}

Thanks for using SnapFind! 🔎

Snap it. Find it. Compare it.
"""
        )

        encoded_message = (
            base64.urlsafe_b64encode(
                message.as_bytes()
            )
            .decode()
        )

        body = {
            "raw": encoded_message
        }

        result = (
            service.users()
            .messages()
            .send(
                userId="me",
                body=body
            )
            .execute()
        )

        return True, result.get("id")

    except Exception as error:

        return False, str(error)


# =========================================================
# CHAT UI
# =========================================================

def render_message(message):

    with st.chat_message(message["role"]):

        if message["kind"] == "text":

            st.write(
                message["content"]
            )

        elif message["kind"] == "image":

            st.image(
                message["content"]
            )


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


# =========================================================
# ONBOARDING
# =========================================================

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
            help=(
                "We'll send your SnapFind "
                "shopping summary here."
            )
        )

        submitted = st.form_submit_button(
            "Let's explore!!"
        )

    if submitted:

        if (
            not name.strip()
            or not email.strip()
        ):

            st.warning(
                "Please enter your name and email."
            )

        else:

            st.session_state.name = (
                name.strip()
            )

            st.session_state.email = (
                email.strip()
            )

            st.session_state.chat = (
                gemini_client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT
                    ),
                )
            )

            st.session_state.messages = []

            st.session_state.onboarded = True

            st.rerun()

    st.stop()


# =========================================================
# GOOGLE OAUTH CALLBACK
# =========================================================

if "code" in st.query_params:

    try:

        if "error" in st.query_params:

            google_error = (
                st.query_params.get("error")
            )

            raise ValueError(
                f"Google returned: {google_error}"
            )

        code = st.query_params["code"]

        returned_state = (
            st.query_params.get("state")
        )

        if not verify_oauth_state(
            returned_state
        ):

            raise ValueError(
                "OAuth state verification failed. "
                "Please click Connect Gmail again."
            )

        credentials = (
            exchange_code_for_credentials(code)
        )

        st.session_state.gmail_credentials = (
            credentials
        )

        st.session_state.pop(
            "authorization_url",
            None
        )

        st.query_params.clear()

        st.success(
            "✅ Gmail connected successfully!"
        )

        st.rerun()

    except Exception as error:

        st.error(
            f"Google authorization failed: {error}"
        )


# =========================================================
# GMAIL AUTHENTICATION
# =========================================================

if "gmail_credentials" not in st.session_state:

    if "authorization_url" not in st.session_state:

        st.session_state.authorization_url = (
            create_google_authorization_url()
        )

    st.info(
        "📧 Connect your Google account to send summaries."
    )

    st.link_button(
        "🔐 Connect Gmail",
        st.session_state.authorization_url
    )


# =========================================================
# HEADER
# =========================================================

header_col, button_col = st.columns(
    [5, 2],
    vertical_alignment="center"
)


with header_col:

    st.title("🔎 SnapFind")


with button_col:

    send_disabled = (
        len(st.session_state.messages) <= 1
        or "gmail_credentials"
        not in st.session_state
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


# =========================================================
# USER INFO
# =========================================================

st.caption(
    f"🔐 Logged in as {st.session_state.name} "
    f"— summaries go to {st.session_state.email}"
)


# =========================================================
# CHAT HISTORY
# =========================================================

if not st.session_state.messages:

    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE
    )

else:

    for message in st.session_state.messages:

        render_message(message)


# =========================================================
# CHAT INPUT
# =========================================================

user_input = st.chat_input(
    "Ask a question, or attach a photo",
    accept_file=True,
    file_type=[
        "jpg",
        "jpeg",
        "png"
    ],
)


if user_input:

    photo = (
        user_input.files[0]
        if user_input.files
        else None
    )

    text = user_input.text

    parts = []


    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # TEXT
    # -----------------------------------------------------

    if text:

        add_message(
            "user",
            "text",
            text
        )

        parts.append(text)


    # -----------------------------------------------------
    # IMAGE ONLY
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # GEMINI RESPONSE
    # -----------------------------------------------------

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