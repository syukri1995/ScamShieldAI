import json
from pathlib import Path
from typing import Any

try:
    import networkx as nx
except Exception:  # pragma: no cover - compatibility fallback for Python 3.14
    nx = None

from database.db import _connect


class SimpleGraph:
    """Minimal graph implementation used when networkx is unavailable."""

    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: list[tuple[str, str, dict[str, Any]]] = []

    def add_node(self, node_id: str, **attrs: Any) -> None:
        existing = self.nodes.get(node_id, {})
        existing.update(attrs)
        self.nodes[node_id] = existing

    def add_edge(self, source: str, target: str, **attrs: Any) -> None:
        self.edges.append((source, target, attrs))


def _new_graph() -> Any:
    if nx is not None:
        return nx.Graph()
    return SimpleGraph()


def get_network_graph(db_path: str | Path | None = None) -> Any:
    """Builds a NetworkX graph from the scam_events data."""
    G = _new_graph()

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


def _simple_connected_components(G: SimpleGraph) -> list[set[str]]:
    adjacency: dict[str, set[str]] = {node: set() for node in G.nodes}
    for source, target, _ in G.edges:
        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set()).add(source)

    visited: set[str] = set()
    components: list[set[str]] = []

    for start_node in adjacency:
        if start_node in visited:
            continue
        stack = [start_node]
        component: set[str] = set()
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            component.add(node)
            for neighbor in adjacency.get(node, set()):
                if neighbor not in visited:
                    stack.append(neighbor)
        components.append(component)

    return components


def get_scam_clusters(G: Any) -> list[set]:
    """Detects clusters of scams using connected components."""
    # Find all connected components
    if nx is not None:
        components = list(nx.connected_components(G))
    else:
        components = _simple_connected_components(G)

    # Filter out single-node components to just find actual networks
    return [c for c in components if len(c) > 1]


def _generate_vis_network_html_from_simple_graph(G: SimpleGraph) -> str:
    nodes_payload = []
    for node_id, attrs in G.nodes.items():
        nodes_payload.append(
            {
                "id": node_id,
                "label": str(node_id),
                "title": attrs.get("title", str(node_id)),
                "group": attrs.get("group", "unknown"),
                "color": attrs.get("color"),
            }
        )

    edges_payload = []
    for source, target, attrs in G.edges:
        edges_payload.append(
            {
                "from": source,
                "to": target,
                "title": attrs.get("title", ""),
                "value": attrs.get("weight", 1),
            }
        )

    nodes_json = json.dumps(nodes_payload)
    edges_json = json.dumps(edges_payload)

    return f"""
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <script src=\"https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js\"></script>
  <style>
    html, body {{ margin: 0; padding: 0; background: #ffffff; }}
    #mynetwork {{ width: 100%; height: 600px; border: 1px solid #e5e7eb; border-radius: 12px; }}
  </style>
</head>
<body>
  <div id=\"mynetwork\"></div>
  <script>
    const nodes = new vis.DataSet({nodes_json});
    const edges = new vis.DataSet({edges_json});
    const container = document.getElementById('mynetwork');
    const data = {{ nodes, edges }};
    const options = {{
      physics: {{
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {{ gravitationalConstant: -35, springLength: 160 }},
        stabilization: {{ iterations: 150 }}
      }},
      nodes: {{ shape: 'dot', size: 16, font: {{ color: '#111827', size: 14 }} }},
      edges: {{ color: {{ color: '#9ca3af' }}, smooth: true, arrows: {{ to: false }} }},
      interaction: {{ hover: true, navigationButtons: true, keyboard: true }}
    }};
    new vis.Network(container, data, options);
  </script>
</body>
</html>
""".strip()


def generate_pyvis_html(G: Any, output_path: str = "network_graph.html") -> str:
    """Generates a PyVis HTML string for the NetworkX graph."""
    try:
        from pyvis.network import Network

        net = Network(
            height="600px",
            width="100%",
            bgcolor="#ffffff",
            font_color="black",
            notebook=False,
        )

        # Configure physics for better visualization of clusters
        net.force_atlas_2based()

        # Load graph into PyVis
        if nx is not None:
            net.from_nx(G)
        else:
            for node_id, attrs in G.nodes.items():
                net.add_node(node_id, **attrs)
            for source, target, attrs in G.edges:
                net.add_edge(source, target, **attrs)

        # Generate HTML file
        net.save_graph(output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except Exception:
        # Fallback renderer for environments where pyvis/networkx are incompatible.
        if isinstance(G, SimpleGraph):
            html_content = _generate_vis_network_html_from_simple_graph(G)
        else:
            # Convert networkx-like object to SimpleGraph structure if available.
            fallback_graph = SimpleGraph()
            for node_id, attrs in G.nodes(data=True):
                fallback_graph.add_node(node_id, **attrs)
            for source, target, attrs in G.edges(data=True):
                fallback_graph.add_edge(source, target, **attrs)
            html_content = _generate_vis_network_html_from_simple_graph(fallback_graph)

    return html_content
