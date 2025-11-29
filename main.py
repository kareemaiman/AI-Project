import pygame
import networkx as nx
import math
import random
import time
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

# =============================================================================
# 1. CONFIGURATION & CONSTANTS
# =============================================================================
# Initial Defaults
INITIAL_SCREEN_WIDTH = 1200
INITIAL_SCREEN_HEIGHT = 800

# Color Palette for UI and Elements
COLORS = {
    "bg": (30, 30, 35),  # Dark background for the map
    "node": (100, 200, 255),  # Stations
    "node_selected": (255, 215, 0),  # Highlighted station
    "edge": (60, 60, 60),  # Tracks
    "text": (230, 230, 230),  # Standard text
    "panel": (45, 45, 50),  # Right-hand side UI panel
    "input_bg": (25, 25, 30),  # Input fields
    "btn_active": (70, 160, 100),  # Green buttons
    "btn_inactive": (180, 60, 60),  # Red/Pause buttons
    "btn_neutral": (80, 80, 100),  # Standard buttons
    "tab_active": (100, 100, 120),  # Active tab header
    "tab_inactive": (50, 50, 60),  # Inactive tab header
    "timeline_bar": (100, 200, 150)  # Gantt chart bars
}

FONT_SIZE = 18
HEADER_FONT_SIZE = 24


# =============================================================================
# 2. DATA STRUCTURES
# =============================================================================

@dataclass
class TrainRequest:
    """DTO representing a request for a train journey."""
    train_id: int
    start_node: str
    end_node: str
    color: Tuple[int, int, int]


@dataclass
class ScheduleEvent:
    """Represents a specific reservation on a track segment."""
    train_id: int
    source: str
    target: str
    start_time: int
    end_time: int


@dataclass
class TrainAgent:
    """Holds the runtime state of a single train."""
    id: int
    pos: str
    color: Tuple[int, int, int]
    busy_until: int
    total_wait: int = 0
    trips_completed: int = 0


# =============================================================================
# 3. GRAPH MODEL
# =============================================================================

class RailwayGraph:
    """Wrapper around NetworkX to manage the physical topology."""

    def __init__(self):
        self.graph = nx.Graph()

    def add_station(self, name: str, x: int, y: int):
        self.graph.add_node(name, pos=(x, y))

    def add_track(self, u: str, v: str):
        pos = nx.get_node_attributes(self.graph, 'pos')
        if u in pos and v in pos:
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            dist = math.hypot(x2 - x1, y2 - y1)
            weight = max(1, int(dist / 5.0))
            self.graph.add_edge(u, v, weight=weight)

    def get_path(self, start: str, end: str) -> List[str]:
        try:
            return nx.shortest_path(self.graph, source=start, target=end, weight='weight')
        except nx.NetworkXNoPath:
            return []

    def get_all_edges(self):
        return list(self.graph.edges())


# =============================================================================
# 4. SCHEDULER (The AI Core)
# =============================================================================

