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
# PREMIUM UI CSS
# =========================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    font-family: 'Inter', sans-serif;
}

.block-container {
    background: rgba(255,255,255,0.05);
    padding: 2rem;
    border-radius: 20px;
    backdrop-filter: blur(20px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

.stChatMessage {
    border-radius: 15px !important;
    padding: 12px !important;
    margin-bottom: 10px !important;
    animation: fadeIn 0.4s ease-in-out;
}

[data-testid="stChatMessage-user"] {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
}

[data-testid="stChatMessage-assistant"] {
    background: rgba(255,255,255,0.08);
    color: #e5e7eb;
}

.stChatInput input {
    border-radius: 12px !important;
    padding: 12px !important;
    background: rgba(255,255,255,0.1);
    color: white;
}

.stButton>button {
    border-radius: 12px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
    padding: 10px 16px;
    transition: all 0.3s ease;
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(99,102,241,0.5);
}

section[data-testid="stSidebar"] {
    background: rgba(15,23,42,0.9);
    backdrop-filter: blur(10px);
}

.card {
    background: rgba(255,255,255,0.05);
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    text-align:center;
}

@keyframes fadeIn {
    from {opacity:0; transform:translateY(10px);}
    to {opacity:1; transform:translateY(0);}
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
# STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user" not in st.session_state:
    st.session_state.user = "guest"

# =========================
# HEADER
# =========================
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
    <h2>🚀 Workflow AI</h2>
    <span style="color:#94a3b8;">Premium Dashboard</span>
</div>
""", unsafe_allow_html=True)

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
# PDF
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
# CHAT DISPLAY
# =========================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

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
# SIDEBAR
# =========================
st.sidebar.title("⚡ Controls")

if st.sidebar.button("Clear Chat"):
    st.session_state.messages=[]
    st.rerun()

if st.sidebar.button("Delete History"):
    c.execute("DELETE FROM history")
    conn.commit()
    st.rerun()

# =========================
# HISTORY
# =========================
st.sidebar.subheader("History")
c.execute("SELECT query FROM history")
rows=c.fetchall()

for i,row in enumerate(rows[-10:]):
    if st.sidebar.button(row[0], key=i):
        st.session_state.messages.append({"role":"user","content":row[0]})
        reply = ask_ai(st.session_state.messages)
        st.session_state.messages.append({"role":"assistant","content":reply})
        st.rerun()

# =========================
# DASHBOARD
# =========================
st.subheader("📊 Insights")

email_count = sum(1 for m in st.session_state.messages if "email" in m["content"].lower())
report_count = sum(1 for m in st.session_state.messages if "report" in m["content"].lower())
summary_count = sum(1 for m in st.session_state.messages if "summary" in m["content"].lower())

col1,col2,col3 = st.columns(3)

with col1:
    st.markdown(f"<div class='card'><h3>Emails</h3><h1>{email_count}</h1></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='card'><h3>Reports</h3><h1>{report_count}</h1></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='card'><h3>Summaries</h3><h1>{summary_count}</h1></div>", unsafe_allow_html=True)

fig = px.pie(
    names=["Emails","Reports","Summaries"],
    values=[email_count,report_count,summary_count],
    hole=0.4
)
st.plotly_chart(fig, use_container_width=True)

# =========================
# DOWNLOAD
# =========================
if st.session_state.messages:
    st.download_button("Download Chat JSON",
        data=json.dumps(st.session_state.messages,indent=2),
        file_name="chat.json")

    st.download_button("Download TXT",
        data="\n".join([m["content"] for m in st.session_state.messages]),
        file_name="chat.txt")
