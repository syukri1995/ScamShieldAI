from pathlib import Path

import networkx as nx
from pyvis.network import Network

from database.db import _connect


def get_network_graph(db_path: str | Path | None = None) -> nx.Graph:
    """Builds a NetworkX graph from the scam_events data."""
    G = nx.Graph()

    with _connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT sender_id, receiver_id, message_text, link, scam_score
            FROM scam_events
        """)
        events = cursor.fetchall()

    for sender_id, receiver_id, message_text, link, scam_score in events:
        if not sender_id:
            continue

        # Add scammer node
        G.add_node(
            sender_id, group="scammer", title=f"Scammer: {sender_id}", color="#EF4444"
        )

        # Add victim node
        if receiver_id:
            G.add_node(
                receiver_id,
                group="victim",
                title=f"Victim: {receiver_id}",
                color="#3B82F6",
            )
            G.add_edge(
                sender_id, receiver_id, title=f"Score: {scam_score}", weight=scam_score
            )

        # Add link node
        if link:
            # We could have multiple links separated by comma or just a single link text
            links = [l.strip() for l in link.split(",") if l.strip()]
            for l in links:
                G.add_node(l, group="link", title=f"Link: {l}", color="#EAB308")
                G.add_edge(sender_id, l)

    return G


def get_scam_clusters(G: nx.Graph) -> list[set]:
    """Detects clusters of scams using connected components."""
    # Find all connected components
    components = list(nx.connected_components(G))
    # Filter out single-node components to just find actual networks
    return [c for c in components if len(c) > 1]


def generate_pyvis_html(G: nx.Graph, output_path: str = "network_graph.html") -> str:
    """Generates a PyVis HTML string for the NetworkX graph."""
    net = Network(
        height="600px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
        notebook=False,
    )

    # Configure physics for better visualization of clusters
    net.force_atlas_2based()

    # Load NetworkX graph into PyVis
    net.from_nx(G)

    # Generate HTML file
    net.save_graph(output_path)

    with open(output_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    return html_content
