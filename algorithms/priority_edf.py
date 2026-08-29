"""
Priority Earliest Deadline First (Priority EDF) Deconfliction Algorithm.

Schedules trains based on service tier (1=Express, 2=Standard, 3=Freight).
Higher priority tiers are allocated tighter headway windows and smaller backoff steps.
"""

import time
from typing import List, Tuple
from algorithms.base import BaseScheduler
from algorithms.dijkstra import dijkstra_path
from core.models import RailwayGraph, ScheduleEvent


class PriorityEDFScheduler(BaseScheduler):
    """Tier-aware priority scheduler minimizing high-priority passenger train delays."""

    def __init__(self, graph: RailwayGraph, safety_margin: float = 15.0):
        """Initializes Priority EDF solver."""
        super().__init__(graph, safety_margin)

    def schedule_route(
        self,
        train_id: int,
        stops: List[str],
        color: Tuple[int, int, int],
        start_time: int,
        priority: int = 2
    ) -> Tuple[List[ScheduleEvent], int, float]:
        """
        Schedules train route with tier-adjusted search step and safety buffers.

        Args:
            train_id: Unique train identifier.
            stops: Route stops sequence.
            color: Train RGB color.
            start_time: Earliest departure tick.
            priority: 1 (Express), 2 (Standard), 3 (Freight).

        Returns:
            Tuple[List[ScheduleEvent], int, float]: (Events, Conflicts avoided, Execution time in ms)
        """
        t0 = time.perf_counter()
        events: List[ScheduleEvent] = []
        conflicts = 0
        curr_t = start_time

        if len(stops) < 2:
            return ([], 0, 0.0)

        # Dynamic search step based on priority
        step = 5 if priority == 1 else (10 if priority == 2 else 20)
        margin = max(5.0, self.table.safety_margin - (2.0 if priority == 1 else 0.0))

        for i in range(len(stops) - 1):
            path = dijkstra_path(self.graph, stops[i], stops[i + 1])
            if not path or len(path) < 2:
                continue

            for j in range(len(path) - 1):
                u, v = path[j], path[j + 1]
                weight = self.graph.graph.edges[u, v].get('weight', 10)

                attempt_t = curr_t
                while True:
                    if not self.table.check_conflict(u, v, attempt_t, attempt_t + weight, margin=margin):
                        evt = ScheduleEvent(train_id, u, v, attempt_t, attempt_t + weight, color)
                        self.table.reserve(u, v, attempt_t, attempt_t + weight, train_id)
                        events.append(evt)
                        curr_t = attempt_t + weight
                        break

                    attempt_t += step
                    conflicts += 1
                    if attempt_t - curr_t > 5000:
                        break

            curr_t += 5

        dt = (time.perf_counter() - t0) * 1000.0
        return (events, conflicts, dt)
