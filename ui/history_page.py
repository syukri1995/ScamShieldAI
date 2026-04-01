import pandas as pd
import streamlit as st

from services.stats_service import get_scan_history


def render() -> None:
    st.title("Scan History")

    history = get_scan_history(limit=500)
    if not history:
        st.info("No scans yet. Analyze content first.")
        return

    df = pd.DataFrame(history)
    label_filter = st.multiselect(
        "Filter by label",
        options=sorted(df["label"].unique().tolist()),
        default=sorted(df["label"].unique().tolist()),
    )

    filtered = df[df["label"].isin(label_filter)].copy()
    filtered["input_preview"] = filtered["input_text"].str.slice(0, 100)

    st.dataframe(
        filtered[["created_at", "label", "risk_score", "input_preview", "explanation"]],
        use_container_width=True,
        hide_index=True,
    )
