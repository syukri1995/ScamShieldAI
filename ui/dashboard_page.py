import pandas as pd
import streamlit as st

from services.stats_service import get_dashboard_stats


def _render_distribution_fallback(dist_df: pd.DataFrame) -> None:
    total = max(1, int(dist_df["count"].sum()))
    for _, row in dist_df.iterrows():
        label = str(row["label"]).title()
        count = int(row["count"])
        ratio = min(1.0, max(0.0, count / total))
        st.write(f"{label}: {count}")
        st.progress(ratio)


def _render_keywords_fallback(kw_df: pd.DataFrame) -> None:
    total = max(1, int(kw_df["count"].sum()))
    for _, row in kw_df.iterrows():
        keyword = str(row["keyword"])
        count = int(row["count"])
        ratio = min(1.0, max(0.0, count / total))
        st.write(f"{keyword}: {count}")
        st.progress(ratio)


def render() -> None:
    # Dashboard overview with key scan metrics and trends.
    st.title("Analytics Dashboard")

    stats = get_dashboard_stats()
    # KPI cards for quick status visibility.
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Scans", stats["total_scans"])
    c2.metric("Scam", stats["scam_count"])
    c3.metric("Suspicious", stats["suspicious_count"])
    c4.metric("Scam Rate", f"{stats['scam_rate']}%")

    st.caption(f"Safe messages: {stats['safe_count']}")

    dist_df = pd.DataFrame(
        {
            "label": ["scam", "suspicious", "safe"],
            "count": [
                stats["scam_count"],
                stats["suspicious_count"],
                stats["safe_count"],
            ],
        }
    )
    # Distribution chart by predicted label.
    st.subheader("Label Distribution")
    _render_distribution_fallback(dist_df)
    st.dataframe(dist_df, hide_index=True, use_container_width=True)

    st.subheader("Most Common Scam Keywords")
    if stats["top_keywords"]:
        kw_df = pd.DataFrame(stats["top_keywords"], columns=["keyword", "count"])
        _render_keywords_fallback(kw_df)
        st.dataframe(kw_df, hide_index=True, use_container_width=True)
    else:
        st.write("No keyword data yet.")