class Scheduler:
    """Handles logic for pathfinding and conflict resolution."""

    def __init__(self, graph_model: RailwayGraph):
        self.graph_model = graph_model
        self.reservations: Dict[Tuple[str, str], List[Tuple[float, float]]] = {}
        self.track_utilization: Dict[Tuple[str, str], int] = {}

    def reset(self):
        self.reservations.clear()
        self.track_utilization.clear()

    def cleanup_old_reservations(self, current_time: int):
        for key in list(self.reservations.keys()):
            self.reservations[key] = [r for r in self.reservations[key] if r[1] > current_time]
            if not self.reservations[key]:
                del self.reservations[key]

    def _check_conflict(self, u: str, v: str, start: float, end: float, margin: float = 20.0) -> bool:
        edge_key = tuple(sorted((u, v)))
        if edge_key not in self.reservations:
            return False

        for r_start, r_end in self.reservations[edge_key]:
            if max(start, r_start) < min(end, r_end + margin):
                return True
        return False

    def _reserve(self, u: str, v: str, start: float, end: float):
        edge_key = tuple(sorted((u, v)))
        if edge_key not in self.reservations:
            self.reservations[edge_key] = []
            self.track_utilization[edge_key] = 0

        self.reservations[edge_key].append((start, end))
        self.track_utilization[edge_key] += 1

    def schedule_request(self, req: TrainRequest, current_time: int, mode="GREEDY") -> Tuple[
        List[ScheduleEvent], int, float]:
        t0 = time.perf_counter()
        path = self.graph_model.get_path(req.start_node, req.end_node)
        if not path: return ([], 0, 0.0)

        new_events = []
        conflicts_avoided = 0

        if mode == "GREEDY":
            curr_t = current_time
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                weight = self.graph_model.graph.edges[u, v]['weight']
                new_events.append(ScheduleEvent(req.train_id, u, v, curr_t, curr_t + weight))
                self._reserve(u, v, curr_t, curr_t + weight)
                curr_t += weight

        elif mode == "CSP":
            start_delay = 0
            found = False
            while start_delay < 5000:
                temp_events = []
                curr_t = current_time + start_delay
                valid_path = True

                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    weight = self.graph_model.graph.edges[u, v]['weight']
                    end_t = curr_t + weight

                    if self._check_conflict(u, v, curr_t, end_t):
                        valid_path = False
                        break

                    temp_events.append(ScheduleEvent(req.train_id, u, v, curr_t, end_t))
                    curr_t += weight

                if valid_path:
                    for evt in temp_events:
                        self._reserve(evt.source, evt.target, evt.start_time, evt.end_time)
                        new_events.append(evt)
                    found = True
                    break

                conflicts_avoided += 1
                start_delay += 10

            if not found:
                print(f"Train {req.train_id} dropped: Network saturated.")

        dt = (time.perf_counter() - t0) * 1000
        return (new_events, conflicts_avoided, dt)


# =============================================================================
# 5. UI COMPONENTS
# =============================================================================

class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = COLORS["input_bg"]
        self.text = text
        self.txt_surface = pygame.font.Font(None, 28).render(text, True, COLORS["text"])
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = COLORS["node"] if self.active else COLORS["input_bg"]
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return self.text
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            self.txt_surface = pygame.font.Font(None, 28).render(self.text, True, COLORS["text"])

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 1)
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 8))


