import os
import time
import urllib.parse
import streamlit as st
from groq import Groq
from dotenv import load_dotenv
from PIL import Image, ImageDraw

# Load environment variables
load_dotenv()

DEFAULT_GROQ_KEY = ""

# Page Configuration
st.set_page_config(
    page_title="VERITAS AI • Autonomous Intelligence Studio",
    page_icon="⚜️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Advanced Custom CSS with Metallic Gold Highlights
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Vibrant Dark Slate Background */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }

    /* Glowing News Ticker / Announcement Marquee */
    .ticker-wrap {
        width: 100%;
        overflow: hidden;
        background: linear-gradient(90deg, rgba(217, 119, 6, 0.18), rgba(245, 158, 11, 0.18));
        border: 1px solid rgba(245, 158, 11, 0.4);
        border-radius: 10px;
        padding: 10px 0;
        margin-bottom: 25px;
        box-sizing: border-box;
        box-shadow: 0 4px 20px rgba(245, 158, 11, 0.15);
    }

    .ticker-move {
        display: inline-block;
        white-space: nowrap;
        padding-left: 100%;
        animation: ticker 22s linear infinite;
        font-weight: 700;
        color: #FBBF24;
        font-size: 0.95rem;
        letter-spacing: 0.6px;
    }

    @keyframes ticker {
        0%   { transform: translate3d(0, 0, 0); }
        100% { transform: translate3d(-100%, 0, 0); }
    }

    /* VERITAS AI Premium Gradient Title */
    .company-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #F59E0B, #D97706, #FBBF24, #FEF08A);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0rem;
        line-height: 1.1;
        letter-spacing: 1.5px;
    }
    
    .company-subtitle {
        color: #CBD5E1;
        font-size: 1rem;
        margin-top: 4px;
        font-weight: 500;
        letter-spacing: 0.5px;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1E293B;
        border-right: 1px solid #334155;
    }

    /* Input Field Styling */
    .stTextInput input {
        background-color: #334155 !important;
        color: #FFFFFF !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
    }
    .stTextInput input:focus {
        border-color: #F59E0B !important;
        box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.3) !important;
    }

    /* Modern Gold Action Button */
    div.stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #D97706 0%, #B45309 100%);
        color: #FFFFFF;
        font-weight: 700;
        font-size: 1.05rem;
        border-radius: 8px;
        padding: 0.75rem 1.2rem;
        border: none;
        transition: all 0.2s ease-in-out;
        box-shadow: 0px 4px 18px rgba(217, 119, 6, 0.35);
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
        transform: translateY(-2px);
        box-shadow: 0px 6px 22px rgba(245, 158, 11, 0.5);
    }

    /* Active Agent Display Cards */
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

    /* Executive Output Card Container */
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
# CORNER FLOOD-FILL BACKGROUND REMOVER FUNCTION
# ---------------------------------------------------------
def get_transparent_logo(image_path, tolerance=55):
    """Flood-fills from corners to isolate and remove outer background cleanly."""
    img = Image.open(image_path).convert("RGBA")
    width, height = img.size

    # Sample outer background color from top-left corner
    bg_color = img.getpixel((0, 0))[:3]

    # Mask image for flood fill
    mask = Image.new("L", (width, height), 0)
    
    # Perform flood fill from all 4 corners
    for corner in [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]:
        ImageDraw.floodfill(img, corner, (0, 0, 0, 0), thresh=tolerance)

    return img

# ---------------------------------------------------------
# SAFE AUTOMATIC API KEY RESOLUTION
# ---------------------------------------------------------
try:
    secret_key = st.secrets.get("GROQ_API_KEY", "")
except Exception:
    secret_key = ""

env_key = os.getenv("GROQ_API_KEY", DEFAULT_GROQ_KEY)
default_key_to_use = secret_key or env_key

