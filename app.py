import os
import sqlite3
import streamlit as st
from groq import Groq

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Workflow AI Pro", layout="centered")

# =========================
# LOGIN SYSTEM (ADDED)
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

def login_page():
    st.title("🔐 Login to Workflow AI")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username:
            st.session_state.user = username
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Enter username")

# If not logged in → show login page ONLY
if not st.session_state.user:
    login_page()
    st.stop()

user = st.session_state.user

# =========================
# API KEY
# =========================
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Add GROQ_API_KEY in Streamlit Secrets")
    st.stop()

client = Groq(api_key=api_key)

# =========================
# DB SETUP (FULL HISTORY FIX)
# =========================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS chat_history (
    user TEXT,
    role TEXT,
    message TEXT
)
""")
conn.commit()

# =========================
# SESSION STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "mode" not in st.session_state:
    st.session_state.mode = "chat"

if "stop_stream" not in st.session_state:
    st.session_state.stop_stream = False

# =========================
# LOAD HISTORY (NOW USER-BASED)
# =========================
def load_history():
    c.execute("SELECT role, message FROM chat_history WHERE user=?", (user,))
    rows = c.fetchall()
    st.session_state.messages = [
        {"role": r, "content": m} for r, m in rows
    ]

if len(st.session_state.messages) == 0:
    load_history()

# =========================
# STREAMING AI
# =========================
def ask_ai_stream(messages):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        stream=True
    )

    full_response = ""
    placeholder = st.empty()

    for chunk in response:
        if st.session_state.stop_stream:
            break

        if chunk.choices[0].delta.content:
            full_response += chunk.choices[0].delta.content
            placeholder.markdown(full_response)

    return full_response

# =========================
# SIDEBAR NAVIGATION
# =========================
st.sidebar.title(f"⚙️ Workflow AI ({user})")

# 🔴 Logout (ADDED)
if st.sidebar.button("🚪 Logout"):
    st.session_state.user = None
    st.session_state.messages = []
    st.rerun()

if st.sidebar.button("💬 Chat"):
    st.session_state.mode = "chat"

if st.sidebar.button("📧 Email"):
    st.session_state.mode = "email"

if st.sidebar.button("📊 Report"):
    st.session_state.mode = "report"

if st.sidebar.button("📝 Summarizer"):
    st.session_state.mode = "summary"

if st.sidebar.button("🧹 Clear Chat"):
    st.session_state.messages = []
    c.execute("DELETE FROM chat_history WHERE user=?", (user,))
    conn.commit()
    st.rerun()

# =========================
# HEADER
# =========================
st.title("🤖 ChatGPT Style AI Pro")

# =========================
# SHOW CHAT
# =========================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =========================
# STOP BUTTON
# =========================
if st.button("⛔ Stop Generating"):
    st.session_state.stop_stream = True

# =========================
# CHAT INPUT
# =========================
user_input = st.chat_input("Message AI...")

if user_input:

    st.session_state.stop_stream = False

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    c.execute(
        "INSERT INTO chat_history VALUES (?,?,?)",
        (user, "user", user_input)
    )
    conn.commit()

    with st.chat_message("assistant"):
        reply = ask_ai_stream(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    c.execute(
        "INSERT INTO chat_history VALUES (?,?,?)",
        (user, "assistant", reply)
    )
    conn.commit()

# =========================
# EMAIL TOOL
# =========================
if st.session_state.mode == "email":
    st.subheader("📧 Email Generator")

    subject = st.text_input("Subject")
    body = st.text_area("Body")

    if st.button("Generate Email"):
        result = ask_ai_stream([
            {"role": "system", "content": "Write professional email"},
            {"role": "user", "content": f"{subject}\n{body}"}
        ])
        st.write(result)

# =========================
# REPORT TOOL
# =========================
if st.session_state.mode == "report":
    st.subheader("📊 Report Generator")

    topic = st.text_input("Topic")

    if st.button("Generate Report"):
        result = ask_ai_stream([
            {"role": "system", "content": "Write structured report"},
            {"role": "user", "content": topic}
        ])
        st.write(result)

# =========================
# SUMMARY TOOL
# =========================
if st.session_state.mode == "summary":
    st.subheader("📝 Summarizer")

    text = st.text_area("Paste text")

    if st.button("Summarize"):
        result = ask_ai_stream([
            {"role": "system", "content": "Summarize in bullet points"},
            {"role": "user", "content": text}
        ])
        st.write(result)

# reset stop flag
st.session_state.stop_stream = False
