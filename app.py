import os
import sqlite3
import uuid
import streamlit as st
from groq import Groq

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Workflow AI Pro", layout="centered")

# =========================
# API KEY
# =========================
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Add GROQ_API_KEY in Streamlit Secrets")
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
    role TEXT,
    message TEXT
)
""")
conn.commit()

# =========================
# SESSION STATE
# =========================
user = "guest"

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "mode" not in st.session_state:
    st.session_state.mode = "chat"

if "stop_stream" not in st.session_state:
    st.session_state.stop_stream = False

# =========================
# CHAT MANAGEMENT
# =========================
def new_chat():
    chat_id = str(uuid.uuid4())[:8]
    st.session_state.chat_id = chat_id
    st.session_state.messages = []

def load_chat(chat_id):
    c.execute("""
        SELECT role, message FROM chats
        WHERE chat_id=? AND user=?
    """, (chat_id, user))

    rows = c.fetchall()
    st.session_state.chat_id = chat_id
    st.session_state.messages = [
        {"role": r, "content": m} for r, m in rows
    ]

def save_message(role, message):
    if not st.session_state.chat_id:
        return

    c.execute("""
        INSERT INTO chats VALUES (?,?,?,?)
    """, (st.session_state.chat_id, user, role, message))
    conn.commit()

def get_all_chats():
    c.execute("""
        SELECT DISTINCT chat_id FROM chats WHERE user=?
    """, (user,))
    return [i[0] for i in c.fetchall()]

# =========================
# STREAMING AI
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
        if st.session_state.stop_stream:
            break

        if chunk.choices[0].delta.content:
            full += chunk.choices[0].delta.content
            box.markdown(full)

    return full

# =========================
# SIDEBAR (CHAT LIST)
# =========================
st.sidebar.title("💬 Chats")

if st.sidebar.button("➕ New Chat"):
    new_chat()
    st.rerun()

chat_list = get_all_chats()

for cid in chat_list:
    if st.sidebar.button(f"Chat {cid}"):
        load_chat(cid)
        st.rerun()

if st.sidebar.button("🧹 Clear Current Chat"):
    if st.session_state.chat_id:
        c.execute("DELETE FROM chats WHERE chat_id=?", (st.session_state.chat_id,))
        conn.commit()
    st.session_state.messages = []
    st.rerun()

# =========================
# HEADER
# =========================
st.title("🤖 Workflow AI Pro (Multi Chat)")

if not st.session_state.chat_id:
    st.info("Click ➕ New Chat to start")
    st.stop()

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

    # USER MESSAGE
    st.session_state.messages.append({"role": "user", "content": user_input})
    save_message("user", user_input)

    with st.chat_message("user"):
        st.markdown(user_input)

    # AI RESPONSE
    with st.chat_message("assistant"):
        reply = ask_ai_stream(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    save_message("assistant", reply)

# =========================
# TOOLS (UNCHANGED)
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

if st.session_state.mode == "report":
    st.subheader("📊 Report Generator")

    topic = st.text_input("Topic")

    if st.button("Generate Report"):
        result = ask_ai_stream([
            {"role": "system", "content": "Write structured report"},
            {"role": "user", "content": topic}
        ])
        st.write(result)

if st.session_state.mode == "summary":
    st.subheader("📝 Summarizer")

    text = st.text_area("Paste text")

    if st.button("Summarize"):
        result = ask_ai_stream([
            {"role": "system", "content": "Summarize in bullet points"},
            {"role": "user", "content": text}
        ])
        st.write(result)

# reset
st.session_state.stop_stream = False