# ---------------------------------------------------------
# SIDEBAR NAVIGATION & SUPPORT SYSTEM
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ Control Center")
    st.caption("Configure multi-agent parameters")
    
    groq_api_key = st.text_input(
        "Groq API Key", 
        value=default_key_to_use, 
        type="password",
        help="Loaded automatically from backend secrets or .env file if available."
    )
    
    st.markdown("---")
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
    
    # Support / Complaint Form
    with st.expander("📩 Submit Support / Complaint"):
        st.caption("Facing issues? Send a direct message to VERITAS AI support.")
        user_email = st.text_input("Your Email:", placeholder="name@domain.com")
        complaint_msg = st.text_area("Description of issue:", placeholder="Describe the issue or error...")
        
        if st.button("Send Complaint"):
            if user_email and complaint_msg:
                admin_email = "support@veritasai.com"
                subject = urllib.parse.quote("VERITAS AI Support Request")
                body = urllib.parse.quote(f"From: {user_email}\n\nMessage:\n{complaint_msg}")
                
                mailto_url = f"mailto:{admin_email}?subject={subject}&body={body}"
                
                st.success("Complaint prepared!")
                st.markdown(f'<a href="{mailto_url}" target="_blank" style="color:#FBBF24; font-weight:bold;">📧 Open Email App to Send Message</a>', unsafe_allow_html=True)
            else:
                st.warning("Please fill in both your email and description.")

# ---------------------------------------------------------
# HEADER SECTION: Dynamic Transparent VERITAS AI Logo
# ---------------------------------------------------------
header_col1, header_col2 = st.columns([1.2, 5], vertical_alignment="center")

with header_col1:
    if os.path.exists("logo.jpg"):
        clean_logo = get_transparent_logo("logo.jpg")
        st.image(clean_logo, width=130)
    elif os.path.exists("logo.png"):
        clean_logo = get_transparent_logo("logo.png")
        st.image(clean_logo, width=130)
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=95)

with header_col2:
    st.markdown('<div class="company-title">VERITAS AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="company-subtitle">Multi-Agent AI Research Assistant • Autonomous Intelligence Studio</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# RUNNING NEWS TICKER
# ---------------------------------------------------------
ticker_message = "🔴 LIVE: Welcome to VERITAS AI's Multi-Agent Research Portal • Automating deep-dive technical insights, risk analysis, and executive synthesis • Powered by Groq Llama 3.3 70B & Streamlit"

st.markdown(f"""
    <div class="ticker-wrap">
        <div class="ticker-move">{ticker_message}</div>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# MAIN WORKFLOW & AGENT EXECUTION
# ---------------------------------------------------------
topic = st.text_input("Enter Research Topic or Query:", placeholder="e.g., Enterprise Risk Management in Autonomous Financial AI")

col1, col2 = st.columns([1, 4])
with col1:
    run_button = st.button("🚀 Run Workflow")

if run_button:
    clean_key = str(groq_api_key).strip()
    
    if not clean_key:
        st.error("Please enter a valid Groq API Key or set GROQ_API_KEY in Streamlit Secrets / .env file.")
    elif not topic:
        st.warning("Please enter a research topic to proceed.")
    else:
        try:
            client = Groq(api_key=clean_key)
            model_name = "llama-3.3-70b-versatile"
            
            with st.status("⚡ Orchestrating VERITAS AI Agents...", expanded=True) as status:
                
                # Agent 1: Research
                st.write("🕵️‍♂️ **Researcher Agent** gathering ground-truth insights...")
                research_prompt = f"Act as an expert researcher for VERITAS AI. Uncover key facts, figures, and technical insights regarding: {topic}."
                res1 = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": research_prompt}]
                )
                research_data = res1.choices[0].message.content
                time.sleep(1)
                
                # Agent 2: Analysis
                st.write("📊 **Data Analyst Agent** structuring findings & key risks...")
                analysis_prompt = f"Act as a Senior Analyst at VERITAS AI. Take these research findings and extract top trends, risks, and strategic takeaways:\n\n{research_data}"
                res2 = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": analysis_prompt}]
                )
                analysis_data = res2.choices[0].message.content
                time.sleep(1)
                
                # Agent 3: Final Report
                st.write("📝 **Report Writer Agent** compiling executive synthesis...")
                report_prompt = f"""Act as a Chief Executive Report Writer for VERITAS AI. Synthesize the research and analysis into a polished executive markdown report with sections for Overview, Key Findings, Strategic Analysis, and Conclusion.

Research:
{research_data}

Analysis:
{analysis_data}"""
                res3 = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": report_prompt}]
                )
                final_report = res3.choices[0].message.content
                
                status.update(label="✅ VERITAS AI Research Workflow Complete!", state="complete", expanded=False)

            # Styled Executive Report Output
            st.markdown("### 📋 Executive Summary")
            
            with st.container():
                st.markdown(f'<div class="report-box">{final_report}</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.download_button(
                label="📥 Download Executive Report (.md)",
                data=final_report,
                file_name=f"VERITAS_AI_Report_{topic.replace(' ', '_')}.md",
                mime="text/markdown"
            )

        except Exception as e:
            st.error(f"Execution Error: {str(e)}")