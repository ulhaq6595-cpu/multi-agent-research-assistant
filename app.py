import os
import time
import urllib.parse
from datetime import datetime
import requests
import streamlit as st
from groq import Groq
from dotenv import load_dotenv
from PIL import Image, ImageDraw

# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="VERITAS AI • Autonomous Intelligence Studio",
    page_icon="⚜️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "search_history" not in st.session_state:
    st.session_state.search_history = []
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False
if "username" not in st.session_state:
    st.session_state.username = "Guest User"

# ---------------------------------------------------------
# CUSTOM CSS (WITH MOBILE NAVIGATION FIX)
# ---------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }

    /* ---------------------------------------------------------
       MOBILE-RESPONSIVE HEADER BUTTONS FIX
       Forces top navigation columns to stay horizontal on mobile
       --------------------------------------------------------- */
    div[data-testid="column"] {
        width: auto !important;
        flex: 1 1 auto !important;
        min-width: 0px !important;
    }

    div[data-testid="stHorizontalBlock"] {
        flex-direction: row !important;
        gap: 6px !important;
        flex-wrap: nowrap !important;
    }

    .stButton > button {
        font-size: 0.78rem !important;
        padding: 6px 10px !important;
        white-space: nowrap !important;
        border-radius: 6px !important;
    }

    /* Notice Banner */
    .notice-banner {
        background: linear-gradient(90deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95));
        border-left: 4px solid #F59E0B;
        border-radius: 8px;
        padding: 14px 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .notice-tag {
        color: #F59E0B;
        font-weight: 800;
        letter-spacing: 0.8px;
        margin-right: 8px;
    }
    .notice-text {
        color: #E2E8F0;
        font-size: 0.95rem;
        line-height: 1.5;
    }

    /* Live Ticker */
    .ticker-wrap {
        width: 100%;
        overflow: hidden;
        background: linear-gradient(90deg, rgba(217, 119, 6, 0.12), rgba(245, 158, 11, 0.12));
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-radius: 8px;
        padding: 8px 0;
        margin-bottom: 25px;
        box-sizing: border-box;
    }
    .ticker-move {
        display: inline-block;
        white-space: nowrap;
        padding-left: 100%;
        animation: ticker 25s linear infinite;
        font-weight: 600;
        color: #FBBF24;
        font-size: 0.88rem;
    }
    @keyframes ticker {
        0%   { transform: translate3d(0, 0, 0); }
        100% { transform: translate3d(-100%, 0, 0); }
    }

    /* Title Styling */
    .company-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #F59E0B, #D97706, #FBBF24, #FEF08A);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
        letter-spacing: 1.5px;
    }
    .company-subtitle {
        color: #CBD5E1;
        font-size: 0.98rem;
        margin-top: 4px;
        font-weight: 500;
    }

    /* History Cards */
    .history-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .history-query {
        color: #F8FAFC;
        font-weight: 600;
        font-size: 0.95rem;
    }
    .history-time {
        color: #94A3B8;
        font-size: 0.8rem;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1E293B;
        border-right: 1px solid #334155;
    }

    .agent-card {
        background: #334155;
        border: 1px solid #475569;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .agent-status {
        font-size: 0.75rem;
        padding: 3px 10px;
        border-radius: 12px;
        background-color: rgba(245, 158, 11, 0.2);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.5);
        font-weight: 700;
    }

    /* Output Report Container */
    .report-box {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 28px;
        margin-top: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------
def get_transparent_logo(image_path, tolerance=55):
    img = Image.open(image_path).convert("RGBA")
    width, height = img.size
    for corner in [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]:
        ImageDraw.floodfill(img, corner, (0, 0, 0, 0), thresh=tolerance)
    return img

def log_to_google_sheets(user_id, search_query, status_msg):
    """Logs search entries reliably via Google Apps Script Webhook."""
    webhook_url = st.secrets.get("WEBHOOK_URL", "")
    if not webhook_url:
        return
    
    now = datetime.now()
    payload = {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%I:%M:%S %p"),
        "user": user_id,
        "search": search_query,
        "status": status_msg
    }
    
    try:
        requests.post(webhook_url, json=payload, timeout=5)
    except Exception as e:
        print(f"[GSHEET LOG ERROR]: {str(e)}")

# Secure API Resolution
try:
    secret_key = st.secrets.get("GROQ_API_KEY", "")
except Exception:
    secret_key = ""

env_key = os.getenv("GROQ_API_KEY", "")
api_key = secret_key or env_key

# ---------------------------------------------------------
# DIALOG MODALS
# ---------------------------------------------------------
@st.dialog("✨ Why VERITAS AI?")
def open_why_veritas():
    st.markdown("### 🚀 How VERITAS AI Outperforms Standard AI Tools")
    st.write("Traditional single-prompt AI models often produce generalized answers. VERITAS AI deploys an **Autonomous Multi-Agent Architecture**:")
    st.markdown("""
    * 🕵️‍♂️ **Researcher Agent:** Performs autonomous context acquisition and ground-truth gathering.
    * 📊 **Analyst Agent:** Cross-checks findings, extracts quantitative trends, and isolates operational risks.
    * 📝 **Report Writer Agent:** Synthesizes multi-stage intelligence into executive-ready reports.
    * ⚡ **Ultra-Low Latency:** Powered by Groq's Llama 3.3 70B engine for fast execution.
    """)

@st.dialog("📜 Search History")
def open_history():
    st.markdown("### 🔍 Recent Search Queries")
    st.caption("Session history tracking")
    if st.session_state.search_history:
        for item in reversed(st.session_state.search_history):
            st.markdown(f"""
                <div class="history-card">
                    <div>
                        <span style="color:#F59E0B; margin-right:8px;">🔍</span>
                        <span class="history-query">{item['query']}</span>
                    </div>
                    <span class="history-time">{item['time']}</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No queries executed in this session yet.")

@st.dialog("👤 User Profile")
def open_profile():
    st.markdown("### 👤 Account Profile")
    st.text_input("User ID / Display Name:", value=st.session_state.username)
    st.text_input("Organization:", value="Data Science & Research Lab")
    st.text_input("Role:", value="Lead Intelligence Analyst")
    if st.button("Save Profile Settings"):
        st.success("Profile saved successfully!")

@st.dialog("🔐 Account Access")
def open_account():
    tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Sign Up"])
    with tab1:
        st.text_input("Email / Username", key="login_email", placeholder="user@veritasai.com")
        st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In"):
            st.session_state.is_logged_in = True
            st.session_state.username = "Anwar ul Haq"
            st.success("Logged in successfully!")
            st.rerun()

    with tab2:
        st.text_input("Full Name", placeholder="John Doe")
        st.text_input("Email Address", placeholder="name@domain.com")
        st.text_input("Create Password", type="password")
        if st.button("Create Account"):
            st.success("Account created successfully! You can now log in.")

# ---------------------------------------------------------
# HEADER & NAVIGATION ROW
# ---------------------------------------------------------
nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1, 1, 1, 1, 1])

with nav_col1:
    if st.button("🏠 Home", key="btn_home", use_container_width=True):
        st.rerun()
with nav_col2:
    if st.button("✨ Why?", key="btn_why", use_container_width=True):
        open_why_veritas()
with nav_col3:
    if st.button("📜 History", key="btn_hist", use_container_width=True):
        open_history()
with nav_col4:
    if st.button("👤 Profile", key="btn_prof", use_container_width=True):
        open_profile()
with nav_col5:
    btn_label = f"👤 {st.session_state.username.split()[0]}" if st.session_state.is_logged_in else "🔐 Login"
    if st.button(btn_label, key="btn_acc", use_container_width=True):
        open_account()

st.markdown("<hr style='border:1px solid #334155; margin-top:10px; margin-bottom:20px;'>", unsafe_allow_html=True)

# Main Branding Header
header_col1, header_col2 = st.columns([1.2, 5], vertical_alignment="center")

with header_col1:
    if os.path.exists("logo.jpg"):
        st.image(get_transparent_logo("logo.jpg"), width=110)
    elif os.path.exists("logo.png"):
        st.image(get_transparent_logo("logo.png"), width=110)
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=90)

with header_col2:
    st.markdown('<div class="company-title">VERITAS AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="company-subtitle">Multi-Agent AI Research Assistant • Autonomous Intelligence Studio</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
    <div class="notice-banner">
        <span class="notice-tag">📌 NOTE:</span>
        <span class="notice-text">
            Engineered by the <b>VERITAS AI Community</b> to eliminate research friction—deploying autonomous multi-agent orchestration to synthesize hours of cross-domain analysis into executive intelligence in seconds.
        </span>
    </div>
""", unsafe_allow_html=True)

ticker_message = "⚡ VERITAS AI PLATFORM • Autonomous Multi-Agent Synthesis • Powered by Groq Llama 3.3 70B Engine • Real-time Ground-Truth Research • Automated Risk & Market Trend Analytics • Direct Telemetry Logging"
st.markdown(f"""
    <div class="ticker-wrap">
        <div class="ticker-move">{ticker_message}</div>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 🤖 Active Agents")
    st.markdown("""
        <div class="agent-card">
            <span>🕵️‍♂️ <b>Researcher Agent</b></span>
            <span class="agent-status">Online</span>
        </div>
        <div class="agent-card">
            <span>📊 <b>Analyst Agent</b></span>
            <span class="agent-status">Online</span>
        </div>
        <div class="agent-card">
            <span>📝 <b>Writer Agent</b></span>
            <span class="agent-status">Online</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    with st.expander("📩 Submit Support / Complaint"):
        st.caption("Facing issues? Send a direct message to VERITAS AI support.")
        user_email = st.text_input("Your Email:", placeholder="name@domain.com")
        complaint_msg = st.text_area("Description of issue:", placeholder="Describe the issue...")
        
        if st.button("Send Complaint"):
            if user_email and complaint_msg:
                admin_email = "support@veritasai.com"
                subject = urllib.parse.quote("VERITAS AI Support Request")
                body = urllib.parse.quote(f"From: {user_email}\n\nMessage:\n{complaint_msg}")
                mailto_url = f"mailto:{admin_email}?subject={subject}&body={body}"
                st.success("Complaint prepared!")
                st.markdown(f'<a href="{mailto_url}" target="_blank" style="color:#FBBF24; font-weight:bold;">📧 Open Email App to Send Message</a>', unsafe_allow_html=True)
            else:
                st.warning("Please fill in both fields.")

# ---------------------------------------------------------
# MAIN WORKFLOW
# ---------------------------------------------------------
topic = st.text_input("Enter Research Topic or Query:", placeholder="e.g., Enterprise Risk Management in Autonomous Financial AI")

if st.button("🚀 Run Workflow"):
    if not api_key:
        st.error("⚠️ System Configuration Error: GROQ_API_KEY missing in Streamlit Secrets.")
    elif not topic.strip():
        st.warning("Please enter a research topic to proceed.")
    else:
        try:
            now_time = datetime.now().strftime("%I:%M %p")
            st.session_state.search_history.append({"time": now_time, "query": topic})

            # Append to Google Sheet via Webhook
            log_to_google_sheets(st.session_state.username, topic, "Success")

            client = Groq(api_key=api_key)
            model_name = "llama-3.3-70b-versatile"
            
            with st.status("⚡ Orchestrating VERITAS AI Agents...", expanded=True) as status:
                st.write("🕵️‍♂️ **Researcher Agent** gathering ground-truth insights...")
                res1 = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": f"Act as an expert researcher for VERITAS AI. Uncover key facts regarding: {topic}"}]
                )
                research_data = res1.choices[0].message.content
                time.sleep(1)
                
                st.write("📊 **Data Analyst Agent** structuring findings & key risks...")
                res2 = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": f"Act as a Senior Analyst at VERITAS AI. Extract top trends and risks from:\n\n{research_data}"}]
                )
                analysis_data = res2.choices[0].message.content
                time.sleep(1)
                
                st.write("📝 **Report Writer Agent** compiling executive synthesis...")
                res3 = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": f"Synthesize into an executive markdown report with Overview, Key Findings, Strategic Analysis, and Conclusion.\n\nResearch:\n{research_data}\n\nAnalysis:\n{analysis_data}"}]
                )
                final_report = res3.choices[0].message.content
                
                status.update(label="✅ VERITAS AI Research Workflow Complete!", state="complete", expanded=False)

            st.markdown("### 📋 Executive Summary")
            st.markdown(f'<div class="report-box">{final_report}</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.download_button(
                label="📥 Download Executive Report (.md)",
                data=final_report,
                file_name=f"VERITAS_AI_Report_{topic.replace(' ', '_')}.md",
                mime="text/markdown"
            )

        except Exception as e:
            log_to_google_sheets(st.session_state.username, topic, f"Failed: {str(e)}")
            st.error(f"Execution Error: {str(e)}")