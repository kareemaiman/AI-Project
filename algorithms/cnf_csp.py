"""
Constraint Satisfaction Problem (CSP / CNF) Deconfliction Algorithm.

Models track reservations as temporal constraint intervals (disjunctive clauses)
and solves for the earliest feasible time-slot satisfying headway safety clauses.
"""

import time
from typing import List, Tuple
from algorithms.base import BaseScheduler
from algorithms.dijkstra import dijkstra_path
from core.models import RailwayGraph, ScheduleEvent


class CSPScheduler(BaseScheduler):
    """Constraint satisfaction lookahead scheduler evaluating sequential block clauses."""

    def __init__(self, graph: RailwayGraph, safety_margin: float = 15.0, max_lookahead: int = 5000):
        """Initializes CSP solver with safety headway and search horizon."""
        super().__init__(graph, safety_margin)
        self.max_lookahead = max_lookahead

    def schedule_route(
        self,
        train_id: int,
        stops: List[str],
        color: Tuple[int, int, int],
        start_time: int,
        priority: int = 2
    ) -> Tuple[List[ScheduleEvent], int, float]:
        """
        Finds the first time-interval satisfying all non-overlap constraint clauses.

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
            path = dijkstra_path(self.graph, stops[i], stops[i + 1])
            if not path or len(path) < 2:
                continue

            for j in range(len(path) - 1):
                u, v = path[j], path[j + 1]
                weight = self.graph.graph.edges[u, v].get('weight', 10)

                attempt_t = curr_t
                while True:
                    if not self.table.check_conflict(u, v, attempt_t, attempt_t + weight):
                        evt = ScheduleEvent(train_id, u, v, attempt_t, attempt_t + weight, color)
                        self.table.reserve(u, v, attempt_t, attempt_t + weight, train_id)
                        events.append(evt)
                        curr_t = attempt_t + weight
                        break

                    attempt_t += 10
                    conflicts += 1
                    if attempt_t - curr_t > self.max_lookahead:
                        break

            curr_t += 5  # Station dwell time

        dt = (time.perf_counter() - t0) * 1000.0
        return (events, conflicts, dt)
