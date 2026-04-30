import os
import sqlite3
import json
import datetime
import tempfile
import streamlit as st
from groq import Groq
from fpdf import FPDF

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Workflow AI", layout="centered")

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
# SESSION STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user" not in st.session_state:
    st.session_state.user = "guest"

if "email_mode" not in st.session_state:
    st.session_state.email_mode = False

if "report_mode" not in st.session_state:
    st.session_state.report_mode = False

# =========================
# UI
# =========================
st.title("🚀 Workflow AI Chat")

# =========================
# CHAT DISPLAY
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
def create_report_pdf(title, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, title, ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)
    return pdf.output(dest="S").encode("latin1")

# =========================
# CHAT INPUT
# =========================
user_input = st.chat_input("Type your message...")

if user_input:
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
# EMAIL GENERATOR (MAIN SCREEN)
# =========================
if st.session_state.email_mode:

    st.subheader("📧 Email Generator")

    subject = st.text_input("Subject")
    body = st.text_area("Email Content")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Generate Email"):
            reply = ask_ai([
                {"role": "system", "content": "Write a professional email"},
                {"role": "user", "content": f"Subject: {subject}\nBody: {body}"}
            ])
            st.session_state.generated_email = reply

    with col2:
        if st.button("Close Email Tool"):
            st.session_state.email_mode = False
            st.rerun()

    if "generated_email" in st.session_state:
        st.markdown("### ✉️ Generated Email")
        st.markdown(st.session_state.generated_email)

# =========================
# REPORT GENERATOR (MAIN SCREEN)
# =========================
if st.session_state.report_mode:

    st.subheader("📊 Report Generator")

    topic = st.text_input("Report Topic")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Create Report"):
            report = ask_ai([
                {"role": "system", "content": "Write a professional report"},
                {"role": "user", "content": topic}
            ])
            st.session_state.report_output = report

    with col2:
        if st.button("Close Report Tool"):
            st.session_state.report_mode = False
            st.rerun()

    if "report_output" in st.session_state:
        st.markdown(st.session_state.report_output)

        st.download_button("Download TXT",
                           st.session_state.report_output,
                           "report.txt")

        pdf_bytes = create_report_pdf(topic, st.session_state.report_output)
        st.download_button("Download PDF",
                           pdf_bytes,
                           "report.pdf")

# =========================
# SIDEBAR
# =========================
st.sidebar.title("⚙️ Tools")

if st.sidebar.button("📧 Email Generator"):
    st.session_state.email_mode = True
    st.session_state.report_mode = False

if st.sidebar.button("📊 Report Generator"):
    st.session_state.report_mode = True
    st.session_state.email_mode = False

if st.sidebar.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# =========================
# HISTORY
# =========================
st.sidebar.subheader("History")

c.execute("SELECT rowid, query FROM history WHERE username=?",
          (st.session_state.user,))
rows = c.fetchall()

for i, (rowid, query) in enumerate(rows[-10:]):
    col1, col2 = st.sidebar.columns([3, 1])

    with col1:
        if st.button(query, key=f"h{i}"):
            st.session_state.messages.append({"role": "user", "content": query})
            reply = ask_ai(st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

    with col2:
        if st.button("❌", key=f"d{i}"):
            c.execute("DELETE FROM history WHERE rowid=?", (rowid,))
            conn.commit()
            st.rerun()

if st.sidebar.button("Delete All History"):
    c.execute("DELETE FROM history WHERE username=?", (st.session_state.user,))
    conn.commit()
    st.rerun()
