import streamlit as st

from services.analyzer_service import analyze_and_store


def render() -> None:
    st.title("Scam Analyzer")
    st.write("Paste a suspicious message, email, or URL and get an AI scam risk score.")

    input_key = "analyzer_input_text"
    if input_key not in st.session_state:
        st.session_state[input_key] = ""

    with st.expander("Try a quick sample"):
        if st.button("Load phishing-like sample", use_container_width=True):
            st.session_state[input_key] = (
                "Urgent: Your bank account is suspended. Verify now at http://bit.ly/reset-now"
            )

    text_input = st.text_area(
        "Suspicious content",
        key=input_key,
        placeholder="Paste message/email/URL here...",
        height=180,
    )

    if st.button("Analyze", type="primary", use_container_width=True):
        try:
            with st.spinner("Analyzing content..."):
                result = analyze_and_store(text_input)

            st.subheader("Result")
            st.metric("Risk Score", f"{result['risk_score']}%")

            if result["label"] == "scam":
                st.error("Label: SCAM")
            elif result["label"] == "suspicious":
                st.warning("Label: SUSPICIOUS")
            else:
                st.success("Label: SAFE")

            st.progress(min(max(result["risk_score"] / 100.0, 0.0), 1.0))
            st.write("**Why this result:**")
            st.write(result["explanation"])

            if result["matched_keywords"]:
                st.write("**Matched suspicious keywords:**")
                st.write(", ".join(result["matched_keywords"]))

        except ValueError as exc:
            st.warning(str(exc))
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
