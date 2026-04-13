import html
import json
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from database.db import fetch_random_history
from services.analyzer_service import analyze_and_store


def _inject_styles() -> None:
    css_path = Path(__file__).with_name("analyzer_page.css")
    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True
    )


def _escape_and_break(text: str) -> str:
    return html.escape(text).replace("\n", "<br>")


def _tone_for(label: str) -> tuple[str, str, str, str, str]:
    if label == "safe":
        return (
            "ss-tone-safe",
            "ss-tone-safe-alert",
            "SAFE MESSAGE",
            "Security Notice",
            "The content appears safe. Keep normal caution and never share OTP or passwords.",
        )
    if label == "suspicious":
        return (
            "ss-tone-suspicious",
            "ss-tone-suspicious-alert",
            "SUSPICIOUS SIGNAL",
            "Security Warning",
            "Potential scam signs detected. Verify sender identity before clicking links or replying.",
        )
    return (
        "",
        "",
        "SCAMSHIELD ACTIVE",
        "Security Alert",
        "High scam probability. Do not click links, do not share data, and report the sender.",
    )


def render() -> None:
    _inject_styles()

    st.title("Analyzer")
    st.caption(
        "Smartphone-style threat analysis for suspicious SMS, email text, and URLs."
    )

    # Keep text input in session state so user content survives reruns.
    input_key = "analyzer_input_text"
    sender_key = "analyzer_sender_text"
    sender_display_key = "analyzer_sender_display"
    result_key = "analyzer_latest_result"
    message_key = "analyzer_latest_message"
    error_key = "analyzer_last_error"

    if input_key not in st.session_state:
        st.session_state[input_key] = ""
    if sender_key not in st.session_state:
        st.session_state[sender_key] = ""
    if sender_display_key not in st.session_state:
        st.session_state[sender_display_key] = "Unknown Sender"
    if result_key not in st.session_state:
        st.session_state[result_key] = None
    if message_key not in st.session_state:
        st.session_state[message_key] = ""
    if error_key not in st.session_state:
        st.session_state[error_key] = ""

    result = st.session_state[result_key]
    latest_message = st.session_state[message_key]
    time_label = datetime.now().strftime("%I:%M %p").lstrip("0")

    left_col, right_col = st.columns([1, 1], gap="large")
    send_clicked = False

    with left_col:
        content_html = ""
        if result:
            card_tone, alert_tone, risk_title, alert_title, advice = _tone_for(
                result["label"]
            )
            score = f"{result['risk_score']:.0f}%"
            ai_tips = str(result.get("ai_tips") or "").strip()
            ai_tips_html = ""
            if ai_tips:
                ai_tips_html = (
                    '<div class="ss-alert-head" style="margin-top:8px;">AI response tips</div>'
                    f'<div class="ss-alert-body">{_escape_and_break(ai_tips)}</div>'
                )

            chip_items = result.get("matched_keywords", [])
            chips = "".join(
                [
                    f'<span class="ss-chip">{html.escape(str(item))}</span>'
                    for item in chip_items
                ]
            )

            if latest_message:
                thread_html = (
                    f'<div class="ss-thread">'
                    f'<div class="ss-from">Scammer</div>'
                    f'<div class="ss-msg">{_escape_and_break(latest_message)}</div>'
                    f'<div class="ss-alert {alert_tone}">'
                    f'<div class="ss-alert-head">{alert_title}</div>'
                    f'<div class="ss-alert-body">{html.escape(advice)}</div>'
                    f"{ai_tips_html}"
                    "</div>"
                    "</div>"
                )
            else:
                thread_html = (
                    f'<div class="ss-thread">'
                    f'<div class="ss-alert {alert_tone}">'
                    f'<div class="ss-alert-head">{alert_title}</div>'
                    f'<div class="ss-alert-body">{html.escape(advice)}</div>'
                    f"{ai_tips_html}"
                    "</div>"
                    "</div>"
                )

            content_html = (
                f'<div class="ss-risk-card {card_tone}">'
                '<div class="ss-risk-head">'
                f'<div class="ss-risk-title">{risk_title}</div>'
                "<div>"
                f'<div class="ss-risk-score">{score}</div>'
                '<div class="ss-risk-label">Risk Score</div>'
                "</div>"
                "</div>"
                f'<div class="ss-chip-row">{chips}</div>'
                "</div>"
                f'<div class="ss-meta">TODAY, {time_label}</div>'
                f"{thread_html}"
            )
        else:
            content_html = (
                '<div class="ss-empty">'
                "Enter a message below to analyze scam risk and receive a live inline warning card."
                "</div>"
            )

        error_html = ""
        if st.session_state[error_key]:
            error_html = f'<div class="ss-inline-error">{html.escape(st.session_state[error_key])}</div>'

        phone_html = (
            '<div class="ss-phone-wrap">'
            '<div class="ss-phone-frame">'
            '<div class="ss-top-notch"></div>'
            '<div class="ss-header">'
            f'<p class="ss-header-title">{html.escape(str(st.session_state.get(sender_display_key, "Unknown Sender")) or "Unknown Sender")}</p>'
            '<div class="ss-header-sub">ScamShield live detection</div>'
            "</div>"
            f'<div class="ss-content">{content_html}{error_html}</div>'
            "</div>"
            "</div>"
        )
        st.markdown(phone_html, unsafe_allow_html=True)

        # Bottom composer-style input that triggers analysis.
        with st.form("analyzer_compose_form", clear_on_submit=True, border=False):
            st.markdown('<div class="ss-compose-wrap">', unsafe_allow_html=True)
            st.markdown('<div class="ss-field-label">Sender</div>', unsafe_allow_html=True)
            st.text_input(
                "Sender",
                key=sender_key,
                label_visibility="collapsed",
                placeholder="Sender name,ID or leave blank for unknown",
            )
            st.markdown('<div class="ss-compose-row">', unsafe_allow_html=True)
            compose_col, send_col = st.columns([5, 1], vertical_alignment="center")
            with compose_col:
                st.text_input(
                    "Enter your message",
                    key=input_key,
                    label_visibility="collapsed",
                    placeholder="Enter your message...",
                    help="Paste an SMS, email, or URL here to analyze it for scams or phishing.",
                )

                # Fetch random history and generate Javascript for dropdown overlay
                history_items = fetch_random_history(limit=4)

                # We need to escape the texts properly for javascript string literal inclusion
                js_array = (
                    json.dumps(history_items)
                    .replace("<", "\\u003c")
                    .replace(">", "\\u003e")
                    .replace("&", "\\u0026")
                )

                dropdown_js = f"""
                <script>
                (function() {{
                    const suggestions = {js_array};
                    if (!suggestions || suggestions.length === 0) return;

                    function setupDropdown() {{
                        // We are inside an iframe (Streamlit HTML component)
                        // Streamlit app DOM is in the parent window
                        const parentDoc = window.parent.document;
                        const inputEl = parentDoc.querySelector('input[aria-label="Enter your message"]');

                        if (!inputEl) {{
                            setTimeout(setupDropdown, 200);
                            return;
                        }}

                        // Prevent adding multiple times
                        if (inputEl.dataset.dropdownInjected) return;
                        inputEl.dataset.dropdownInjected = 'true';

                        // Ensure parent has relative positioning so our absolute div stays near
                        const inputContainer = inputEl.closest('div[data-baseweb="input"]').parentNode;
                        if(inputContainer) {{
                            inputContainer.style.position = 'relative';
                        }}

                        const dropdown = parentDoc.createElement('div');
                        dropdown.setAttribute('role', 'listbox');
                        dropdown.setAttribute('aria-label', 'Message suggestions');
                        dropdown.style.cssText = `
                            position: absolute;
                            top: 100%;
                            left: 0;
                            right: 0;
                            background-color: rgba(255, 255, 255, 0.92);
                            border: 1px solid #d1d5db;
                            border-radius: 8px;
                            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                            z-index: 9999;
                            margin-top: 4px;
                            display: none;
                            backdrop-filter: blur(4px);
                            overflow: hidden;
                        `;

                        suggestions.forEach((text, index) => {{
                            const item = parentDoc.createElement('div');
                            // Truncate long texts
                            const displayText = text.length > 50 ? text.substring(0, 47) + '...' : text;
                            item.textContent = displayText;
                            item.setAttribute('role', 'option');
                            item.setAttribute('aria-selected', 'false');
                            item.style.cssText = `
                                padding: 8px 12px;
                                cursor: pointer;
                                font-size: 14px;
                                color: #374151;
                                border-bottom: ${{index < suggestions.length - 1 ? '1px solid #f3f4f6' : 'none'}};
                                transition: background-color 0.1s;
                                white-space: nowrap;
                                overflow: hidden;
                                text-overflow: ellipsis;
                            `;

                            item.onmouseover = () => item.style.backgroundColor = 'rgba(243, 244, 246, 0.9)';
                            item.onmouseout = () => item.style.backgroundColor = 'transparent';

                            item.onmousedown = (e) => {{
                                // Use mousedown instead of click to fire before input blur event
                                e.preventDefault();

                                // React uses a setter to detect input changes, just setting .value isn't enough
                                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                                nativeInputValueSetter.call(inputEl, text);

                                const ev = new Event('input', {{ bubbles: true }});
                                inputEl.dispatchEvent(ev);

                                dropdown.style.display = 'none';
                            }};
                            dropdown.appendChild(item);
                        }});

                        if (inputContainer) {{
                            inputContainer.appendChild(dropdown);
                        }}

                        inputEl.addEventListener('focus', () => {{
                            dropdown.style.display = 'block';
                        }});

                        inputEl.addEventListener('blur', () => {{
                            dropdown.style.display = 'none';
                        }});
                    }}

                    setupDropdown();
                }})();
                </script>
                """
                components.html(dropdown_js, height=0)

            with send_col:
                send_clicked = st.form_submit_button(
                    "Send",
                    use_container_width=True,
                    help="Analyze this message for potential scams.",
                )

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(
                '<div class="ss-composer-tip">Tip: Paste full SMS or email body for better analysis.</div>',
                unsafe_allow_html=True,
            )

    with right_col:
        st.subheader("Analysis Details")

        if result:
            st.metric("Risk Score", f"{result['risk_score']:.2f}%")
            st.metric(
                "Confidence", f"{max(0.0, 100.0 - float(result['risk_score'])):.2f}%"
            )
            st.write(f"**Label:** {str(result.get('label', '')).upper()}")
            st.write("**Why this result**")
            st.write(str(result.get("explanation", "-")))

            ai_tips = str(result.get("ai_tips") or "").strip()
            if ai_tips:
                st.write("**AI response tips**")
                st.write(ai_tips)
            elif str(result.get("label", "")).lower() == "safe":
                st.caption("AI tips are generated only for suspicious or scam results.")
            else:
                st.caption(
                    "AI tips are currently unavailable. Check API key or provider connectivity."
                )

            keywords = result.get("matched_keywords", [])
            st.write("**Matched keywords**")
            if keywords:
                st.write(", ".join([str(item) for item in keywords]))
            else:
                st.write("No keyword matches found.")

            if latest_message:
                st.write("**Latest analyzed message**")
                st.caption(latest_message[:300])
        else:
            st.info(
                "Run an analysis from the phone panel to populate detailed metrics here."
            )

        st.markdown(
            '<p class="ss-side-note">This panel is optimized for desktop while the smartphone panel mirrors your intended end-user chat experience.</p>',
            unsafe_allow_html=True,
        )

    if send_clicked:
        try:
            text_input = st.session_state.get(input_key, "")
            sender_input = str(st.session_state.get(sender_key, "")).strip() or None
            st.session_state[sender_display_key] = sender_input or "Unknown Sender"
            # Perform scoring and persistence in one service call.
            with st.spinner("Analyzing content..."):
                result = analyze_and_store(text_input, sender_id=sender_input)
            st.session_state[result_key] = result
            st.session_state[message_key] = text_input.strip()
            st.session_state[error_key] = ""
            st.rerun()

        # ValueError is expected for invalid user input (e.g., empty text).
        except ValueError as exc:
            st.session_state[error_key] = str(exc)
            st.rerun()
        # Catch-all safeguard to keep UI responsive on unexpected failures.
        except Exception as exc:
            st.session_state[error_key] = f"Analysis failed: {exc}"
            st.rerun()
