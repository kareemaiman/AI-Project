# Smart Rail: Automated API & Function Directory (`functions.md`)

> **Generated on:** 2026-08-30 01:41:10  
> **Note:** Do not manually edit this file. It is automatically compiled by `scripts/parse_functions.py`.

---

## Module: [`algorithms/__init__.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/algorithms/__init__.py)
**Description:** Smart Rail Algorithms Package.

Hosts individual pathfinding and scheduling deconfliction algorithms:
BFS, DFS, Dijkstra, Floyd-Warshall, Greedy, CSP/CNF, Priority EDF, and Dynamic Reroute.

---

## Module: [`algorithms/base.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/algorithms/base.py)
**Description:** Smart Rail Base Scheduling & Reservation Table Primitives.

Defines the spatial-temporal reservation table and abstract BaseScheduler interface
shared across all deconfliction solvers.

### Classes

#### `class ReservationTable` (Line 13)
Manages spatial-temporal track block occupancy across undirected graph edges.

| Method | Signature | Description |
| :--- | :--- | :--- |
| `__init__` | `__init__(self, safety_margin: float)` | Initializes empty reservation table with specified safety headway. |
| `reset` | `reset(self) -> None` | Clears all track block reservations. |
| `get_edge_key` | `get_edge_key(self, u: str, v: str) -> Tuple[str, str]` | Returns a canonical alphabetical key for an undirected track segment. |
| `check_conflict` | `check_conflict(self, u: str, v: str, start: float, end: float, margin: Optional[float]) -> bool` | Checks whether the track segment (u, v) is occupied during [start, end]. |
| `reserve` | `reserve(self, u: str, v: str, start: float, end: float, train_id: int) -> None` | Locks a temporal interval [start, end] on track (u, v) for a train. |
| `cleanup_old` | `cleanup_old(self, current_time: int) -> None` | Purges reservations that expired before current simulation tick. |

#### `class BaseScheduler` (Line 75)
Abstract base class for all multi-train scheduling and deconfliction algorithms.

| Method | Signature | Description |
| :--- | :--- | :--- |
| `__init__` | `__init__(self, graph: RailwayGraph, safety_margin: float)` | Initializes scheduler with reference graph model and reservation table. |
| `reset` | `reset(self) -> None` | Clears all active reservations. |
| `cleanup_old_reservations` | `cleanup_old_reservations(self, current_time: int) -> None` | Purges expired reservations from table. |
| `schedule_route` | `schedule_route(self, train_id: int, stops: List[str], color: Tuple[int, int, int], start_time: int, priority: int) -> Tuple[List[ScheduleEvent], int, float]` | Schedules a full multi-stop train route. |

---

## Module: [`algorithms/bfs.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/algorithms/bfs.py)
**Description:** Breadth-First Search (BFS) Pathfinding Algorithm.

Finds the route between two stations with the fewest intermediate station hops.

### Standalone Functions

| Function | Signature | Description |
| :--- | :--- | :--- |
| `bfs_path` | `bfs_path(graph: RailwayGraph, start: str, end: str) -> List[str]` | Computes unweighted shortest path (fewest station hops) using Breadth-First Search. |

---

## Module: [`algorithms/cnf_csp.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/algorithms/cnf_csp.py)
**Description:** Constraint Satisfaction Problem (CSP / CNF) Deconfliction Algorithm.

Models track reservations as temporal constraint intervals (disjunctive clauses)
and solves for the earliest feasible time-slot satisfying headway safety clauses.

### Classes

#### `class CSPScheduler` (Line 15)
Constraint satisfaction lookahead scheduler evaluating sequential block clauses.

| Method | Signature | Description |
| :--- | :--- | :--- |
| `__init__` | `__init__(self, graph: RailwayGraph, safety_margin: float, max_lookahead: int)` | Initializes CSP solver with safety headway and search horizon. |
| `schedule_route` | `schedule_route(self, train_id: int, stops: List[str], color: Tuple[int, int, int], start_time: int, priority: int) -> Tuple[List[ScheduleEvent], int, float]` | Finds the first time-interval satisfying all non-overlap constraint clauses. |

