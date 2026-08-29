"""
Smart Rail Core Models & Topology Representation.

Defines the mathematical data structures for graph stations and track edges,
atomic scheduled reservations, dynamic train agents, and route manifests.
"""

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple
import networkx as nx


@dataclass
class ScheduleEvent:
    """Represents an atomic time-locked reservation on a track segment."""
    train_id: int
    source: str
    target: str
    start_time: int
    end_time: int
    color: Tuple[int, int, int] = (200, 200, 200)


@dataclass
class TrainAgent:
    """Holds the runtime physics and state machine of a single active train."""
    id: int
    color: Tuple[int, int, int]
    current_node: str

    schedule_queue: Deque[ScheduleEvent] = field(default_factory=deque)
    current_event: Optional[ScheduleEvent] = None

    visual_pos: Tuple[float, float] = (0.0, 0.0)
    status: str = "WAITING"  # "MOVING", "WAITING", "DELAYED", "ARRIVED"

    total_wait: int = 0
    total_journey_time: int = 0
    trips_completed: int = 0
    delay_accumulated: int = 0


@dataclass
class RouteConfig:
    """Configuration manifest for a train's requested sequence of stops and priority."""
    train_id: int
    stops: List[str]
    color: Tuple[int, int, int]
    start_delay: int = 0
    priority: int = 2  # 1 = Express (Highest), 2 = Standard, 3 = Freight (Lowest)


class RailwayGraph:
    """
    Railway network topology manager backed by an undirected NetworkX Graph.
    Manages station nodes with 2D coordinates and track edges with traversal weights.
    """

    def __init__(self, speed_pixels_per_tick: float = 5.0):
        """Initializes an empty graph and station coordinate cache."""
        self.graph: nx.Graph = nx.Graph()
        self.cached_pos: Dict[str, Tuple[int, int]] = {}
        self.speed = speed_pixels_per_tick

    def add_station(self, name: str, x: int, y: int) -> bool:
        """Adds a station node at coordinate (x, y)."""
        cleaned_name = name.strip()
        if not cleaned_name:
            return False
        self.graph.add_node(cleaned_name, pos=(x, y))
        self.cached_pos[cleaned_name] = (x, y)
        return True

    def add_track(self, u: str, v: str) -> bool:
        """Connects two stations with an undirected track segment weighted by travel duration."""
        if u == v or u not in self.cached_pos or v not in self.cached_pos:
            return False
        x1, y1 = self.cached_pos[u]
        x2, y2 = self.cached_pos[v]
        dist = math.hypot(x2 - x1, y2 - y1)
        weight = max(1, int(dist / max(0.1, self.speed)))
        self.graph.add_edge(u, v, weight=weight)
        return True

    def remove_station(self, name: str) -> bool:
        """Removes a station and all connected tracks from the graph."""
        if name in self.graph:
            self.graph.remove_node(name)
            self.cached_pos.pop(name, None)
            return True
        return False

    def remove_track(self, u: str, v: str) -> bool:
        """Removes an undirected track between stations u and v."""
        if self.graph.has_edge(u, v):
            self.graph.remove_edge(u, v)
            return True
        return False

    def has_station(self, name: str) -> bool:
        """Checks if a station exists in the graph."""
        return name in self.cached_pos

    def get_all_edges(self) -> List[Tuple[str, str]]:
        """Returns all undirected track segments in the network."""
        return list(self.graph.edges())

    def get_pos(self, node_name: str) -> Tuple[int, int]:
        """Returns the world-space coordinate of a given station."""
        return self.cached_pos.get(node_name, (0, 0))

    def clear(self) -> None:
        """Clears all stations and tracks from the network."""
        self.graph.clear()
        self.cached_pos.clear()
