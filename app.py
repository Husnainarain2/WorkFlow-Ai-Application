import os, sqlite3, json, datetime, tempfile
import streamlit as st
from groq import Groq
from fpdf import FPDF
import plotly.express as px
import plotly.graph_objects as go

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Workflow AI", layout="wide")

# =========================
# LIGHT PREMIUM CSS
# =========================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>

.stApp {
    background: #f5f7fb;
    font-family: 'Inter', sans-serif;
}

/* Main container */
.block-container {
    padding: 2rem;
}

/* Cards */
.card {
    background: white;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    text-align:center;
}

/* Chat */
.stChatMessage {
    border-radius: 12px !important;
    padding: 12px !important;
}

[data-testid="stChatMessage-user"] {
    background: #2563eb;
    color: white;
}

[data-testid="stChatMessage-assistant"] {
    background: #f1f5f9;
}

/* Buttons */
.stButton>button {
    border-radius: 10px;
    background: #2563eb;
    color: white;
    border: none;
}
.stButton>button:hover {
    background: #1e40af;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: white;
}

/* Input */
.stChatInput input {
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# API KEY
# =========================
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Add GROQ_API_KEY in Streamlit Secrets")
    st.stop()

client = Groq(api_key=api_key)

# =========================
# DB
# =========================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS history (username TEXT, query TEXT)")
conn.commit()

# =========================
# SESSION
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user" not in st.session_state:
    st.session_state.user = "guest"

# =========================
# HEADER
# =========================
st.title("🚀 Workflow AI")

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
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )
    return res.choices[0].message.content

# =========================
# PDF FUNCTION
# =========================
def create_pdf(title, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",16)
    pdf.cell(200,10,title,ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0,10,content)
    return pdf.output(dest="S").encode("latin1")

# =========================
# INPUT
# =========================
user_input = st.chat_input("Type your message...")

# =========================
# PDF UPLOAD
# =========================
uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_pdf:
    import PyPDF2
    reader = PyPDF2.PdfReader(uploaded_pdf)
    text = ""
    for p in reader.pages:
        text += p.extract_text() + "\n"

    st.text_area("PDF Content", text, height=200)

    if st.button("Ask AI about PDF"):
        reply = ask_ai([
            {"role":"system","content":"Analyze PDF"},
            {"role":"user","content":text}
        ])
        st.markdown(reply)

# =========================
# CHAT LOGIC
# =========================
if user_input:
    st.session_state.messages.append({"role":"user","content":user_input})

    c.execute("INSERT INTO history VALUES (?,?)",(st.session_state.user,user_input))
    conn.commit()

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = ask_ai(st.session_state.messages)
            st.markdown(reply)

    st.session_state.messages.append({"role":"assistant","content":reply})

# =========================
# SIDEBAR (ALL TOOLS HERE)
# =========================
st.sidebar.title("⚙️ Tools")

# --- Chat Control ---
if st.sidebar.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# --- History ---
st.sidebar.subheader("History")
c.execute("SELECT rowid, query FROM history WHERE username=?", (st.session_state.user,))
rows = c.fetchall()

for i,(rowid,query) in enumerate(rows[-10:]):
    col1,col2 = st.sidebar.columns([3,1])
    with col1:
        if st.button(query, key=f"h{i}"):
            st.session_state.messages.append({"role":"user","content":query})
            reply = ask_ai(st.session_state.messages)
            st.session_state.messages.append({"role":"assistant","content":reply})
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

# --- Email Tool ---
st.sidebar.subheader("📧 Email Generator")
subject = st.sidebar.text_input("Subject")
body = st.sidebar.text_area("Body")

if st.sidebar.button("Generate Email"):
    reply = ask_ai([
        {"role":"system","content":"Write professional email"},
        {"role":"user","content":f"{subject}\n{body}"}
    ])
    st.sidebar.markdown(reply)

# --- Summarize ---
if st.sidebar.button("📄 Summarize Chat"):
    summary = ask_ai([
        {"role":"system","content":"Summarize chat"},
        {"role":"user","content":str(st.session_state.messages)}
    ])
    st.sidebar.markdown(summary)

# --- Report ---
st.sidebar.subheader("📊 Report")
topic = st.sidebar.text_input("Report Topic")

if st.sidebar.button("Generate Report"):
    report = ask_ai([
        {"role":"system","content":"Write report"},
        {"role":"user","content":topic}
    ])
    st.markdown(report)

    st.download_button("Download TXT", report, "report.txt")
    pdf_bytes = create_pdf(topic, report)
    st.download_button("Download PDF", pdf_bytes, "report.pdf")

# =========================
# DASHBOARD
# =========================
st.subheader("📊 Dashboard")

email_count = sum(1 for m in st.session_state.messages if "email" in m["content"].lower())
report_count = sum(1 for m in st.session_state.messages if "report" in m["content"].lower())
summary_count = sum(1 for m in st.session_state.messages if "summary" in m["content"].lower())

col1,col2,col3 = st.columns(3)

with col1:
    st.markdown(f"<div class='card'><h3>Emails</h3><h2>{email_count}</h2></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='card'><h3>Reports</h3><h2>{report_count}</h2></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='card'><h3>Summaries</h3><h2>{summary_count}</h2></div>", unsafe_allow_html=True)

fig = px.pie(
    names=["Emails","Reports","Summaries"],
    values=[email_count,report_count,summary_count],
    hole=0.4
)
st.plotly_chart(fig, use_container_width=True)
