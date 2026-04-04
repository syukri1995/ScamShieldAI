import streamlit as st

from services.analyzer_service import analyze_and_store


def render() -> None:
    # Main heading and short instructions for the analyzer page.
    st.title("Scam Analyzer")
    st.write("Paste a suspicious message, email, or URL and get an AI scam risk score.")

    # Keep text input in session state so user content survives reruns.
    input_key = "analyzer_input_text"
    if input_key not in st.session_state:
        st.session_state[input_key] = ""

    # Optional helper sample for quick testing of the analyzer pipeline.
    with st.expander("Try a quick sample"):
        if st.button("Load phishing-like sample", use_container_width=True):
            st.session_state[input_key] = (
                "Urgent: Your bank account is suspended. Verify now at http://bit.ly/reset-now"
            )

    # Primary text area where users paste suspicious content.
    text_input = st.text_area(
        "Suspicious content",
        key=input_key,
        placeholder="Paste message/email/URL here...",
        height=180,
        help="Paste the full body of a suspicious email, text message, or a questionable URL to get a comprehensive risk analysis.",
    )

    # Run analysis only when the user explicitly clicks Analyze.
    if st.button("Analyze", type="primary", use_container_width=True):
        try:
            # Perform scoring and persistence in one service call.
            with st.spinner("Analyzing content..."):
                result = analyze_and_store(text_input)

            # Top-level result summary.
            st.subheader("Result")
            st.metric("Risk Score", f"{result['risk_score']}%")

            # 3-column layout: label, visualized risk, and simple confidence hint.
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Show a status badge based on model/service label.
                if result["label"] == "scam":
                    st.error("🚨 SCAM")
                elif result["label"] == "suspicious":
                    st.warning("⚠️ SUSPICIOUS")
                else:
                    st.success("✅ SAFE")
            
            with col2:
                # Duplicate metric plus progress bar for quick visual scanning.
                st.metric("Risk Level", f"{result['risk_score']}%")
                st.progress(min(max(result["risk_score"] / 100.0, 0.0), 1.0))
            
            with col3:
                # Confidence is presented as the inverse of risk score.
                st.write("**Confidence**")
                st.write(f"`{100 - result['risk_score']}%`")
            
            # Explainability section from analyzer output.
            st.divider()
            st.write("**Why this result:**")
            st.write(result["explanation"])
            
            # Show keywords only when matches were found.
            if result["matched_keywords"]:
                st.write("**Matched suspicious keywords:**")
                st.write(", ".join(result["matched_keywords"]))

        # ValueError is expected for invalid user input (e.g., empty text).
        except ValueError as exc:
            st.warning(str(exc))
        # Catch-all safeguard to keep UI responsive on unexpected failures.
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
