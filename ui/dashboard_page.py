import pandas as pd
import streamlit as st

from services.stats_service import get_dashboard_stats


def render() -> None:
    st.title("Analytics Dashboard")

    stats = get_dashboard_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Scans", stats["total_scans"])
    c2.metric("Scam", stats["scam_count"])
    c3.metric("Suspicious", stats["suspicious_count"])
    c4.metric("Scam Rate", f"{stats['scam_rate']}%")

    st.caption(f"Safe messages: {stats['safe_count']}")

    dist_df = pd.DataFrame(
        {
            "label": ["scam", "suspicious", "safe"],
            "count": [stats["scam_count"], stats["suspicious_count"], stats["safe_count"]],
        }
    )
    st.subheader("Label Distribution")
    st.bar_chart(dist_df.set_index("label"))

    st.subheader("Most Common Scam Keywords")
    if stats["top_keywords"]:
        kw_df = pd.DataFrame(stats["top_keywords"], columns=["keyword", "count"])
        st.bar_chart(kw_df.set_index("keyword"))
    else:
        st.write("No keyword data yet.")
