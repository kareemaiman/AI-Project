"""
Dijkstra Shortest Path Algorithm.

Computes the time-optimal path between stations weighted by track travel durations.
"""

import heapq
from typing import Dict, List, Optional
from core.models import RailwayGraph


def dijkstra_path(graph: RailwayGraph, start: str, end: str) -> List[str]:
    """
    Computes time-optimal shortest path using Dijkstra's priority queue algorithm.

    Args:
        graph: RailwayGraph instance.
        start: Starting station name.
        end: Destination station name.

    Returns:
        List[str]: Sequence of station names minimizing cumulative track duration.
    """
    if start not in graph.cached_pos or end not in graph.cached_pos:
        return []
    if start == end:
        return [start]

    distances: Dict[str, float] = {node: float('inf') for node in graph.cached_pos}
    distances[start] = 0.0
    parent: Dict[str, Optional[str]] = {start: None}

    # Priority queue storing (distance, node)
    pq = [(0.0, start)]

    while pq:
        curr_dist, curr_node = heapq.heappop(pq)

        if curr_node == end:
            path = []
            cur: Optional[str] = end
            while cur is not None:
                path.append(cur)
                cur = parent[cur]
            return path[::-1]

        if curr_dist > distances[curr_node]:
            continue

        for neighbor in graph.graph.neighbors(curr_node):
            weight = graph.graph.edges[curr_node, neighbor].get('weight', 10)
            new_dist = curr_dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                parent[neighbor] = curr_node
                heapq.heappush(pq, (new_dist, neighbor))

    return []
