"""
Floyd-Warshall All-Pairs Shortest Path Algorithm.

Computes the all-pairs distance matrix and intermediate predecessor matrix
for instant O(1) routing across the entire railway graph.
"""

from typing import Dict, List, Optional, Tuple
from core.models import RailwayGraph


def floyd_warshall_all_pairs(
    graph: RailwayGraph
) -> Tuple[Dict[Tuple[str, str], float], Dict[Tuple[str, str], Optional[str]]]:
    """
    Computes all-pairs shortest paths using the dynamic programming Floyd-Warshall algorithm.

    Args:
        graph: RailwayGraph instance.

    Returns:
        Tuple: (Distances map: (u, v) -> min_distance, Next-hop map: (u, v) -> next_node)
    """
    nodes = list(graph.cached_pos.keys())
    dist: Dict[Tuple[str, str], float] = {}
    next_node: Dict[Tuple[str, str], Optional[str]] = {}

    # Initialize matrices
    for u in nodes:
        for v in nodes:
            if u == v:
                dist[(u, v)] = 0.0
                next_node[(u, v)] = v
            elif graph.graph.has_edge(u, v):
                w = float(graph.graph.edges[u, v].get('weight', 10))
                dist[(u, v)] = w
                next_node[(u, v)] = v
            else:
                dist[(u, v)] = float('inf')
                next_node[(u, v)] = None

    # Triple nested DP loop
    for k in nodes:
        for i in nodes:
            for j in nodes:
                if dist[(i, k)] + dist[(k, j)] < dist[(i, j)]:
                    dist[(i, j)] = dist[(i, k)] + dist[(k, j)]
                    next_node[(i, j)] = next_node[(i, k)]

    return dist, next_node


def reconstruct_floyd_path(
    next_node: Dict[Tuple[str, str], Optional[str]],
    start: str,
    end: str
) -> List[str]:
    """Reconstructs shortest path from Floyd-Warshall next-hop table."""
    if next_node.get((start, end)) is None:
        return []
    path = [start]
    curr = start
    while curr != end:
        curr = next_node[(curr, end)]
        if curr is None:
            return []
        path.append(curr)
    return path
