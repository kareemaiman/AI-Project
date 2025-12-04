import pygame
import pygame_gui
import math
import random
from typing import List, Dict, Tuple, Optional

from config import *
from models import RailwayGraph, ScheduleEvent, TrainAgent, RouteConfig
from scheduler import Scheduler


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((INITIAL_SCREEN_WIDTH, INITIAL_SCREEN_HEIGHT), pygame.RESIZABLE)
        self.width, self.height = INITIAL_SCREEN_WIDTH, INITIAL_SCREEN_HEIGHT

        pygame.display.set_caption("Smart Rail: Egyptian Railway Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", FONT_SIZE)
        self.header_font = pygame.font.SysFont("Arial", HEADER_FONT_SIZE, bold=True)
        self.status_font = pygame.font.SysFont("Consolas", 14)

        # UI Manager
        self.ui_manager = pygame_gui.UIManager((self.width, self.height))

        # Systems
        self.graph = RailwayGraph()
        self.scheduler = Scheduler(self.graph)

        # State Variables
        self.train_agents: Dict[int, TrainAgent] = {}
        self.train_route_configs: Dict[int, RouteConfig] = {}
        self.planned_events: List[ScheduleEvent] = []  # Persistent store for Gantt Chart

        self.mode = "EDITOR"
        self.algorithm_mode = "CSP"
        self.sim_time = 0
        self.paused = False
        self.sim_speed = 1.0
        self.speed_accumulator = 0.0

        self.selected_node_for_link = None
        self.active_tab = "CONFIG"

        # Camera & Navigation
        self.cam_offset_x = 0
        self.cam_offset_y = 0
        self.zoom = 1.0
        self.is_dragging_map = False
        self.last_mouse_pos = (0, 0)

        # Gantt Chart Cache
        self.table_surface: Optional[pygame.Surface] = None
        self.table_dirty = True
        self.table_scroll_y = 0

        # Edit Interaction
        self.train_list_rects: List[Tuple[pygame.Rect, int]] = []
        self.selected_train = None

        # Metrics
        self.total_collisions_avoided = 0
        self.total_scheduling_time = 0.0
        self.scheduling_ops = 0

        self.init_ui()
        self.load_scenario_egypt()

    def init_ui(self):
        """Setup all buttons and input fields using pygame_gui."""
        self.ui_manager.clear_and_reset()
        self.ui_manager.set_window_resolution((self.width, self.height))

        panel_x = self.width - 350
        panel_w = 350
        tab_w = 87

        # --- TAB BUTTONS ---
        self.btn_tab_config = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((panel_x, 0), (tab_w, 40)),
                                                           text='CONFIG', manager=self.ui_manager)
        self.btn_tab_schedules = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + tab_w, 0), (tab_w, 40)), text='SCHED', manager=self.ui_manager)
        self.btn_tab_status = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + tab_w * 2, 0), (tab_w, 40)), text='STATS', manager=self.ui_manager)
        self.btn_tab_table = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((panel_x + tab_w * 3, 0), (tab_w, 40)), text='TABLE', manager=self.ui_manager)

        # --- CONFIG TAB ---
        self.input_name = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 10, 130), (200, 32)), manager=self.ui_manager)
        self.input_name.set_text("StationX")
        self.input_x = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((panel_x + 10, 200), (90, 32)),
                                                           manager=self.ui_manager)
        self.input_x.set_text("400")
        self.input_y = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((panel_x + 120, 200), (90, 32)),
                                                           manager=self.ui_manager)
        self.input_y.set_text("300")

        self.btn_algo = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((panel_x + 10, 400), (200, 40)),
                                                     text=f"ALGO: {self.algorithm_mode}", manager=self.ui_manager)
        self.slider_speed = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((panel_x + 10, 500), (200, 20)), start_value=1.0, value_range=(0.1, 10.0),
            manager=self.ui_manager)
        self.btn_scenario = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((panel_x + 10, 550), (200, 40)),
                                                         text="SCENARIO: EGYPT", manager=self.ui_manager)
        self.btn_run = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((panel_x + 10, 600), (200, 50)),
                                                    text="START SIMULATION", manager=self.ui_manager)

        # --- SCHEDULES TAB ---
        self.input_tid = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((panel_x + 20, 110), (60, 32)),
                                                             manager=self.ui_manager)
        self.input_tid.set_text("101")
        self.input_tcolor = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 90, 110), (120, 32)), manager=self.ui_manager)
        self.input_tcolor.set_text("255 50 50")
        self.input_tstart = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 220, 110), (80, 32)), manager=self.ui_manager)
        self.input_tstart.set_text("0")

        # Color Quick Selectors
        colors = [(255, 50, 50), (50, 255, 50), (50, 50, 255), (255, 255, 50), (50, 255, 255), (255, 50, 255)]
        self.btn_colors = []
        for i, col in enumerate(colors):
            btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((panel_x + 90 + (i * 20), 145), (20, 20)),
                                               text="", manager=self.ui_manager)
            btn.colours['normal_bg'] = pygame.Color(col)
            btn.colours['hovered_bg'] = pygame.Color(col)
            btn.colours['active_bg'] = pygame.Color(col)
            btn.rebuild()
            self.btn_colors.append((btn, col))

        # Stops Dropdown - Correct Initialization to prevent Crash
        self.drop_stops = pygame_gui.elements.UIDropDownMenu(
            options_list=["Select Station"],
            starting_option="Select Station",
            relative_rect=pygame.Rect((panel_x + 20, 250), (300, 30)),
            manager=self.ui_manager
        )
        # Immediately hide it to prevent it appearing on other tabs on startup
        self.drop_stops.hide()

        self.input_troute = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((panel_x + 20, 280), (300, 32)), manager=self.ui_manager)
        self.input_troute.set_text("Cairo Alexandria")

        self.btn_add_train = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((panel_x + 50, 320), (250, 40)),
                                                          text="ADD / UPDATE TRAIN", manager=self.ui_manager)
        self.btn_current_trains = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((panel_x + 50, 365), (250, 30)),
                                                             text="CLEAR", manager=self.ui_manager)
        self.btn_clear_trains = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((panel_x + 50, 400), (250, 30)),
                                                             text="CLEAR ALL", manager=self.ui_manager)

        # --- MAP CONTROLS ---
        self.btn_zoom_in = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((20, self.height - 60), (40, 40)),
                                                        text="+", manager=self.ui_manager)
        self.btn_zoom_out = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((70, self.height - 60), (40, 40)),
                                                         text="-", manager=self.ui_manager)

        self.update_ui_visibility()

    def update_ui_visibility(self):
        """Helper to show/hide elements based on active tab."""
        # Config Tab
        is_cfg = (self.active_tab == "CONFIG")
        self.input_name.visible = is_cfg
        self.input_x.visible = is_cfg
        self.input_y.visible = is_cfg
        self.btn_algo.visible = is_cfg
        if is_cfg:
            self.slider_speed.show()
        else:
            self.slider_speed.hide()
        self.btn_scenario.visible = is_cfg
        self.btn_run.visible = is_cfg

        # Schedules Tab
        is_sched = (self.active_tab == "SCHEDULES")
        self.input_tid.visible = is_sched
        self.input_tcolor.visible = is_sched
        self.input_tstart.visible = is_sched
        self.input_troute.visible = is_sched
        self.btn_add_train.visible = is_sched
        self.btn_current_trains.visible = is_sched
        self.btn_clear_trains.visible = is_sched

        # Explicitly show/hide the dropdown to fix "appears on every tab" bug
        if is_sched:
            self.drop_stops.show()
        else:
            self.drop_stops.hide()

        for btn, _ in self.btn_colors:
            btn.visible = is_sched
            if is_sched:
                btn.show()
            else:
                btn.hide()

    def update_stops_dropdown(self):
        """Recreates the dropdown list to avoid internal state errors in pygame_gui."""
        # Use existing position
        rect = self.drop_stops.relative_rect

        # Kill old
        self.drop_stops.kill()

        # Create new with updated nodes
        nodes = ["Select Station"] + sorted(list(self.graph.graph.nodes()))
        self.drop_stops = pygame_gui.elements.UIDropDownMenu(
            options_list=nodes,
            starting_option="Select Station",
            relative_rect=rect,
            manager=self.ui_manager
        )

        # Consolidate visibility logic via update_ui_visibility
        self.update_ui_visibility()

    # --- COORDINATE TRANSFORMS ---
    def to_screen(self, x, y):
        return int(x * self.zoom + self.cam_offset_x), int(y * self.zoom + self.cam_offset_y)

    def to_world(self, sx, sy):
        return (sx - self.cam_offset_x) / self.zoom, (sy - self.cam_offset_y) / self.zoom

    # --- SCENARIOS ---
    def _generate_default_trains(self, count=7):
        self.train_route_configs.clear()
        nodes = list(self.graph.graph.nodes())
        if not nodes: return

        for i in range(1, count + 1):
            route_len = random.randint(3, 6)
            route = [random.choice(nodes)]
            for _ in range(route_len - 1):
                next_node = random.choice(nodes)
                # Ensure we don't pick the same node twice in a row
                while next_node == route[-1] and len(nodes) > 1:
                    next_node = random.choice(nodes)
                route.append(next_node)

            # Simple circular color generation
            color = ((i * 50) % 255, (i * 80 + 100) % 255, (i * 120 + 50) % 255)
            self.train_route_configs[i] = RouteConfig(train_id=i, stops=route, color=color, start_delay=(i - 1) * 30)
        self.table_dirty = True

    def load_scenario_egypt(self):
        self.graph = RailwayGraph()
        nodes = [
            ("Alexandria", 450, 100), ("Port Said", 650, 100),
            ("Tanta", 520, 180), ("Ismailia", 650, 200),
            ("Cairo", 550, 250), ("Suez", 680, 250),
            ("Beni Suef", 550, 350), ("Minya", 550, 450),
            ("Asyut", 580, 520), ("Sohag", 600, 580),
            ("Qena", 620, 630), ("Luxor", 620, 680),
            ("Aswan", 620, 780), ("Hurghada", 750, 500),
            ("Safaga", 750, 550)
        ]
        for n, x, y in nodes: self.graph.add_station(n, x, y)
        tracks = [
            ("Alexandria", "Tanta"), ("Tanta", "Cairo"),
            ("Port Said", "Ismailia"), ("Ismailia", "Cairo"), ("Ismailia", "Suez"),
            ("Cairo", "Suez"), ("Cairo", "Beni Suef"),
            ("Beni Suef", "Minya"), ("Minya", "Asyut"), ("Asyut", "Sohag"),
            ("Sohag", "Qena"), ("Qena", "Luxor"), ("Luxor", "Aswan"),
            ("Qena", "Safaga"), ("Safaga", "Hurghada")
        ]
        for u, v in tracks: self.graph.add_track(u, v)
        self.scheduler = Scheduler(self.graph)
        self._generate_default_trains(5)
        self.update_stops_dropdown()
        self.btn_scenario.set_text("SCENARIO: EGYPT")
        print("Egypt Scenario Loaded")

    def load_scenario_hub(self):
        self.graph = RailwayGraph()
        nodes = [("Central Hub", 600, 400), ("NorthA", 600, 200), ("NorthB", 600, 100),
                 ("EastA", 800, 400), ("EastB", 900, 400), ("SouthA", 600, 600), ("SouthB", 600, 700),
                 ("WestA", 400, 400), ("WestB", 300, 400)]
        for n, x, y in nodes: self.graph.add_station(n, x, y)
        tracks = [("Central Hub", "NorthA"), ("NorthA", "NorthB"), ("Central Hub", "EastA"), ("EastA", "EastB"),
                  ("Central Hub", "SouthA"), ("SouthA", "SouthB"), ("Central Hub", "WestA"), ("WestA", "WestB"),
                  ("NorthA", "EastA"), ("EastA", "SouthA"), ("SouthA", "WestA"), ("WestA", "NorthA")]
        for u, v in tracks: self.graph.add_track(u, v)
        self.scheduler = Scheduler(self.graph)
        self._generate_default_trains(8)
        self.update_stops_dropdown()
        self.btn_scenario.set_text("SCENARIO: HUB")
        print("Hub Scenario Loaded")

    def load_scenario_london(self):
        """Loads a rough approximation of the London Rail Network."""
        self.graph = RailwayGraph()
        nodes = [
            ("Paddington", 200, 300), ("Marylebone", 300, 250),
            ("Euston", 400, 200), ("Kings Cross", 500, 200),
            ("Liverpool St", 700, 250), ("London Bridge", 650, 450),
            ("Waterloo", 500, 500), ("Victoria", 350, 500),
            ("Clapham Jct", 200, 600), ("Stratford", 800, 150)
        ]
        for n, x, y in nodes: self.graph.add_station(n, x, y)

        tracks = [
            ("Paddington", "Marylebone"), ("Marylebone", "Euston"),
            ("Euston", "Kings Cross"), ("Kings Cross", "Stratford"),
            ("Kings Cross", "Liverpool St"), ("Liverpool St", "Stratford"),
            ("Liverpool St", "London Bridge"), ("London Bridge", "Waterloo"),
            ("Waterloo", "Victoria"), ("Victoria", "Clapham Jct"),
            ("Clapham Jct", "Waterloo"), ("Paddington", "Victoria")
        ]
        for u, v in tracks: self.graph.add_track(u, v)
        self.scheduler = Scheduler(self.graph)
        self._generate_default_trains(6)
        self.update_stops_dropdown()
        self.btn_scenario.set_text("SCENARIO: LONDON")
        print("London Scenario Loaded")

    def load_scenario_empty(self):
        """Loads a blank canvas with no trains."""
        self.graph = RailwayGraph()
        self.scheduler = Scheduler(self.graph)
        self.train_route_configs.clear()
        self.update_stops_dropdown()
        self.btn_scenario.set_text("SCENARIO: EMPTY")
        print("Empty Scenario Loaded")

    def cycle_scenario(self):
        txt = self.btn_scenario.text
        if "EGYPT" in txt:
            self.load_scenario_hub()
        elif "HUB" in txt:
            self.load_scenario_london()
        elif "LONDON" in txt:
            self.load_scenario_empty()
        else:
            self.load_scenario_egypt()
        self.reset_sim()

    def add_custom_train(self):
        try:
            tid = int(self.input_tid.get_text())
            c_str = self.input_tcolor.get_text().replace(',', ' ').split()
            c_vals = tuple([min(255, max(0, int(c))) for c in c_str])
            if len(c_vals) != 3: c_vals = (255, 255, 255)

            route_str = self.input_troute.get_text().strip()
            route = [n for n in route_str.split() if n in self.graph.cached_pos]

            if len(route) < 2:
                print("Error: Route must have at least 2 valid stations.")
                return

            delay = int(self.input_tstart.get_text())
            self.train_route_configs[tid] = RouteConfig(tid, route, c_vals, delay)
            self.table_dirty = True
            print(f"Train {tid} added/updated.")
        except ValueError:
            print("Invalid input format.")

    def reset_sim(self):
        self.mode = "EDITOR"
        self.paused = False
        self.sim_time = 0
        self.train_agents.clear()
        self.scheduler.reset()
        self.planned_events.clear()  # Clear scheduled events
        self.total_collisions_avoided = 0
        self.total_scheduling_time = 0
        self.btn_run.set_text("START SIMULATION")
        self.table_dirty = True

    def start_simulation(self):
        if not self.train_route_configs: return
        self.reset_sim()

        # Init agents and Schedule Full Routes
        for tid, cfg in self.train_route_configs.items():
            if not cfg.stops: continue

            # Create Agent
            start_node = cfg.stops[0]
            agent = TrainAgent(id=tid, color=cfg.color, current_node=start_node)
            agent.visual_pos = self.graph.cached_pos[start_node]
            self.train_agents[tid] = agent

            # Schedule the ENTIRE route (loop 24h to fill gantt)
            curr_plan_time = self.sim_time + cfg.start_delay
            # Plan 24 hours ahead for the chart
            while curr_plan_time < 1440:
                events, _, _ = self.scheduler.schedule_route(tid, cfg.stops, cfg.color, curr_plan_time,
                                                             self.algorithm_mode)
                if not events: break
                self.planned_events.extend(events)
                agent.schedule_queue.extend(events)
                curr_plan_time = events[-1].end_time + 100  # Dwell time loop

        self.mode = "RUNNING"
        self.btn_run.set_text("STOP SIMULATION")
        self.table_dirty = True

    def schedule_agent_route(self, tid, start_time):
        # NOTE: This method is used for dynamic reshceduling during run
        agent = self.train_agents[tid]
        cfg = self.train_route_configs[tid]

        # Schedule full path
        events, conflicts, dt = self.scheduler.schedule_route(tid, cfg.stops, cfg.color, start_time,
                                                              self.algorithm_mode)

        self.total_collisions_avoided += conflicts
        self.total_scheduling_time += dt
        self.scheduling_ops += 1

        # Note: We don't add to planned_events here to keep chart static

        # Fill agent queue (Dynamic view for execution)
        agent.schedule_queue.extend(events)

        if events and not agent.current_event:
            actual_start = events[0].start_time
            agent.delay_accumulated = actual_start - start_time

    def update_simulation(self):
        self.sim_time += 1

        # Cleanup old data every 500 ticks
        if self.sim_time % 500 == 0:
            self.scheduler.cleanup_old_reservations(self.sim_time)

        for tid, agent in self.train_agents.items():
            # 1. Update Current Event Logic
            if not agent.current_event and agent.schedule_queue:
                # Peek at next event
                next_evt = agent.schedule_queue[0]
                if self.sim_time >= next_evt.start_time:
                    agent.current_event = agent.schedule_queue.popleft()

            # 2. Update Status & Visuals
            if agent.current_event:
                evt = agent.current_event
                # Accumulate Journey Time
                agent.total_journey_time += 1

                if self.sim_time <= evt.end_time:
                    # MOVING
                    agent.status = "MOVING"
                    dur = evt.end_time - evt.start_time
                    if dur > 0:
                        t = (self.sim_time - evt.start_time) / dur
                        x1, y1 = self.graph.cached_pos[evt.source]
                        x2, y2 = self.graph.cached_pos[evt.target]
                        agent.visual_pos = (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
                else:
                    # Event Finished
                    agent.status = "WAITING"
                    agent.current_node = evt.target
                    agent.visual_pos = self.graph.cached_pos[evt.target]
                    agent.current_event = None
                    agent.trips_completed += 1
            else:
                # No active event
                if agent.schedule_queue:
                    # Waiting for next event start
                    next_start = agent.schedule_queue[0].start_time
                    if next_start > self.sim_time + 10 and agent.delay_accumulated > 10:
                        agent.status = "DELAYED"
                    else:
                        agent.status = "WAITING"
                        agent.total_wait += 1  # Count waiting time
                else:
                    # Route Finished -> Loop
                    agent.status = "ARRIVED"
                    self.schedule_agent_route(tid, self.sim_time + 100)

    def run(self):
        running = True
        while running:
            time_delta = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self.init_ui()

                self.ui_manager.process_events(event)

                if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                    if event.ui_element == self.slider_speed:
                        self.sim_speed = self.slider_speed.get_current_value()

                # Handle Dropdown Selection
                if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    if event.ui_element == self.drop_stops:
                        if event.text != "Select Station":  # Don't add placeholder
                            current_text = self.input_troute.get_text()
                            if current_text:
                                self.input_troute.set_text(current_text + " " + event.text)
                            else:
                                self.input_troute.set_text(event.text)

                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.btn_tab_config:
                        self.active_tab = "CONFIG"
                        self.update_ui_visibility()
                    elif event.ui_element == self.btn_tab_schedules:
                        self.active_tab = "SCHEDULES"
                        self.update_ui_visibility()
                    elif event.ui_element == self.btn_tab_status:
                        self.active_tab = "STATS"
                        self.update_ui_visibility()
                    elif event.ui_element == self.btn_tab_table:
                        self.active_tab = "TABLE"
                        # Only update if we haven't generated it yet (start of sim)
                        # or if we are in editor mode (adding trains)
                        if self.mode == "EDITOR":
                            self.table_dirty = True
                        self.update_ui_visibility()
                    elif event.ui_element == self.btn_run:
                        if self.mode == "EDITOR":
                            self.start_simulation()
                        else:
                            self.reset_sim()
                    elif event.ui_element == self.btn_scenario:
                        self.cycle_scenario()
                    elif event.ui_element == self.btn_algo:
                        self.algorithm_mode = "GREEDY" if self.algorithm_mode == "CSP" else "CSP"
                        self.btn_algo.set_text(f"ALGO: {self.algorithm_mode}")
                    elif event.ui_element == self.btn_add_train:
                        self.add_custom_train()
                    elif event.ui_element == self.btn_clear_trains:
                        self.train_route_configs.clear()
                    elif event.ui_element == self.btn_current_trains:
                        del self.train_route_configs[self.selected_train]
                    elif event.ui_element == self.btn_zoom_in:
                        self.zoom *= 1.1
                    elif event.ui_element == self.btn_zoom_out:
                        self.zoom /= 1.1

                    # Color Buttons
                    for btn, col in self.btn_colors:
                        if event.ui_element == btn:
                            self.input_tcolor.set_text(f"{col[0]} {col[1]} {col[2]}")

                # Key Events
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    if self.active_tab == "CONFIG":
                        try:
                            self.graph.add_station(self.input_name.get_text(), int(self.input_x.get_text()),
                                                   int(self.input_y.get_text()))
                            self.update_stops_dropdown()
                        except:
                            pass

                # Mouse Interaction
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.active_tab == "SCHEDULES":
                        mx, my = event.pos
                        for rect, tid in self.train_list_rects:
                            if rect.collidepoint(mx, my):
                                cfg = self.train_route_configs[tid]
                                self.selected_train = tid
                                self.input_tid.set_text(str(tid))
                                self.input_tcolor.set_text(f"{cfg.color[0]} {cfg.color[1]} {cfg.color[2]}")
                                self.input_tstart.set_text(str(cfg.start_delay))
                                self.input_troute.set_text(" ".join(cfg.stops))

                    if event.pos[0] < self.width - 350:
                        wx, wy = self.to_world(*event.pos)

                        # --- RIGHT CLICK TO DELETE ---
                        if event.button == 3 and self.mode == "EDITOR":
                            # 1. Check Stations
                            clicked_node = None
                            for n, (nx_x, nx_y) in self.graph.cached_pos.items():
                                if math.hypot(wx - nx_x, wy - nx_y) < (20 / self.zoom):
                                    clicked_node = n
                                    break

                            if clicked_node:
                                # Remove Node
                                self.graph.graph.remove_node(clicked_node)
                                del self.graph.cached_pos[clicked_node]
                                for tid, cfg in self.train_route_configs.items():
                                    if clicked_node in cfg.stops:
                                        cfg.stops = [s for s in cfg.stops if s != clicked_node]
                                self.update_stops_dropdown()
                                self.table_dirty = True
                                print(f"Deleted Station: {clicked_node}")
                            else:
                                # 2. Check Edges (Distance to line segment)
                                clicked_edge = None
                                for u, v in self.graph.get_all_edges():
                                    x1, y1 = self.graph.cached_pos[u]
                                    x2, y2 = self.graph.cached_pos[v]

                                    # Point-Line Distance Logic
                                    # A = wx,wy, B=x1,y1, C=x2,y2
                                    # Proj P onto AB
                                    l2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
                                    if l2 == 0: continue
                                    t = ((wx - x1) * (x2 - x1) + (wy - y1) * (y2 - y1)) / l2
                                    t = max(0, min(1, t))
                                    px = x1 + t * (x2 - x1)
                                    py = y1 + t * (y2 - y1)
                                    dist = math.hypot(wx - px, wy - py)

                                    if dist < (10 / self.zoom):
                                        clicked_edge = (u, v)
                                        break

                                if clicked_edge:
                                    self.graph.graph.remove_edge(*clicked_edge)
                                    self.table_dirty = True
                                    print(f"Deleted Track: {clicked_edge}")

                        # --- LEFT CLICK TO SELECT/LINK ---
                        elif event.button == 1:
                            clicked = None
                            for n, (nx_x, nx_y) in self.graph.cached_pos.items():
                                if math.hypot(wx - nx_x, wy - nx_y) < (20 / self.zoom):
                                    clicked = n
                                    break

                            if clicked and self.mode == "EDITOR":
                                if self.selected_node_for_link is None:
                                    self.selected_node_for_link = clicked
                                elif self.selected_node_for_link != clicked:
                                    self.graph.add_track(self.selected_node_for_link, clicked)
                                    self.table_dirty = True
                                    self.selected_node_for_link = None
                                else:
                                    self.selected_node_for_link = None
                            elif not clicked:
                                self.is_dragging_map = True
                                self.last_mouse_pos = event.pos

                elif event.type == pygame.MOUSEBUTTONUP:
                    self.is_dragging_map = False

                elif event.type == pygame.MOUSEMOTION and self.is_dragging_map:
                    mx, my = event.pos
                    self.cam_offset_x += mx - self.last_mouse_pos[0]
                    self.cam_offset_y += my - self.last_mouse_pos[1]
                    self.last_mouse_pos = (mx, my)

                if event.type == pygame.MOUSEWHEEL and self.active_tab == "TABLE":
                    self.table_scroll_y += event.y * 20
                    self.table_scroll_y = min(0, self.table_scroll_y)

            self.ui_manager.update(time_delta)

            if self.mode == "RUNNING" and not self.paused:
                self.speed_accumulator += self.sim_speed
                if self.speed_accumulator > 10: self.speed_accumulator = 10
                while self.speed_accumulator >= 1.0:
                    self.update_simulation()
                    self.speed_accumulator -= 1.0

            self.draw()
            pygame.display.flip()

    def draw(self):
        self.screen.fill(COLORS["bg"])
        self.draw_map_background()  # New Cartesian Grid
        self.draw_map()
        self.draw_ui_panel()
        self.ui_manager.draw_ui(self.screen)
        self.draw_overlay_info()

    def draw_map_background(self):
        """Draws a Cartesian grid on the map."""
        # Grid Spacing
        spacing = int(100 * self.zoom)
        start_x = int(self.cam_offset_x % spacing)
        start_y = int(self.cam_offset_y % spacing)

        for x in range(start_x, self.width, spacing):
            pygame.draw.line(self.screen, COLORS["grid"], (x, 0), (x, self.height))
        for y in range(start_y, self.height, spacing):
            pygame.draw.line(self.screen, COLORS["grid"], (0, y), (self.width, y))

    def draw_map(self):
        for u, v in self.graph.get_all_edges():
            p1 = self.to_screen(*self.graph.cached_pos[u])
            p2 = self.to_screen(*self.graph.cached_pos[v])
            pygame.draw.line(self.screen, COLORS["edge"], p1, p2, 2)

        # Highlight Active Events (Moving Trains)
        for agent in self.train_agents.values():
            if agent.current_event:
                evt = agent.current_event
                p1 = self.to_screen(*self.graph.cached_pos[evt.source])
                p2 = self.to_screen(*self.graph.cached_pos[evt.target])
                pygame.draw.line(self.screen, COLORS["edge_active"], p1, p2, 4)

        for node, (x, y) in self.graph.cached_pos.items():
            col = COLORS["node_selected"] if node == self.selected_node_for_link else COLORS["node"]
            sx, sy = self.to_screen(x, y)

            if -50 < sx < self.width + 50 and -50 < sy < self.height + 50:
                pygame.draw.circle(self.screen, col, (sx, sy), int(8 * self.zoom))
                if self.zoom > 0.6:
                    lbl = self.font.render(node, True, COLORS["text"])
                    self.screen.blit(lbl, (sx + 10, sy - 10))

        for agent in self.train_agents.values():
            sx, sy = self.to_screen(*agent.visual_pos)
            if agent.status == "DELAYED":
                pygame.draw.circle(self.screen, COLORS["status_delayed"], (sx, sy), int(14 * self.zoom), 2)
            pygame.draw.circle(self.screen, agent.color, (sx, sy), int(10 * self.zoom))

    def draw_ui_panel(self):
        panel_x = self.width - 350
        pygame.draw.rect(self.screen, COLORS["panel"], (panel_x, 0, 350, self.height))
        pygame.draw.line(self.screen, (100, 100, 100), (panel_x, 0), (panel_x, self.height), 2)

        if self.active_tab == "CONFIG":
            self.draw_tab_config(panel_x)
        elif self.active_tab == "SCHEDULES":
            self.draw_tab_schedules(panel_x)
        elif self.active_tab == "STATS":
            self.draw_tab_stats(panel_x)
        elif self.active_tab == "TABLE":
            self.draw_tab_table(panel_x)

    def draw_tab_config(self, px):
        y = 60
        self.screen.blit(self.header_font.render("Editor Settings:", True, COLORS["text"]), (px + 10, y))
        y += 40
        self.screen.blit(self.font.render("Station Name:", True, COLORS["text"]), (px + 10, y))
        y += 70
        self.screen.blit(self.font.render("X:", True, COLORS["text"]), (px + 10, y))
        self.screen.blit(self.font.render("Y:", True, COLORS["text"]), (px + 120, y))
        y += 80
        self.screen.blit(self.status_font.render("(Press Enter to Add Station)", True, (150, 150, 150)), (px + 10, y))
        y += 40
        self.screen.blit(self.header_font.render("Simulation Control:", True, COLORS["text"]), (px + 10, y))
        y += 80
        self.screen.blit(self.font.render("Algorithm Mode:", True, COLORS["text"]), (px + 10, y))
        y += 100
        self.screen.blit(self.font.render(f"Sim Speed: {self.sim_speed:.1f}x", True, COLORS["text"]), (px + 10, y))

    def draw_tab_schedules(self, px):
        y = 60
        self.screen.blit(self.header_font.render("Schedule Management", True, COLORS["text"]), (px + 10, y))
        y += 25
        self.screen.blit(self.font.render("ID:", True, COLORS["text"]), (px + 20, y + 5))
        self.screen.blit(self.font.render("Color:", True, COLORS["text"]), (px + 120, y + 5))
        self.screen.blit(self.font.render("Delay:", True, COLORS["text"]), (px + 230, y + 5))
        y += 100
        self.screen.blit(self.font.render("Stops (Space Separated):", True, COLORS["text"]), (px + 10, y))
        y += 30
        self.screen.blit(self.status_font.render("Select stops via dropdown:", True, (150, 150, 150)), (px + 10, y))
        y += 230
        self.screen.blit(self.header_font.render("Current Manifest (Click to Edit)", True, COLORS["text"]),
                         (px + 10, y))
        y += 30

        self.train_list_rects.clear()
        for tid, cfg in list(self.train_route_configs.items())[:12]:
            stops_str = " -> ".join([s[:3] for s in cfg.stops])
            txt = f"#{tid} {stops_str}"
            if len(txt) > 35: txt = txt[:32] + "..."

            row_rect = pygame.Rect(px + 10, y, 320, 20)
            self.train_list_rects.append((row_rect, tid))

            mx, my = pygame.mouse.get_pos()
            if row_rect.collidepoint(mx, my):
                pygame.draw.rect(self.screen, (60, 60, 70), row_rect)

            pygame.draw.rect(self.screen, cfg.color, (px + 10, y + 5, 10, 10))
            self.screen.blit(self.status_font.render(txt, True, COLORS["text"]), (px + 25, y + 2))
            y += 24

    def draw_tab_stats(self, px):
        y = 60
        self.screen.blit(self.header_font.render("Live Metrics", True, COLORS["text"]), (px + 10, y))
        y += 30

        avg_lat = (self.total_scheduling_time / self.scheduling_ops) if self.scheduling_ops > 0 else 0
        self.screen.blit(self.font.render(f"Avg Calculation: {avg_lat:.2f} ms", True, (150, 255, 150)), (px + 20, y))
        y += 20
        self.screen.blit(
            self.font.render(f"Conflicts Resolved: {self.total_collisions_avoided}", True, (255, 100, 100)),
            (px + 20, y))
        y += 40

        self.screen.blit(self.header_font.render("Train Stats", True, COLORS["text"]), (px + 10, y))
        y += 30

        for agent in self.train_agents.values():
            if y > self.height - 20: break

            # Format total Journey time
            total_min = agent.total_journey_time + agent.total_wait
            J_hrs = total_min // 60
            J_mins = total_min % 60

            # Format total waiting time
            total_min = agent.total_wait
            W_hrs = total_min // 60
            W_mins = total_min % 60

            # Determine next destination
            next_dest = "End"
            if agent.current_event:
                next_dest = agent.current_event.target
            elif agent.schedule_queue:
                next_dest = agent.schedule_queue[0].target

            c = COLORS["status_moving"] if agent.status == "MOVING" else COLORS["status_waiting"]
            info = f"#{agent.id} Journey: {J_hrs}h {J_mins}m | Wait: {W_hrs}h {W_mins}m \n Next: {next_dest}"

            self.screen.blit(self.status_font.render(info, True, c), (px + 20, y))
            y += 40

    def draw_tab_table(self, px):
        """Draws a Static Gantt Chart of Track Reservations."""
        y = 60
        self.screen.blit(self.header_font.render("Track Usage (Gantt)", True, COLORS["text"]), (px + 10, y))
        y += 40

        # Sort edges for Y-Axis
        edges = sorted(self.graph.get_all_edges(), key=lambda e: e[0])

        # Generate surface if dirty
        if self.table_dirty:
            h = max(600, len(edges) * 30 + 50)
            self.table_surface = pygame.Surface((340, h))
            self.table_surface.fill(COLORS["panel"])

            # X-Axis Time (0 - 1440)
            window_size = 1440  # 1 Day
            graph_w = 260
            x_offset = 70

            # Draw Time Grid Lines
            for hr in range(0, 25, 4):
                tx = x_offset + (hr * 60 / window_size) * graph_w
                pygame.draw.line(self.table_surface, (70, 70, 70), (tx, 0), (tx, h))
                self.table_surface.blit(self.status_font.render(f"{hr}", True, (150, 150, 150)), (tx - 5, 0))

            ty = 20
            # Use PLANNED EVENTS for correct, static display of schedule
            for u, v in edges:
                lbl = self.status_font.render(f"{u[:3]}-{v[:3]}", True, (180, 180, 180))
                self.table_surface.blit(lbl, (5, ty))

                # Check persistent schedule list
                for evt in self.planned_events:
                    # Check if event matches this edge (undirected check)
                    match = (evt.source == u and evt.target == v) or (evt.source == v and evt.target == u)
                    if match:
                        r_start, r_end = evt.start_time, evt.end_time

                        disp_start = r_start % window_size
                        disp_end = r_end % window_size
                        if disp_end < disp_start: disp_end = window_size

                        rx = x_offset + (disp_start / window_size) * graph_w
                        rw = ((disp_end - disp_start) / window_size) * graph_w

                        col = evt.color if hasattr(evt, 'color') else (200, 200, 200)
                        pygame.draw.rect(self.table_surface, col, (rx, ty, max(2, int(rw)), 15))

                pygame.draw.line(self.table_surface, (60, 60, 60), (0, ty + 20), (340, ty + 20), 1)
                ty += 30

            self.table_dirty = False

        # Clip and Draw
        timeline_rect = pygame.Rect(px + 5, y, 340, self.height - y - 10)
        self.screen.set_clip(timeline_rect)
        if self.table_surface:
            self.screen.blit(self.table_surface, (px + 5, y + self.table_scroll_y))

            # Draw "Now" Line on top
            curr_day_ticks = self.sim_time % 1440
            now_x = (px + 5) + 70 + (curr_day_ticks / 1440) * 260
            pygame.draw.line(self.screen, (255, 255, 255), (now_x, y), (now_x, self.height), 1)

        self.screen.set_clip(None)

    def draw_overlay_info(self):
        total_minutes = self.sim_time
        day = (total_minutes // 1440) + 1
        mins_rem = total_minutes % 1440
        hrs = mins_rem // 60
        mns = mins_rem % 60

        txt = f"Day {day} - {hrs:02d}:{mns:02d}"
        surf = self.header_font.render(txt, True, (255, 255, 255))
        pygame.draw.rect(self.screen, (0, 0, 0), (20, 20, 180, 40), border_radius=5)
        self.screen.blit(surf, (30, 25))

    def _get_edge_key(self, u, v):
        return tuple(sorted((u, v)))


if __name__ == "__main__":
    App().run()