class Button:
    def __init__(self, x, y, w, h, text, color=COLORS["btn_neutral"], callback=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.callback = callback
        self.font = pygame.font.SysFont("Arial", 16, bold=True)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        txt = self.font.render(self.text, True, (255, 255, 255))
        screen.blit(txt, (self.rect.centerx - txt.get_width() // 2, self.rect.centery - txt.get_height() // 2))

    def check_click(self, pos):
        if self.rect.collidepoint(pos) and self.callback:
            self.callback()


class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial_val):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.dragging = False

        # Calculate initial handle position
        pct = (self.val - self.min_val) / (self.max_val - self.min_val)
        self.handle_x = x + (w * pct)
        self.handle_rect = pygame.Rect(self.handle_x - 10, y - 5, 20, h + 10)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos):
                self.dragging = True
            elif self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_val_from_pos(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_val_from_pos(event.pos[0])

    def update_val_from_pos(self, x):
        x = max(self.rect.left, min(x, self.rect.right))
        self.handle_x = x
        self.handle_rect.x = x - 10
        pct = (x - self.rect.left) / self.rect.width
        self.val = self.min_val + pct * (self.max_val - self.min_val)

    def draw(self, screen):
        # Draw line
        pygame.draw.rect(screen, (150, 150, 150), self.rect, border_radius=2)
        # Draw filled part
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, self.handle_x - self.rect.x, self.rect.height)
        pygame.draw.rect(screen, COLORS["btn_active"], fill_rect, border_radius=2)
        # Draw Handle
        pygame.draw.rect(screen, (200, 200, 200), self.handle_rect, border_radius=5)


# =============================================================================
# 6. MAIN APPLICATION
# =============================================================================

class App:
    def __init__(self):
        pygame.init()
        # Enable Resizable Window
        self.screen = pygame.display.set_mode((INITIAL_SCREEN_WIDTH, INITIAL_SCREEN_HEIGHT), pygame.RESIZABLE)
        self.width, self.height = INITIAL_SCREEN_WIDTH, INITIAL_SCREEN_HEIGHT

        pygame.display.set_caption("Smart Rail: Network Packet Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", FONT_SIZE)
        self.header_font = pygame.font.SysFont("Arial", HEADER_FONT_SIZE, bold=True)

        # Systems
        self.graph = RailwayGraph()
        self.scheduler = Scheduler(self.graph)

        # State Variables
        self.active_events: List[ScheduleEvent] = []
        self.train_agents: Dict[int, TrainAgent] = {}
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

        # Metrics Accumulators
        self.total_collisions_avoided = 0
        self.total_scheduling_time = 0.0
        self.scheduling_ops = 0

        # UI Initialization
        self.init_ui()
        self.load_scenario_1()

    def init_ui(self):
        """Setup all buttons and input fields based on current window dimensions."""
        panel_x = self.width - 350
        panel_w = 350

        # Inputs
        self.input_name = InputBox(panel_x + 50, 130, 200, 32, "StationX")
        self.input_x = InputBox(panel_x + 50, 200, 90, 32, "400")
        self.input_y = InputBox(panel_x + 160, 200, 90, 32, "300")
        self.input_trains = InputBox(panel_x + 170, 340, 80, 32, "5")

        # Tabs
        self.tab_config = pygame.Rect(panel_x, 0, 116, 40)
        self.tab_status = pygame.Rect(panel_x + 116, 0, 116, 40)
        self.tab_timeline = pygame.Rect(panel_x + 232, 0, 118, 40)

        # Buttons
        self.btn_run = Button(panel_x + 50, 680, 200, 50, "START SIMULATION", COLORS["btn_active"], self.toggle_run)
        self.btn_scenario = Button(panel_x + 50, 620, 200, 40, "LOAD SCENARIO: HUB", COLORS["btn_neutral"],
                                   self.cycle_scenario)

        # Slider for Speed (0.1x to 10.0x)
        self.slider_speed = Slider(panel_x + 50, 560, 200, 10, 0.1, 10.0, self.sim_speed)

        # Map Controls (Overlay)
        self.btn_zoom_in = Button(20, self.height - 60, 40, 40, "+", COLORS["btn_neutral"], self.zoom_in)
        self.btn_zoom_out = Button(70, self.height - 60, 40, 40, "-", COLORS["btn_neutral"], self.zoom_out)

    # --- COORDINATE TRANSFORMS ---
    def to_screen(self, x, y):
        """Converts World Coords -> Screen Coords"""
        return int(x * self.zoom + self.cam_offset_x), int(y * self.zoom + self.cam_offset_y)

    def to_world(self, sx, sy):
        """Converts Screen Coords -> World Coords"""
        return (sx - self.cam_offset_x) / self.zoom, (sy - self.cam_offset_y) / self.zoom

    # --- CAMERA ACTIONS ---
    def zoom_in(self):
        self.zoom *= 1.1

    def zoom_out(self):
        self.zoom /= 1.1

    # --- SCENARIOS ---
    def load_scenario_1(self):
        self.graph = RailwayGraph()
        self.graph.add_station("Central", 600, 400)
        self.graph.add_station("North", 600, 100)
        self.graph.add_station("East", 800, 400)
        self.graph.add_station("South", 600, 700)
        self.graph.add_station("West", 400, 400)

        self.graph.add_track("Central", "North")
        self.graph.add_track("Central", "East")
        self.graph.add_track("Central", "South")
        self.graph.add_track("Central", "West")
        self.graph.add_track("North", "East")
        self.graph.add_track("East", "South")
        self.graph.add_track("South", "West")
        self.graph.add_track("West", "North")
        self.scheduler = Scheduler(self.graph)
        print("Scenario 1 Loaded")

    def load_scenario_2(self):
        self.graph = RailwayGraph()
        nodes = [
            ("Hub", 600, 400), ("A1", 400, 200), ("A2", 300, 100),
            ("B1", 800, 200), ("B2", 900, 100), ("C1", 800, 600),
            ("C2", 900, 700), ("D1", 400, 600), ("D2", 300, 700)
        ]
        for n, x, y in nodes: self.graph.add_station(n, x, y)

        tracks = [
            ("Hub", "A1"), ("A1", "A2"), ("Hub", "B1"), ("B1", "B2"),
            ("Hub", "C1"), ("C1", "C2"), ("Hub", "D1"), ("D1", "D2"),
            ("A1", "B1"), ("B1", "C1"), ("C1", "D1"), ("D1", "A1")
        ]
        for u, v in tracks: self.graph.add_track(u, v)
        self.scheduler = Scheduler(self.graph)
        print("Scenario 2 Loaded")

    def load_scenario_3(self):
        self.graph = RailwayGraph()
        self.scheduler = Scheduler(self.graph)
        print("Scenario 3 Loaded")

    def cycle_scenario(self):
        if self.btn_scenario.text.endswith("HUB"):
            self.load_scenario_2()
            self.btn_scenario.text = "LOAD SCENARIO: Custom"
        elif self.btn_scenario.text.endswith("Custom"):
            self.load_scenario_3()
            self.btn_scenario.text = "LOAD SCENARIO: LOOP"
        else:
            self.load_scenario_1()
            self.btn_scenario.text = "LOAD SCENARIO: HUB"
        self.reset_sim()

    def reset_sim(self):
        self.mode = "EDITOR"
        self.paused = False
        self.sim_time = 0
        self.active_events.clear()
        self.train_agents.clear()
        self.scheduler.reset()
        self.total_collisions_avoided = 0
        self.total_scheduling_time = 0
        self.scheduling_ops = 0
        self.btn_run.text = "START SIMULATION"
        self.btn_run.color = COLORS["btn_active"]

    def toggle_run(self):
        if self.mode == "EDITOR":
            self.start_simulation()
        else:
            self.reset_sim()

    def start_simulation(self):
        try:
            count = int(self.input_trains.text)
        except:
            count = 1

        nodes = list(self.graph.graph.nodes())
        if len(nodes) < 2: return

        self.scheduler.reset()
        self.active_events.clear()
        self.train_agents.clear()

        for i in range(count):
            start = random.choice(nodes)
            color = (random.randint(100, 255), random.randint(80, 255), random.randint(80, 255))
            self.train_agents[i] = TrainAgent(id=i, pos=start, color=color, busy_until=0)
            self.schedule_next_leg(i)

        self.mode = "RUNNING"
        self.btn_run.text = "RESET SIMULATION"
        self.btn_run.color = COLORS["btn_inactive"]

    def schedule_next_leg(self, train_id):
        agent = self.train_agents[train_id]
        nodes = list(self.graph.graph.nodes())

        target = random.choice(nodes)
        while target == agent.pos:
            target = random.choice(nodes)

        req = TrainRequest(train_id, agent.pos, target, agent.color)
        events, avoided, latency = self.scheduler.schedule_request(req, self.sim_time, self.algorithm_mode)

        self.total_collisions_avoided += avoided
        self.total_scheduling_time += latency
        self.scheduling_ops += 1

        if events:
            self.active_events.extend(events)
            initial_wait = events[0].start_time - self.sim_time
            agent.total_wait += initial_wait
            agent.busy_until = events[-1].end_time
            agent.pos = events[-1].target
            agent.trips_completed += 1
        else:
            agent.busy_until = self.sim_time + 50
            agent.total_wait += 50

    # --- MAIN LOOP ---
    def run(self):
        running = True
        while running:
            self.screen.fill(COLORS["bg"])
            dt_ms = self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False

                # --- WINDOW RESIZE ---
                if event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self.init_ui()  # Re-layout UI

                # --- INPUTS ---
                if self.active_tab == "CONFIG" and self.mode == "EDITOR":
                    self.input_name.handle_event(event)
                    self.input_x.handle_event(event)
                    self.input_y.handle_event(event)
                    self.input_trains.handle_event(event)
                    # Add Station
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                        if self.input_name.active:
                            try:
                                self.graph.add_station(self.input_name.text, int(self.input_x.text),
                                                       int(self.input_y.text))
                            except:
                                pass

                # --- SLIDER ---
                if self.active_tab == "CONFIG":
                    self.slider_speed.handle_event(event)
                    self.sim_speed = self.slider_speed.val

                # --- MOUSE EVENTS ---
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()

                    # 1. Check UI Interaction first (Right Panel)
                    panel_start_x = self.width - 350
                    if mx > panel_start_x:
                        if self.tab_config.collidepoint((mx, my)):
                            self.active_tab = "CONFIG"
                        elif self.tab_status.collidepoint((mx, my)):
                            self.active_tab = "STATUS"
                        elif self.tab_timeline.collidepoint((mx, my)):
                            self.active_tab = "TIMELINE"

                        if self.active_tab == "CONFIG":
                            self.btn_run.check_click((mx, my))
                            self.btn_scenario.check_click((mx, my))

                            # Algo Toggle
                            algo_rect = pygame.Rect(panel_start_x + 50, 420, 200, 40)
                            if algo_rect.collidepoint((mx, my)):
                                self.algorithm_mode = "CSP" if self.algorithm_mode == "GREEDY" else "GREEDY"

                    # 2. Check Map Zoom Controls
                    elif self.btn_zoom_in.rect.collidepoint((mx, my)):
                        self.zoom_in()
                    elif self.btn_zoom_out.rect.collidepoint((mx, my)):
                        self.zoom_out()

                    # 3. Map Interaction (Click or Drag)
                    else:
                        # Check if clicking a node (World Coordinates)
                        wx, wy = self.to_world(mx, my)
                        pos = nx.get_node_attributes(self.graph.graph, 'pos')
                        clicked_node = None
                        for node, (nx_x, nx_y) in pos.items():
                            if math.hypot(wx - nx_x, wy - nx_y) < 20:  # 20 is node radius tolerance
                                clicked_node = node
                                break

                        if clicked_node and self.mode == "EDITOR":
                            self.handle_link(clicked_node)
                        else:
                            # Start Dragging Camera
                            self.is_dragging_map = True
                            self.last_mouse_pos = (mx, my)

                elif event.type == pygame.MOUSEBUTTONUP:
                    self.is_dragging_map = False

                elif event.type == pygame.MOUSEMOTION:
                    if self.is_dragging_map:
                        mx, my = pygame.mouse.get_pos()
                        dx = mx - self.last_mouse_pos[0]
                        dy = my - self.last_mouse_pos[1]
                        self.cam_offset_x += dx
                        self.cam_offset_y += dy
                        self.last_mouse_pos = (mx, my)

            # Logic Update (Accumulator for fractional speeds)
            if self.mode == "RUNNING" and not self.paused:
                self.speed_accumulator += self.sim_speed
                while self.speed_accumulator >= 1.0:
                    self.update_simulation()
                    self.speed_accumulator -= 1.0

            # Rendering
            self.draw_map()
            self.draw_ui_panel()
            self.draw_overlay_info()

            pygame.display.flip()

    def handle_link(self, clicked_node):
        if self.selected_node_for_link is None:
            self.selected_node_for_link = clicked_node
        elif self.selected_node_for_link != clicked_node:
            self.graph.add_track(self.selected_node_for_link, clicked_node)
            self.selected_node_for_link = None
        else:
            self.selected_node_for_link = None

    def update_simulation(self):
        self.sim_time += 1
        if self.sim_time % 500 == 0:
            self.scheduler.cleanup_old_reservations(self.sim_time)
        for agent in self.train_agents.values():
            if self.sim_time >= agent.busy_until:
                self.schedule_next_leg(agent.id)
        self.active_events = [e for e in self.active_events if e.end_time > self.sim_time]

    # --- DRAWING ---
    def draw_map(self):
        # Draw Tracks
        pos = nx.get_node_attributes(self.graph.graph, 'pos')
        for u, v in self.graph.graph.edges():
            is_busy = False
            edge_key = tuple(sorted((u, v)))
            if edge_key in self.scheduler.reservations:
                for start, end in self.scheduler.reservations[edge_key]:
                    if start <= self.sim_time <= end:
                        is_busy = True
                        break

            color = (150, 100, 100) if is_busy else COLORS["edge"]
            width = 5 if is_busy else 2

            p1 = self.to_screen(*pos[u])
            p2 = self.to_screen(*pos[v])
            pygame.draw.line(self.screen, color, p1, p2, width)

        # Draw Stations
        for node, (x, y) in pos.items():
            col = COLORS["node_selected"] if node == self.selected_node_for_link else COLORS["node"]
            sx, sy = self.to_screen(x, y)

            # Culling: Don't draw if way off screen
            if -50 < sx < self.width + 50 and -50 < sy < self.height + 50:
                pygame.draw.circle(self.screen, col, (sx, sy), int(12 * self.zoom))
                if self.zoom > 0.5:  # Hide text if zoomed out too far
                    lbl = self.font.render(node, True, COLORS["text"])
                    self.screen.blit(lbl, (sx - 10, sy - 30 * self.zoom))

        # Draw Trains
        for event in self.active_events:
            if event.start_time <= self.sim_time <= event.end_time:
                dur = event.end_time - event.start_time
                if dur == 0: continue
                t = (self.sim_time - event.start_time) / dur

                x1, y1 = pos[event.source]
                x2, y2 = pos[event.target]
                curr_x = x1 + t * (x2 - x1)
                curr_y = y1 + t * (y2 - y1)

                scx, scy = self.to_screen(curr_x, curr_y)
                agent = self.train_agents[event.train_id]
                radius = int(10 * self.zoom)
                pygame.draw.circle(self.screen, agent.color, (scx, scy), radius)
                pygame.draw.circle(self.screen, (0, 0, 0), (scx, scy), radius, 1)

    def draw_ui_panel(self):
        panel_x = self.width - 350

        # Background
        pygame.draw.rect(self.screen, COLORS["panel"], (panel_x, 0, 350, self.height))
        pygame.draw.line(self.screen, (100, 100, 100), (panel_x, 0), (panel_x, self.height), 2)

        # Tabs
        for r, t, name in [(self.tab_config, "CONFIG", "CONFIG"),
                           (self.tab_status, "STATUS", "STATUS"),
                           (self.tab_timeline, "TIMELINE", "TIMELINE")]:
            col = COLORS["tab_active"] if self.active_tab == t else COLORS["tab_inactive"]
            pygame.draw.rect(self.screen, col, r, border_radius=5)
            txt = self.font.render(name, True, COLORS["text"])
            self.screen.blit(txt, (r.x + 10, r.y + 10))

        # Content Areas
        if self.active_tab == "CONFIG":
            self.draw_tab_config(panel_x)
        elif self.active_tab == "STATUS":
            self.draw_tab_status(panel_x)
        elif self.active_tab == "TIMELINE":
            self.draw_tab_timeline(panel_x)

    def draw_tab_config(self, px):
        y = 60
        self.screen.blit(self.header_font.render("Map Editor", True, COLORS["text"]), (px + 10, y))
        y += 40
        self.screen.blit(self.font.render("Station Name:", True, COLORS["text"]), (px + 10, y))
        self.input_name.draw(self.screen)
        y += 70
        self.screen.blit(self.font.render("Pos X:", True, COLORS["text"]), (px + 10, y))
        self.input_x.draw(self.screen)
        self.screen.blit(self.font.render("Pos Y:", True, COLORS["text"]), (px + 120, y))
        self.input_y.draw(self.screen)

        y += 80
        pygame.draw.line(self.screen, (100, 100, 100), (px + 10, y), (self.width - 20, y), 1)
        y += 20

        self.screen.blit(self.header_font.render("Simulation Settings", True, COLORS["text"]), (px + 10, y))
        y += 50

        self.screen.blit(self.font.render("Initial Trains:", True, COLORS["text"]), (px + 10, y + 5))
        self.input_trains.draw(self.screen)
        y += 60

        self.screen.blit(self.font.render("Scheduler Algorithm:", True, COLORS["text"]), (px + 10, y))
        y += 30
        mode_rect = pygame.Rect(px + 50, y, 200, 40)
        mode_col = (100, 200, 150) if self.algorithm_mode == "CSP" else (200, 100, 100)
        pygame.draw.rect(self.screen, mode_col, mode_rect, border_radius=5)
        mtxt = self.font.render(self.algorithm_mode, True, (0, 0, 0))
        self.screen.blit(mtxt, (mode_rect.centerx - mtxt.get_width() // 2, mode_rect.y + 10))
        y += 80

        # Controls
        self.screen.blit(self.font.render(f"Sim Speed: {self.sim_speed:.1f}x", True, COLORS["text"]), (px + 10, 530))
        self.slider_speed.draw(self.screen)

        self.btn_scenario.draw(self.screen)
        self.btn_run.draw(self.screen)

    def draw_tab_status(self, px):
        y = 60
        self.screen.blit(self.header_font.render("Live Statistics", True, COLORS["text"]), (px + 10, y))
        y += 40

        avg_sched = (self.total_scheduling_time / self.scheduling_ops) if self.scheduling_ops > 0 else 0
        stats = [
            f"Sim Time: {self.sim_time} ticks",
            f"Active Trains: {len(self.train_agents)}",
            f"Collisions Avoided: {self.total_collisions_avoided}",
            f"Scheduling Latency: {avg_sched:.2f}ms",
            f"Ops Performed: {self.scheduling_ops}"
        ]

        for s in stats:
            self.screen.blit(self.font.render(s, True, (200, 255, 200)), (px + 10, y))
            y += 30

        y += 20
        pygame.draw.line(self.screen, (100, 100, 100), (px + 10, y), (self.width - 20, y), 1)
        y += 20
        self.screen.blit(self.header_font.render("Train Status", True, COLORS["text"]), (px + 10, y))
        y += 30

        for i, agent in enumerate(list(self.train_agents.values())[:10]):
            status = "Moving" if self.sim_time < agent.busy_until else "Waiting"
            col = agent.color
            pygame.draw.rect(self.screen, col, (px + 10, y, 20, 20))

            info = f"#{agent.id} -> {agent.pos[:8]} ({status})"
            self.screen.blit(self.font.render(info, True, COLORS["text"]), (px + 40, y))
            y += 25

    def draw_tab_timeline(self, px):
        y = 60
        self.screen.blit(self.header_font.render("Track Occupancy", True, COLORS["text"]), (px + 10, y))
        y += 30

        window_size = 1000
        bar_height = 15
        chart_w = 300

        edges = self.graph.get_all_edges()

        pygame.draw.line(self.screen, (255, 255, 255), (px + 10, y), (px + 10, 750), 1)
        pygame.draw.line(self.screen, (255, 255, 255), (px + 10, 750), (self.width - 20, 750), 1)

        start_y = y + 10

        for idx, (u, v) in enumerate(edges[:20]):
            if start_y > 720: break

            lbl = self.font.render(f"{u[:3]}-{v[:3]}", True, (180, 180, 180))
            self.screen.blit(lbl, (px + 15, start_y))

            edge_key = tuple(sorted((u, v)))
            if edge_key in self.scheduler.reservations:
                for r_start, r_end in self.scheduler.reservations[edge_key]:
                    if r_end < self.sim_time or r_start > self.sim_time + window_size:
                        continue

                    disp_start = max(0, r_start - self.sim_time)
                    disp_end = min(window_size, r_end - self.sim_time)

                    x_pos = (px + 90) + (disp_start / window_size) * (chart_w - 80)
                    w = ((disp_end - disp_start) / window_size) * (chart_w - 80)

                    if w < 1: w = 1

                    pygame.draw.rect(self.screen, COLORS["timeline_bar"], (x_pos, start_y, w, bar_height))

            start_y += 25

    def draw_overlay_info(self):
        # Draw Zoom Controls Overlay
        self.btn_zoom_in.draw(self.screen)
        self.btn_zoom_out.draw(self.screen)

        # Draw Timer
        minutes = int(self.sim_time / 3600)
        seconds = int((self.sim_time / 60) % 60)

        surf = self.header_font.render(f"{minutes:02d}:{seconds:02d}", True, (255, 255, 255))
        bg = surf.get_rect(topleft=(20, 20))
        bg.inflate_ip(20, 10)
        pygame.draw.rect(self.screen, (0, 0, 0), bg, border_radius=5)
        self.screen.blit(surf, (30, 25))


if __name__ == "__main__":
    App().run()