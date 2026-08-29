# Code Wiki: Smart Rail System Blueprint (code_wiki.md)

---

## 1. Meta Information
* **Project Name:** Smart Rail (Multi-Train AI Scheduling & Conflict Resolution Simulator)
* **Version:** 2.0.0 (Data-Driven Enterprise Architecture)
* **Last Updated:** 2026-08-30
* **Primary Author & Maintainer:** Kareem & Team

---

## 2. Technical Stack
* **Language:** Python 3.9+
* **GUI & Graphics Engine:** `pygame` (v2.5+), `pygame_gui` (v0.6.9+)
* **Graph Modeling:** `networkx` (v3.0+)
* **Configuration & Serialization:** JSON schema with multi-layer fallback validation
* **Logging:** Centralized rotating file handler (`smart_rail.log`) and console streams
* **Architecture Pattern:** Decoupled Model-View-Controller (MVC) + Strategy Pattern for Solvers

---

## 3. Codebase Package Architecture

```
ai project/
├── data/
│   ├── config.json               # Centralized configuration (zero hardcoded values)
│   └── maps/                     # Standardized JSON scenario files
│       ├── egypt.json            # Egypt National Rail network
│       ├── hub.json              # Radial spoke-and-hub benchmark
│       ├── london.json           # London terminal network
│       └── empty.json            # Blank canvas
├── core/
│   ├── config_manager.py         # JSON config loader, schema validator & fallback recovery
│   ├── logger.py                 # Structured rotating logger (smart_rail.log) & error formatters
│   ├── models.py                 # RailwayGraph, TrainAgent, RouteConfig, ScheduleEvent
│   ├── scenario_manager.py       # JSON map loader, dynamic directory scanner & JSON map exporter
│   └── simulation_engine.py      # Discrete tick loop, multi-agent stepping & deconfliction metrics
├── algorithms/
│   ├── base.py                   # Base interface & spatial-temporal reservation table
│   ├── bfs.py                    # Breadth-First Search (minimum station hops)
│   ├── dfs.py                    # Depth-First Search (deep route exploration)
│   ├── dijkstra.py               # Dijkstra shortest path (time-optimal)
│   ├── floyd_warshall.py         # Floyd-Warshall all-pairs shortest path matrix
│   ├── cnf_csp.py                # Constraint Satisfaction Problem (CSP / CNF lookahead)
│   ├── greedy.py                 # Greedy earliest-available reservation with step backoff
│   ├── priority_edf.py           # Priority Earliest Deadline First (Express vs Freight)
│   └── dynamic_reroute.py        # Dynamic k-shortest paths alternative corridor deconfliction
├── generators/
│   └── map_generator.py          # Procedural MST-based random railway graph & fleet generator
├── ui/
│   ├── ui_widgets.py             # Responsive Pygame-GUI widget hierarchy & auto-spacing
│   ├── ui_views.py               # Rendering pipeline (map, grid, HUD, tabs, 24h Gantt chart)
│   └── event_handler.py          # Mouse canvas interactions (station linking, deleting, panning)
├── scripts/
│   └── parse_functions.py        # AST docstring parser regenerating functions.md
├── main.py                       # Top-level application controller (< 350 lines)
├── test_suite.py                 # 6 automated unit & integration test suites
├── requirements.txt              # Package dependencies
├── manual_tests.csv              # QA test matrix
├── project_plan.md               # Architecture goals and scope
├── dev_rules.md                  # Development safety baseline (<400 lines rule)
├── code_wiki.md                  # System blueprint (this document)
├── functions.md                  # Auto-generated API catalog
└── README.md                     # GitHub README
```

---

## 4. Algorithmic Strategies

| Algorithm | Type | Implementation File | Key Metric / Optimization |
| :--- | :--- | :--- | :--- |
| **BFS** | Pathfinding | [`algorithms/bfs.py`](file:///c:/Users/karee/OneDrive/Desktop/random%20projects/ai%20project/algorithms/bfs.py) | Unweighted shortest path (fewest station hops). |
| **DFS** | Pathfinding | [`algorithms/dfs.py`](file:///c:/Users/karee/OneDrive/Desktop/random%20projects/ai%20project/algorithms/dfs.py) | Deep path exploration / loop avoidance. |
| **Dijkstra** | Pathfinding | [`algorithms/dijkstra.py`](file:///c:/Users/karee/OneDrive/Desktop/random%20projects/ai%20project/algorithms/dijkstra.py) | Time-weighted travel duration minimization. |
| **Floyd-Warshall** | Pathfinding | [`algorithms/floyd_warshall.py`](file:///c:/Users/karee/OneDrive/Desktop/random%20projects/ai%20project/algorithms/floyd_warshall.py) | $O(1)$ all-pairs shortest paths query matrix. |
| **Greedy** | Deconfliction | [`algorithms/greedy.py`](file:///c:/Users/karee/OneDrive/Desktop/random%20projects/ai%20project/algorithms/greedy.py) | Incremental slot allocation with fixed-step backoff. |
| **CSP / CNF** | Deconfliction | [`algorithms/cnf_csp.py`](file:///c:/Users/karee/OneDrive/Desktop/random%20projects/ai%20project/algorithms/cnf_csp.py) | Multi-interval disjunctive headway constraint clauses. |
| **Priority EDF** | Deconfliction | [`algorithms/priority_edf.py`](file:///c:/Users/karee/OneDrive/Desktop/random%20projects/ai%20project/algorithms/priority_edf.py) | Express tier preemption & priority dispatching. |
| **Dynamic Reroute** | Deconfliction | [`algorithms/dynamic_reroute.py`](file:///c:/Users/karee/OneDrive/Desktop/random%20projects/ai%20project/algorithms/dynamic_reroute.py) | K-shortest path load balancing around congested tracks. |

---

## 5. Data-Driven Architecture & Persistence
1. **`data/config.json`:** Controls all UI layout coordinates, simulation speed multipliers, colors, logging levels, and typography without hardcoded magic constants.
2. **`data/maps/*.json`:** Any `.json` file added to `data/maps/` is dynamically detected and selectable in the simulator UI.
3. **Custom Map Export:** Clicking `SAVE MAP JSON` in the editor saves the current canvas topology and train fleet directly to `data/maps/<name>.json`.

---

## 6. Error Handling & Logging Strategy
* **Logging:** Configured via [`core/logger.py`](file:///c:/Users/karee/OneDrive/Desktop/random%20projects/ai%20project/core/logger.py) with rotating file handler `smart_rail.log`.
* **Graceful Degradation:** Automatic default fallback on JSON parse failure, non-crashing handling of unselected train removal, safe integer coordinate validation, and informative GUI banner feedback.
