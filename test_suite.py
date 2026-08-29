"""
Comprehensive Unit, Integration, Stress, and Regression Test Suite for Smart Rail.
"""

from algorithms import (
    ALGORITHM_REGISTRY,
    PATHFINDING_REGISTRY,
    CSPScheduler,
    DynamicRerouteScheduler,
    GreedyScheduler,
    PriorityEDFScheduler,
    bfs_path,
    dfs_path,
    dijkstra_path,
    floyd_warshall_all_pairs,
)
from algorithms.floyd_warshall import reconstruct_floyd_path
from core.config_manager import ConfigManager
from core.models import RailwayGraph, RouteConfig
from core.scenario_manager import ScenarioManager
from core.simulation_engine import SimulationEngine
from generators.map_generator import generate_random_map, generate_random_trains
from ui.ui_widgets import SimulatorUI
import pygame
import pygame_gui


def test_config_manager():
    cfg = ConfigManager("data/config.json")
    assert cfg.get("window", "width") == 1280
    assert len(cfg.get_color("bg")) == 3
    assert len(cfg.get_preset_train_colors()) > 0
    print("[PASS] test_config_manager")


def test_scenario_manager_and_json_save():
    sm = ScenarioManager("data/maps")
    scenarios = sm.scan_scenarios()
    assert "EGYPT" in scenarios
    assert "HUB" in scenarios
    assert "LONDON" in scenarios
    assert "EMPTY" in scenarios

    g, trains, _ = sm.load_scenario("EGYPT")
    assert len(g.cached_pos) == 15
    assert len(trains) == 5

    # Test saving custom scenario
    g_custom = RailwayGraph()
    g_custom.add_station("TestAlpha", 100, 200)
    g_custom.add_station("TestBeta", 300, 400)
    g_custom.add_track("TestAlpha", "TestBeta")
    t_custom = {99: RouteConfig(99, ["TestAlpha", "TestBeta"], (255, 0, 0), 0, 1)}

    ok, msg = sm.save_scenario("autotest_map", g_custom, t_custom)
    assert ok is True
    assert "AUTOTEST_MAP" in sm.scan_scenarios()

    g_loaded, t_loaded, _ = sm.load_scenario("AUTOTEST_MAP")
    assert len(g_loaded.cached_pos) == 2
    assert len(t_loaded) == 1
    print("[PASS] test_scenario_manager_and_json_save")


def test_pathfinding_algorithms():
    g = RailwayGraph()
    g.add_station("A", 0, 0)
    g.add_station("B", 100, 0)
    g.add_station("C", 200, 0)
    g.add_station("D", 300, 0)
    g.add_track("A", "B")
    g.add_track("B", "C")
    g.add_track("C", "D")
    g.add_track("A", "D")  # Long direct bypass

    p_bfs = bfs_path(g, "A", "D")
    assert p_bfs == ["A", "D"]

    p_dfs = dfs_path(g, "A", "D")
    assert len(p_dfs) >= 2
    assert p_dfs[0] == "A" and p_dfs[-1] == "D"

    p_dijkstra = dijkstra_path(g, "A", "C")
    assert p_dijkstra == ["A", "B", "C"]

    dist_mat, next_mat = floyd_warshall_all_pairs(g)
    assert dist_mat[("A", "B")] == 20.0
    p_floyd = reconstruct_floyd_path(next_mat, "A", "C")
    assert p_floyd == ["A", "B", "C"]
    print("[PASS] test_pathfinding_algorithms (BFS, DFS, Dijkstra, Floyd-Warshall)")


