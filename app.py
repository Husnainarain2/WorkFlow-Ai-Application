import os
import sqlite3
import streamlit as st
from groq import Groq

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Workflow AI SaaS", layout="wide")

# =========================
# API KEY
# =========================
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Add GROQ_API_KEY in Streamlit Secrets")
    st.stop()

client = Groq(api_key=api_key)

# =========================
# DB
# =========================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS history (username TEXT, query TEXT)")
conn.commit()

# =========================
# SESSION STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "page" not in st.session_state:
    st.session_state.page = "chat"

# =========================
# AI FUNCTION
# =========================
def ask_ai(messages):
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )
    return res.choices[0].message.content

# =========================
# PREMIUM CSS (SAAS STYLE)
# =========================
st.markdown("""
<style>

.stApp {
    background: #f6f7fb;
    font-family: Inter, sans-serif;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: white;
    border-right: 1px solid #eee;
}

/* Buttons */
.stButton>button {
    width: 100%;
    border-radius: 10px;
    padding: 10px;
    background: #4f46e5;
    color: white;
    border: none;
}

.stButton>button:hover {
    background: #3730a3;
}

/* Chat bubbles */
[data-testid="stChatMessage-user"] {
    background: #4f46e5;
    color: white;
    border-radius: 12px;
    padding: 10px;
}

[data-testid="stChatMessage-assistant"] {
    background: #ffffff;
    border: 1px solid #eee;
    border-radius: 12px;
    padding: 10px;
}

/* Header */
.saas-header {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 10px;
}

/* Cards */
.card {
    background: white;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR NAVIGATION
# =========================
st.sidebar.title("⚙️ Workflow AI")

if st.sidebar.button("💬 Chat"):
    st.session_state.page = "chat"

if st.sidebar.button("📧 Email Generator"):
    st.session_state.page = "email"

if st.sidebar.button("📊 Report Generator"):
    st.session_state.page = "report"

if st.sidebar.button("📝 Summarizer"):
    st.session_state.page = "summary"

if st.sidebar.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# =========================
# HEADER
# =========================
st.markdown('<div class="saas-header">🚀 Workflow AI SaaS Dashboard</div>', unsafe_allow_html=True)

# =========================
# CHAT PAGE
# =========================
if st.session_state.page == "chat":

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask anything...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = ask_ai(st.session_state.messages)
                st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

# =========================
# EMAIL PAGE
# =========================
if st.session_state.page == "email":

    st.subheader("📧 Email Generator")

    subject = st.text_input("Subject")
    body = st.text_area("Message")

    if st.button("Generate Email"):
        result = ask_ai([
            {"role": "system", "content": "Write professional email"},
            {"role": "user", "content": f"{subject}\n{body}"}
        ])
        st.markdown("### Output")
        st.write(result)

# =========================
# REPORT PAGE
# =========================
if st.session_state.page == "report":

    st.subheader("📊 Report Generator")

    topic = st.text_input("Report Topic")

    if st.button("Generate Report"):
        result = ask_ai([
            {"role": "system", "content": "Write structured report"},
            {"role": "user", "content": topic}
        ])
        st.markdown("### Report")
        st.write(result)

# =========================
# SUMMARY PAGE
# =========================
if st.session_state.page == "summary":

    st.subheader("📝 Text Summarizer")

    text = st.text_area("Paste text")

    if st.button("Summarize"):
        result = ask_ai([
            {"role": "system", "content": "Summarize in bullet points"},
            {"role": "user", "content": text}
        ])
        st.markdown("### Summary")
        st.write(result)
