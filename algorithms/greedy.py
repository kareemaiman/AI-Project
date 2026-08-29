"""
Greedy Earliest-Deadline Scheduling Algorithm.

Assigns earliest possible track reservations per leg, pushing departure forward
iteratively by fixed-step delays upon detecting contention.
"""

import time
from typing import List, Tuple
from algorithms.base import BaseScheduler
from algorithms.dijkstra import dijkstra_path
from core.models import RailwayGraph, ScheduleEvent


class GreedyScheduler(BaseScheduler):
    """Greedy incremental reservation deconfliction algorithm."""

    def __init__(self, graph: RailwayGraph, safety_margin: float = 15.0, step_delay: int = 20):
        """Initializes Greedy scheduler with configurable backoff step."""
        super().__init__(graph, safety_margin)
        self.step_delay = step_delay

    def schedule_route(
        self,
        train_id: int,
        stops: List[str],
        color: Tuple[int, int, int],
        start_time: int,
        priority: int = 2
    ) -> Tuple[List[ScheduleEvent], int, float]:
        """
        Schedules consecutive legs greedily, stepping departure forward on collision.

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

                # Greedy step backoff
                while self.table.check_conflict(u, v, curr_t, curr_t + weight):
                    curr_t += self.step_delay
                    conflicts += 1

                evt = ScheduleEvent(train_id, u, v, curr_t, curr_t + weight, color)
                self.table.reserve(u, v, curr_t, curr_t + weight, train_id)
                events.append(evt)
                curr_t += weight

            curr_t += 5  # Dwell time

        dt = (time.perf_counter() - t0) * 1000.0
        return (events, conflicts, dt)