def test_deconfliction_schedulers():
    g = RailwayGraph()
    g.add_station("Node1", 0, 0)
    g.add_station("Node2", 100, 0)
    g.add_track("Node1", "Node2")

    schedulers = [
        ("GREEDY", GreedyScheduler(g, safety_margin=10.0)),
        ("CSP", CSPScheduler(g, safety_margin=10.0)),
        ("PRIORITY_EDF", PriorityEDFScheduler(g, safety_margin=10.0)),
        ("DYNAMIC_REROUTE", DynamicRerouteScheduler(g, safety_margin=10.0)),
    ]

    for name, s in schedulers:
        s.reset()
        e1, c1, _ = s.schedule_route(1, ["Node1", "Node2"], (255, 0, 0), 0, priority=1)
        assert len(e1) == 1
        t1_end = e1[0].end_time

        e2, c2, _ = s.schedule_route(2, ["Node2", "Node1"], (0, 255, 0), 0, priority=2)
        assert len(e2) == 1
        t2_start = e2[0].start_time

        assert t2_start >= t1_end, f"[{name}] Head-on collision prevented: T1 ends at {t1_end}, T2 starts at {t2_start}"
        assert c2 > 0, f"[{name}] Conflicts were avoided"

    print("[PASS] test_deconfliction_schedulers (GREEDY, CSP, PRIORITY_EDF, DYNAMIC_REROUTE)")


def test_random_map_generator():
    g_rand, trains_rand = generate_random_map(num_stations=8)
    assert len(g_rand.cached_pos) == 8
    assert len(g_rand.get_all_edges()) >= 7
    assert len(trains_rand) >= 4
    for t in trains_rand.values():
        assert len(t.stops) >= 2
        assert t.priority in (1, 2, 3)
    print("[PASS] test_random_map_generator")


def test_simulation_engine_lifecycle():
    cfg = ConfigManager("data/config.json")
    sm = ScenarioManager("data/maps")
    g, trains, _ = sm.load_scenario("HUB")

    engine = SimulationEngine(g, cfg)
    agents = {}
    planned = []

    assert engine.start(trains, agents, planned) is True
    assert len(agents) == len(trains)
    assert len(planned) > 0

    for _ in range(100):
        engine.update_tick(agents, trains)

    assert engine.sim_time == 100
    engine.reset(agents, planned)
    assert engine.mode == "EDITOR"
    assert len(agents) == 0
    print("[PASS] test_simulation_engine_lifecycle")


def test_responsive_ui_metrics():
    cfg = ConfigManager("data/config.json")
    pygame.init()
    resolutions = [(800, 600), (1024, 768), (1280, 720), (1600, 900), (1920, 1080), (2560, 1440)]

    for w, h in resolutions:
        pygame.display.set_mode((w, h))
        mgr = pygame_gui.UIManager((w, h))
        ui = SimulatorUI(mgr, cfg, w, h)
        panel_x, panel_w, content_w, tab_w = ui.get_layout_metrics()

        assert panel_w >= 320 and panel_w <= 420
        assert panel_x == w - panel_w
        assert content_w == panel_w - 30
        assert tab_w > 0
    pygame.quit()
    print("[PASS] test_responsive_ui_metrics (6 arbitrary screen aspect ratios)")


def test_multi_algorithm_stress_matrix():
    cfg = ConfigManager("data/config.json")
    sm = ScenarioManager("data/maps")
    scenarios = ["EGYPT", "HUB", "LONDON"]
    algorithms = ["CSP", "GREEDY", "PRIORITY_EDF", "DYNAMIC_REROUTE"]

    for sc in scenarios:
        g, trains, _ = sm.load_scenario(sc)
        for algo in algorithms:
            engine = SimulationEngine(g, cfg)
            engine.set_algorithm(algo)
            agents = {}
            planned = []

            ok = engine.start(trains, agents, planned)
            assert ok is True, f"Failed starting {sc} with {algo}"

            # Step 100 ticks stress test
            for _ in range(100):
                engine.update_tick(agents, trains)

            assert engine.sim_time == 100
            engine.reset(agents, planned)
            assert engine.mode == "EDITOR"

    print("[PASS] test_multi_algorithm_stress_matrix (12 scenario-algorithm matrix combinations)")


if __name__ == "__main__":
    test_config_manager()
    test_scenario_manager_and_json_save()
    test_pathfinding_algorithms()
    test_deconfliction_schedulers()
    test_random_map_generator()
    test_simulation_engine_lifecycle()
    test_responsive_ui_metrics()
    test_multi_algorithm_stress_matrix()
    print("=======================================================")
    print("ALL 8 COMPREHENSIVE TEST SUITES PASSED (100%)")
    print("=======================================================")
