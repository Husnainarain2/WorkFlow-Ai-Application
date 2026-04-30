import os, sqlite3, json, hashlib
import streamlit as st
from groq import Groq

# =========================
# API KEY
# =========================
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("❌ Add GROQ_API_KEY in Streamlit Secrets")
    st.stop()
client = Groq(api_key=api_key)

# =========================
# DB SETUP
# =========================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS history (username TEXT, query TEXT)")
conn.commit()

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Workflow AI", layout="centered")

# =========================
# THEME HANDLING
# =========================
if "theme" not in st.session_state:
    st.session_state.theme = "light"  # default

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

def apply_theme():
    if st.session_state.theme == "dark":
        st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg,#0f172a,#1e293b); color:white; }
        .stChatMessage { background-color:#1e293b; color:white; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp { background:#f9fafb; color:black; }
        .stChatMessage { background-color:#e5e7eb; color:black; }
        </style>
        """, unsafe_allow_html=True)

apply_theme()

# =========================
# UI
# =========================
st.title("🚀 Workflow AI Chat")

# =========================
# CHAT HISTORY
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user" not in st.session_state:
    st.session_state.user = "guest"

# =========================
# SHOW CHAT
# =========================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =========================
# FUNCTION
# =========================
def ask_ai(messages):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )
    return response.choices[0].message.content

# =========================
# INPUT
# =========================
user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Save query to history DB
    c.execute("INSERT INTO history VALUES (?,?)", (st.session_state.user, user_input))
    conn.commit()

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = ask_ai(st.session_state.messages)
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# =========================
# SIDEBAR
# =========================
if st.sidebar.button("🗑 Clear Chat"):
    st.session_state.messages = []
    st.rerun()

if st.sidebar.button("🌗 Toggle Theme"):
    toggle_theme()
    st.rerun()

# --- Download Chat ---
st.sidebar.subheader("⬇ Download Chat")
if st.session_state.messages:
    st.sidebar.download_button(
        label="Download JSON",
        data=json.dumps(st.session_state.messages, indent=2),
        file_name="chat_history.json",
        mime="application/json"
    )
    st.sidebar.download_button(
        label="Download TXT",
        data="\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages]),
        file_name="chat_history.txt",
        mime="text/plain"
    )

# --- Show History ---
st.sidebar.subheader("🔎 Search History")
c.execute("SELECT query FROM history WHERE username=?", (st.session_state.user,))
rows = c.fetchall()
for i, r in enumerate(rows[-10:]):
    if st.sidebar.button(r[0], key=f"hist_{i}"):
        st.session_state.messages.append({"role": "user", "content": r[0]})
        with st.chat_message("user"):
            st.markdown(r[0])
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = ask_ai(st.session_state.messages)
                st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
