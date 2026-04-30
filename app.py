import os
import sqlite3
import streamlit as st
import uuid
from groq import Groq

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Workflow AI Pro", layout="centered")

# =========================
# DB SETUP (UPDATED FOR MULTI CHAT)
# =========================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

# USERS
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

# CHAT SESSIONS (NEW)
c.execute("""
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id TEXT,
    user TEXT,
    title TEXT
)
""")

# CHAT HISTORY (UPDATED)
c.execute("""
CREATE TABLE IF NOT EXISTS chat_history (
    session_id TEXT,
    user TEXT,
    role TEXT,
    message TEXT
)
""")

conn.commit()

# =========================
# SESSION STATE
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "mode" not in st.session_state:
    st.session_state.mode = "chat"

if "stop_stream" not in st.session_state:
    st.session_state.stop_stream = False

# =========================
# AUTH (YOUR SAME CODE)
# =========================
def auth_page():
    st.title("🔐 Workflow AI Login System")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        username = st.text_input("Login Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE username=? AND password=?",
                      (username, password))
            user = c.fetchone()

            if user:
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_user = st.text_input("Create Username")
        new_pass = st.text_input("Create Password", type="password")

        if st.button("Sign Up"):
            try:
                c.execute("INSERT INTO users VALUES (?,?)",
                          (new_user, new_pass))
                conn.commit()
                st.success("Account created!")
            except:
                st.error("User already exists")

if not st.session_state.user:
    auth_page()
    st.stop()

user = st.session_state.user

# =========================
# CREATE NEW CHAT
# =========================
def new_chat():
    session_id = str(uuid.uuid4())
    st.session_state.session_id = session_id
    st.session_state.messages = []

    c.execute("INSERT INTO chat_sessions VALUES (?,?,?)",
              (session_id, user, "New Chat"))
    conn.commit()

# first chat
if not st.session_state.session_id:
    new_chat()

# =========================
# LOAD CHAT HISTORY
# =========================
def load_chat(session_id):
    c.execute("""
        SELECT role, message FROM chat_history
        WHERE session_id=? AND user=?
        ORDER BY rowid ASC
    """, (session_id, user))
    rows = c.fetchall()

    st.session_state.messages = [
        {"role": r, "content": m} for r, m in rows
    ]

# =========================
# API
# =========================
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

def ask_ai_stream(messages):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        stream=True
    )

    full_response = ""
    box = st.empty()

    for chunk in response:
        if st.session_state.stop_stream:
            break

        if chunk.choices[0].delta.content:
            full_response += chunk.choices[0].delta.content
            box.markdown(full_response)

    return full_response

# =========================
# SIDEBAR (🔥 NEW CHAT HISTORY)
# =========================
st.sidebar.title(f"⚙️ Workflow AI ({user})")

if st.sidebar.button("➕ New Chat"):
    new_chat()
    st.rerun()

st.sidebar.markdown("### 📜 Chat History")

c.execute("SELECT session_id, title FROM chat_sessions WHERE user=?", (user,))
sessions = c.fetchall()

for sid, title in sessions[::-1]:
    if st.sidebar.button(title or "Chat", key=sid):
        st.session_state.session_id = sid
        load_chat(sid)
        st.rerun()

# logout
if st.sidebar.button("🚪 Logout"):
    st.session_state.user = None
    st.session_state.messages = []
    st.session_state.session_id = None
    st.rerun()

# =========================
# UI TITLE
# =========================
st.title("🤖 ChatGPT Style AI Pro (Multi Chat)")

# =========================
# SHOW CHAT
# =========================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =========================
# CHAT INPUT
# =========================
user_input = st.chat_input("Message AI...")

if user_input:

    st.session_state.messages.append({"role": "user", "content": user_input})

    c.execute("""
        INSERT INTO chat_history VALUES (?,?,?,?)
    """, (st.session_state.session_id, user, "user", user_input))
    conn.commit()

    with st.chat_message("assistant"):
        reply = ask_ai_stream(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    c.execute("""
        INSERT INTO chat_history VALUES (?,?,?,?)
    """, (st.session_state.session_id, user, "assistant", reply))
    conn.commit()

# =========================
# TOOLS (UNCHANGED)
# =========================
if st.session_state.mode == "email":
    st.subheader("📧 Email Generator")

if st.session_state.mode == "report":
    st.subheader("📊 Report Generator")

if st.session_state.mode == "summary":
    st.subheader("📝 Summarizer")

st.session_state.stop_stream = False
