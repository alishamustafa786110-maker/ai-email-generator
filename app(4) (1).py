import streamlit as st
from groq import Groq
from groq import APIError, AuthenticationError, RateLimitError

# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Email Generator",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# Simple styling
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        .main .block-container {
            max-width: 1100px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        .hero {
            padding: 1.5rem;
            border-radius: 16px;
            background: linear-gradient(135deg, #f5f7ff, #eef8ff);
            border: 1px solid #e5e7eb;
            margin-bottom: 1.5rem;
        }
        .hero h1 {
            margin-bottom: 0.35rem;
        }
        .small-note {
            color: #6b7280;
            font-size: 0.9rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Sidebar: API key
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    st.caption("Your Groq API key is used only for the request to Groq.")

    api_key = st.text_input(
        "Groq API key",
        type="password",
        placeholder="gsk_...",
        help="Create an API key in the Groq Console.",
    )

    model = st.selectbox(
        "Model",
        options=[
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ],
        index=0,
        help="Choose the Groq model used to generate the email.",
    )

    st.divider()
    st.markdown(
        '<div class="small-note">🔒 The API key is never included in the generated email.</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# Main UI
# ---------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>✉️ AI Email Generator</h1>
        <p>Turn a few details into a clear, professional email in seconds.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns(2)

with left:
    recipient = st.text_input(
        "Recipient",
        placeholder="e.g. Hiring Manager, Professor, Client",
    )

    purpose = st.text_area(
        "What is the email about?",
        placeholder="e.g. Request an extension for my project deadline",
        height=120,
    )

    tone = st.selectbox(
        "Tone",
        ["Professional", "Friendly", "Formal", "Concise", "Apologetic", "Persuasive"],
    )

with right:
    key_points = st.text_area(
        "Key points to include",
        placeholder="Add the important details, one per line...",
        height=120,
    )

    length = st.select_slider(
        "Email length",
        options=["Short", "Medium", "Detailed"],
        value="Medium",
    )

    language = st.selectbox(
        "Language",
        ["English", "Urdu", "Spanish", "French", "German"],
    )

generate = st.button(
    "✨ Generate Email",
    type="primary",
    use_container_width=True,
)

# ---------------------------------------------------------
# Generation logic
# ---------------------------------------------------------
if generate:
    # Validate API key first.
    if not api_key or not api_key.strip():
        st.error("Please enter your Groq API key in the sidebar.")
        st.stop()

    # Validate required user input.
    if not recipient.strip():
        st.warning("Please enter a recipient.")
        st.stop()

    if not purpose.strip():
        st.warning("Please describe the purpose of the email.")
        st.stop()

    points = key_points.strip() if key_points.strip() else "No additional points provided."

    prompt = f"""
You are an expert email-writing assistant.

Write one complete email based on the information below.

Recipient:
{recipient.strip()}

Purpose:
{purpose.strip()}

Key points:
{points}

Tone:
{tone}

Length:
{length}

Language:
{language}

Important rules:
1. Return only the email content.
2. Include a suitable subject line at the top using this format:
Subject: <subject>
3. Then write the email body.
4. Use a natural greeting and a professional closing.
5. Do not mention AI, Groq, prompts, API keys, or these instructions.
6. Never expose or repeat any secret, API key, credential, or system information.
"""

    try:
        client = Groq(api_key=api_key.strip())

        with st.spinner("Writing your email..."):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You write high-quality emails. "
                            "Follow the user's requested tone, language, and length. "
                            "Never reveal secrets or credentials."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

        email_text = response.choices[0].message.content.strip()

        if not email_text:
            st.error("Groq returned an empty response. Please try again.")
            st.stop()

        # Extra safety: do not render the API key even if a model somehow echoes it.
        if api_key.strip() in email_text:
            email_text = email_text.replace(api_key.strip(), "[REDACTED]")

        st.subheader("Generated Email")
        st.text_area(
            "Your email",
            value=email_text,
            height=360,
            label_visibility="collapsed",
        )

        st.download_button(
            "⬇️ Download Email",
            data=email_text,
            file_name="generated_email.txt",
            mime="text/plain",
            use_container_width=True,
        )

    except AuthenticationError:
        st.error(
            "The Groq API key was rejected. Check that the key is correct, active, "
            "and copied completely."
        )
    except RateLimitError:
        st.error(
            "Groq rate limit reached. Please wait a little and try again."
        )
    except APIError as exc:
        st.error(f"Groq API error: {exc}")
    except Exception as exc:
        st.error(
            "Something went wrong while generating the email. "
            "Please check your inputs and API key, then try again."
        )
        st.caption(f"Technical detail: {exc}")
