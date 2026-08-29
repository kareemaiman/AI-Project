"""
Automated Screenshot Capture Script for Smart Rail Simulator.

Renders simulation states and UI tabs to high-resolution PNG images in docs/screenshots/.
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
import pygame_gui

from core.config_manager import ConfigManager
from core.models import RailwayGraph, RouteConfig, ScheduleEvent, TrainAgent
from core.scenario_manager import ScenarioManager
from core.simulation_engine import SimulationEngine
from generators.map_generator import generate_random_map
from ui.ui_views import (
    draw_map,
    draw_map_background,
    draw_overlay_info,
    draw_tab_config,
    draw_tab_schedules,
    draw_tab_stats,
    draw_tab_table,
    render_gantt_surface,
)
from ui.ui_widgets import SimulatorUI


def capture_all_screenshots():
    """Renders and saves 4 core visual demonstration screenshots to docs/screenshots/."""
    out_dir = Path("docs/screenshots")
    out_dir.mkdir(parents=True, exist_ok=True)

    pygame.init()
    cfg = ConfigManager("data/config.json")
    width, height = 1280, 720
    screen = pygame.display.set_mode((width, height))
    surface = pygame.Surface((width, height))

    font = pygame.font.SysFont("Arial", 15)
    header_font = pygame.font.SysFont("Arial", 20, bold=True)
    status_font = pygame.font.SysFont("Consolas", 13)

    ui_manager = pygame_gui.UIManager((width, height))
    ui = SimulatorUI(ui_manager, cfg, width, height)
    scenario_mgr = ScenarioManager("data/maps")

    def to_screen(x, y):
        return int(x), int(y)

    # -------------------------------------------------------------
    # 1. Egypt Simulation in Action (Moving Trains)
    # -------------------------------------------------------------
    graph, trains, _ = scenario_mgr.load_scenario("EGYPT")
    engine = SimulationEngine(graph, cfg)
    agents = {}
    planned = []
    engine.start(trains, agents, planned)
    # Step 30 ticks to put trains in motion
    for _ in range(30):
        engine.update_tick(agents, trains)

    surface.fill(cfg.get_color("bg"))
    draw_map_background(surface, width, height, 1.0, 0, 0, cfg)
    draw_map(surface, graph, agents, None, 1.0, to_screen, font, cfg)
    panel_w = cfg.get("window", "panel_width", 350)
    panel_x = width - panel_w
    pygame.draw.rect(surface, cfg.get_color("panel"), (panel_x, 0, panel_w, height))
    pygame.draw.line(surface, cfg.get_color("panel_border"), (panel_x, 0), (panel_x, height), 2)
    draw_tab_config(surface, panel_x, header_font, font, status_font, 1.0, "Active Fleet in Motion", cfg)
    ui_manager.draw_ui(surface)
    draw_overlay_info(surface, header_font, engine.sim_time, cfg)

    path1 = out_dir / "egypt_simulation.png"
    pygame.image.save(surface, str(path1))
    print(f"Captured: {path1}")

    # -------------------------------------------------------------
    # 2. Central Hub Network (Stats Tab)
    # -------------------------------------------------------------
    graph_hub, trains_hub, _ = scenario_mgr.load_scenario("HUB")
    engine_hub = SimulationEngine(graph_hub, cfg)
    agents_hub = {}
    planned_hub = []
    engine_hub.start(trains_hub, agents_hub, planned_hub)
    for _ in range(50):
        engine_hub.update_tick(agents_hub, trains_hub)

    surface.fill(cfg.get_color("bg"))
    draw_map_background(surface, width, height, 1.0, 0, 0, cfg)
    draw_map(surface, graph_hub, agents_hub, None, 1.0, to_screen, font, cfg)
    pygame.draw.rect(surface, cfg.get_color("panel"), (panel_x, 0, panel_w, height))
    pygame.draw.line(surface, cfg.get_color("panel_border"), (panel_x, 0), (panel_x, height), 2)
    draw_tab_stats(surface, panel_x, header_font, font, status_font, engine_hub.total_scheduling_time, engine_hub.scheduling_ops, engine_hub.total_collisions_avoided, agents_hub, height, cfg)
    draw_overlay_info(surface, header_font, engine_hub.sim_time, cfg)

    path2 = out_dir / "hub_network.png"
    pygame.image.save(surface, str(path2))
    print(f"Captured: {path2}")

    # -------------------------------------------------------------
    # 3. 24-Hour Gantt Chart Timeline (Table Tab)
    # -------------------------------------------------------------
    surface.fill(cfg.get_color("bg"))
    draw_map_background(surface, width, height, 1.0, 0, 0, cfg)
    draw_map(surface, graph, agents, None, 1.0, to_screen, font, cfg)
    pygame.draw.rect(surface, cfg.get_color("panel"), (panel_x, 0, panel_w, height))
    pygame.draw.line(surface, cfg.get_color("panel_border"), (panel_x, 0), (panel_x, height), 2)
    gantt_surf = render_gantt_surface(graph, planned, status_font, cfg)
    draw_tab_table(surface, panel_x, header_font, status_font, gantt_surf, 0, 180, height, cfg)
    draw_overlay_info(surface, header_font, 180, cfg)

    path3 = out_dir / "gantt_chart.png"
    pygame.image.save(surface, str(path3))
    print(f"Captured: {path3}")

    # -------------------------------------------------------------
    # 4. Procedural Random Map Generator
    # -------------------------------------------------------------
    graph_rand, trains_rand = generate_random_map(num_stations=10)
    engine_rand = SimulationEngine(graph_rand, cfg)
    agents_rand = {}
    planned_rand = []
    engine_rand.start(trains_rand, agents_rand, planned_rand)

    surface.fill(cfg.get_color("bg"))
    draw_map_background(surface, width, height, 1.0, 0, 0, cfg)
    draw_map(surface, graph_rand, agents_rand, None, 1.0, to_screen, font, cfg)
    pygame.draw.rect(surface, cfg.get_color("panel"), (panel_x, 0, panel_w, height))
    pygame.draw.line(surface, cfg.get_color("panel_border"), (panel_x, 0), (panel_x, height), 2)
    draw_tab_schedules(surface, panel_x, header_font, font, status_font, trains_rand, [], None, cfg)
    draw_overlay_info(surface, header_font, 0, cfg)

    path4 = out_dir / "random_map.png"
    pygame.image.save(surface, str(path4))
    print(f"Captured: {path4}")

    pygame.quit()
    print("All screenshots generated successfully!")


if __name__ == "__main__":
    capture_all_screenshots()
