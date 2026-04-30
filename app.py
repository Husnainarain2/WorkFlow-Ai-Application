import os
import sqlite3
import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
from groq import Groq

# =========================
# FIREBASE INIT
# =========================
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Workflow AI Pro", layout="centered")

# =========================
# GROQ API
# =========================
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

# =========================
# DB
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
if "user" not in st.session_state:
    st.session_state.user = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# =========================
# AUTH UI
# =========================
def auth_page():

    st.title("🔐 Login / Signup / Google Auth")

    tab1, tab2, tab3 = st.tabs(["Login", "Sign Up", "Google Login"])

    # ---------------- LOGIN ----------------
    with tab1:
        email = st.text_input("Login Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            try:
                user = auth.get_user_by_email(email)
                st.session_state.user = email
                st.success("Login successful")
                st.rerun()
            except:
                st.error("User not found")

    # ---------------- SIGNUP ----------------
    with tab2:
        email = st.text_input("Signup Email")
        password = st.text_input("Password", type="password")

        if st.button("Create Account"):
            try:
                auth.create_user(email=email, password=password)
                st.success("Account created! Now login")
            except:
                st.error("Error creating account")

    # ---------------- GOOGLE LOGIN ----------------
    with tab3:
        st.info("Use Firebase Google Sign-In (frontend redirect required)")
        st.markdown("👉 Enable Google login in Firebase Auth")

        if st.button("Continue with Google"):
            st.warning("Use Firebase hosted auth or redirect flow for full Google OAuth")
            st.info("After setup, user will auto-login here")

# =========================
# CHECK LOGIN
# =========================
if not st.session_state.user:
    auth_page()
    st.stop()

user = st.session_state.user

# =========================
# LOAD HISTORY (USER BASED)
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
# AI STREAM
# =========================
def ask_ai_stream(messages):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        stream=True
    )

    full = ""
    box = st.empty()

    for chunk in response:
        if chunk.choices[0].delta.content:
            full += chunk.choices[0].delta.content
            box.markdown(full)

    return full

# =========================
# SIDEBAR
# =========================
st.sidebar.title(f"👤 {user}")

if st.sidebar.button("🚪 Logout"):
    st.session_state.user = None
    st.session_state.messages = []
    st.rerun()

if st.sidebar.button("🧹 Clear Chat"):
    st.session_state.messages = []
    c.execute("DELETE FROM chat_history WHERE user=?", (user,))
    conn.commit()
    st.rerun()

# =========================
# UI
# =========================
st.title("🤖 Workflow AI Pro (Full SaaS Auth)")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =========================
# CHAT INPUT
# =========================
user_input = st.chat_input("Ask AI...")

if user_input:

    st.session_state.messages.append({"role": "user", "content": user_input})

    c.execute("INSERT INTO chat_history VALUES (?,?,?)",
              (user, "user", user_input))
    conn.commit()

    with st.chat_message("assistant"):
        reply = ask_ai_stream(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    c.execute("INSERT INTO chat_history VALUES (?,?,?)",
              (user, "assistant", reply))
    conn.commit()
