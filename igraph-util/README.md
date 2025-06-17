# igraph-util

This directory contains utility functions and scripts for working with igraph in Python. It is intended for experimenting with and extending igraph-related functionality in a modular way.

## Files

- `graph_utils.py`: Utility class for creating nodes, connecting edges, searching for edges by attribute, and inserting nodes between edges in an igraph Graph.

## Example Usage

```python
from igraph_util.graph_utils import GraphUtil

g = GraphUtil()
g.add_node('A')
g.add_node('B')
g.add_edge('A', 'B', {'type': 'link'})
# Insert node 'C' between edge with type 'link'
g.insert_node_between_edge('type', 'link', 'C', {'type': 'A-C'}, {'type': 'C-B'})
print(g.get_edges())
``` 