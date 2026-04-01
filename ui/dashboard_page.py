import pandas as pd
import streamlit as st

from services.stats_service import get_dashboard_stats


def render() -> None:
    st.title("Analytics Dashboard")

    stats = get_dashboard_stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Scans", stats["total_scans"])
    c2.metric("Scam", stats["scam_count"])
    c3.metric("Safe/Suspicious", stats["safe_count"])

    dist_df = pd.DataFrame(
        {
            "label": ["scam", "safe_or_suspicious"],
            "count": [stats["scam_count"], stats["safe_count"]],
        }
    )
    st.subheader("Scam vs Safe")
    st.bar_chart(dist_df.set_index("label"))

    st.subheader("Most Common Scam Keywords")
    if stats["top_keywords"]:
        kw_df = pd.DataFrame(stats["top_keywords"], columns=["keyword", "count"])
        st.bar_chart(kw_df.set_index("keyword"))
    else:
        st.write("No keyword data yet.")
