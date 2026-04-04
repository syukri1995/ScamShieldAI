import streamlit as st

from database.db import init_db
from ui import analyzer_page, dashboard_page, history_page

# Configure global Streamlit settings and ensure database schema exists at startup.
st.set_page_config(page_title="ScamShield AI", page_icon="🛡", layout="wide")
init_db()

# Simple sidebar router to switch between app pages.
st.sidebar.title("ScamShield AI")
page = st.sidebar.radio("Navigate", ["Analyzer", "History", "Dashboard"])

if page == "Analyzer":
    analyzer_page.render()
elif page == "History":
    history_page.render()
else:
    dashboard_page.render()
