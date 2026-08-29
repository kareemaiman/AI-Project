"""
Smart Rail Base Scheduling & Reservation Table Primitives.

Defines the spatial-temporal reservation table and abstract BaseScheduler interface
shared across all deconfliction solvers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from core.models import RailwayGraph, ScheduleEvent


class ReservationTable:
    """Manages spatial-temporal track block occupancy across undirected graph edges."""

    def __init__(self, safety_margin: float = 15.0):
        """Initializes empty reservation table with specified safety headway."""
        self.safety_margin = safety_margin
        self.reservations: Dict[Tuple[str, str], List[Tuple[float, float, int]]] = {}

    def reset(self) -> None:
        """Clears all track block reservations."""
        self.reservations.clear()

    def get_edge_key(self, u: str, v: str) -> Tuple[str, str]:
        """Returns a canonical alphabetical key for an undirected track segment."""
        return (u, v) if u < v else (v, u)

    def check_conflict(
        self,
        u: str,
        v: str,
        start: float,
        end: float,
        margin: Optional[float] = None
    ) -> bool:
        """
        Checks whether the track segment (u, v) is occupied during [start, end].

        Returns:
            bool: True if conflicting reservation exists, False if free.
        """
        effective_margin = self.safety_margin if margin is None else margin
        edge_key = self.get_edge_key(u, v)

        if edge_key not in self.reservations:
            return False

        for r_start, r_end, _ in self.reservations[edge_key]:
            if start < (r_end + effective_margin) and end > (r_start - effective_margin):
                return True
        return False

    def reserve(self, u: str, v: str, start: float, end: float, train_id: int) -> None:
        """Locks a temporal interval [start, end] on track (u, v) for a train."""
        edge_key = self.get_edge_key(u, v)
        if edge_key not in self.reservations:
            self.reservations[edge_key] = []
        self.reservations[edge_key].append((start, end, train_id))

    def cleanup_old(self, current_time: int) -> None:
        """Purges reservations that expired before current simulation tick."""
        keys_to_remove = []
        for key, res_list in self.reservations.items():
            active = [r for r in res_list if r[1] > current_time - 100]
            if active:
                self.reservations[key] = active
            else:
                keys_to_remove.append(key)

        for k in keys_to_remove:
            del self.reservations[k]


class BaseScheduler(ABC):
    """Abstract base class for all multi-train scheduling and deconfliction algorithms."""

    def __init__(self, graph: RailwayGraph, safety_margin: float = 15.0):
        """Initializes scheduler with reference graph model and reservation table."""
        self.graph = graph
        self.table = ReservationTable(safety_margin)

    def reset(self) -> None:
        """Clears all active reservations."""
        self.table.reset()

    def cleanup_old_reservations(self, current_time: int) -> None:
        """Purges expired reservations from table."""
        self.table.cleanup_old(current_time)

    @abstractmethod
    def schedule_route(
        self,
        train_id: int,
        stops: List[str],
        color: Tuple[int, int, int],
        start_time: int,
        priority: int = 2
    ) -> Tuple[List[ScheduleEvent], int, float]:
        """
        Schedules a full multi-stop train route.

        Returns:
            Tuple[List[ScheduleEvent], int, float]: (Events, Conflicts avoided count, Latency in ms)
        """
        pass
