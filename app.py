import os
import sqlite3
import streamlit as st
from groq import Groq

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Workflow AI Pro", layout="centered", page_icon="⚡")

# =========================
# CUSTOM CSS INJECTION (LIGHT THEME)
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

/* ─── Root Variables - Light Theme ─── */
:root {
    --bg:        #ffffff;
    --surface:   #f8f9fb;
    --card:      #ffffff;
    --border:    #e0e3e8;
    --accent:    #5b4fb3;
    --accent2:   #ff6b9d;
    --accent3:   #00b8a9;
    --text:      #1a1a1a;
    --muted:     #666666;
    --success:   #00b8a9;
    --font-head: 'Syne', sans-serif;
    --font-mono: 'DM Mono', monospace;
}

/* ─── Global Reset ─── */
html, body, [class*="css"] {
    font-family: var(--font-mono) !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* ─── Hide Streamlit Branding ─── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem !important; max-width: 780px !important; }

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

/* ─── Sidebar ─── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    padding: 1.5rem 1rem !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Sidebar title */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] .stMarkdown h1 {
    font-family: var(--font-head) !important;
    font-size: 1.1rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.05em !important;
    color: var(--accent) !important;
    margin-bottom: 1.5rem !important;
}

/* ─── Sidebar Buttons ─── */
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background: transparent !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    padding: 0.55rem 1rem !important;
    margin-bottom: 6px !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.02em !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #f0f0f0 !important;
    color: var(--accent) !important;
    border-color: var(--accent) !important;
    transform: translateX(3px) !important;
}

/* ─── Main Area Buttons ─── */
.stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    padding: 0.55rem 1.4rem !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.05em !important;
}
.stButton > button:hover {
    background: #7b6fc4 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(91, 79, 179, 0.2) !important;
}

