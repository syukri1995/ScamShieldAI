import pandas as pd
import streamlit as st

from services.stats_service import get_scan_history


def render() -> None:
    # History browser for previously analyzed messages.
    st.title("Scan History")

    history = get_scan_history(limit=500)
    if not history:
        st.info("No scans yet. Analyze content first.")
        return

    # Normalize key fields for robust filtering and display.
    df = pd.DataFrame(history)
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["label"] = df["label"].astype(str)
    df["input_text"] = df["input_text"].astype(str)

    # Text, score, and label filters.
    search_query = st.text_input(
        "Search message text",
        placeholder="e.g. verify account, lottery",
        help="Search for specific keywords within the analyzed messages.",
    )

    min_score, max_score = st.slider(
        "Risk score range",
        min_value=0,
        max_value=100,
        value=(0, 100),
        step=1,
        help="0 is completely safe, 100 is highly suspicious.",
    )

    label_options = sorted([str(x) for x in df["label"].unique()])
    label_filter = st.multiselect(
        "Filter by label",
        options=label_options,
        default=label_options,
        help="Select the categories of scans you want to view.",
    )

    # Apply selected filters to a working dataframe copy.
    filtered = df[df["label"].isin(label_filter)].copy()
    filtered = filtered[
        (filtered["risk_score"] >= min_score) & (filtered["risk_score"] <= max_score)
    ]

    if search_query.strip():
        filtered = filtered[
            filtered["input_text"].str.contains(
                search_query.strip(), case=False, na=False, regex=False
            )
        ]

    # Show shortened preview to keep table compact.
    filtered["input_preview"] = filtered["input_text"].str.slice(0, 100)
    if "ai_tips" in filtered.columns:
        filtered["ai_tips_preview"] = (
            filtered["ai_tips"].fillna("").astype(str).str.slice(0, 120)
        )

    # Quick summary for currently filtered set.
    c1, c2 = st.columns(2)
    c1.metric("Filtered Rows", len(filtered))
    c2.metric(
        "Avg Risk",
        round(float(filtered["risk_score"].mean()), 2) if not filtered.empty else 0.0,
    )

    display_columns = [
        "created_at",
        "label",
        "risk_score",
        "input_preview",
        "explanation",
    ]
    if "ai_tips_preview" in filtered.columns:
        display_columns.append("ai_tips_preview")

    st.dataframe(filtered[display_columns], use_container_width=True, hide_index=True)
