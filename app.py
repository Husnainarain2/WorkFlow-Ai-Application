import os
import sqlite3
import streamlit as st
from groq import Groq

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Workflow AI Pro",
    layout="centered",
    page_icon="⚡"
)

# =========================
# CUSTOM CSS INJECTION
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

/* ─── Root Variables ─── */
:root {
    --bg:        #0a0a0f;
    --surface:   #111118;
    --card:      #16161f;
    --border:    #2a2a3d;
    --accent:    #7c6eff;
    --accent2:   #ff6b9d;
    --accent3:   #00e5c5;
    --text:      #e8e8f0;
    --muted:     #6b6b8a;
    --success:   #00e5c5;
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
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
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
    color: var(--muted) !important;
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
    background: var(--card) !important;
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
    background: #9184ff !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(124, 110, 255, 0.35) !important;
}

/* Stop button special style */
.stButton:has(button:contains("Stop")) > button {
    background: transparent !important;
    border: 1px solid #ff4d4d !important;
    color: #ff4d4d !important;
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
    box-shadow: 0 0 0 2px rgba(124,110,255,0.15) !important;
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
    box-shadow: 0 0 0 2px rgba(124,110,255,0.15) !important;
}

/* ─── Chat Messages ─── */
[data-testid="stChatMessage"] {
    background: var(--card) !important;
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

/* User messages */
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
    background: rgba(0,229,197,0.08) !important;
    border: 1px solid var(--success) !important;
    border-radius: 8px !important;
    color: var(--success) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
}
.stError {
    background: rgba(255,77,77,0.08) !important;
    border: 1px solid #ff4d4d !important;
    border-radius: 8px !important;
    color: #ff4d4d !important;
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
}

