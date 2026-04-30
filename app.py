import os
import sqlite3
import json
import uuid
import streamlit as st
from groq import Groq

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Workflow AI Pro", layout="centered")

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Add GROQ_API_KEY in Secrets")
    st.stop()

client = Groq(api_key=api_key)

# =========================
# DB SETUP (MULTI CHAT)
# =========================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS chats (
    chat_id TEXT,
    user TEXT,
    title TEXT,
    messages TEXT
)
""")
conn.commit()

user = "guest"

# =========================
# SESSION STATE
# =========================
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# =========================
# LOAD ALL CHATS
# =========================
def get_chats():
    c.execute("SELECT chat_id, title FROM chats WHERE user=?", (user,))
    return c.fetchall()

def load_chat(chat_id):
    c.execute("SELECT messages FROM chats WHERE chat_id=?", (chat_id,))
    row = c.fetchone()

    if row:
        st.session_state.messages = json.loads(row[0])
        st.session_state.current_chat = chat_id

def save_chat():
    if not st.session_state.current_chat:
        return

    c.execute("""
    UPDATE chats
    SET messages=?
    WHERE chat_id=?
    """, (json.dumps(st.session_state.messages), st.session_state.current_chat))

    conn.commit()

def new_chat():
    chat_id = str(uuid.uuid4())[:8]
    title = "New Chat"

    c.execute("""
    INSERT INTO chats VALUES (?,?,?,?)
    """, (chat_id, user, title, json.dumps([])))

    conn.commit()

    st.session_state.current_chat = chat_id
    st.session_state.messages = []

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
# SIDEBAR (CHATGPT STYLE)
# =========================
st.sidebar.title("💬 Chats")

if st.sidebar.button("➕ New Chat"):
    new_chat()
    st.rerun()

chats = get_chats()

for chat_id, title in chats:
    col1, col2 = st.sidebar.columns([4, 1])

    with col1:
        if st.button(title, key=chat_id):
            load_chat(chat_id)
            st.rerun()

    with col2:
        if st.button("🗑", key=f"del_{chat_id}"):
            c.execute("DELETE FROM chats WHERE chat_id=?", (chat_id,))
            conn.commit()
            st.rerun()

# =========================
# MAIN UI
# =========================
st.title("🤖 ChatGPT Pro Clone (Multi Chat)")

if not st.session_state.current_chat:
    st.info("Click ➕ New Chat to start")
    st.stop()

# =========================
# SHOW MESSAGES
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

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        reply = ask_ai_stream(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    # auto-save
    save_chat()

# =========================
# AUTO TITLE UPDATE
# =========================
def update_title():
    if len(st.session_state.messages) == 2:
        first = st.session_state.messages[0]["content"]
        c.execute("UPDATE chats SET title=? WHERE chat_id=?",
                  (first[:25], st.session_state.current_chat))
        conn.commit()

update_title()
