import math
import networkx as nx
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Deque
from collections import deque


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ScheduleEvent:
    """Represents a specific reservation on a track segment."""
    train_id: int
    source: str
    target: str
    start_time: int
    end_time: int
    color: Tuple[int, int, int]


@dataclass
class TrainAgent:
    """Holds the runtime state of a single train."""
    id: int
    color: Tuple[int, int, int]
    current_node: str  # Logical current stop

    # Event Queue for the full scheduled route
    schedule_queue: Deque[ScheduleEvent] = field(default_factory=deque)
    current_event: Optional[ScheduleEvent] = None

    # Visual / Physics State
    visual_pos: Tuple[float, float] = (0, 0)
    status: str = "WAITING"  # "MOVING", "WAITING", "DELAYED"

    # Statistics
    total_wait: int = 0
    total_journey_time: int = 0
    trips_completed: int = 0
    delay_accumulated: int = 0  # Delay relative to original plan


@dataclass
class RouteConfig:
    """Configuration for a train's route."""
    train_id: int
    stops: List[str]
    color: Tuple[int, int, int]
    start_delay: int = 0


# =============================================================================
# GRAPH MODEL
# =============================================================================

class RailwayGraph:
    """Wrapper around NetworkX to manage the physical topology."""

    def __init__(self):
        self.graph = nx.Graph()
        self.cached_pos = {}  # Cache for rendering performance

    def add_station(self, name: str, x: int, y: int):
        self.graph.add_node(name, pos=(x, y))
        self.cached_pos[name] = (x, y)

    def add_track(self, u: str, v: str):
        if u in self.cached_pos and v in self.cached_pos:
            x1, y1 = self.cached_pos[u]
            x2, y2 = self.cached_pos[v]
            dist = math.hypot(x2 - x1, y2 - y1)
            # Weight represents travel time. speed = 5 pixels/tick
            weight = max(1, int(dist / 5.0))
            self.graph.add_edge(u, v, weight=weight)

    def get_path(self, start: str, end: str) -> List[str]:
        try:
            return nx.shortest_path(self.graph, source=start, target=end, weight='weight')
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_all_edges(self):
        return list(self.graph.edges())

    def get_pos(self, node_name):
        return self.cached_pos.get(node_name, (0, 0))