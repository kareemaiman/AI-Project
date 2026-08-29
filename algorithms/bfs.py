"""
Breadth-First Search (BFS) Pathfinding Algorithm.

Finds the route between two stations with the fewest intermediate station hops.
"""

from collections import deque
from typing import Dict, List, Optional
from core.models import RailwayGraph


def bfs_path(graph: RailwayGraph, start: str, end: str) -> List[str]:
    """
    Computes unweighted shortest path (fewest station hops) using Breadth-First Search.

    Args:
        graph: RailwayGraph instance.
        start: Starting station name.
        end: Destination station name.

    Returns:
        List[str]: Sequence of station names from start to end, or empty list if unreachable.
    """
    if start not in graph.cached_pos or end not in graph.cached_pos:
        return []
    if start == end:
        return [start]

    queue = deque([start])
    visited = {start}
    parent: Dict[str, Optional[str]] = {start: None}

    while queue:
        curr = queue.popleft()
        if curr == end:
            # Reconstruct path
            path = []
            curr_node: Optional[str] = end
            while curr_node is not None:
                path.append(curr_node)
                curr_node = parent[curr_node]
            return path[::-1]

        for neighbor in graph.graph.neighbors(curr):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = curr
                queue.append(neighbor)

    return []