---

## Module: [`algorithms/dfs.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/algorithms/dfs.py)
**Description:** Depth-First Search (DFS) Pathfinding Algorithm.

Explores paths deeply to discover alternative loop-free routes between stations.

### Standalone Functions

| Function | Signature | Description |
| :--- | :--- | :--- |
| `dfs_path` | `dfs_path(graph: RailwayGraph, start: str, end: str) -> List[str]` | Computes a path between two stations using Depth-First Search exploration. |

---

## Module: [`algorithms/dijkstra.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/algorithms/dijkstra.py)
**Description:** Dijkstra Shortest Path Algorithm.

Computes the time-optimal path between stations weighted by track travel durations.

### Standalone Functions

| Function | Signature | Description |
| :--- | :--- | :--- |
| `dijkstra_path` | `dijkstra_path(graph: RailwayGraph, start: str, end: str) -> List[str]` | Computes time-optimal shortest path using Dijkstra's priority queue algorithm. |

---

## Module: [`algorithms/dynamic_reroute.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/algorithms/dynamic_reroute.py)
**Description:** Dynamic Re-routing & Multi-Path Deconfliction Algorithm.

Explores alternative physical track corridors when primary shortest-path tracks
experience severe congestion, dynamically load-balancing the railway network.

### Classes

#### `class DynamicRerouteScheduler` (Line 16)
Dynamic multi-path scheduler exploring k-shortest alternative track routes.

| Method | Signature | Description |
| :--- | :--- | :--- |
| `__init__` | `__init__(self, graph: RailwayGraph, safety_margin: float, k_paths: int)` | Initializes dynamic reroute scheduler. |
| `_get_k_shortest_paths` | `_get_k_shortest_paths(self, start: str, end: str) -> List[List[str]]` | Returns up to k shortest distinct physical paths between start and end. |
| `schedule_route` | `schedule_route(self, train_id: int, stops: List[str], color: Tuple[int, int, int], start_time: int, priority: int) -> Tuple[List[ScheduleEvent], int, float]` | Evaluates candidate alternative paths per leg and selects the path with earliest arrival. |

---

## Module: [`algorithms/floyd_warshall.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/algorithms/floyd_warshall.py)
**Description:** Floyd-Warshall All-Pairs Shortest Path Algorithm.

Computes the all-pairs distance matrix and intermediate predecessor matrix
for instant O(1) routing across the entire railway graph.

### Standalone Functions

| Function | Signature | Description |
| :--- | :--- | :--- |
| `floyd_warshall_all_pairs` | `floyd_warshall_all_pairs(graph: RailwayGraph) -> Tuple[Dict[Tuple[str, str], float], Dict[Tuple[str, str], Optional[str]]]` | Computes all-pairs shortest paths using the dynamic programming Floyd-Warshall algorithm. |
| `reconstruct_floyd_path` | `reconstruct_floyd_path(next_node: Dict[Tuple[str, str], Optional[str]], start: str, end: str) -> List[str]` | Reconstructs shortest path from Floyd-Warshall next-hop table. |

---

## Module: [`algorithms/greedy.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/algorithms/greedy.py)
**Description:** Greedy Earliest-Deadline Scheduling Algorithm.

Assigns earliest possible track reservations per leg, pushing departure forward
iteratively by fixed-step delays upon detecting contention.

### Classes

#### `class GreedyScheduler` (Line 15)
Greedy incremental reservation deconfliction algorithm.

| Method | Signature | Description |
| :--- | :--- | :--- |
| `__init__` | `__init__(self, graph: RailwayGraph, safety_margin: float, step_delay: int)` | Initializes Greedy scheduler with configurable backoff step. |
| `schedule_route` | `schedule_route(self, train_id: int, stops: List[str], color: Tuple[int, int, int], start_time: int, priority: int) -> Tuple[List[ScheduleEvent], int, float]` | Schedules consecutive legs greedily, stepping departure forward on collision. |

---

## Module: [`algorithms/priority_edf.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/algorithms/priority_edf.py)
**Description:** Priority Earliest Deadline First (Priority EDF) Deconfliction Algorithm.

