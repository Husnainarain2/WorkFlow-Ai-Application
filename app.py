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

# Collapsible Tools Section
with st.sidebar.expander("☰ Tools", expanded=False):
    # Chat Controls
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    if st.button("Toggle Theme"):
        toggle_theme()
        st.rerun()

    # Email Tools
    st.markdown("#### Email")
    if st.button("Write Email"):
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
    st.markdown("#### Summarization")
    if st.button("Summarize Chat"):
        summary = ask_ai([
            {"role": "system", "content": "Summarize the following chat into key points."},
            {"role": "user", "content": "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])}
        ])
        st.subheader("Chat Summary")
        st.markdown(summary)

    # Reports
        # Reports
    st.markdown("#### Reports")
    if st.button("Generate Report"):
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

            # Generate charts dynamically from session data
            email_count = sum(1 for m in st.session_state.messages if "Subject:" in m["content"])
            summary_count = sum(1 for m in st.session_state.messages if "Summary" in m["content"])
            report_count = sum(1 for m in st.session_state.messages if "Report" in m["content"])
            scheduling_count = sum(1 for m in st.session_state.messages if "Schedule" in m["content"])

            tasks = {"Emails": email_count, "Summaries": summary_count,
                     "Reports": report_count, "Scheduling": scheduling_count}
            fig1 = px.pie(names=list(tasks.keys()), values=list(tasks.values()), hole=0.4, title="Tasks Breakdown")

            time_saved = round((email_count+summary_count+report_count+scheduling_count) * 0.25, 2)
            fig2 = go.Figure(go.Indicator(mode="gauge+number", value=time_saved,
                                          title={'text': "Time Saved (hrs)"},
                                          gauge={'axis': {'range': [0, 40]}, 'bar': {'color': "green"}}))

            workflows = {"Drafting Reports": report_count*10,
                         "Summarizing Meetings": summary_count*5,
                         "Email Automation": email_count*8}
            fig3 = go.Figure()
            for task, progress in workflows.items():
                fig3.add_trace(go.Bar(x=[min(progress,100)], y=[task],
                                      orientation='h', text=f"{min(progress,100)}%", textposition="outside"))
            fig3.update_layout(title="Active Workflows Progress", xaxis=dict(range=[0,100]))

            # Download buttons
            st.download_button("Download Report (TXT)", data=report_text, file_name="report.txt", mime="text/plain")
            pdf_bytes = create_report_pdf(report_topic, report_text, charts=[fig1, fig2, fig3])
            st.download_button("Download Report (PDF)", data=pdf_bytes, file_name="report.pdf", mime="application/pdf")

    # Downloads
    st.markdown("#### Downloads")
    if st.session_state.messages:
        st.download_button("Download JSON",
            data=json.dumps(st.session_state.messages, indent=2),
            file_name="chat_history.json",
            mime="application/json")
        st.download_button("Download TXT",
            data="\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages]),
            file_name="chat_history.txt",
            mime="text/plain")

    # =========================
# DATA VISUALIZATION TOGGLE
# =========================
st.sidebar.markdown("#### Data Visualization")

# Toggle button
if "show_dashboard" not in st.session_state:
    st.session_state.show_dashboard = False

if st.sidebar.button("Toggle Dashboard Charts"):
    st.session_state.show_dashboard = not st.session_state.show_dashboard

# Show or hide charts in main page
if st.session_state.show_dashboard:
    st.header("Workflow Insights Dashboard")

    # --- Collect live stats from session ---
    email_count = sum(1 for m in st.session_state.messages if "Subject:" in m["content"])
    summary_count = sum(1 for m in st.session_state.messages if "Summary" in m["content"])
    report_count = sum(1 for m in st.session_state.messages if "Report" in m["content"])
    scheduling_count = sum(1 for m in st.session_state.messages if "Schedule" in m["content"])

    total_tasks = email_count + summary_count + report_count + scheduling_count
    time_saved = round(total_tasks * 0.25, 2)  # 15 mins per task

    # --- Donut chart ---
    tasks = {"Emails": email_count, "Summaries": summary_count,
             "Reports": report_count, "Scheduling": scheduling_count}
    fig1 = px.pie(names=list(tasks.keys()), values=list(tasks.values()), hole=0.4,
                  title="Tasks Automated Breakdown")
    st.plotly_chart(fig1, use_container_width=True)

    # --- Gauge chart ---
    fig2 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=time_saved,
        title={'text': "Time Saved (hrs)"},
        gauge={'axis': {'range': [0, 40]}, 'bar': {'color': "green"}}
    ))
    st.plotly_chart(fig2, use_container_width=True)

    # --- Progress bars ---
    workflows = {"Drafting Reports": report_count*10,
                 "Summarizing Meetings": summary_count*5,
                 "Email Automation": email_count*8}
    fig3 = go.Figure()
    for task, progress in workflows.items():
        fig3.add_trace(go.Bar(
            x=[min(progress,100)],
            y=[task],
            orientation='h',
            text=f"{min(progress,100)}%",
            textposition="outside"
        ))
    fig3.update_layout(title="Active Workflows Progress", xaxis=dict(range=[0,100]))
    st.plotly_chart(fig3, use_container_width=True)
