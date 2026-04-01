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
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["label"] = df["label"].astype(str)
    df["input_text"] = df["input_text"].astype(str)

    search_query = st.text_input("Search message text", placeholder="e.g. verify account, lottery")

    min_score, max_score = st.slider(
        "Risk score range",
        min_value=0,
        max_value=100,
        value=(0, 100),
        step=1,
    )

    label_options = sorted([str(x) for x in df["label"].unique()])
    label_filter = st.multiselect(
        "Filter by label",
        options=label_options,
        default=label_options,
    )

    filtered = df[df["label"].isin(label_filter)].copy()
    filtered = filtered[(filtered["risk_score"] >= min_score) & (filtered["risk_score"] <= max_score)]

    if search_query.strip():
        filtered = filtered[filtered["input_text"].str.contains(search_query.strip(), case=False, na=False)]

    filtered["input_preview"] = filtered["input_text"].str.slice(0, 100)

    c1, c2 = st.columns(2)
    c1.metric("Filtered Rows", len(filtered))
    c2.metric("Avg Risk", round(float(filtered["risk_score"].mean()), 2) if not filtered.empty else 0.0)

    st.dataframe(
        filtered[["created_at", "label", "risk_score", "input_preview", "explanation"]],
        use_container_width=True,
        hide_index=True,
    )