Schedules trains based on service tier (1=Express, 2=Standard, 3=Freight).
Higher priority tiers are allocated tighter headway windows and smaller backoff steps.

### Classes

#### `class PriorityEDFScheduler` (Line 15)
Tier-aware priority scheduler minimizing high-priority passenger train delays.

| Method | Signature | Description |
| :--- | :--- | :--- |
| `__init__` | `__init__(self, graph: RailwayGraph, base_safety_margin: float)` | Initializes Priority EDF solver. |
| `schedule_route` | `schedule_route(self, train_id: int, stops: List[str], color: Tuple[int, int, int], start_time: int, priority: int) -> Tuple[List[ScheduleEvent], int, float]` | Schedules train route with tier-adjusted search step and safety buffers. |

---

## Module: [`core/__init__.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/core/__init__.py)
**Description:** Smart Rail Core Package.

---

## Module: [`core/config_manager.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/core/config_manager.py)
**Description:** Smart Rail Configuration Manager & Schema Validator.

Loads data-driven configuration from data/config.json with comprehensive validation,
fallback default recovery, and runtime config access.

### Classes

#### `class ConfigManager` (Line 85)
Manages reading, caching, and validating data/config.json.

| Method | Signature | Description |
| :--- | :--- | :--- |
| `__init__` | `__init__(self, config_path: str)` | Initializes configuration loader with target path. |
| `load` | `load(self) -> Dict[str, Any]` | Loads configuration from JSON file. If missing or corrupted, |
| `save_defaults` | `save_defaults(self) -> None` | Writes the default configuration to the JSON file path. |
| `_validate_and_merge` | `_validate_and_merge(self, loaded: Dict[str, Any]) -> Dict[str, Any]` | Ensures all required nested keys exist, filling missing keys from fallback. |
| `get` | `get(self, section: str, key: str, default: Any) -> Any` | Retrieves a configuration value safely. |
| `get_color` | `get_color(self, name: str) -> Tuple[int, int, int]` | Returns an RGB color tuple by key name. |
| `get_preset_train_colors` | `get_preset_train_colors(self) -> List[Tuple[int, int, int]]` | Returns list of preset RGB train colors. |

---

## Module: [`core/logger.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/core/logger.py)
**Description:** Smart Rail Structured Logging & Diagnostic Error Handler.

Provides multi-handler rotating logging to smart_rail.log and console,
with traceback capture, exception isolation, and graceful recovery utilities.

### Standalone Functions

| Function | Signature | Description |
| :--- | :--- | :--- |
| `setup_logger` | `setup_logger(log_file: str, level: str, max_bytes: int, backup_count: int) -> logging.Logger` | Configures and initializes the centralized rotating file and console logger. |
| `get_logger` | `get_logger() -> logging.Logger` | Returns the singleton logger instance, creating it with defaults if uninitialized. |

---

## Module: [`core/models.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/core/models.py)
**Description:** Smart Rail Core Models & Topology Representation.

Defines the mathematical data structures for graph stations and track edges,
atomic scheduled reservations, dynamic train agents, and route manifests.

### Classes

#### `class ScheduleEvent` (Line 16)
Represents an atomic time-locked reservation on a track segment.

#### `class TrainAgent` (Line 27)
Holds the runtime physics and state machine of a single active train.

#### `class RouteConfig` (Line 46)
Configuration manifest for a train's requested sequence of stops and priority.

#### `class RailwayGraph` (Line 55)
Railway network topology manager backed by an undirected NetworkX Graph.
Manages station nodes with 2D coordinates and track edges with traversal weights.