/* ─── Subheaders ─── */
h1, h2, h3 {
    font-family: var(--font-head) !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HERO BANNER HTML
# =========================
def render_hero(title, subtitle, icon="⚡"):
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #16161f 0%, #1a1a2e 100%);
        border: 1px solid #2a2a3d;
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute; top: -30px; right: -30px;
            width: 140px; height: 140px;
            background: radial-gradient(circle, rgba(124,110,255,0.18) 0%, transparent 70%);
            border-radius: 50%;
        "></div>
        <div style="
            position: absolute; bottom: -20px; left: 20%;
            width: 80px; height: 80px;
            background: radial-gradient(circle, rgba(255,107,157,0.12) 0%, transparent 70%);
            border-radius: 50%;
        "></div>
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
        <h1 style="
            font-family: 'Syne', sans-serif;
            font-size: 1.8rem;
            font-weight: 800;
            color: #e8e8f0;
            margin: 0 0 0.4rem 0;
            letter-spacing: -0.03em;
        ">{title}</h1>
        <p style="
            font-family: 'DM Mono', monospace;
            font-size: 0.82rem;
            color: #6b6b8a;
            margin: 0;
            letter-spacing: 0.04em;
        ">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

# =========================
# BADGE / CHIP HTML
# =========================
def badge(text, color="#7c6eff"):
    return f"""<span style="
        display: inline-block;
        background: {color}1a;
        border: 1px solid {color}55;
        color: {color};
        font-family: 'DM Mono', monospace;
        font-size: 0.7rem;
        font-weight: 500;
        padding: 2px 10px;
        border-radius: 20px;
        letter-spacing: 0.06em;
        margin-right: 6px;
    ">{text}</span>"""

# =========================
# TOOL CARD HTML
# =========================
def tool_card(icon, title, desc, color="#7c6eff"):
    st.markdown(f"""
    <div style="
        background: #16161f;
        border: 1px solid #2a2a3d;
        border-left: 3px solid {color};
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    ">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
            <span style="font-size: 1.2rem;">{icon}</span>
            <span style="
                font-family: 'Syne', sans-serif;
                font-weight: 700;
                font-size: 1rem;
                color: #e8e8f0;
            ">{title}</span>
        </div>
        <p style="
            font-family: 'DM Mono', monospace;
            font-size: 0.78rem;
            color: #6b6b8a;
            margin: 0;
            line-height: 1.6;
        ">{desc}</p>
    </div>
    """, unsafe_allow_html=True)

# =========================
# DIVIDER
# =========================
def divider(label=""):
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; margin: 1.2rem 0;">
        <div style="flex:1; height:1px; background:#2a2a3d;"></div>
        {f'<span style="font-family:DM Mono,monospace; font-size:0.7rem; color:#6b6b8a; letter-spacing:0.08em; text-transform:uppercase;">{label}</span>' if label else ''}
        <div style="flex:1; height:1px; background:#2a2a3d;"></div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# DB SETUP
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

# =========================
# AUTH PAGE
# =========================
def auth_page():
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1.5rem;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">⚡</div>
        <h1 style="
            font-family: 'Syne', sans-serif;
            font-size: 2rem;
            font-weight: 800;
            color: #e8e8f0;
            margin: 0 0 0.4rem;
            letter-spacing: -0.03em;
        ">Workflow AI Pro</h1>
        <p style="
            font-family: 'DM Mono', monospace;
            font-size: 0.78rem;
            color: #6b6b8a;
            letter-spacing: 0.06em;
        ">SIGN IN TO CONTINUE</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔑  Login", "✨  Sign Up"])

    with tab1:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        username = st.text_input("Username", key="login_user", placeholder="your_username")
        password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("Login →", use_container_width=True):
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
            if user:
                st.session_state.user = username
                st.success("✓ Login successful")
                st.rerun()
            else:
                st.error("✗ Invalid credentials")

    with tab2:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        new_user = st.text_input("Choose Username", key="signup_user", placeholder="new_username")
        new_pass = st.text_input("Choose Password", type="password", key="signup_pass", placeholder="••••••••")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("Create Account →", use_container_width=True):
            try:
                c.execute("INSERT INTO users VALUES (?,?)", (new_user, new_pass))
                conn.commit()
                st.success("✓ Account created — go to Login")
            except:
                st.error("✗ Username already taken")

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
# LOAD HISTORY
# =========================
def load_history():
    c.execute("SELECT role, message FROM chat_history WHERE user=?", (user,))
    rows = c.fetchall()
    st.session_state.messages = [{"role": r, "content": m} for r, m in rows]

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
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 1.4rem; margin-bottom: 4px;">⚡</div>
        <div style="
            font-family: 'Syne', sans-serif;
            font-weight: 800;
            font-size: 1rem;
            color: #7c6eff;
            letter-spacing: 0.04em;
        ">WORKFLOW AI PRO</div>
        <div style="
            font-family: 'DM Mono', monospace;
            font-size: 0.72rem;
            color: #6b6b8a;
            margin-top: 2px;
        ">logged in as <span style="color: #00e5c5;">{user}</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="
        font-family: 'DM Mono', monospace;
        font-size: 0.68rem;
        color: #6b6b8a;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 8px;
        padding-left: 4px;
    ">Navigation</div>
    """, unsafe_allow_html=True)

    if st.button("💬  Chat"):
        st.session_state.mode = "chat"
    if st.button("📧  Email Generator"):
        st.session_state.mode = "email"
    if st.button("📊  Report Builder"):
        st.session_state.mode = "report"
    if st.button("📝  Summarizer"):
        st.session_state.mode = "summary"

    st.markdown("""
    <div style="
        font-family: 'DM Mono', monospace;
        font-size: 0.68rem;
        color: #6b6b8a;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin: 1.2rem 0 8px;
        padding-left: 4px;
    ">Account</div>
    """, unsafe_allow_html=True)

    if st.button("🧹  Clear History"):
        st.session_state.messages = []
        c.execute("DELETE FROM chat_history WHERE user=?", (user,))
        conn.commit()
        st.rerun()

    if st.button("🚪  Logout"):
        st.session_state.user = None
        st.session_state.messages = []
        st.rerun()

    # Model info badge
    st.markdown(f"""
    <div style="
        margin-top: 2rem;
        padding: 0.75rem 1rem;
        background: #111118;
        border: 1px solid #2a2a3d;
        border-radius: 10px;
    ">
        <div style="font-family: 'DM Mono', monospace; font-size: 0.68rem; color: #6b6b8a; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 4px;">Model</div>
        <div style="font-family: 'DM Mono', monospace; font-size: 0.75rem; color: #7c6eff;">llama-3.1-8b-instant</div>
        <div style="font-family: 'DM Mono', monospace; font-size: 0.68rem; color: #6b6b8a; margin-top: 4px;">via Groq API</div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# MAIN CONTENT