/* ─── Text Inputs & Areas ─── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.85rem !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(91,79,179,0.1) !important;
}
.stTextInput > label,
.stTextArea > label {
    font-family: var(--font-mono) !important;
    font-size: 0.75rem !important;
    color: var(--muted) !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

/* ─── Chat Input ─── */
[data-testid="stChatInput"] {
    border-top: 1px solid var(--border) !important;
    background: var(--bg) !important;
}
[data-testid="stChatInput"] textarea {
    background: var(--card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.85rem !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(91,79,179,0.1) !important;
}

/* ─── Chat Messages ─── */
[data-testid="stChatMessage"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem 1.25rem !important;
    margin-bottom: 0.75rem !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageContent"]) {
    font-family: var(--font-mono) !important;
    font-size: 0.875rem !important;
    line-height: 1.7 !important;
}

/* User messages - accent left border */
[data-testid="stChatMessage"][data-testid*="user"] {
    border-left: 3px solid var(--accent) !important;
}

/* ─── Tabs ─── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    border-radius: 7px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    background: var(--accent) !important;
    color: #fff !important;
}

/* ─── Success / Error messages ─── */
.stSuccess {
    background: rgba(0,184,169,0.08) !important;
    border: 1px solid var(--success) !important;
    border-radius: 8px !important;
    color: #00856b !important;
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
}
.stError {
    background: rgba(255,77,77,0.08) !important;
    border: 1px solid #ff4d4d !important;
    border-radius: 8px !important;
    color: #d32f2f !important;
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
}

/* ─── Subheaders ─── */
h1, h2, h3 {
    font-family: var(--font-head) !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
    color: var(--text) !important;
}

/* ─── Select boxes ─── */
.stSelectbox > div > div > select {
    background: var(--card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* ─── Toggle Button ─── */
[key="toggle_sidebar"] {
    position: sticky !important;
    top: 0 !important;
    z-index: 999 !important;
}

[key="toggle_sidebar"] > button {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 1rem !important;
    padding: 0.6rem 0.75rem !important;
    min-width: 45px !important;
}

[key="toggle_sidebar"] > button:hover {
    background: #7b6fc4 !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# DB SETUP (USERS + CHAT)
# =========================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

# USERS TABLE
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

# CHAT TABLE
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

if "mode" not in st.session_state:
    st.session_state.mode = "chat"

if "stop_stream" not in st.session_state:
    st.session_state.stop_stream = False

if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True

# =========================
# AUTH PAGE (LOGIN + SIGNUP)
# =========================
def auth_page():
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1.5rem;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">⚡</div>
        <h1 style="
            font-family: 'Syne', sans-serif;
            font-size: 2rem;
            font-weight: 800;
            color: #1a1a1a;
            margin: 0 0 0.4rem;
            letter-spacing: -0.03em;
        ">Workflow AI Pro</h1>
        <p style="
            font-family: 'DM Mono', monospace;
            font-size: 0.78rem;
            color: #666666;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        ">Sign In to Continue</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔑 Login", "✨ Sign Up"])

    with tab1:
        username = st.text_input("Login Username", placeholder="your_username")
        password = st.text_input("Password", type="password", placeholder="••••••••")

        if st.button("Login", use_container_width=True):
            c.execute("SELECT * FROM users WHERE username=? AND password=?",
                      (username, password))
            user = c.fetchone()

            if user:
                st.session_state.user = username
                st.success("✓ Login successful!")
                st.rerun()
            else:
                st.error("✗ Invalid credentials")

    with tab2:
        new_user = st.text_input("Create Username", placeholder="new_username")
        new_pass = st.text_input("Create Password", type="password", placeholder="••••••••")

        if st.button("Sign Up", use_container_width=True):
            try:
                c.execute("INSERT INTO users VALUES (?,?)",
                          (new_user, new_pass))
                conn.commit()
                st.success("✓ Account created! Now login")
            except:
                st.error("✗ Username already exists")

# =========================
# CHECK LOGIN
# =========================
if not st.session_state.user:
    auth_page()
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
# TOGGLE BUTTON (TOP)
# =========================
col1, col2 = st.columns([1, 10])
with col1:
    if st.button("☰" if st.session_state.sidebar_open else "→", key="toggle_sidebar", help="Toggle Sidebar"):
        st.session_state.sidebar_open = not st.session_state.sidebar_open
        st.rerun()

# =========================
# SIDEBAR
# =========================
if st.session_state.sidebar_open:
    st.sidebar.markdown("""
    <div style="
        padding-bottom: 1rem;
        border-bottom: 1px solid #e0e3e8;
        margin-bottom: 1.2rem;
    ">
        <h2 style="
            font-family: 'Syne', sans-serif;
            font-size: 1rem;
            font-weight: 800;
            color: #5b4fb3;
            margin: 0 0 0.5rem;
            letter-spacing: 0.04em;
        ">⚙️ Workflow AI</h2>
        <p style="
            font-family: 'DM Mono', monospace;
            font-size: 0.72rem;
            color: #666666;
            margin: 0;
            letter-spacing: 0.04em;
        ">User: <span style="color: #5b4fb3; font-weight: 600;">{user}</span></p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("""
    <div style="
        font-family: 'DM Mono', monospace;
        font-size: 0.68rem;
        color: #666666;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 10px;
        padding-left: 4px;
        font-weight: 600;
    ">📚 Tools</div>
    """, unsafe_allow_html=True)

    # Tool buttons
    if st.sidebar.button("💬 Chat", use_container_width=True, key="btn_chat"):
        st.session_state.mode = "chat"
        st.rerun()

    if st.sidebar.button("📧 Email Generator", use_container_width=True, key="btn_email"):
        st.session_state.mode = "email"
        st.rerun()

    if st.sidebar.button("📊 Report Generator", use_container_width=True, key="btn_report"):
        st.session_state.mode = "report"
        st.rerun()

    if st.sidebar.button("📝 Summarizer", use_container_width=True, key="btn_summary"):
        st.session_state.mode = "summary"
        st.rerun()

    st.sidebar.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    st.sidebar.markdown("""
    <div style="
        font-family: 'DM Mono', monospace;
        font-size: 0.68rem;
        color: #666666;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 10px;
        padding-left: 4px;
        font-weight: 600;
    ">⚡ Actions</div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🧹 Clear Chat History", use_container_width=True, key="btn_clear"):
        st.session_state.messages = []
        c.execute("DELETE FROM chat_history WHERE user=?", (user,))
        conn.commit()
        st.success("✓ Chat history cleared")
        st.rerun()

    if st.sidebar.button("🚪 Logout", use_container_width=True, key="btn_logout"):
        st.session_state.user = None
        st.session_state.messages = []
        st.rerun()

    st.sidebar.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Model info box
    st.sidebar.markdown("""
    <div style="
        padding: 1rem;
        background: #f8f9fb;
        border: 1px solid #e0e3e8;
        border-radius: 10px;
        margin-top: 1rem;
    ">
        <div style="font-family: 'DM Mono', monospace; font-size: 0.68rem; color: #666666; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 6px; font-weight: 600;">Current Model</div>
        <div style="font-family: 'DM Mono', monospace; font-size: 0.8rem; color: #5b4fb3; font-weight: 600;">llama-3.1-8b</div>
        <div style="font-family: 'DM Mono', monospace; font-size: 0.68rem; color: #666666; margin-top: 6px;">via Groq API</div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# TITLE
# =========================
st.markdown("""
<div style="
    background: linear-gradient(135deg, #f8f9fb 0%, #ffffff 100%);
    border: 1px solid #e0e3e8;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
">
    <h1 style="
        font-family: 'Syne', sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        color: #1a1a1a;
        margin: 0 0 0.3rem;
        letter-spacing: -0.03em;
    ">🤖 ChatGPT Style AI Pro</h1>
    <p style="
        font-family: 'DM Mono', monospace;
        font-size: 0.82rem;
        color: #666666;
        margin: 0;
        letter-spacing: 0.04em;
    ">Powered by Groq & Llama 3.1</p>
</div>
""", unsafe_allow_html=True)

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

    c.execute("INSERT INTO chat_history VALUES (?,?,?)",
              (user, "user", user_input))
    conn.commit()

    with st.chat_message("assistant"):
        reply = ask_ai_stream(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    c.execute("INSERT INTO chat_history VALUES (?,?,?)",
              (user, "assistant", reply))
    conn.commit()

# =========================
# TOOLS
# =========================
if st.session_state.mode == "email":
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #fef5f7 0%, #fff9fa 100%);
        border: 1px solid #f0d5dd;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
    ">
        <h2 style="
            font-family: 'Syne', sans-serif;
            font-size: 1.3rem;
            font-weight: 800;
            color: #1a1a1a;
            margin: 0;
            letter-spacing: -0.02em;
        ">📧 Email Generator</h2>
    </div>
    """, unsafe_allow_html=True)
    
    subject = st.text_input("Subject", placeholder="e.g., Follow-up on project proposal")
    body = st.text_area("Body", placeholder="Enter email context or key points...")

    if st.button("Generate Email", use_container_width=True):
        result = ask_ai_stream([
            {"role": "system", "content": "Write professional email"},
            {"role": "user", "content": f"{subject}\n{body}"}
        ])
        st.write(result)

if st.session_state.mode == "report":
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #f0f5ff 0%, #f8faff 100%);
        border: 1px solid #d0dff7;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
    ">
        <h2 style="
            font-family: 'Syne', sans-serif;
            font-size: 1.3rem;
            font-weight: 800;
            color: #1a1a1a;
            margin: 0;
            letter-spacing: -0.02em;
        ">📊 Report Generator</h2>
    </div>
    """, unsafe_allow_html=True)
    
    topic = st.text_input("Topic", placeholder="Enter report topic or question...")

    if st.button("Generate Report", use_container_width=True):
        result = ask_ai_stream([
            {"role": "system", "content": "Write structured report"},
            {"role": "user", "content": topic}
        ])
        st.write(result)

if st.session_state.mode == "summary":
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #f0fff9 0%, #f8fffd 100%);
        border: 1px solid #d0f5ea;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
    ">
        <h2 style="
            font-family: 'Syne', sans-serif;
            font-size: 1.3rem;
            font-weight: 800;
            color: #1a1a1a;
            margin: 0;
            letter-spacing: -0.02em;
        ">📝 Summarizer</h2>
    </div>
    """, unsafe_allow_html=True)
    
    text = st.text_area("Paste text", placeholder="Paste article, report, or any text to summarize...", height=150)

    if st.button("Summarize", use_container_width=True):
        result = ask_ai_stream([
            {"role": "system", "content": "Summarize in bullet points"},
            {"role": "user", "content": text}
        ])
        st.write(result)

# reset
st.session_state.stop_stream = False