| Method | Signature | Description |
| :--- | :--- | :--- |
| `__init__` | `__init__(self, speed_pixels_per_tick: float)` | Initializes an empty graph and station coordinate cache. |
| `add_station` | `add_station(self, name: str, x: int, y: int) -> bool` | Adds a station node at coordinate (x, y). |
| `add_track` | `add_track(self, u: str, v: str) -> bool` | Connects two stations with an undirected track segment weighted by travel duration. |
| `remove_station` | `remove_station(self, name: str) -> bool` | Removes a station and all connected tracks from the graph. |
| `remove_track` | `remove_track(self, u: str, v: str) -> bool` | Removes an undirected track between stations u and v. |
| `has_station` | `has_station(self, name: str) -> bool` | Checks if a station exists in the graph. |
| `get_all_edges` | `get_all_edges(self) -> List[Tuple[str, str]]` | Returns all undirected track segments in the network. |
| `get_pos` | `get_pos(self, node_name: str) -> Tuple[int, int]` | Returns the world-space coordinate of a given station. |
| `clear` | `clear(self) -> None` | Clears all stations and tracks from the network. |

---

## Module: [`core/scenario_manager.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/core/scenario_manager.py)
**Description:** Smart Rail Scenario Manager & JSON Serialization Engine.

Scans, loads, validates, and exports railway topology maps and train manifests
to and from JSON files located in data/maps/.

### Classes

#### `class ScenarioManager` (Line 15)
Manages discovery, loading, and persistence of railway maps in JSON format.

| Method | Signature | Description |
| :--- | :--- | :--- |
| `__init__` | `__init__(self, maps_dir: str)` | Initializes scenario manager with target maps directory. |
| `scan_scenarios` | `scan_scenarios(self) -> List[str]` | Scans data/maps/ for all available .json scenario files. |
| `load_scenario` | `load_scenario(self, name: str, speed: float) -> Tuple[RailwayGraph, Dict[int, RouteConfig], str]` | Loads a railway graph and train manifest from a named JSON map file. |
| `save_scenario` | `save_scenario(self, name: str, graph: RailwayGraph, trains: Dict[int, RouteConfig], description: str) -> Tuple[bool, str]` | Serializes the current network topology and train fleet into a JSON file. |

---

## Module: [`core/simulation_engine.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/core/simulation_engine.py)
**Description:** Smart Rail Discrete Simulation Engine & Multi-Agent Physics Stepper.

Coordinates discrete simulation ticks, dynamic train agent physics updates,
multi-algorithm deconfliction dispatching, and live telemetry tracking.

### Classes

#### `class SimulationEngine` (Line 15)
Controls the discrete temporal progression and multi-agent physics loop.

| Method | Signature | Description |
| :--- | :--- | :--- |
| `__init__` | `__init__(self, graph: RailwayGraph, config_manager: ConfigManager)` | Initializes simulation engine with reference graph and configuration. |
| `set_algorithm` | `set_algorithm(self, algo_name: str) -> None` | Dynamically switches the active deconfliction algorithm solver. |
| `update_graph` | `update_graph(self, new_graph: RailwayGraph) -> None` | Updates graph topology reference in both engine and scheduler. |
| `reset` | `reset(self, train_agents: Dict[int, TrainAgent], planned_events: List[ScheduleEvent]) -> None` | Resets the simulation to editor mode and clears run states. |
| `start` | `start(self, train_route_configs: Dict[int, RouteConfig], train_agents: Dict[int, TrainAgent], planned_events: List[ScheduleEvent]) -> bool` | Pre-computes 24-hour schedule and bootstraps runtime train agents. |
| `schedule_agent_loop` | `schedule_agent_loop(self, tid: int, start_time: int, train_agents: Dict[int, TrainAgent], train_route_configs: Dict[int, RouteConfig]) -> None` | Reschedules a completed train agent for continuous loop simulation. |
| `update_tick` | `update_tick(self, train_agents: Dict[int, TrainAgent], train_route_configs: Dict[int, RouteConfig]) -> None` | Executes a single discrete simulation tick across all train agents. |

---

## Module: [`generators/__init__.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/generators/__init__.py)
**Description:** Smart Rail Procedural Generators Package.

---

## Module: [`generators/map_generator.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/generators/map_generator.py)
**Description:** Smart Rail Procedural Railway Topology & Fleet Generator.

Generates connected random railway graphs using Euclidean distance-based
spanning trees with cross-link tracks and valid multi-stop train manifests.

### Standalone Functions

