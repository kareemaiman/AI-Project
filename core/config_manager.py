"""
Smart Rail Configuration Manager & Schema Validator.

Loads data-driven configuration from data/config.json with comprehensive validation,
fallback default recovery, and runtime config access.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
from core.logger import get_logger


# Baseline hardcoded safety fallbacks in case config.json is deleted or corrupted
FALLBACK_CONFIG: Dict[str, Any] = {
    "window": {
        "title": "Smart Rail: Multi-Train AI Conflict Resolution Simulator",
        "width": 1280,
        "height": 720,
        "panel_width": 350,
        "tab_width": 87,
        "target_fps": 60
    },
    "simulation": {
        "speed_pixels_per_tick": 5.0,
        "default_safety_margin_ticks": 15.0,
        "station_dwell_ticks": 5,
        "cleanup_interval_ticks": 500,
        "loop_restart_delay_ticks": 100,
        "day_window_minutes": 1440,
        "max_speed_multiplier": 10.0,
        "default_speed_multiplier": 1.0
    },
    "logging": {
        "level": "INFO",
        "log_file": "smart_rail.log",
        "max_bytes": 2097152,
        "backup_count": 3
    },
    "colors": {
        "bg": [28, 28, 34],
        "grid": [42, 42, 50],
        "node": [90, 195, 250],
        "node_selected": [255, 215, 0],
        "node_hover": [140, 225, 255],
        "edge": [65, 65, 75],
        "edge_active": [120, 120, 135],
        "text": [235, 235, 240],
        "text_muted": [160, 160, 170],
        "panel": [38, 38, 46],
        "panel_border": [60, 60, 72],
        "input_bg": [24, 24, 30],
        "btn_active": [65, 155, 95],
        "btn_inactive": [175, 55, 55],
        "btn_neutral": [75, 75, 95],
        "tab_active": [95, 95, 115],
        "tab_inactive": [48, 48, 58],
        "timeline_bar": [95, 195, 145],
        "timeline_grid": [65, 65, 75],
        "status_waiting": [255, 195, 75],
        "status_moving": [75, 240, 110],
        "status_delayed": [255, 75, 75],
        "status_arrived": [160, 120, 240]
    },
    "preset_train_colors": [
        [255, 70, 70],
        [60, 220, 90],
        [70, 140, 255],
        [255, 215, 0],
        [50, 220, 220],
        [220, 80, 220],
        [255, 140, 40],
        [170, 90, 255]
    ],
    "typography": {
        "font_family": "Arial",
        "status_font_family": "Consolas",
        "font_size": 15,
        "header_font_size": 20,
        "status_font_size": 13
    }
}


class ConfigManager:
    """Manages reading, caching, and validating data/config.json."""

    def __init__(self, config_path: str = "data/config.json"):
        """Initializes configuration loader with target path."""
        self.config_path = Path(config_path)
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> Dict[str, Any]:
        """
        Loads configuration from JSON file. If missing or corrupted,
        gracefully falls back to default settings and restores file.
        """
        logger = get_logger()
        if not self.config_path.exists():
            logger.warning(f"Config file not found at {self.config_path}. Generating default configuration.")
            self.data = dict(FALLBACK_CONFIG)
            self.save_defaults()
            return self.data

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self.data = self._validate_and_merge(loaded)
            logger.info(f"Loaded configuration successfully from {self.config_path}")
        except Exception as e:
            logger.error(f"Error parsing config file {self.config_path}: {e}. Falling back to default configuration.")
            self.data = dict(FALLBACK_CONFIG)

        return self.data

    def save_defaults(self) -> None:
        """Writes the default configuration to the JSON file path."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(FALLBACK_CONFIG, f, indent=2)
        except Exception as e:
            get_logger().error(f"Failed to save default config to {self.config_path}: {e}")

    def _validate_and_merge(self, loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures all required nested keys exist, filling missing keys from fallback."""
        merged = dict(FALLBACK_CONFIG)
        for section, content in loaded.items():
            if isinstance(content, dict) and section in merged:
                merged[section].update(content)
            else:
                merged[section] = content
        return merged

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Retrieves a configuration value safely."""
        return self.data.get(section, {}).get(key, default)

    def get_color(self, name: str) -> Tuple[int, int, int]:
        """Returns an RGB color tuple by key name."""
        raw = self.data.get("colors", {}).get(name, [200, 200, 200])
        return tuple(raw) if len(raw) == 3 else (200, 200, 200)

    def get_preset_train_colors(self) -> List[Tuple[int, int, int]]:
        """Returns list of preset RGB train colors."""
        raw_list = self.data.get("preset_train_colors", [])
        return [tuple(c) for c in raw_list if len(c) == 3]
