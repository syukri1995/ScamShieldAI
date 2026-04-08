import streamlit as st

from database.db import init_db
from ui import analyzer_page, dashboard_page, history_page, network_dashboard

# Configure global Streamlit settings and ensure database schema exists at startup.
st.set_page_config(page_title="ScamShield AI", page_icon="🛡️", layout="wide")
init_db()

# Professional sidebar header with a logo/icon and styled title
st.sidebar.markdown(
    """
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="margin-bottom: 0px; color: #0F172A; font-size: 26px; font-weight: 800; letter-spacing: -0.5px;">
            <span style="color: #2563EB;">🛡️</span> ScamShield
        </h1>
        <p style="color: #64748B; font-size: 13px; margin-top: 2px; font-weight: 500;">
            AI Threat Analysis
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown('<p style="font-size: 12px; font-weight: 600; color: #94A3B8; margin-bottom: -10px; text-transform: uppercase; letter-spacing: 1px;">Menu</p>', unsafe_allow_html=True)

# Simple sidebar router to switch between app pages using styled labels.
page = st.sidebar.radio(
    "Navigate",
    ["🔍 Analyzer", "📜 History", "📊 Analytics Dashboard", "🕸️ Network Visualization", "🚫 Blocked Accounts"],
    label_visibility="collapsed"
)

st.sidebar.divider()

# Footer in the sidebar
st.sidebar.markdown(
    """
    <div style="font-size: 12px; color: #94A3B8; text-align: center; margin-top: 20px;">
        <p style="margin-bottom: 4px;">Protecting against phishing, smishing, and scam links.</p>
        <p style="font-weight: 600;">© ScamShield AI</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if page == "🔍 Analyzer":
    analyzer_page.render()
elif page == "📜 History":
    history_page.render()
elif page == "📊 Analytics Dashboard":
    dashboard_page.render()
elif page == "🕸️ Network Visualization":
    network_dashboard.render_network_dashboard()
elif page == "🚫 Blocked Accounts":
    network_dashboard.render_blocked_accounts()
