import os
import streamlit as st
import sqlite3
import json
import hashlib
import base64
from groq import Groq

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Workflow AI",
    page_icon="🚀",
    layout="wide"
)

# =========================
# THEME TOGGLE
# =========================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

def apply_theme():
    if st.session_state.theme == "dark":
        st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #0f172a, #1e293b); color: white; }
        section[data-testid="stSidebar"] { background-color: #0b1220; }
        .user-bubble { background: #2563eb; padding: 12px; border-radius: 12px; margin: 8px 0; max-width: 70%; margin-left: auto; color: white; font-size: 15px; }
        .ai-bubble { background: #1e293b; padding: 12px; border-radius: 12px; margin: 8px 0; max-width: 70%; color: white; font-size: 15px; }
        h1 { color: #60a5fa; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp { background: #f9fafb; color: black; }
        section[data-testid="stSidebar"] { background-color: #e5e7eb; }
        .user-bubble { background: #3b82f6; padding: 12px; border-radius: 12px; margin: 8px 0; max-width: 70%; margin-left: auto; color: white; font-size: 15px; }
        .ai-bubble { background: #d1d5db; padding: 12px; border-radius: 12px; margin: 8px 0; max-width: 70%; color: black; font-size: 15px; }
        h1 { color: #1e40af; }
        </style>
        """, unsafe_allow_html=True)

apply_theme()

# =========================
# API KEY
# =========================
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("❌ Add GROQ_API_KEY in Streamlit Secrets")
    st.stop()

client = Groq(api_key=api_key)

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS chats (
    username TEXT,
    project TEXT,
    messages TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS history (
    username TEXT,
    query TEXT
)""")

conn.commit()

# =========================
# AUTH SYSTEM
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def auth():
    st.title("Workflow AI Login")
    tab1, tab2 = st.tabs(["🔐 Login", "🆕 Signup"])

    with tab1:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hash_password(p)))
            if c.fetchone():
                st.session_state.user = u
                st.session_state.project = "default"
                load_chat()
                st.rerun()
            else:
                st.error("❌ Invalid login")

    with tab2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            try:
                c.execute("INSERT INTO users VALUES (?,?)", (nu, hash_password(np)))
                conn.commit()
                st.success("Account created ✔")
            except:
                st.error("User already exists")

if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "project" not in st.session_state:
    st.session_state.project = "default"

if not st.session_state.user:
    auth()
    st.stop()

# =========================
# CHAT FUNCTIONS
# =========================
def ask_ai(messages):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )
    return response.choices[0].message.content

def save_chat():
    c.execute("DELETE FROM chats WHERE username=? AND project=?", (st.session_state.user, st.session_state.project))
    c.execute("INSERT INTO chats VALUES (?,?,?)",
              (st.session_state.user, st.session_state.project, json.dumps(st.session_state.messages)))
    conn.commit()

def load_chat():
    c.execute("SELECT messages FROM chats WHERE username=? AND project=?", (st.session_state.user, st.session_state.project))
    data = c.fetchone()
    st.session_state.messages = json.loads(data[0]) if data else []

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header(f"👤 {st.session_state.user}")
    st.button("🌗 Toggle Theme", on_click=toggle_theme)
    new_proj = st.text_input("New Project Name")
    if st.button("➕ New Project") and new_proj:
        st.session_state.project = new_proj
        st.session_state.messages = []
        save_chat()
        st.rerun()
    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        save_chat()
        st.rerun()
    if st.button("⬇ Download Chat"):
        st.download_button("Download JSON", json.dumps(st.session_state.messages), file_name="chat.json")
        st.download_button("Download TXT", "\n".join([m["content"] for m in st.session_state.messages]), file_name="chat.txt")
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.messages = []
        st.rerun()

# =========================
# TITLE
# =========================
st.title(f"🚀 Workflow AI - {st.session_state.project}")

# =========================
# SHOW CHAT
# =========================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-bubble'>🧑 {msg['content']}</div>", unsafe_allow_html=True)
        if "image" in msg:
            st.image(base64.b64decode(msg["image"]), caption="Uploaded Image", use_column_width=True)
    else:
        st.markdown(f"<div class='ai-bubble'>🤖 {msg['content']}</div>", unsafe_allow_html=True)

# =========================
# INPUT + IMAGE UPLOAD
# =========================
col1, col2 = st.columns([3,1])
with col1:
    user_input = st.chat_input("Type your message...")
with col2:
    uploaded_file = st.file_uploader("📷 Upload Image", type=["png","jpg","jpeg"])

if uploaded_file:
    img_bytes = uploaded_file.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    st.session_state.messages.append({
        "role": "user",
        "content": f"[Image Uploaded: {uploaded_file.name}]",
        "image": img_b64
    })
    c.execute("INSERT INTO history VALUES (?,?)", (st.session_state.user, f"Image: {uploaded_file.name}"))
    conn.commit()
    save_chat()
    st.rerun()

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    c.execute("INSERT INTO history VALUES (?,?)", (st.session_state.user, user_input))
    conn.commit()

    with st.spinner("Thinking..."):
        reply = ask_ai(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    save_chat()
    st.rerun()