# =========================

# ── CHAT MODE ──
if st.session_state.mode == "chat":
    render_hero("AI Chat", "Ask anything — get instant, streamed responses.", "💬")

    msg_count = len(st.session_state.messages)
    st.markdown(f"""
    <div style="margin-bottom: 1.2rem;">
        {badge(f"{msg_count // 2} exchanges", '#7c6eff')}
        {badge('streaming enabled', '#00e5c5')}
    </div>
    """, unsafe_allow_html=True)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("⛔ Stop"):
            st.session_state.stop_stream = True

    user_input = st.chat_input("Message AI...")

    if user_input:
        st.session_state.stop_stream = False
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        c.execute("INSERT INTO chat_history VALUES (?,?,?)", (user, "user", user_input))
        conn.commit()
        with st.chat_message("assistant"):
            reply = ask_ai_stream(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        c.execute("INSERT INTO chat_history VALUES (?,?,?)", (user, "assistant", reply))
        conn.commit()

# ── EMAIL MODE ──
elif st.session_state.mode == "email":
    render_hero("Email Generator", "Generate polished professional emails in seconds.", "📧")

    tool_card(
        "📧", "Professional Email Writer",
        "Enter a subject and key points — AI will draft a clean, context-aware email for you.",
        "#ff6b9d"
    )

    subject = st.text_input("Email Subject", placeholder="e.g. Follow-up on project proposal")
    body = st.text_area("Key Points / Context", height=130,
                         placeholder="e.g. Following up after meeting, asking for timeline, keeping tone friendly...")

    if st.button("Generate Email →", use_container_width=True):
        if subject or body:
            divider("AI output")
            with st.spinner(""):
                result = ask_ai_stream([
                    {"role": "system", "content": "You are an expert email writer. Write a professional, well-structured email. Use clear paragraphs. Do not include placeholders."},
                    {"role": "user", "content": f"Subject: {subject}\nContext: {body}"}
                ])
        else:
            st.error("✗ Please fill in at least one field")

# ── REPORT MODE ──
elif st.session_state.mode == "report":
    render_hero("Report Builder", "Generate structured, detailed reports on any topic.", "📊")

    tool_card(
        "📊", "Intelligent Report Generator",
        "Provide a topic or question and receive a well-organized report with headings, analysis, and conclusions.",
        "#7c6eff"
    )

    topic = st.text_input("Report Topic", placeholder="e.g. Impact of AI on healthcare in 2025")
    col1, col2 = st.columns(2)
    with col1:
        length = st.selectbox("Length", ["Concise (300 words)", "Medium (600 words)", "Detailed (1000+ words)"])
    with col2:
        tone = st.selectbox("Tone", ["Professional", "Academic", "Executive Summary"])

    if st.button("Generate Report →", use_container_width=True):
        if topic:
            divider("AI output")
            with st.spinner(""):
                result = ask_ai_stream([
                    {"role": "system", "content": f"You are a professional report writer. Write a {tone.lower()} report with clear headings (##), subheadings, and structured paragraphs. Target length: {length}."},
                    {"role": "user", "content": topic}
                ])
        else:
            st.error("✗ Please enter a topic")

# ── SUMMARY MODE ──
elif st.session_state.mode == "summary":
    render_hero("Summarizer", "Condense long text into clear, actionable bullet points.", "📝")

    tool_card(
        "📝", "Smart Text Summarizer",
        "Paste any text — articles, reports, notes — and get a concise bullet-point summary instantly.",
        "#00e5c5"
    )

    text = st.text_area("Paste Text to Summarize", height=200,
                          placeholder="Paste article, report, notes, or any long text here...")

    if st.button("Summarize →", use_container_width=True):
        if text.strip():
            divider("AI output")
            with st.spinner(""):
                result = ask_ai_stream([
                    {"role": "system", "content": "Summarize the following text into clear, concise bullet points. Capture key ideas, facts, and conclusions. Be thorough but avoid redundancy."},
                    {"role": "user", "content": text}
                ])
        else:
            st.error("✗ Please paste some text first")

# Reset stop flag
st.session_state.stop_stream = False
