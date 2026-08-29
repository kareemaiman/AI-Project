"""
Smart Rail: Multi-Train AI Scheduling & Conflict Resolution Simulator.

Top-level application entry point initializing data-driven configuration,
structured logging, modular UI, algorithms, and simulation lifecycle.
"""

import sys
from typing import Dict, List, Optional, Tuple
import pygame
import pygame_gui

from algorithms import ALGORITHM_REGISTRY
from core.config_manager import ConfigManager
from core.logger import get_logger, setup_logger
from core.models import RailwayGraph, RouteConfig, ScheduleEvent, TrainAgent
from core.scenario_manager import ScenarioManager
from core.simulation_engine import SimulationEngine
from generators.map_generator import generate_random_map
from ui.event_handler import MapInteractionHandler
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


class App:
    """Main application controller managing GUI events, simulation stepping, and rendering."""

    def __init__(self):
        """Initializes configuration, logging, display window, and core managers."""
        self.cfg = ConfigManager("data/config.json")
        log_file = self.cfg.get("logging", "log_file", "smart_rail.log")
        log_level = self.cfg.get("logging", "level", "INFO")
        self.logger = setup_logger(log_file=log_file, level=log_level)
        self.logger.info("Initializing Smart Rail Simulator application.")

        pygame.init()
        self.width = self.cfg.get("window", "width", 1280)
        self.height = self.cfg.get("window", "height", 720)
        title = self.cfg.get("window", "title", "Smart Rail")
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()

        # Typography
        f_name = self.cfg.get("typography", "font_family", "Arial")
        st_name = self.cfg.get("typography", "status_font_family", "Consolas")
        self.font = pygame.font.SysFont(f_name, self.cfg.get("typography", "font_size", 15))
        self.header_font = pygame.font.SysFont(f_name, self.cfg.get("typography", "header_font_size", 20), bold=True)
        self.status_font = pygame.font.SysFont(st_name, self.cfg.get("typography", "status_font_size", 13))

        # Core Subsystems
        self.scenario_mgr = ScenarioManager("data/maps")
        self.ui_manager = pygame_gui.UIManager((self.width, self.height))
        self.ui = SimulatorUI(self.ui_manager, self.cfg, self.width, self.height)
        self.graph = RailwayGraph(self.cfg.get("simulation", "speed_pixels_per_tick", 5.0))
        self.engine = SimulationEngine(self.graph, self.cfg)
        self.map_handler = MapInteractionHandler()

        # State Variables
        self.train_agents: Dict[int, TrainAgent] = {}
        self.train_route_configs: Dict[int, RouteConfig] = {}
        self.planned_events: List[ScheduleEvent] = []
        self.active_tab = "CONFIG"
        self.scenario_name = "EGYPT"
        self.algorithm_list = list(ALGORITHM_REGISTRY.keys())
        self.algo_idx = 0
        self.feedback_message = ""
        self.selected_train: Optional[int] = None
        self.train_list_rects: List[Tuple[pygame.Rect, int]] = []

        # Camera & Gantt
        self.cam_offset_x = 0.0
        self.cam_offset_y = 0.0
        self.zoom = 1.0
        self.table_surface: Optional[pygame.Surface] = None
        self.table_dirty = True
        self.table_scroll_y = 0

        self.load_scenario("EGYPT")

    def to_screen(self, x: float, y: float) -> Tuple[int, int]:
        """Converts world coordinates to screen pixel coordinates."""
        return int(x * self.zoom + self.cam_offset_x), int(y * self.zoom + self.cam_offset_y)

    def to_world(self, sx: float, sy: float) -> Tuple[float, float]:
        """Converts screen pixel coordinates to world coordinates."""
        return (sx - self.cam_offset_x) / self.zoom, (sy - self.cam_offset_y) / self.zoom

    def load_scenario(self, name: str) -> None:
        """Loads a named scenario map from JSON."""
        speed = self.cfg.get("simulation", "speed_pixels_per_tick", 5.0)
        self.graph, self.train_route_configs, msg = self.scenario_mgr.load_scenario(name, speed=speed)
        self.scenario_name = name.upper()
        self.engine.update_graph(self.graph)
        self.ui.btn_scenario.set_text(f"MAP: {self.scenario_name}")
        self.ui.update_stops_dropdown(list(self.graph.cached_pos.keys()), self.active_tab)
        self.engine.reset(self.train_agents, self.planned_events)
        self.ui.btn_run.set_text("START SIMULATION")
        self.table_dirty = True
        self.feedback_message = msg

    def cycle_scenario(self) -> None:
        """Cycles to the next available scenario map."""
        scenarios = self.scenario_mgr.scan_scenarios()
        if not scenarios:
            return
        curr_idx = scenarios.index(self.scenario_name) if self.scenario_name in scenarios else 0
        self.load_scenario(scenarios[(curr_idx + 1) % len(scenarios)])

    def cycle_algorithm(self) -> None:
        """Cycles to next deconfliction algorithm."""
        self.algo_idx = (self.algo_idx + 1) % len(self.algorithm_list)
        algo_name = self.algorithm_list[self.algo_idx]
        self.engine.set_algorithm(algo_name)
        self.ui.btn_algo.set_text(f"ALGO: {algo_name}")
        self.feedback_message = f"Selected {algo_name}."

    def generate_random_network(self) -> None:
        """Procedurally generates a connected random railway topology."""
        self.graph, self.train_route_configs = generate_random_map(num_stations=10)
        self.scenario_name = "RANDOM"
        self.engine.update_graph(self.graph)
        self.ui.btn_scenario.set_text("MAP: RANDOM")
        self.ui.update_stops_dropdown(list(self.graph.cached_pos.keys()), self.active_tab)
        self.engine.reset(self.train_agents, self.planned_events)
        self.ui.btn_run.set_text("START SIMULATION")
        self.table_dirty = True
        self.feedback_message = "Generated Random Railway Network."

    def save_current_map(self) -> None:
        """Saves active network to a JSON file."""
        name = f"custom_map_{len(self.scenario_mgr.available_scenarios)+1}"
        _, msg = self.scenario_mgr.save_scenario(name, self.graph, self.train_route_configs)
        self.feedback_message = msg

    def add_custom_train(self) -> None:
        """Registers or updates a train manifest from UI inputs."""
        try:
            tid = int(self.ui.input_tid.get_text().strip())
            c_str = self.ui.input_tcolor.get_text().replace(',', ' ').split()
            c_vals = tuple(min(255, max(0, int(c))) for c in c_str)
            if len(c_vals) != 3:
                c_vals = (255, 70, 70)
            route = [n for n in self.ui.input_troute.get_text().strip().split() if self.graph.has_station(n)]
            if len(route) < 2:
                self.feedback_message = "Error: Route needs >= 2 valid stations."
                return
            delay = max(0, int(self.ui.input_tstart.get_text().strip()))
            priority = max(1, min(3, int(self.ui.input_tpriority.get_text().strip())))
            self.train_route_configs[tid] = RouteConfig(tid, route, c_vals, delay, priority)
            self.table_dirty = True
            self.feedback_message = f"Train #{tid} registered."
        except ValueError:
            self.feedback_message = "Invalid input values."

    def delete_selected_train(self) -> None:
        """Removes the selected train cleanly."""
        if self.selected_train is not None and self.selected_train in self.train_route_configs:
            del self.train_route_configs[self.selected_train]
            self.selected_train = None
            self.table_dirty = True
            self.feedback_message = "Selected train removed."
        else:
            self.feedback_message = "Select a train first."

    def toggle_simulation(self) -> None:
        """Toggles simulation execution state."""
        if self.engine.mode == "EDITOR":
            if self.engine.start(self.train_route_configs, self.train_agents, self.planned_events):
                self.ui.btn_run.set_text("STOP SIMULATION")
                self.table_dirty = True
            else:
                self.feedback_message = "Add train manifests first."
        else:
            self.engine.reset(self.train_agents, self.planned_events)
            self.ui.btn_run.set_text("START SIMULATION")
            self.table_dirty = True

    def handle_events(self) -> bool:
        """Processes Pygame window, UI widgets, and mouse events."""
        panel_x, panel_w, _, _ = self.ui.get_layout_metrics()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                self.ui.width, self.ui.height = self.width, self.height
                self.ui.setup_ui(self.active_tab, self.engine.algorithm_name, self.engine.sim_speed, self.scenario_name)
                self.ui.update_stops_dropdown(list(self.graph.cached_pos.keys()), self.active_tab)

            self.ui_manager.process_events(event)

            if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED and event.ui_element == self.ui.slider_speed:
                self.engine.sim_speed = self.ui.slider_speed.get_current_value()
            elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                if event.ui_element == self.ui.drop_stops:
                    if event.text != "Select Station":
                        curr = self.ui.input_troute.get_text().strip()
                        self.ui.input_troute.set_text(f"{curr} {event.text}".strip())
                elif event.ui_element == self.ui.drop_algo:
                    self.engine.set_algorithm(event.text)
                    self.feedback_message = f"Selected {event.text}."
            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                self._handle_button_press(event.ui_element)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and self.active_tab == "CONFIG":
                self._handle_add_station()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_down(event, panel_w)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.map_handler.is_dragging_map = False
            elif event.type == pygame.MOUSEMOTION and self.map_handler.is_dragging_map:
                mx, my = event.pos
                self.cam_offset_x += mx - self.map_handler.last_mouse_pos[0]
                self.cam_offset_y += my - self.map_handler.last_mouse_pos[1]
                self.map_handler.last_mouse_pos = (mx, my)
            elif event.type == pygame.MOUSEWHEEL and self.active_tab == "TABLE":
                self.table_scroll_y = min(0, self.table_scroll_y + event.y * 24)

        return True

    def _handle_add_station(self) -> None:
        try:
            s_name = self.ui.input_name.get_text().strip()
            s_x = int(self.ui.input_x.get_text().strip())
            s_y = int(self.ui.input_y.get_text().strip())
            if self.graph.add_station(s_name, s_x, s_y):
                self.ui.update_stops_dropdown(list(self.graph.cached_pos.keys()), self.active_tab)
                self.table_dirty = True
                self.feedback_message = f"Added Station '{s_name}'."
        except ValueError:
            self.feedback_message = "Coordinates must be integers."

    def _handle_mouse_down(self, event, panel_w) -> None:
        if self.active_tab == "SCHEDULES":
            for rect, tid in self.train_list_rects:
                if rect.collidepoint(event.pos):
                    cfg = self.train_route_configs.get(tid)
                    if cfg:
                        self.selected_train = tid
                        self.ui.input_tid.set_text(str(tid))
                        self.ui.input_tcolor.set_text(f"{cfg.color[0]} {cfg.color[1]} {cfg.color[2]}")
                        self.ui.input_tstart.set_text(str(cfg.start_delay))
                        self.ui.input_tpriority.set_text(str(cfg.priority))
                        self.ui.input_troute.set_text(" ".join(cfg.stops))
                    return

        if event.pos[0] < self.width - panel_w:
            _, modified, msg = self.map_handler.handle_map_click(
                event, self.graph, self.engine.mode == "EDITOR", self.zoom, self.to_world
            )
            if modified:
                self.ui.update_stops_dropdown(list(self.graph.cached_pos.keys()), self.active_tab)
                self.table_dirty = True
            if msg:
                self.feedback_message = msg

    def _handle_button_press(self, elem) -> None:
        if elem == self.ui.btn_tab_config: self.active_tab = "CONFIG"
        elif elem == self.ui.btn_tab_schedules: self.active_tab = "SCHEDULES"
        elif elem == self.ui.btn_tab_status: self.active_tab = "STATS"
        elif elem == self.ui.btn_tab_table:
            self.active_tab = "TABLE"
            if self.engine.mode == "EDITOR": self.table_dirty = True
        elif elem == self.ui.btn_run: self.toggle_simulation()
        elif elem == self.ui.btn_scenario: self.cycle_scenario()
        elif elem == self.ui.btn_random_map: self.generate_random_network()
        elif elem == self.ui.btn_save_map: self.save_current_map()
        elif elem == self.ui.btn_add_train: self.add_custom_train()
        elif elem == self.ui.btn_clear_trains:
            self.train_route_configs.clear()
            self.table_dirty = True
            self.feedback_message = "Cleared all trains."
        elif elem == self.ui.btn_current_trains: self.delete_selected_train()
        elif elem == self.ui.btn_zoom_in: self.zoom = min(2.5, self.zoom * 1.15)
        elif elem == self.ui.btn_zoom_out: self.zoom = max(0.4, self.zoom / 1.15)

        for btn, col in self.ui.btn_colors:
            if elem == btn:
                self.ui.input_tcolor.set_text(f"{col[0]} {col[1]} {col[2]}")

        self.ui.update_visibility(self.active_tab)

    def draw(self) -> None:
        """Renders all graphics, UI sidebar tabs, HUD overlay, and flips display."""
        self.screen.fill(self.cfg.get_color("bg"))
        draw_map_background(self.screen, self.width, self.height, self.zoom, self.cam_offset_x, self.cam_offset_y, self.cfg)
        draw_map(self.screen, self.graph, self.train_agents, self.map_handler.selected_node_for_link, self.zoom, self.to_screen, self.font, self.cfg)

        panel_x, panel_w, content_w, _ = self.ui.get_layout_metrics()
        pygame.draw.rect(self.screen, self.cfg.get_color("panel"), (panel_x, 0, panel_w, self.height))
        pygame.draw.line(self.screen, self.cfg.get_color("panel_border"), (panel_x, 0), (panel_x, self.height), 2)

        if self.active_tab == "CONFIG":
            draw_tab_config(self.screen, panel_x, content_w, self.header_font, self.font, self.status_font, self.engine.sim_speed, self.feedback_message, self.cfg)
        elif self.active_tab == "SCHEDULES":
            draw_tab_schedules(self.screen, panel_x, content_w, self.header_font, self.font, self.status_font, self.train_route_configs, self.train_list_rects, self.selected_train, self.cfg)
        elif self.active_tab == "STATS":
            draw_tab_stats(self.screen, panel_x, content_w, self.header_font, self.font, self.status_font, self.engine.total_scheduling_time, self.engine.scheduling_ops, self.engine.total_collisions_avoided, self.train_agents, self.height, self.cfg)
        elif self.active_tab == "TABLE":
            if self.table_dirty or self.table_surface is None:
                self.table_surface = render_gantt_surface(self.graph, self.planned_events, self.status_font, content_w, self.cfg)
                self.table_dirty = False
            draw_tab_table(self.screen, panel_x, content_w, self.header_font, self.status_font, self.table_surface, self.table_scroll_y, self.engine.sim_time, self.height, self.cfg)

        self.ui_manager.draw_ui(self.screen)
        draw_overlay_info(self.screen, self.header_font, self.engine.sim_time, self.cfg)

    def run(self) -> None:
        """Main application lifecycle and 60 FPS event loop."""
        running = True
        fps = self.cfg.get("window", "target_fps", 60)
        max_speed = self.cfg.get("simulation", "max_speed_multiplier", 10.0)

        while running:
            time_delta = self.clock.tick(fps) / 1000.0
            running = self.handle_events()
            self.ui_manager.update(time_delta)

            if self.engine.mode == "RUNNING":
                self.engine.speed_accumulator += self.engine.sim_speed
                if self.engine.speed_accumulator > max_speed:
                    self.engine.speed_accumulator = max_speed
                while self.engine.speed_accumulator >= 1.0:
                    self.engine.update_tick(self.train_agents, self.train_route_configs)
                    self.engine.speed_accumulator -= 1.0

            self.draw()
            pygame.display.flip()

        pygame.quit()
        self.logger.info("Application exited cleanly.")
        sys.exit()


if __name__ == "__main__":
    App().run()