| Function | Signature | Description |
| :--- | :--- | :--- |
| `generate_random_map` | `generate_random_map(num_stations: int, area_width: int, area_height: int, extra_tracks_ratio: float) -> Tuple[RailwayGraph, Dict[int, RouteConfig]]` | Procedurally generates a guaranteed-connected planar railway network. |
| `generate_random_trains` | `generate_random_trains(graph: RailwayGraph, count: int) -> Dict[int, RouteConfig]` | Generates procedural train manifests with varied stops, priority tiers, and colors. |

---

## Module: [`main.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/main.py)
**Description:** Smart Rail: Multi-Train AI Scheduling & Conflict Resolution Simulator.

Top-level application entry point initializing data-driven configuration,
structured logging, modular UI, algorithms, and simulation lifecycle.

### Classes

#### `class App` (Line 34)
Main application controller managing GUI events, simulation stepping, and rendering.

| Method | Signature | Description |
| :--- | :--- | :--- |
| `__init__` | `__init__(self)` | Initializes configuration, logging, display window, and core managers. |
| `to_screen` | `to_screen(self, x: float, y: float) -> Tuple[int, int]` | Converts world coordinates to screen pixel coordinates. |
| `to_world` | `to_world(self, sx: float, sy: float) -> Tuple[float, float]` | Converts screen pixel coordinates to world coordinates. |
| `load_scenario` | `load_scenario(self, name: str) -> None` | Loads a named scenario map from JSON. |
| `cycle_scenario` | `cycle_scenario(self) -> None` | Cycles to the next available scenario map. |
| `cycle_algorithm` | `cycle_algorithm(self) -> None` | Cycles to next deconfliction algorithm. |
| `generate_random_network` | `generate_random_network(self) -> None` | Procedurally generates a connected random railway topology. |
| `save_current_map` | `save_current_map(self) -> None` | Saves active network to a JSON file. |
| `add_custom_train` | `add_custom_train(self) -> None` | Registers or updates a train manifest from UI inputs. |
| `delete_selected_train` | `delete_selected_train(self) -> None` | Removes the selected train cleanly. |
| `toggle_simulation` | `toggle_simulation(self) -> None` | Toggles simulation execution state. |
| `handle_events` | `handle_events(self) -> bool` | Processes Pygame window, UI widgets, and mouse events. |
| `_handle_add_station` | `_handle_add_station(self) -> None` | No docstring provided. |
| `_handle_mouse_down` | `_handle_mouse_down(self, event, panel_w) -> None` | No docstring provided. |
| `_handle_button_press` | `_handle_button_press(self, elem) -> None` | No docstring provided. |
| `draw` | `draw(self) -> None` | Renders all graphics, UI sidebar tabs, HUD overlay, and flips display. |
| `run` | `run(self) -> None` | Main application lifecycle and 60 FPS event loop. |

---

## Module: [`ui/__init__.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/ui/__init__.py)
**Description:** Smart Rail UI Package.

---

## Module: [`ui/event_handler.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/ui/event_handler.py)
**Description:** Smart Rail Mouse & Keyboard Interaction Event Handler.

Encapsulates map-level interactions: station selection, track linking,
right-click deletion of graph nodes and segments, and train manifest picking.

### Classes

#### `class MapInteractionHandler` (Line 14)
Handles canvas clicks, drag panning, zoom adjustments, and station/track editing.

| Method | Signature | Description |
| :--- | :--- | :--- |
| `__init__` | `__init__(self)` | Initializes interaction state variables. |
| `handle_map_click` | `handle_map_click(self, event: pygame.event.Event, graph: RailwayGraph, is_editor_mode: bool, zoom: float, to_world_fn) -> Tuple[Optional[str], bool, str]` | Processes map click for station linking or right-click deletion. |

---

## Module: [`ui/ui_views.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/ui/ui_views.py)
**Description:** Smart Rail UI Views & Visual Rendering Pipeline.

Draws Cartesian background grids, network topology, train animations,
sidebar tab panels, HUD overlays, and 24-hour spatial-temporal Gantt charts.

### Standalone Functions

