## 🚀 Workflow AI (Streamlit + Groq)

A simple AI Chat Application built with Streamlit and Groq API (Llama 3.1).
It supports real-time chat like ChatGPT and is deployable on Streamlit Cloud.

## ✨ Features
💬 ChatGPT-style AI chat
🧠 Powered by Groq (Llama 3.1 model)
⚡ Fast responses
🌐 Web-based UI (Streamlit)
🗂 Chat history (session-based)
☁️ Deployable on Streamlit Cloud
📁 Project Structure
## WorkFlow-AI/
│── app.py
│── requirements.txt
│── .gitignore
│── README.md
## ⚙️ Installation (Local Setup)
1. Clone the repository
git clone https://github.com/your-username/WorkFlow-AI.git
cd WorkFlow-AI
2. Create virtual environment (optional)
python -m venv .venv
.venv\Scripts\activate   # Windows
3. Install dependencies
pip install -r requirements.txt
## 🔐 API Key Setup
Option 1: Local (.env file)

Create a .env file:

GROQ_API_KEY=your_api_key_here
Option 2: Streamlit Cloud (Recommended)

Go to:

App → Settings → Secrets

Add:

GROQ_API_KEY = "your_api_key_here"
▶️ Run the App
python -m streamlit run app.py
