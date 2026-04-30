import os, sqlite3, json, hashlib, datetime
import streamlit as st
from groq import Groq
from fpdf import FPDF
import plotly.express as px
import plotly.graph_objects as go


# =========================
# API KEY
# =========================
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Add GROQ_API_KEY in Streamlit Secrets")
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


st.markdown("""
<style>
/* Sidebar hamburger icon */
.sidebar-toggle {
    font-size: 24px;
    cursor: pointer;
    padding: 8px;
    border-radius: 6px;
    background-color: #2563eb;
    color: white;
    text-align: center;
    margin-bottom: 10px;
    transition: background-color 0.3s ease;
}
.sidebar-toggle:hover {
    background-color: #1e40af;
}
</style>
""", unsafe_allow_html=True)



# =========================
# THEME HANDLING
# =========================
if "theme" not in st.session_state:
    st.session_state.theme = "light"

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
st.title("Workflow AI Chat")

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

import tempfile

def create_report_pdf(title, content, charts=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)
    pdf.ln(10)

    # Insert charts if provided
    if charts:
        for chart in charts:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                chart.write_image(tmpfile.name, format="png")
                pdf.image(tmpfile.name, w=160)
                pdf.ln(10)

    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 0, "C")

    return pdf.output(dest="S").encode("latin1")

# =========================
# INPUT
# =========================
user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
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
st.sidebar.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #111827;
    color: white;
    padding: 20px;
}
.sidebar-title {
    font-size: 14px;
    font-weight: bold;
    color: #9CA3AF;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- Search History Section ---
st.sidebar.markdown('<div class="sidebar-title">Search History</div>', unsafe_allow_html=True)
c.execute("SELECT rowid, query FROM history WHERE username=?", (st.session_state.user,))
rows = c.fetchall()
for i, (rowid, query) in enumerate(rows[-10:]):
    cols = st.sidebar.columns([3,1])
    with cols[0]:
        if st.button(query, key=f"hist_{i}"):
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
        if st.button("✖", key=f"del_{i}"):
            c.execute("DELETE FROM history WHERE rowid=?", (rowid,))
            conn.commit()
            st.sidebar.success(f"Deleted: {query}")
            st.rerun()

if st.sidebar.button("Delete All History"):
    c.execute("DELETE FROM history WHERE username=?", (st.session_state.user,))
    conn.commit()
    st.sidebar.success("All history deleted!")
    st.rerun()

# --- Navigation Menu ---
st.sidebar.markdown('<div class="sidebar-title">Main</div>', unsafe_allow_html=True)
menu = st.sidebar.radio("",
    ["🏠 Dashboard", "💬 Chat", "✉ Email", "📄 Summarization", "📊 Reports", "⬇ Downloads"],
    label_visibility="collapsed"
)

st.sidebar.markdown('<div class="sidebar-title">Other</div>', unsafe_allow_html=True)
other = st.sidebar.radio("",
    ["📈 Data Visualization", "⚙ Settings"],
    label_visibility="collapsed"
)

# =========================
# MAIN PAGE PANELS
# =========================
if menu == "🏠 Dashboard":
    st.header("Workflow Insights Dashboard")
    # show metrics + charts (donut, gauge, progress bars)

elif menu == "💬 Chat":
    st.header("Chat")
    # existing chat input + messages

elif menu == "✉ Email":
    st.header("Email Tools")
    # your email composition logic

elif menu == "📄 Summarization":
    st.header("Summarization")
    # summarization logic

elif menu == "📊 Reports":
    st.header("Report Generator")
    # report generation + charts + PDF export

elif menu == "⬇ Downloads":
    st.header("Downloads")
    # download buttons

elif other == "📈 Data Visualization":
    st.header("Workflow Insights Dashboard")
    # toggle charts block

elif other == "⚙ Settings":
    st.header("Settings")
    # theme toggle, clear chat, etc.