| Function | Signature | Description |
| :--- | :--- | :--- |
| `draw_map_background` | `draw_map_background(surface: pygame.Surface, width: int, height: int, zoom: float, cam_offset_x: float, cam_offset_y: float, cfg: ConfigManager) -> None` | Draws Cartesian grid aligned with camera pan/zoom offsets. |
| `draw_map` | `draw_map(surface: pygame.Surface, graph: RailwayGraph, train_agents: Dict[int, TrainAgent], selected_node_for_link: Optional[str], zoom: float, to_screen: Callable[[float, float], Tuple[int, int]], font: pygame.font.Font, cfg: ConfigManager) -> None` | Renders tracks, station nodes, labels, active segments, and train sprites. |
| `draw_tab_config` | `draw_tab_config(surface: pygame.Surface, panel_x: int, header_font: pygame.font.Font, font: pygame.font.Font, status_font: pygame.font.Font, sim_speed: float, feedback_message: str, cfg: ConfigManager) -> None` | Renders the CONFIG tab controls, editor guides, and feedback banners. |
| `draw_tab_schedules` | `draw_tab_schedules(surface: pygame.Surface, panel_x: int, header_font: pygame.font.Font, font: pygame.font.Font, status_font: pygame.font.Font, train_route_configs: Dict[int, RouteConfig], train_list_rects: List[Tuple[pygame.Rect, int]], selected_train: Optional[int], cfg: ConfigManager) -> None` | Renders the SCHEDULES tab train manifest list, priority tag, and controls. |
| `draw_tab_stats` | `draw_tab_stats(surface: pygame.Surface, panel_x: int, header_font: pygame.font.Font, font: pygame.font.Font, status_font: pygame.font.Font, total_scheduling_time: float, scheduling_ops: int, total_collisions_avoided: int, train_agents: Dict[int, TrainAgent], screen_height: int, cfg: ConfigManager) -> None` | Renders the STATS live telemetry metrics and individual train journey stats. |
| `render_gantt_surface` | `render_gantt_surface(graph: RailwayGraph, planned_events: List[ScheduleEvent], status_font: pygame.font.Font, cfg: ConfigManager) -> pygame.Surface` | Builds and caches the static 24-hour spatial-temporal Gantt chart surface. |
| `draw_tab_table` | `draw_tab_table(surface: pygame.Surface, panel_x: int, header_font: pygame.font.Font, status_font: pygame.font.Font, gantt_surface: Optional[pygame.Surface], table_scroll_y: int, sim_time: int, screen_height: int, cfg: ConfigManager) -> None` | Renders the TABLE tab displaying the spatial-temporal track usage Gantt chart. |
| `draw_overlay_info` | `draw_overlay_info(surface: pygame.Surface, header_font: pygame.font.Font, sim_time: int, cfg: ConfigManager) -> None` | Renders top-left simulation clock overlay (Day & 24h Time). |

---

## Module: [`ui/ui_widgets.py`](file:///C:/Users/karee/OneDrive/Desktop/random projects/ai project/ui/ui_widgets.py)
**Description:** Smart Rail UI Widget Construction & Hierarchy Module.

Manages Pygame-GUI widget creation, layout positioning, tab visibility,
algorithm selection, scenario switching, and custom map export triggers.

### Classes

#### `class SimulatorUI` (Line 14)
Constructs and manages all Pygame-GUI interactive elements in the sidebar.

| Method | Signature | Description |
| :--- | :--- | :--- |
| `__init__` | `__init__(self, manager: pygame_gui.UIManager, cfg: ConfigManager, width: int, height: int)` | Initializes UI widgets using settings from ConfigManager. |
| `setup_ui` | `setup_ui(self, active_tab: str, algorithm_name: str, sim_speed: float, scenario_name: str) -> None` | Constructs and positions all sidebar widgets and inputs. |
| `update_visibility` | `update_visibility(self, active_tab: str) -> None` | Toggles widget visibility based on active sidebar tab. |
| `update_stops_dropdown` | `update_stops_dropdown(self, stations: List[str], active_tab: str) -> None` | Recreates station dropdown selector with updated station names. |

---
