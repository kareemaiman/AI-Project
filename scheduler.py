import time
from typing import List, Dict, Tuple
from models import RailwayGraph, ScheduleEvent


# =============================================================================
# SCHEDULER (The AI Core)
# =============================================================================

class Scheduler:
    """Handles logic for pathfinding and conflict resolution."""

    def __init__(self, graph_model: RailwayGraph):
        self.graph_model = graph_model
        # Reservation Table: Maps (u, v) -> List of (start, end, train_id)
        self.reservations: Dict[Tuple[str, str], List[Tuple[float, float, int]]] = {}

    def reset(self):
        self.reservations.clear()

    def cleanup_old_reservations(self, current_time: int):
        """Removes reservations that are completely in the past."""
        keys_to_remove = []
        for key in self.reservations:
            # Keep reservations that end in the future or very recent past
            self.reservations[key] = [r for r in self.reservations[key] if r[1] > current_time - 100]
            if not self.reservations[key]:
                keys_to_remove.append(key)

        for k in keys_to_remove:
            del self.reservations[k]

    def _get_edge_key(self, u: str, v: str) -> Tuple[str, str]:
        """Returns a canonical key for undirected edges."""
        return (u, v) if u < v else (v, u)

    def _check_conflict(self, u: str, v: str, start: float, end: float, margin: float = 15.0) -> bool:
        """Checks if the track segment (u,v) is free during [start, end]."""
        edge_key = self._get_edge_key(u, v)
        if edge_key not in self.reservations:
            return False

        for r_start, r_end, _ in self.reservations[edge_key]:
            # Strict Overlap Check:
            # New interval [start, end]
            # Reserved interval effective: [r_start, r_end + margin]
            # They overlap if max(start, r_start) < min(end, r_end + margin)

            # Simplified: if we start before they finish (plus safety) AND they start before we finish.
            if start < (r_end + margin) and (end + margin) > r_start:
                return True
        return False

    def _reserve(self, u: str, v: str, start: float, end: float, train_id: int):
        edge_key = self._get_edge_key(u, v)
        if edge_key not in self.reservations:
            self.reservations[edge_key] = []
        self.reservations[edge_key].append((start, end, train_id))

    def schedule_route(self, train_id: int, stops: List[str], color: Tuple[int, int, int], start_time: int,
                       mode="GREEDY") -> Tuple[List[ScheduleEvent], int, float]:
        """
        Schedules the ENTIRE sequence of stops for a train.
        Returns: (List of All Events, Conflicts Avoided, Calculation Time)
        """
        t0 = time.perf_counter()

        all_events = []
        conflicts_avoided = 0
        curr_t = start_time

        # Iterate through the sequence of stops: A->B, B->C, ...
        for i in range(len(stops) - 1):
            start_node = stops[i]
            end_node = stops[i + 1]

            # Find physical path between stops (might involve intermediate nodes)
            path = self.graph_model.get_path(start_node, end_node)
            if not path or len(path) < 2:
                continue  # Skip invalid leg

            # Schedule this leg
            for j in range(len(path) - 1):
                u, v = path[j], path[j + 1]
                weight = self.graph_model.graph.edges[u, v]['weight']

                if mode == "GREEDY":
                    # Greedy: Try to book immediately, if blocked, wait and retry
                    while self._check_conflict(u, v, curr_t, curr_t + weight):
                        curr_t += 20  # Wait 20 ticks
                        conflicts_avoided += 1

                    evt = ScheduleEvent(train_id, u, v, curr_t, curr_t + weight, color)
                    self._reserve(u, v, curr_t, curr_t + weight, train_id)
                    all_events.append(evt)
                    curr_t += weight

                elif mode == "CSP":
                    # CSP: Lookahead logic for the specific segment
                    # In a full route context, this is simplified to "wait until slot available"
                    # A true CSP would optimize the whole timeline, but here we iterate.
                    # We look for the first valid slot.
                    attempt_t = curr_t
                    while True:
                        if not self._check_conflict(u, v, attempt_t, attempt_t + weight):
                            # Found slot
                            evt = ScheduleEvent(train_id, u, v, attempt_t, attempt_t + weight, color)
                            self._reserve(u, v, attempt_t, attempt_t + weight, train_id)
                            all_events.append(evt)
                            curr_t = attempt_t + weight
                            break
                        else:
                            attempt_t += 10
                            conflicts_avoided += 1
                            if attempt_t - curr_t > 5000:  # Safety break
                                break

            # Station Dwell Time (Optional, prevents instant departures)
            curr_t += 5

        dt = (time.perf_counter() - t0) * 1000
        return (all_events, conflicts_avoided, dt)