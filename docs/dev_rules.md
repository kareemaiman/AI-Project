# Development Rules & Architectural Standards (dev_rules.md)

This document establishes the safety baseline, coding standards, and architectural constraints for **Smart Rail**.

---

## 1. File Size & Modularity Constraints
* **Line Limit:** Every source code file MUST be strictly **under 400 lines of code**.
* **Package Structure:**
  - **`core/`:** Configuration loading (`config_manager.py`), logging (`logger.py`), models (`models.py`), scenario persistence (`scenario_manager.py`), and discrete tick physics (`simulation_engine.py`).
  - **`algorithms/`:** Standalone pathfinding and deconfliction solvers (each algorithm in its own dedicated file: `bfs.py`, `dfs.py`, `dijkstra.py`, `floyd_warshall.py`, `cnf_csp.py`, `greedy.py`, `priority_edf.py`, `dynamic_reroute.py`).
  - **`generators/`:** Procedural topology and train manifest generators (`map_generator.py`).
  - **`ui/`:** View presentation (`ui_views.py`), GUI widget hierarchy (`ui_widgets.py`), and event handlers (`event_handler.py`).

---

## 2. Configuration & Parameter Centralization
* Never hardcode magic numbers, dimensions, colors, font sizes, or simulation constants inside application code.
* All configuration must reside in `data/config.json` and be accessed programmatically via `ConfigManager`.

---

## 3. Error Handling, Logging & User Feedback
* **Structured Logging:** All major lifecycle events, file I/O operations, and errors must be logged via `core.logger.get_logger()`.
* **Graceful Degradation:** Malformed JSON files or corrupted configs must trigger automatic fallback to default configurations without crashing.
* **Safe State Access:** Always validate inputs, bounds, and dictionary keys before mutation.

---

## 4. Documentation & Automated Mapping
* **Inline Documentation:** Every class, method, and function must include clean docstrings with type annotations.
* **Automated Sync:** Whenever files or functions are added or modified, run `python scripts/parse_functions.py` to regenerate `functions.md`.
