from unittest.mock import MagicMock, patch
from services.scam_network import get_scam_clusters

def test_get_scam_clusters_empty():
    """Test get_scam_clusters with an empty graph."""
    mock_G = MagicMock()
    # Mock networkx.connected_components to return an empty generator
    with patch("networkx.connected_components", return_value=iter([])):
        clusters = get_scam_clusters(mock_G)
        assert clusters == []

def test_get_scam_clusters_single_node_components():
    """Test get_scam_clusters with only single-node components."""
    mock_G = MagicMock()
    # Mock networkx.connected_components to return single-node sets
    components = [{"node1"}, {"node2"}, {"node3"}]
    with patch("networkx.connected_components", return_value=iter(components)):
        clusters = get_scam_clusters(mock_G)
        assert clusters == []

def test_get_scam_clusters_mixed_components():
    """Test get_scam_clusters with both single-node and multi-node components."""
    mock_G = MagicMock()
    # Mock networkx.connected_components to return a mix of components
    components = [
        {"node1"},                # Single node
        {"node2", "node3"},       # Two nodes
        {"node4"},                # Single node
        {"node5", "node6", "7"}   # Three nodes
    ]
    with patch("networkx.connected_components", return_value=iter(components)):
        clusters = get_scam_clusters(mock_G)
        # Should only return components with length > 1
        assert len(clusters) == 2
        assert {"node2", "node3"} in clusters
        assert {"node5", "node6", "7"} in clusters

def test_get_scam_clusters_all_multi_node():
    """Test get_scam_clusters where all components are multi-node."""
    mock_G = MagicMock()
    components = [
        {"a", "b"},
        {"c", "d", "e"}
    ]
    with patch("networkx.connected_components", return_value=iter(components)):
        clusters = get_scam_clusters(mock_G)
        assert len(clusters) == 2
        assert clusters == components
