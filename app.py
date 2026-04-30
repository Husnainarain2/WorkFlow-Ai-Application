import os, sqlite3, json, hashlib, datetime
import streamlit as st
from groq import Groq
from fpdf import FPDF

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

def create_report_pdf(title, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)
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
st.sidebar.markdown("## Tools")

# Chat Controls
if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

if st.sidebar.button("Toggle Theme"):
    toggle_theme()
    st.rerun()

# Email Tools
st.sidebar.markdown("### Email")
if st.sidebar.button("Write Email"):
    st.session_state.email_mode = True
if "email_mode" in st.session_state and st.session_state.email_mode:
    st.subheader("Compose Email")
    subject = st.text_input("Subject")
    body = st.text_area("Body")
    if st.button("Generate Email"):
        reply = ask_ai([
            {"role": "system", "content": "You are an assistant that writes professional emails."},
            {"role": "user", "content": f"Subject: {subject}\nBody: {body}"}
        ])
        st.write("Suggested Email Draft:")
        st.markdown(reply)

# Summarization
st.sidebar.markdown("### Summarization")
if st.sidebar.button("Summarize Chat"):
    summary = ask_ai([
        {"role": "system", "content": "Summarize the following chat into key points."},
        {"role": "user", "content": "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])}
    ])
    st.subheader("Chat Summary")
    st.markdown(summary)

# Reports
st.sidebar.markdown("### Reports")
if st.sidebar.button("Generate Report"):
    st.session_state.report_mode = True
if "report_mode" in st.session_state and st.session_state.report_mode:
    st.subheader("Report Generator")
    report_topic = st.text_input("Report Topic", placeholder="e.g., Project Progress, Meeting Notes")
    if st.button("Create Report"):
        report_text = ask_ai([
            {"role": "system", "content": "You are an assistant that writes structured professional reports."},
            {"role": "user", "content": f"Create a detailed report on: {report_topic}"}
        ])
        st.write("Generated Report:")
        st.markdown(report_text)
        st.download_button("Download Report (TXT)", data=report_text, file_name="report.txt", mime="text/plain")
        pdf_bytes = create_report_pdf(report_topic, report_text)
        st.download_button("Download Report (PDF)", data=pdf_bytes, file_name="report.pdf", mime="application/pdf")

# Downloads
st.sidebar.markdown("### Downloads")
if st.session_state.messages:
    st.sidebar.download_button("Download JSON",
        data=json.dumps(st.session_state.messages, indent=2),
        file_name="chat_history.json",
        mime="application/json")
    st.sidebar.download_button("Download TXT",
        data="\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages]),
        file_name="chat_history.txt",
        mime="text/plain")

# History
st.sidebar.markdown("### Search History")
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
