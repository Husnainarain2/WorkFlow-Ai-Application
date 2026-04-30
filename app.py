import os
import sqlite3
import json
import datetime
import tempfile
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

# =========================
# CSS
# =========================
st.markdown("""
<style>
.sidebar-toggle {
    font-size: 24px;
    cursor: pointer;
    padding: 8px;
    border-radius: 6px;
    background-color: #2563eb;
    color: white;
    text-align: center;
    margin-bottom: 10px;
}
.sidebar-toggle:hover {
    background-color: #1e40af;
}
</style>
""", unsafe_allow_html=True)

# =========================
# THEME
# =========================
if "theme" not in st.session_state:
    st.session_state.theme = "light"

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

def apply_theme():
    if st.session_state.theme == "dark":
        st.markdown("""
        <style>
        .stApp { background: #0f172a; color: white; }
        .stChatMessage { background-color: #1e293b; color: white; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp { background: #f9fafb; color: black; }
        .stChatMessage { background-color: #e5e7eb; color: black; }
        </style>
        """, unsafe_allow_html=True)

apply_theme()

# =========================
# UI
# =========================
st.title("Workflow AI Chat")

# =========================
# SESSION
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
# AI FUNCTION
# =========================
def ask_ai(messages):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )
    return response.choices[0].message.content

# =========================
# PDF FUNCTION
# =========================
def create_report_pdf(title, content, charts=None):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, title, ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)
    pdf.ln(10)

    if charts:
        for chart in charts:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                chart.write_image(tmpfile.name)
                pdf.image(tmpfile.name, w=160)
                pdf.ln(10)

    pdf.set_font("Arial", "I", 10)
    pdf.cell(
        0, 10,
        f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        0, 0, "C"
    )

    return pdf.output(dest="S").encode("latin1")

# =========================
# INPUT
# =========================
col1, col2 = st.columns([2, 2])

with col1:
    user_input = st.chat_input("Type your message...")

with col2:
    uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"])

# =========================
# PDF LOGIC
# =========================
if uploaded_pdf:
    import PyPDF2
    reader = PyPDF2.PdfReader(uploaded_pdf)

    text_content = ""
    for page in reader.pages:
        text_content += page.extract_text() + "\n"

    st.subheader("Uploaded PDF Content")
    st.text_area("Extracted Text", text_content, height=300)

    if st.button("Ask AI about PDF"):
        reply = ask_ai([
            {"role": "system", "content": "Analyze PDF"},
            {"role": "user", "content": text_content}
        ])
        st.markdown(reply)

# =========================
# CHAT LOGIC
# =========================
elif user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    c.execute("INSERT INTO history VALUES (?,?)",
              (st.session_state.user, user_input))
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
st.sidebar.markdown("### Search History")

c.execute("SELECT rowid, query FROM history WHERE username=?",
          (st.session_state.user,))
rows = c.fetchall()

for i, (rowid, query) in enumerate(rows[-10:]):
    col1, col2 = st.sidebar.columns([3, 1])

    with col1:
        if st.button(query, key=f"hist_{i}"):
            st.session_state.messages.append(
                {"role": "user", "content": query})
            reply = ask_ai(st.session_state.messages)
            st.session_state.messages.append(
                {"role": "assistant", "content": reply})
            st.rerun()

    with col2:
        if st.button("✖", key=f"del_{i}"):
            c.execute("DELETE FROM history WHERE rowid=?", (rowid,))
            conn.commit()
            st.rerun()

if st.sidebar.button("Delete All History"):
    c.execute("DELETE FROM history WHERE username=?",
              (st.session_state.user,))
    conn.commit()
    st.rerun()

# =========================
# TOOLS
# =========================
with st.sidebar.expander("☰ Tools"):

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    if st.button("Toggle Theme"):
        toggle_theme()
        st.rerun()

    # Email
    st.markdown("### Email")
    subject = st.text_input("Subject")
    body = st.text_area("Body")

    if st.button("Generate Email"):
        reply = ask_ai([
            {"role": "system", "content": "Write professional email"},
            {"role": "user", "content": f"{subject}\n{body}"}
        ])
        st.markdown(reply)

    # Summarize
    if st.button("Summarize Chat"):
        summary = ask_ai([
            {"role": "system", "content": "Summarize chat"},
            {"role": "user", "content": str(st.session_state.messages)}
        ])
        st.markdown(summary)
