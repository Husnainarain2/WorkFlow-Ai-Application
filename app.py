import os
import streamlit as st
import sqlite3
import json
from groq import Groq

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Workflow AI",
    page_icon="",
    layout="wide"
)

# =========================
# CUSTOM UI (MODERN DARK UI)
# =========================
st.markdown("""
<style>

/* Background */
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0b1220;
}

/* Chat bubbles */
.user-bubble {
    background: #2563eb;
    padding: 12px;
    border-radius: 12px;
    margin: 8px 0;
    max-width: 70%;
    margin-left: auto;
    color: white;
    font-size: 15px;
}

.ai-bubble {
    background: #1e293b;
    padding: 12px;
    border-radius: 12px;
    margin: 8px 0;
    max-width: 70%;
    color: white;
    font-size: 15px;
}

/* Title */
h1 {
    color: #60a5fa;
}

</style>
""", unsafe_allow_html=True)

# =========================
# API KEY (STREAMLIT SECRETS)
# =========================
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("❌ Add GROQ_API_KEY in Streamlit Secrets")
    st.stop()

client = Groq(api_key=api_key)

# =========================
# DATABASE (SQLite)
# =========================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS chats (
    username TEXT,
    messages TEXT
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

# =========================
# AUTH SYSTEM
# =========================
def auth():
    st.title("Workflow AI Login")

    tab1, tab2 = st.tabs(["🔐 Login", "🆕 Signup"])

    # LOGIN
    with tab1:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")

        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
            if c.fetchone():
                st.session_state.user = u

                # load chat
                c.execute("SELECT messages FROM chats WHERE username=?", (u,))
                data = c.fetchone()

                if data:
                    st.session_state.messages = json.loads(data[0])
                else:
                    st.session_state.messages = []

                st.rerun()
            else:
                st.error("❌ Invalid login")

    # SIGNUP
    with tab2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")

        if st.button("Create Account"):
            try:
                c.execute("INSERT INTO users VALUES (?,?)", (nu, np))
                conn.commit()
                st.success("Account created ✔")
            except:
                st.error("User already exists")

# =========================
# RUN AUTH
# =========================
if not st.session_state.user:
    auth()
    st.stop()

# =========================
# AI FUNCTION
# =========================
def ask_ai(messages):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )
    return response.choices[0].message.content

# =========================
# SAVE CHAT
# =========================
def save_chat():
    c.execute("DELETE FROM chats WHERE username=?", (st.session_state.user,))
    c.execute(
        "INSERT INTO chats VALUES (?,?)",
        (st.session_state.user, json.dumps(st.session_state.messages))
    )
    conn.commit()

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header(f"👤 {st.session_state.user}")

    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        save_chat()
        st.rerun()

    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.messages = []
        st.rerun()

# =========================
# TITLE
# =========================
st.title("🚀 Workflow AI SaaS Chat")

# =========================
# SHOW CHAT
# =========================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-bubble'>🧑 {msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-bubble'>🤖 {msg['content']}</div>", unsafe_allow_html=True)

# =========================
# INPUT
# =========================
user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("Thinking..."):
        reply = ask_ai(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    save_chat()
    st.rerun()
