import os
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st
from dotenv import load_dotenv


load_dotenv()

st.set_page_config(
    page_title="Letterly — thoughtful emails, faster",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600&display=swap');
    :root { --ink:#202a28; --muted:#75817c; --green:#316c58; --line:#e7ebe7; --paper:#fbfcfa; }
    .stApp { background:var(--paper); color:var(--ink); font-family:'DM Sans',sans-serif; }
    [data-testid="stHeader"] { background:transparent; }
    .block-container { max-width:1120px; padding-top:2rem; padding-bottom:4rem; }
    .brand { font-size:17px; font-weight:700; letter-spacing:-.5px; color:#244f40; }
    .brand span { color:#9caa9f; font-weight:400; }
    .hero { padding:55px 0 29px; text-align:center; }
    .eyebrow { color:var(--green); font-weight:700; letter-spacing:2px; font-size:11px; text-transform:uppercase; }
    .hero h1 { font-family:'Playfair Display',serif; font-size:clamp(38px,5vw,58px); font-weight:500; letter-spacing:-1.8px; line-height:1.12; margin:12px 0; color:var(--ink); }
    .hero p { color:var(--muted); font-size:16px; margin:0 auto; max-width:550px; }
    div[data-testid="stTabs"] button { font-weight:600; }
    div[data-testid="stTabs"] [aria-selected="true"] { color:var(--green); }
    .panel { background:white; border:1px solid var(--line); border-radius:18px; padding:25px 27px; }
    .section-title { font-size:14px; font-weight:700; margin:2px 0 14px; }
    .hint { color:var(--muted); font-size:13px; margin-top:-9px; margin-bottom:14px; }
    .result-title { font-family:'Playfair Display',serif; font-size:24px; font-weight:500; margin:0 0 4px; }
    .result-sub { color:var(--muted); font-size:13px; margin:0 0 19px; }
    .stButton > button[kind="primary"] { background:#316c58; border:0; border-radius:10px; padding:.65rem 1rem; font-weight:700; }
    .stButton > button[kind="primary"]:hover { background:#255744; border:0; }
    div[data-baseweb="select"] > div, textarea, input { border-radius:10px !important; }
    .footer { text-align:center; color:#929c97; font-size:12px; margin-top:35px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def build_prompt(task: str, text: str, tone: str, context: str = "") -> str:
    return f"""You are an expert writing assistant. Create a clear, natural, professional email.
Task: {task}
Desired tone: {tone}
Additional context: {context or 'None provided'}
User's notes or source email:
<user_text>
{text}
</user_text>

Follow the user's intent and preserve all important facts. Do not invent dates, promises, names, or reasons. For a reply, respond to the source email directly. Make the wording concise and human. Return exactly this format, with no markdown fences:
Subject: a suitable subject line
---BODY---
the complete email body"""


def generate_email(task: str, text: str, tone: str, context: str = "") -> tuple[str, str]:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip().rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "smollm2:1.7b-instruct-q4_0").strip()
    request_data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": build_prompt(task, text, tone, context)}],
        "stream": False,
    }).encode("utf-8")
    request = Request(
        f"{base_url}/api/chat",
        data=request_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        raise RuntimeError(
            "Could not connect to Ollama. Make sure Ollama is running and OLLAMA_BASE_URL is correct."
        ) from exc
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        if exc.code == 404:
            raise RuntimeError(f"Ollama could not find model '{model}'. Pull it with: ollama pull {model}") from exc
        raise RuntimeError(f"Ollama returned an error ({exc.code}): {details}") from exc
    result = payload.get("message", {}).get("content", "").strip()
    if not result:
        raise RuntimeError("The model returned an empty response. Please try again.")
    subject_match = re.search(r"^Subject:\s*(.+)$", result, re.MULTILINE | re.IGNORECASE)
    subject = subject_match.group(1).strip() if subject_match else ""
    body = result.split("---BODY---", 1)[-1].strip() if "---BODY---" in result else result
    body = re.sub(r"^Subject:.*(?:\n|$)", "", body, count=1, flags=re.IGNORECASE).strip()
    return subject, body


st.markdown('<div class="brand">letterly <span>✳</span></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero"><div class="eyebrow">A little help finding the right words</div>'
    '<h1>Good emails start<br>with a thought.</h1>'
    '<p>Tell us what you need to say. We’ll help you say it with clarity and care.</p></div>',
    unsafe_allow_html=True,
)

write_tab, reply_tab, polish_tab = st.tabs(["✦  Write an email", "↩  Reply to an email", "✎  Improve my writing"])

with write_tab:
    left, right = st.columns([1.04, .96], gap="large")
    with left:
        st.markdown('<div class="section-title">What would you like to say?</div>', unsafe_allow_html=True)
        description = st.text_area("Describe your email", placeholder="I need to ask my professor for an extension on an assignment because I’ve been sick this week…", height=190, label_visibility="collapsed", key="write_description")
        a, b = st.columns(2)
        with a:
            tone = st.selectbox("Tone", ["Professional", "Friendly", "Formal", "Apologetic"], key="write_tone")
        with b:
            context = st.text_input("Optional details", placeholder="Recipient, deadline, sign-off…", key="write_context")
        make = st.button("✦  Generate email", type="primary", use_container_width=True, key="write_button")
        if make:
            if not description.strip():
                st.warning("Add a few notes about what you want to say first.")
            else:
                with st.spinner("Finding the right words…"):
                    try:
                        st.session_state["email_subject"], st.session_state["email_body"] = generate_email("Write a new email", description.strip(), tone, context.strip())
                        st.session_state["email_ready"] = True
                    except Exception as exc:
                        st.error(str(exc))
    with right:
        st.markdown('<div class="panel"><div class="result-title">Your draft</div><p class="result-sub">Your email will appear here, ready for a final touch.</p>', unsafe_allow_html=True)
        if st.session_state.get("email_ready"):
            st.text_input("Subject", key="email_subject", label_visibility="collapsed", placeholder="Subject")
            st.text_area("Email body", key="email_body", label_visibility="collapsed", height=238)
            st.caption("Click into either field to edit, then select and copy your draft.")
        else:
            st.markdown('<div style="height:265px;display:grid;place-items:center;border:1px dashed #dce3dd;border-radius:12px;color:#99a49e;text-align:center;font-size:14px">✉️<br>Made for the message you have in mind</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

with reply_tab:
    st.markdown('<div class="panel"><div class="section-title">Paste the email you received</div><p class="hint">We’ll draft a thoughtful reply that addresses the message.</p>', unsafe_allow_html=True)
    original = st.text_area("Original email", placeholder="Paste the email you’d like to reply to…", height=180, label_visibility="collapsed", key="reply_source")
    c1, c2, c3 = st.columns([1, 1, 1.3])
    with c1: reply_tone = st.selectbox("Reply tone", ["Professional", "Friendly", "Formal", "Apologetic"], key="reply_tone")
    with c2: reply_context = st.text_input("Your response", placeholder="Key points to include…", key="reply_context")
    with c3:
        st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
        reply_button = st.button("↩  Draft my reply", type="primary", use_container_width=True, key="reply_button")
    if reply_button:
        if not original.strip():
            st.warning("Paste the email you want to reply to first.")
        else:
            with st.spinner("Writing a thoughtful reply…"):
                try:
                    st.session_state["reply_subject"], st.session_state["reply_body"] = generate_email("Reply to the email below", original.strip(), reply_tone, reply_context.strip())
                    st.session_state["reply_ready"] = True
                except Exception as exc: st.error(str(exc))
    if st.session_state.get("reply_ready"):
        st.markdown('<div class="section-title" style="margin-top:24px">Your reply</div>', unsafe_allow_html=True)
        st.text_input("Reply subject", key="reply_subject")
        st.text_area("Reply body", key="reply_body", height=220)
        st.caption("Select and copy your reply. You can edit it here first.")
    st.markdown("</div>", unsafe_allow_html=True)

with polish_tab:
    st.markdown('<div class="panel"><div class="section-title">Make your words work better</div><p class="hint">Fix grammar, smooth out a sentence, or make a message easier to read.</p>', unsafe_allow_html=True)
    draft = st.text_area("Text to improve", placeholder="Paste a sentence or email you’d like us to improve…", height=180, label_visibility="collapsed", key="polish_source")
    p1, p2 = st.columns([1, 2])
    with p1: polish_tone = st.selectbox("Writing style", ["Keep my style", "Professional", "Friendly", "Formal", "Apologetic"], key="polish_tone")
    with p2:
        st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
        polish_button = st.button("✎  Improve writing", type="primary", use_container_width=True, key="polish_button")
    if polish_button:
        if not draft.strip(): st.warning("Paste the text you’d like to improve first.")
        else:
            with st.spinner("Polishing your words…"):
                try:
                    _, st.session_state["polished_text"] = generate_email("Correct grammar and improve the supplied writing while preserving its meaning. Return only the revised text as the body.", draft.strip(), polish_tone)
                    st.session_state["polish_ready"] = True
                except Exception as exc: st.error(str(exc))
    if st.session_state.get("polish_ready"):
        st.markdown('<div class="section-title" style="margin-top:24px">Improved version</div>', unsafe_allow_html=True)
        st.text_area("Improved text", key="polished_text", height=200)
        st.caption("Edit if you like, then select and copy the improved version.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="footer">Thoughtful words, made a little easier. Always review your draft before sending.</div>', unsafe_allow_html=True)
