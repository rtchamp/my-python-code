from igraph import Graph
from typing import Any, Dict, List, Optional, Tuple

class GraphUtil:
    def __init__(self, directed: bool = False):
        """
        Initialize a new igraph Graph.
        """
        self.g = Graph(directed=directed)
        self.node_id_map = {}  # Map from custom node data to igraph vertex index

    def add_node(self, node_data: Any) -> int:
        """
        Add a node with the given data. Returns the node index.
        """
        idx = self.g.vcount()
        self.g.add_vertex()
        self.g.vs[idx]["data"] = node_data
        self.node_id_map[node_data] = idx
        return idx

    def add_edge(self, source_data: Any, target_data: Any, edge_data: Optional[Dict] = None):
        """
        Add an edge between nodes identified by their data. Optionally attach edge data.
        """
        source_idx = self.node_id_map[source_data]
        target_idx = self.node_id_map[target_data]
        eid = self.g.ecount()
        self.g.add_edge(source_idx, target_idx)
        if edge_data:
            self.g.es[eid].update_attributes(edge_data)

    def find_edge_by_data(self, key: str, value: Any) -> Optional[Tuple[int, int, int]]:
        """
        Find the first edge with a given attribute key/value. Returns (edge_id, source_idx, target_idx) or None.
        """
        for e in self.g.es:
            if key in e.attributes() and e[key] == value:
                return (e.index, e.source, e.target)
        return None

    def insert_node_between_edge(self, edge_key: str, edge_value: Any, new_node_data: Any, new_edge_data1: Optional[Dict] = None, new_edge_data2: Optional[Dict] = None):
        """
        Find an edge by attribute, remove it, insert a new node between its endpoints, and connect new edges.
        """
        found = self.find_edge_by_data(edge_key, edge_value)
        if not found:
            raise ValueError("Edge not found")
        edge_id, source_idx, target_idx = found
        # Remove the edge
        self.g.delete_edges(edge_id)
        # Add the new node
        new_idx = self.add_node(new_node_data)
        # Add new edges
        self.g.add_edge(source_idx, new_idx)
        if new_edge_data1:
            self.g.es[self.g.get_eid(source_idx, new_idx)].update_attributes(new_edge_data1)
        self.g.add_edge(new_idx, target_idx)
        if new_edge_data2:
            self.g.es[self.g.get_eid(new_idx, target_idx)].update_attributes(new_edge_data2)

    def get_edges(self) -> List[Tuple[Any, Any, Dict]]:
        """
        Return a list of all edges as (source_data, target_data, edge_attributes).
        """
        result = []
        for e in self.g.es:
            src = self.g.vs[e.source]["data"]
            tgt = self.g.vs[e.target]["data"]
            attrs = e.attributes()
            result.append((src, tgt, attrs))
        return result

    def get_nodes(self) -> List[Any]:
        """
        Return a list of all node data.
        """
        return [v["data"] for v in self.g.vs] 