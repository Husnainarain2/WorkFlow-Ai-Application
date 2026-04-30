import os
import sqlite3
import streamlit as st
from groq import Groq

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="AI Assistant", layout="wide")

# =========================
# API KEY
# =========================
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Add GROQ_API_KEY in Streamlit Secrets")
    st.stop()

client = Groq(api_key=api_key)

# =========================
# DB (HISTORY + MEMORY)
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

c.execute("""
CREATE TABLE IF NOT EXISTS user_memory (
    user TEXT PRIMARY KEY,
    memory TEXT
)
""")

conn.commit()

# =========================
# SESSION STATE
# =========================
if "user" not in st.session_state:
    st.session_state.user = "guest"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "theme" not in st.session_state:
    st.session_state.theme = "light"

# =========================
# THEME TOGGLE
# =========================
def apply_theme():
    if st.session_state.theme == "dark":
        st.markdown("""
        <style>
        .stApp { background:#0f172a; color:white; }
        .stChatMessage { background:#1e293b; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp { background:#f6f7fb; color:black; }
        .stChatMessage { background:white; }
        </style>
        """, unsafe_allow_html=True)

apply_theme()

# =========================
# MEMORY FUNCTIONS
# =========================
def get_memory(user):
    c.execute("SELECT memory FROM user_memory WHERE user=?", (user,))
    row = c.fetchone()
    return row[0] if row else ""

def update_memory(user, text):
    c.execute("""
        INSERT INTO user_memory(user, memory)
        VALUES(?, ?)
        ON CONFLICT(user) DO UPDATE SET memory=excluded.memory
    """, (user, text))
    conn.commit()

# =========================
# AI FUNCTION (WITH MEMORY)
# =========================
def ask_ai(messages, memory=""):
    system_prompt = f"""
You are a helpful AI assistant.

User memory:
{memory}
"""

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=full_messages
    )
    return res.choices[0].message.content

# =========================
# SIDEBAR (CHATGPT STYLE)
# =========================
with st.sidebar:
    st.title("⚙️ Controls")

    if st.button("💬 Chat"):
        st.session_state.page = "chat"

    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    # THEME TOGGLE
    if st.button("🌓 Toggle Theme"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()

# default page
if "page" not in st.session_state:
    st.session_state.page = "chat"

# =========================
# HEADER
# =========================
st.title("🤖 ChatGPT Style AI Assistant")

# =========================
# LOAD MEMORY
# =========================
memory = get_memory(st.session_state.user)

# =========================
# CHAT PAGE
# =========================
if st.session_state.page == "chat":

    # show chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Message AI...")

    if user_input:

        st.session_state.messages.append({"role": "user", "content": user_input})

        # save history
        c.execute("INSERT INTO chat_history VALUES (?,?,?)",
                  (st.session_state.user, "user", user_input))
        conn.commit()

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = ask_ai(st.session_state.messages, memory)
                st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

        # =========================
        # UPDATE MEMORY (SMART SUMMARY)
        # =========================
        if len(st.session_state.messages) % 6 == 0:
            mem = ask_ai([
                {"role": "system", "content": "Summarize user preferences in 1-2 lines."},
                {"role": "user", "content": str(st.session_state.messages[-6:])}
            ])

            update_memory(st.session_state.user, mem)

# =========================
# MEMORY DISPLAY (OPTIONAL DEBUG)
# =========================
with st.expander("🧠 AI Memory (User Profile)"):
    st.write(memory if memory else "No memory yet.")
