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

   # email 
st.sidebar.subheader("✉️ Email Tools")

if st.sidebar.button("Write Email"):
    st.session_state.email_mode = True

if "email_mode" in st.session_state and st.session_state.email_mode:
    st.subheader("Compose Email")
    subject = st.text_input("Subject")
    body = st.text_area("Body")

    if st.button("Generate Email"):
        # Here you can call your AI model to polish/summarize the email
        reply = ask_ai([
            {"role": "system", "content": "You are an assistant that writes professional emails."},
            {"role": "user", "content": f"Subject: {subject}\nBody: {body}"}
        ])
        st.write("📧 Suggested Email Draft:")
        st.markdown(reply)
st.sidebar.subheader("📄 Summarization")

if st.sidebar.button("Summarize Chat"):
    summary = ask_ai([
        {"role": "system", "content": "Summarize the following chat into key points."},
        {"role": "user", "content": "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])}
    ])
    st.write("📝 Chat Summary:")
    st.markdown(summary)

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
c.execute("SELECT rowid, query FROM history WHERE username=?", (st.session_state.user,))
rows = c.fetchall()

for i, (rowid, query) in enumerate(rows[-10:]):  # show last 10
    cols = st.sidebar.columns([3,1])  # two columns: query + delete button
    with cols[0]:
        if st.button(query, key=f"hist_{i}"):
            # Replay old query
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    reply = ask_ai(st.session_state.messages)
                    st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
    with cols[1]:
        if st.button("❌", key=f"del_{i}"):
            # Delete this single history item
            c.execute("DELETE FROM history WHERE rowid=?", (rowid,))
            conn.commit()
            st.sidebar.success(f"Deleted: {query}")
            st.rerun()

# --- Delete All History ---
if st.sidebar.button("❌ Delete All History"):
    c.execute("DELETE FROM history WHERE username=?", (st.session_state.user,))
    conn.commit()
    st.sidebar.success("All history deleted!")
    st.rerun()

