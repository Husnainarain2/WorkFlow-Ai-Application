import os
import streamlit as st
from groq import Groq

# =========================
# API KEY (FROM STREAMLIT SECRETS)
# =========================
import os

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("❌ Add GROQ_API_KEY in Streamlit Secrets")
    st.stop()
client = Groq(api_key=api_key)

# =========================
# UI
# =========================
st.set_page_config(page_title="Workflow AI", layout="centered")
st.title("🚀 Workflow AI Chat")

# =========================
# CHAT HISTORY
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

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

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = ask_ai(st.session_state.messages)
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# =========================
# CLEAR CHAT
# =========================
if st.sidebar.button("🗑 Clear Chat"):
    st.session_state.messages = []
    st.rerun()
