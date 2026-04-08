import streamlit as st
import streamlit.components.v1 as components
import tempfile
import os

from services.scam_network import get_network_graph, get_scam_clusters, generate_pyvis_html
from services.risk_engine import get_blocked_users, get_top_dangerous_accounts, unblock_user

def render_network_dashboard() -> None:
    st.title("Scam Network Visualization")

    st.markdown(
        "Interactive graph showing relationships between scam accounts, victims, and malicious links. "
        "Scammers are red, victims are blue, and links are yellow."
    )

    # Generate and display graph
    with st.spinner("Generating network graph..."):
        try:
            G = get_network_graph()

            if len(G.nodes) == 0:
                st.info("No network data available yet. Scans will populate this graph.")
            else:
                # Detect clusters
                clusters = get_scam_clusters(G)
                st.caption(f"Detected **{len(clusters)}** potential scam network clusters.")

                # We use a temporary file to save the PyVis HTML
                with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
                    html_path = tmp_file.name

                html_content = generate_pyvis_html(G, output_path=html_path)

                # Display in Streamlit
                components.html(html_content, height=650)

                # Cleanup temp file
                if os.path.exists(html_path):
                    os.remove(html_path)
        except Exception as e:
            st.error(f"Error rendering graph: {e}")

def render_blocked_accounts() -> None:
    st.title("Blocked Accounts")

    st.markdown("Accounts automatically flagged and blocked by the risk engine.")

    # Unblock action handling
    if "unblock_id" in st.session_state and st.session_state.unblock_id:
        user_id = st.session_state.unblock_id
        try:
            unblock_user(user_id)
            st.success(f"Successfully unblocked {user_id}.")
        except Exception as e:
            st.error(f"Failed to unblock {user_id}: {e}")
        st.session_state.unblock_id = None

    blocked = get_blocked_users()

    if not blocked:
        st.success("No accounts are currently blocked.")
    else:
        # Display as table with an unblock button
        cols = st.columns((2, 1, 1, 1, 1))
        cols[0].write("**User ID**")
        cols[1].write("**Scam Count**")
        cols[2].write("**Risk Score**")
        cols[3].write("**Status**")
        cols[4].write("**Action**")

        st.divider()

        for user in blocked:
            cols = st.columns((2, 1, 1, 1, 1))
            cols[0].write(user["user_id"])
            cols[1].write(str(user["scam_count"]))
            cols[2].write(f"{user['risk_score']:.2f}")
            cols[3].write(f"🛑 {user['status'].upper()}")

            # Using a callback for unblocking
            button_key = f"unblock_{user['user_id']}"
            if cols[4].button("Unblock", key=button_key, help=f"Unblock {user['user_id']}"):
                st.session_state.unblock_id = user["user_id"]
                st.rerun()

    st.divider()

    st.subheader("Top 10 Most Dangerous Accounts")
    dangerous_accounts = get_top_dangerous_accounts()

    if dangerous_accounts:
        st.dataframe(
            dangerous_accounts,
            column_config={
                "user_id": "User ID",
                "scam_count": "Scam Count",
                "risk_score": st.column_config.ProgressColumn(
                    "Risk Score",
                    help="Accumulated risk score",
                    format="%.2f",
                    min_value=0,
                    max_value=max(10.0, max([a["risk_score"] for a in dangerous_accounts] + [0]))
                ),
                "status": "Status"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No risk data available.")
