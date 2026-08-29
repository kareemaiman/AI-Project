"""
Smart Rail Scenario Manager & JSON Serialization Engine.

Scans, loads, validates, and exports railway topology maps and train manifests
to and from JSON files located in data/maps/.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from core.logger import get_logger
from core.models import RailwayGraph, RouteConfig


class ScenarioManager:
    """Manages discovery, loading, and persistence of railway maps in JSON format."""

    def __init__(self, maps_dir: str = "data/maps"):
        """Initializes scenario manager with target maps directory."""
        self.maps_dir = Path(maps_dir)
        self.maps_dir.mkdir(parents=True, exist_ok=True)
        self.available_scenarios: Dict[str, Path] = {}
        self.scan_scenarios()

    def scan_scenarios(self) -> List[str]:
        """
        Scans data/maps/ for all available .json scenario files.

        Returns:
            List[str]: Alphabetically sorted list of scenario names.
        """
        logger = get_logger()
        self.available_scenarios.clear()
        for json_file in sorted(self.maps_dir.glob("*.json")):
            key = json_file.stem.upper()
            self.available_scenarios[key] = json_file

        logger.info(f"Discovered {len(self.available_scenarios)} scenario maps in {self.maps_dir}")
        return list(self.available_scenarios.keys())

    def load_scenario(
        self,
        name: str,
        speed: float = 5.0
    ) -> Tuple[RailwayGraph, Dict[int, RouteConfig], str]:
        """
        Loads a railway graph and train manifest from a named JSON map file.

        Args:
            name: Scenario key or file stem (e.g. 'EGYPT', 'HUB').
            speed: Simulation traversal speed for track weight computation.

        Returns:
            Tuple: (Configured RailwayGraph, Dict of RouteConfig, Status message)
        """
        logger = get_logger()
        key = name.strip().upper()
        if key not in self.available_scenarios:
            # Fallback to first available or empty
            if self.available_scenarios:
                key = next(iter(self.available_scenarios.keys()))
                logger.warning(f"Scenario '{name}' not found. Defaulting to '{key}'.")
            else:
                return RailwayGraph(speed), {}, "No maps found."

        target_file = self.available_scenarios[key]
        graph = RailwayGraph(speed)
        trains: Dict[int, RouteConfig] = {}

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 1. Parse stations
            for s in data.get("stations", []):
                graph.add_station(s["name"], int(s["x"]), int(s["y"]))

            # 2. Parse track segments
            for u, v in data.get("tracks", []):
                graph.add_track(u, v)

            # 3. Parse train manifest
            for t in data.get("trains", []):
                tid = int(t["id"])
                stops = [s for s in t.get("stops", []) if graph.has_station(s)]
                color = tuple(t.get("color", [255, 70, 70]))
                delay = max(0, int(t.get("start_delay", 0)))
                priority = int(t.get("priority", 2))
                if len(stops) >= 2:
                    trains[tid] = RouteConfig(tid, stops, color, delay, priority)

            logger.info(f"Loaded scenario '{key}' ({len(graph.cached_pos)} stations, {len(trains)} trains).")
            return graph, trains, f"Loaded {key}"

        except Exception as e:
            logger.error(f"Failed to load scenario from {target_file}: {e}")
            return RailwayGraph(speed), {}, f"Error loading {key}: {e}"

    def save_scenario(
        self,
        name: str,
        graph: RailwayGraph,
        trains: Dict[int, RouteConfig],
        description: str = "Custom user-authored railway topology."
    ) -> Tuple[bool, str]:
        """
        Serializes the current network topology and train fleet into a JSON file.

        Args:
            name: Filename or map title (e.g. 'Cairo_Suburban').
            graph: Active RailwayGraph instance.
            trains: Active dictionary of RouteConfigs.
            description: Optional summary description.

        Returns:
            Tuple[bool, str]: (Success status, user-facing feedback message)
        """
        logger = get_logger()
        safe_name = "".join(c for c in name.strip() if c.isalnum() or c in ("_", "-")).lower()
        if not safe_name:
            safe_name = "custom_map"

        file_path = self.maps_dir / f"{safe_name}.json"

        payload = {
            "name": name.strip(),
            "description": description,
            "stations": [{"name": n, "x": pos[0], "y": pos[1]} for n, pos in graph.cached_pos.items()],
            "tracks": graph.get_all_edges(),
            "trains": [
                {
                    "id": cfg.train_id,
                    "stops": cfg.stops,
                    "color": list(cfg.color),
                    "start_delay": cfg.start_delay,
                    "priority": cfg.priority
                }
                for cfg in trains.values()
            ]
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            self.scan_scenarios()
            logger.info(f"Saved custom scenario to {file_path}")
            return True, f"Saved '{safe_name}.json' successfully!"
        except Exception as e:
            logger.error(f"Failed to save scenario to {file_path}: {e}")
            return False, f"Error saving map: {e}"
