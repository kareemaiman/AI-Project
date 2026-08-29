"""
Smart Rail Responsive UI Widget Construction & Hierarchy Module.

Dynamically computes widget coordinates, spacing, and dimensions based on
window resolution to guarantee clean presentation across all screen aspect ratios.
"""

from typing import List, Tuple
import pygame
import pygame_gui
from core.config_manager import ConfigManager


class SimulatorUI:
    """Constructs and dynamically layouts Pygame-GUI interactive elements in the sidebar."""

    def __init__(self, manager: pygame_gui.UIManager, cfg: ConfigManager, width: int, height: int):
        """Initializes UI widgets using settings from ConfigManager."""
        self.manager = manager
        self.cfg = cfg
        self.width = width
        self.height = height

        self.btn_colors: List[Tuple[pygame_gui.elements.UIButton, Tuple[int, int, int]]] = []
        self.setup_ui("CONFIG", "CSP", 1.0, "EGYPT")

    def get_layout_metrics(self) -> Tuple[int, int, int, int]:
        """Calculates responsive layout metrics for the sidebar."""
        panel_w = min(420, max(330, int(self.width * 0.28)))
        panel_x = self.width - panel_w
        content_w = panel_w - 30
        tab_w = panel_w // 4
        return panel_x, panel_w, content_w, tab_w

    def setup_ui(
        self,
        active_tab: str,
        algorithm_name: str,
        sim_speed: float,
        scenario_name: str
    ) -> None:
        """Constructs and responsively positions all sidebar widgets and inputs."""
        self.manager.clear_and_reset()
        self.manager.set_window_resolution((self.width, self.height))

        panel_x, panel_w, content_w, tab_w = self.get_layout_metrics()

        # --- Tab Switcher Buttons (Proportional) ---
        tab_h = 38
        self.btn_tab_config = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x, 0), (tab_w, tab_h)),
            text='CONFIG', manager=self.manager
        )
        self.btn_tab_schedules = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + tab_w, 0), (tab_w, tab_h)),
            text='SCHED', manager=self.manager
        )
        self.btn_tab_status = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + tab_w * 2, 0), (tab_w, tab_h)),
            text='STATS', manager=self.manager
        )
        self.btn_tab_table = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + tab_w * 3, 0), (panel_w - tab_w * 3, tab_h)),
            text='TABLE', manager=self.manager
        )

        # --- CONFIG Tab Widgets (Auto-Spaced) ---
        half_w = (content_w - 10) // 2
        self.input_name = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 15, 90), (content_w, 28)), manager=self.manager
        )
        self.input_name.set_text("StationX")

        self.input_x = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 15, 144), (half_w, 28)), manager=self.manager
        )
        self.input_x.set_text("400")

        self.input_y = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 15 + half_w + 10, 144), (half_w, 28)), manager=self.manager
        )
        self.input_y.set_text("300")

        algo_opts = ["CSP", "GREEDY", "PRIORITY_EDF", "DYNAMIC_REROUTE"]
        start_algo = algorithm_name.upper() if algorithm_name.upper() in algo_opts else "CSP"
        self.drop_algo = pygame_gui.elements.UIDropDownMenu(
            options_list=algo_opts,
            starting_option=start_algo,
            relative_rect=pygame.Rect((panel_x + 15, 278), (content_w, 30)),
            manager=self.manager
        )

        self.slider_speed = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((panel_x + 15, 336), (content_w, 18)),
            start_value=sim_speed, value_range=(0.1, 10.0), manager=self.manager
        )

        self.btn_scenario = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + 15, 366), (content_w, 32)),
            text=f"MAP: {scenario_name}", manager=self.manager
        )
        self.btn_random_map = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + 15, 404), (content_w, 30)),
            text="GENERATE RANDOM MAP", manager=self.manager
        )
        self.btn_save_map = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + 15, 440), (content_w, 30)),
            text="SAVE MAP JSON", manager=self.manager
        )
        self.btn_run = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + 15, 478), (content_w, 42)),
            text="START SIMULATION", manager=self.manager
        )

        # --- SCHEDULES Tab Widgets (Auto-Spaced) ---
        col1_w = int(content_w * 0.18)
        col2_w = int(content_w * 0.38)
        col3_w = int(content_w * 0.22)
        col4_w = content_w - (col1_w + col2_w + col3_w + 18)

        self.input_tid = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 15, 90), (col1_w, 28)), manager=self.manager
        )
        self.input_tid.set_text("101")

        self.input_tcolor = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 15 + col1_w + 6, 90), (col2_w, 28)), manager=self.manager
        )
        self.input_tcolor.set_text("255 70 70")

        self.input_tstart = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 15 + col1_w + col2_w + 12, 90), (col3_w, 28)), manager=self.manager
        )
        self.input_tstart.set_text("0")

        self.input_tpriority = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 15 + col1_w + col2_w + col3_w + 18, 90), (col4_w, 28)), manager=self.manager
        )
        self.input_tpriority.set_text("2")

        # Color Presets (Auto-Distributed)
        self.btn_colors.clear()
        presets = self.cfg.get_preset_train_colors()
        swatch_step = max(18, content_w // (len(presets) + 1))
        for i, col in enumerate(presets):
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((panel_x + 15 + (i * swatch_step), 124), (16, 16)),
                text="", manager=self.manager
            )
            btn.colours['normal_bg'] = pygame.Color(col)
            btn.colours['hovered_bg'] = pygame.Color(col)
            btn.colours['active_bg'] = pygame.Color(col)
            btn.rebuild()
            self.btn_colors.append((btn, col))

        # Station Selector Dropdown & Route Manifest
        self.drop_stops = pygame_gui.elements.UIDropDownMenu(
            options_list=["Select Station"], starting_option="Select Station",
            relative_rect=pygame.Rect((panel_x + 15, 168), (content_w, 28)), manager=self.manager
        )
        self.input_troute = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 15, 222), (content_w, 28)), manager=self.manager
        )
        self.input_troute.set_text("Cairo Alexandria")

        self.btn_add_train = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + 15, 258), (content_w, 34)),
            text="ADD / UPDATE TRAIN", manager=self.manager
        )
        btn_half_w = (content_w - 10) // 2
        self.btn_current_trains = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + 15, 298), (btn_half_w, 28)),
            text="CLEAR SELECTED", manager=self.manager
        )
        self.btn_clear_trains = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + 15 + btn_half_w + 10, 298), (btn_half_w, 28)),
            text="CLEAR ALL TRAINS", manager=self.manager
        )

        # --- Map Zoom Controls (Docked bottom-left) ---
        self.btn_zoom_in = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((20, self.height - 55), (38, 38)),
            text="+", manager=self.manager
        )
        self.btn_zoom_out = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((65, self.height - 55), (38, 38)),
            text="-", manager=self.manager
        )

        self.update_visibility(active_tab)

    def update_visibility(self, active_tab: str) -> None:
        """Toggles widget visibility based on active sidebar tab."""
        is_cfg = (active_tab == "CONFIG")
        self.input_name.visible = is_cfg
        self.input_x.visible = is_cfg
        self.input_y.visible = is_cfg
        if is_cfg:
            self.drop_algo.show()
            self.slider_speed.show()
        else:
            self.drop_algo.hide()
            self.slider_speed.hide()

        self.btn_scenario.visible = is_cfg
        self.btn_random_map.visible = is_cfg
        self.btn_save_map.visible = is_cfg
        self.btn_run.visible = is_cfg

        is_sched = (active_tab == "SCHEDULES")
        self.input_tid.visible = is_sched
        self.input_tcolor.visible = is_sched
        self.input_tstart.visible = is_sched
        self.input_tpriority.visible = is_sched
        self.input_troute.visible = is_sched
        self.btn_add_train.visible = is_sched
        self.btn_current_trains.visible = is_sched
        self.btn_clear_trains.visible = is_sched

        if is_sched:
            self.drop_stops.show()
        else:
            self.drop_stops.hide()

        for btn, _ in self.btn_colors:
            btn.visible = is_sched

    def update_stops_dropdown(self, station_names: List[str], active_tab: str) -> None:
        """Refreshes the station selector dropdown with active network stations."""
        opts = ["Select Station"] + sorted(station_names)
        panel_x, _, content_w, _ = self.get_layout_metrics()
        self.drop_stops.kill()
        self.drop_stops = pygame_gui.elements.UIDropDownMenu(
            options_list=opts, starting_option="Select Station",
            relative_rect=pygame.Rect((panel_x + 15, 168), (content_w, 28)), manager=self.manager
        )
        if active_tab != "SCHEDULES":
            self.drop_stops.hide()
