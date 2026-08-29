"""
Depth-First Search (DFS) Pathfinding Algorithm.

Explores paths deeply to discover alternative loop-free routes between stations.
"""

from typing import List, Set
from core.models import RailwayGraph


def dfs_path(graph: RailwayGraph, start: str, end: str) -> List[str]:
    """
    Computes a path between two stations using Depth-First Search exploration.

    Args:
        graph: RailwayGraph instance.
        start: Starting station name.
        end: Destination station name.

    Returns:
        List[str]: Sequence of station names from start to end, or empty list.
    """
    if start not in graph.cached_pos or end not in graph.cached_pos:
        return []
    if start == end:
        return [start]

    visited: Set[str] = set()

    def _dfs(current: str, target: str, current_path: List[str]) -> List[str]:
        if current == target:
            return current_path
        visited.add(current)

        for neighbor in graph.graph.neighbors(current):
            if neighbor not in visited:
                result = _dfs(neighbor, target, current_path + [neighbor])
                if result:
                    return result
        return []

    return _dfs(start, end, [start])
