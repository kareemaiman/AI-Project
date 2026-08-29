"""
Dynamic Re-routing & Multi-Path Deconfliction Algorithm.

Explores alternative physical track corridors when primary shortest-path tracks
experience severe congestion, dynamically load-balancing the railway network.
"""

import itertools
import time
from typing import List, Tuple
import networkx as nx
from algorithms.base import BaseScheduler
from core.models import RailwayGraph, ScheduleEvent


class DynamicRerouteScheduler(BaseScheduler):
    """Dynamic multi-path scheduler exploring k-shortest alternative track routes."""

    def __init__(self, graph: RailwayGraph, safety_margin: float = 15.0, k_paths: int = 3):
        """Initializes dynamic reroute scheduler."""
        super().__init__(graph, safety_margin)
        self.k_paths = k_paths

    def _get_k_shortest_paths(self, start: str, end: str) -> List[List[str]]:
        """Returns up to k shortest distinct physical paths between start and end."""
        if start not in self.graph.graph or end not in self.graph.graph:
            return []
        try:
            generator = nx.shortest_simple_paths(self.graph.graph, source=start, target=end, weight='weight')
            return list(itertools.islice(generator, self.k_paths))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def schedule_route(
        self,
        train_id: int,
        stops: List[str],
        color: Tuple[int, int, int],
        start_time: int,
        priority: int = 2
    ) -> Tuple[List[ScheduleEvent], int, float]:
        """
        Evaluates candidate alternative paths per leg and selects the path with earliest arrival.

        Returns:
            Tuple[List[ScheduleEvent], int, float]: (Events, Conflicts avoided count, Latency in ms)
        """
        t0 = time.perf_counter()
        events: List[ScheduleEvent] = []
        conflicts = 0
        curr_t = start_time

        if len(stops) < 2:
            return ([], 0, 0.0)

        for i in range(len(stops) - 1):
            candidate_paths = self._get_k_shortest_paths(stops[i], stops[i + 1])
            if not candidate_paths:
                continue

            best_leg_events: List[ScheduleEvent] = []
            best_leg_arrival = float('inf')
            best_leg_conflicts = 0

            # Evaluate each alternative path candidate
            for path in candidate_paths:
                path_events: List[ScheduleEvent] = []
                path_conflicts = 0
                path_t = curr_t

                for j in range(len(path) - 1):
                    u, v = path[j], path[j + 1]
                    weight = self.graph.graph.edges[u, v].get('weight', 10)

                    attempt_t = path_t
                    while True:
                        if not self.table.check_conflict(u, v, attempt_t, attempt_t + weight):
                            evt = ScheduleEvent(train_id, u, v, attempt_t, attempt_t + weight, color)
                            path_events.append(evt)
                            path_t = attempt_t + weight
                            break

                        attempt_t += 10
                        path_conflicts += 1
                        if attempt_t - path_t > 3000:
                            path_t = float('inf')
                            break

                    if path_t == float('inf'):
                        break

                if path_t < best_leg_arrival:
                    best_leg_arrival = path_t
                    best_leg_events = path_events
                    best_leg_conflicts = path_conflicts

            # Commit the best evaluated route to reservation table
            for evt in best_leg_events:
                self.table.reserve(evt.source, evt.target, evt.start_time, evt.end_time, train_id)
                events.append(evt)

            conflicts += best_leg_conflicts
            curr_t = (best_leg_events[-1].end_time if best_leg_events else curr_t) + 5

        dt = (time.perf_counter() - t0) * 1000.0
        return (events, conflicts, dt)
