"""
Smart Rail UI Widget Construction & Hierarchy Module.

Manages Pygame-GUI widget creation, layout positioning, tab visibility,
algorithm selection, scenario switching, and custom map export triggers.
"""

from typing import List, Tuple
import pygame
import pygame_gui
from core.config_manager import ConfigManager


class SimulatorUI:
    """Constructs and manages all Pygame-GUI interactive elements in the sidebar."""

    def __init__(self, manager: pygame_gui.UIManager, cfg: ConfigManager, width: int, height: int):
        """Initializes UI widgets using settings from ConfigManager."""
        self.manager = manager
        self.cfg = cfg
        self.width = width
        self.height = height

        self.btn_colors: List[Tuple[pygame_gui.elements.UIButton, Tuple[int, int, int]]] = []
        self.setup_ui("CONFIG", "CSP", 1.0, "EGYPT")

    def setup_ui(
        self,
        active_tab: str,
        algorithm_name: str,
        sim_speed: float,
        scenario_name: str
    ) -> None:
        """Constructs and positions all sidebar widgets and inputs."""
        self.manager.clear_and_reset()
        self.manager.set_window_resolution((self.width, self.height))

        panel_w = self.cfg.get("window", "panel_width", 350)
        tab_w = self.cfg.get("window", "tab_width", 87)
        panel_x = self.width - panel_w

        # --- Tab Switcher Buttons ---
        self.btn_tab_config = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x, 0), (tab_w, 40)),
            text='CONFIG', manager=self.manager
        )
        self.btn_tab_schedules = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + tab_w, 0), (tab_w, 40)),
            text='SCHED', manager=self.manager
        )
        self.btn_tab_status = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + tab_w * 2, 0), (tab_w, 40)),
            text='STATS', manager=self.manager
        )
        self.btn_tab_table = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + tab_w * 3, 0), (tab_w, 40)),
            text='TABLE', manager=self.manager
        )

        # --- CONFIG Tab Widgets ---
        self.input_name = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 15, 95), (200, 30)), manager=self.manager
        )
        self.input_name.set_text("StationX")
        self.input_x = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 15, 155), (90, 30)), manager=self.manager
        )
        self.input_x.set_text("400")
        self.input_y = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 125, 155), (90, 30)), manager=self.manager
        )
        self.input_y.set_text("300")

        self.drop_algo = pygame_gui.elements.UIDropDownMenu(
            options_list=["CSP", "GREEDY", "PRIORITY_EDF", "DYNAMIC_REROUTE"],
            starting_option=algorithm_name if algorithm_name in ["CSP", "GREEDY", "PRIORITY_EDF", "DYNAMIC_REROUTE"] else "CSP",
            relative_rect=pygame.Rect((panel_x + 15, 305), (220, 32)),
            manager=self.manager
        )
        self.slider_speed = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((panel_x + 15, 375), (220, 20)),
            start_value=sim_speed, value_range=(0.1, 10.0), manager=self.manager
        )
        self.btn_scenario = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + 15, 415), (220, 34)),
            text=f"MAP: {scenario_name}", manager=self.manager
        )
        self.btn_random_map = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + 15, 455), (220, 32)),
            text="GENERATE RANDOM MAP", manager=self.manager
        )
        self.btn_save_map = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + 15, 492), (220, 32)),
            text="SAVE MAP JSON", manager=self.manager
        )
        self.btn_run = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + 15, 540), (220, 44)),
            text="START SIMULATION", manager=self.manager
        )

        # --- SCHEDULES Tab Widgets ---
        self.input_tid = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 15, 95), (55, 30)), manager=self.manager
        )
        self.input_tid.set_text("101")
        self.input_tcolor = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 75, 95), (105, 30)), manager=self.manager
        )
        self.input_tcolor.set_text("255 70 70")
        self.input_tstart = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 185, 95), (60, 30)), manager=self.manager
        )
        self.input_tstart.set_text("0")
        self.input_tpriority = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 250, 95), (65, 30)), manager=self.manager
        )
        self.input_tpriority.set_text("2")

        # Color Preset Buttons
        self.btn_colors.clear()
        presets = self.cfg.get_preset_train_colors()
        for i, col in enumerate(presets):
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((panel_x + 75 + (i * 22), 132), (18, 18)),
                text="", manager=self.manager
            )
            btn.colours['normal_bg'] = pygame.Color(col)
            btn.colours['hovered_bg'] = pygame.Color(col)
            btn.colours['active_bg'] = pygame.Color(col)
            btn.rebuild()
            self.btn_colors.append((btn, col))

        # Station Selector Dropdown
        self.drop_stops = pygame_gui.elements.UIDropDownMenu(
            options_list=["Select Station"], starting_option="Select Station",
            relative_rect=pygame.Rect((panel_x + 15, 205), (310, 28)), manager=self.manager
        )
        self.input_troute = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 15, 240), (310, 30)), manager=self.manager
        )
        self.input_troute.set_text("Cairo Alexandria")

        self.btn_add_train = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + 35, 280), (270, 36)),
            text="ADD / UPDATE TRAIN", manager=self.manager
        )
        self.btn_current_trains = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + 35, 322), (270, 28)),
            text="CLEAR SELECTED", manager=self.manager
        )
        self.btn_clear_trains = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + 35, 355), (270, 28)),
            text="CLEAR ALL TRAINS", manager=self.manager
        )

        # --- Map Zoom Controls ---
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
        else:
            self.drop_algo.hide()
        self.btn_scenario.visible = is_cfg
        self.btn_random_map.visible = is_cfg
        self.btn_save_map.visible = is_cfg
        self.btn_run.visible = is_cfg
        if is_cfg:
            self.slider_speed.show()
        else:
            self.slider_speed.hide()

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
            if is_sched:
                btn.show()
            else:
                btn.hide()

    def update_stops_dropdown(self, stations: List[str], active_tab: str) -> None:
        """Recreates station dropdown selector with updated station names."""
        rect = self.drop_stops.relative_rect
        self.drop_stops.kill()
        nodes = ["Select Station"] + sorted(stations)
        self.drop_stops = pygame_gui.elements.UIDropDownMenu(
            options_list=nodes, starting_option="Select Station",
            relative_rect=rect, manager=self.manager
        )
        self.update_visibility(active_tab)
