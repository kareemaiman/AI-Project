"""
Smart Rail Procedural Railway Topology & Fleet Generator.

Generates connected random railway graphs using Euclidean distance-based
spanning trees with cross-link tracks and valid multi-stop train manifests.
"""

import math
import random
from typing import Dict, List, Tuple
from core.models import RailwayGraph, RouteConfig


STATION_NAME_PREFIXES = [
    "North", "South", "East", "West", "Central", "Upper", "Lower", "Port",
    "Grand", "New", "Old", "Valley", "Coast", "Junction", "Hill", "Lake"
]
STATION_NAME_SUFFIXES = [
    "City", "Bay", "Hills", "Crossing", "Terminus", "Heights", "Harbor",
    "Gate", "Park", "Ridge", "Plaza", "Oasis", "Depot", "Station"
]


def generate_random_map(
    num_stations: int = 10,
    area_width: int = 800,
    area_height: int = 600,
    extra_tracks_ratio: float = 0.4
) -> Tuple[RailwayGraph, Dict[int, RouteConfig]]:
    """
    Procedurally generates a guaranteed-connected planar railway network.

    Args:
        num_stations: Number of station nodes to place.
        area_width: Max X bounding range.
        area_height: Max Y bounding range.
        extra_tracks_ratio: Proportion of additional loop tracks added beyond MST.

    Returns:
        Tuple[RailwayGraph, Dict[int, RouteConfig]]: Procedural graph and default train fleet.
    """
    graph = RailwayGraph()
    used_names = set()
    station_coords: List[Tuple[str, int, int]] = []

    # 1. Place stations with spatial Poisson-disc / minimum distance spacing
    min_dist = 90
    for _ in range(num_stations * 5):
        if len(station_coords) >= num_stations:
            break
        x = random.randint(150, area_width)
        y = random.randint(80, area_height)

        # Check spacing against existing stations
        if any(math.hypot(x - sx, y - sy) < min_dist for _, sx, sy in station_coords):
            continue

        # Generate unique station name
        for _ in range(50):
            p = random.choice(STATION_NAME_PREFIXES)
            s = random.choice(STATION_NAME_SUFFIXES)
            cand = f"{p} {s}"
            if cand not in used_names:
                used_names.add(cand)
                break
        else:
            cand = f"Station_{len(station_coords)+1}"

        station_coords.append((cand, x, y))
        graph.add_station(cand, x, y)

    if len(station_coords) < 2:
        return graph, {}

    # 2. Build Minimum Spanning Tree (MST) using Prim's algorithm to guarantee connectivity
    connected = [station_coords[0]]
    unconnected = station_coords[1:]

    while unconnected:
        best_dist = float('inf')
        best_u: str = ""
        best_v_idx: int = -1

        for u_name, ux, uy in connected:
            for idx, (v_name, vx, vy) in enumerate(unconnected):
                d = math.hypot(ux - vx, uy - vy)
                if d < best_dist:
                    best_dist = d
                    best_u = u_name
                    best_v_idx = idx

        chosen_v = unconnected.pop(best_v_idx)
        graph.add_track(best_u, chosen_v[0])
        connected.append(chosen_v)

    # 3. Add extra local cross-tracks for alternative routing loops
    all_pairs = []
    for i in range(len(station_coords)):
        for j in range(i + 1, len(station_coords)):
            u_name, ux, uy = station_coords[i]
            v_name, vx, vy = station_coords[j]
            if not graph.graph.has_edge(u_name, v_name):
                d = math.hypot(ux - vx, uy - vy)
                all_pairs.append((d, u_name, v_name))

    all_pairs.sort(key=lambda item: item[0])
    extra_count = int(len(station_coords) * extra_tracks_ratio)
    for _, u, v in all_pairs[:extra_count]:
        graph.add_track(u, v)

    # 4. Generate procedural train fleet
    num_trains = max(4, min(10, num_stations - 2))
    trains = generate_random_trains(graph, count=num_trains)

    return graph, trains


def generate_random_trains(graph: RailwayGraph, count: int = 6) -> Dict[int, RouteConfig]:
    """
    Generates procedural train manifests with varied stops, priority tiers, and colors.

    Args:
        graph: Active RailwayGraph topology.
        count: Number of trains to instantiate.

    Returns:
        Dict[int, RouteConfig]: Map of train ID to RouteConfig.
    """
    configs: Dict[int, RouteConfig] = {}
    nodes = list(graph.cached_pos.keys())
    if len(nodes) < 2:
        return configs

    for i in range(1, count + 1):
        route_len = min(len(nodes), random.randint(3, 5))
        route: List[str] = [random.choice(nodes)]

        for _ in range(route_len - 1):
            candidates = [n for n in nodes if n != route[-1]]
            if not candidates:
                break
            route.append(random.choice(candidates))

        # Assign priority (30% Express, 50% Standard, 20% Freight)
        rand_val = random.random()
        priority = 1 if rand_val < 0.3 else (2 if rand_val < 0.8 else 3)

        color = ((i * 55 + 30) % 255, (i * 85 + 70) % 255, (i * 125 + 50) % 255)
        configs[i] = RouteConfig(
            train_id=i,
            stops=route,
            color=color,
            start_delay=(i - 1) * 20,
            priority=priority
        )

    return configs
