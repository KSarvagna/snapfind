# 🔎 SnapFind

> **Snap it. Find it. Compare it.**

SnapFind is an AI-powered visual shopping assistant built with **Streamlit** and **Google Gemini**.

Upload a photo of a product you see in the real world—such as clothing, furniture, gadgets, accessories, or home decor—and SnapFind uses Gemini's vision capabilities to analyze what is shown and explain the product in simple language.

After your discovery, SnapFind can generate a concise shopping summary and send it to your **Gmail** using the Gmail API.

---

## ✨ Features

- 📸 **Image upload** — Upload JPG, JPEG, or PNG product photos.
- 🤖 **AI product analysis** — Gemini analyzes the uploaded image.
- 🔎 **Product identification** — Identifies visible product type, brand, model, color, material, style, and distinguishing features when possible.
- 🎯 **Match confidence** — Separates confident identification from likely or uncertain matches.
- 💬 **Follow-up chat** — Ask Gemini questions about the product after the image analysis.
- 💰 **Shopping guidance** — Discuss similar or potentially cheaper alternatives based on the information available in the conversation.
- 📧 **Gmail summaries** — Generate a shopping summary and send it to the user's email.
- 🔐 **OAuth authentication** — Gmail sending uses Google's OAuth flow instead of storing a Gmail password.

---

## 🧠 How It Works

```text
User
  │
  ▼
📸 Upload Product Image
  │
  ▼
Streamlit Interface
  │
  ▼
Google Gemini Vision
  │
  ├── Product identification
  ├── Visible details
  ├── Match confidence
  └── Shopping discussion
  │
  ▼
📝 Generate Shopping Summary
  │
  ▼
📧 Gmail API
  │
  ▼
User's Inbox
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Web interface |
| Google Gemini | Vision analysis and conversational AI |
| Gmail API | Sending shopping summaries |
| Google OAuth 2.0 | Secure Gmail authorization |
| Git & GitHub | Version control |

---

## 📁 Project Structure

```text
snapfind/
│
├── app.py              # Main Streamlit application
├── prompts.py          # Gemini system, welcome, and summary prompts
├── requirements.txt    # Python dependencies
├── test_gemini.py      # Gemini API test
├── test_gmail.py       # Gmail API test
├── .gitignore          # Protects local secrets and generated files
│
└── .streamlit/
    └── secrets.toml    # Local API key configuration (not committed)
```

---

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/KSarvagna/snapfind.git
cd snapfind
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Gemini

Create:

```text
.streamlit/secrets.toml
```

Add your Gemini API key:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
```

**Never commit this file to GitHub.**

### 5. Configure Gmail

SnapFind uses the Gmail API with Google OAuth 2.0 to send shopping summaries.

For deployment on Streamlit Community Cloud, add these values through the app's **Secrets** settings:

```toml
GEMINI_API_KEY = "your-gemini-api-key"

GOOGLE_CLIENT_ID = "your-google-client-id"
GOOGLE_CLIENT_SECRET = "your-google-client-secret"

### 6. Start SnapFind

```bash
streamlit run app.py
```

Open the local Streamlit URL shown in your terminal.

---

## 🔐 Security

SnapFind uses local files for development credentials.

The following files are intentionally excluded from GitHub:

```text
.streamlit/secrets.toml
credentials.json
token.json
venv/
```

Do **not** publish API keys, OAuth client secrets, access tokens, or refresh tokens.

If a secret is accidentally committed, revoke or rotate it immediately and remove it from the repository history.

---

## ⚠️ Current Scope

SnapFind currently focuses on **visual product understanding and AI-assisted shopping discussion**.

It does **not** perform a real-time web-wide reverse image search or guarantee an exact online product listing.

Gemini should distinguish between confirmed information and visual guesses rather than inventing brands, models, prices, or links.

---

## 🔮 Future Improvements

Possible future versions could include:

- 🌐 Real-time product/web search
- 🛒 Direct shopping links
- 💸 Live price comparison across stores
- 🎯 Stronger exact-match detection
- 📷 Better image search and product retrieval
- 🧾 Saved product discoveries
- 📱 Mobile-friendly interface
- ☁️ Secure cloud deployment

---

## 👩‍💻 Author

**KSarvagna**

Built as a hands-on AI/GenAI project combining computer vision, conversational AI, Streamlit, and Gmail integration.

---

## 📌 Project

**SnapFind — Snap it. Find it. Compare it.**

Built with ❤️ using Python, Streamlit, Gemini, and Gmail API.
