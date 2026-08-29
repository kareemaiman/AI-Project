"""
Smart Rail Discrete Simulation Engine & Multi-Agent Physics Stepper.

Coordinates discrete simulation ticks, dynamic train agent physics updates,
multi-algorithm deconfliction dispatching, and live telemetry tracking.
"""

from typing import Dict, List
from algorithms import ALGORITHM_REGISTRY, BaseScheduler, CSPScheduler
from core.config_manager import ConfigManager
from core.logger import get_logger
from core.models import RailwayGraph, RouteConfig, ScheduleEvent, TrainAgent


class SimulationEngine:
    """Controls the discrete temporal progression and multi-agent physics loop."""

    def __init__(self, graph: RailwayGraph, config_manager: ConfigManager):
        """Initializes simulation engine with reference graph and configuration."""
        self.graph = graph
        self.cfg = config_manager
        self.mode = "EDITOR"  # "EDITOR" or "RUNNING"
        self.algorithm_name = "CSP"

        # Instantiate default solver
        self.scheduler: BaseScheduler = CSPScheduler(
            self.graph,
            safety_margin=self.cfg.get("simulation", "default_safety_margin_ticks", 15.0)
        )

        self.sim_time = 0
        self.sim_speed = float(self.cfg.get("simulation", "default_speed_multiplier", 1.0))
        self.speed_accumulator = 0.0

        # Telemetry metrics
        self.total_collisions_avoided = 0
        self.total_scheduling_time = 0.0
        self.scheduling_ops = 0

    def set_algorithm(self, algo_name: str) -> None:
        """Dynamically switches the active deconfliction algorithm solver."""
        logger = get_logger()
        algo_key = algo_name.upper()
        if algo_key in ALGORITHM_REGISTRY:
            self.algorithm_name = algo_key
            solver_cls = ALGORITHM_REGISTRY[algo_key]
            margin = self.cfg.get("simulation", "default_safety_margin_ticks", 15.0)
            self.scheduler = solver_cls(self.graph, safety_margin=margin)
            logger.info(f"Switched active deconfliction algorithm to: {algo_key}")

    def update_graph(self, new_graph: RailwayGraph) -> None:
        """Updates graph topology reference in both engine and scheduler."""
        self.graph = new_graph
        self.set_algorithm(self.algorithm_name)

    def reset(
        self,
        train_agents: Dict[int, TrainAgent],
        planned_events: List[ScheduleEvent]
    ) -> None:
        """Resets the simulation to editor mode and clears run states."""
        self.mode = "EDITOR"
        self.sim_time = 0
        self.speed_accumulator = 0.0
        train_agents.clear()
        self.scheduler.reset()
        planned_events.clear()
        self.total_collisions_avoided = 0
        self.total_scheduling_time = 0.0
        self.scheduling_ops = 0

    def start(
        self,
        train_route_configs: Dict[int, RouteConfig],
        train_agents: Dict[int, TrainAgent],
        planned_events: List[ScheduleEvent]
    ) -> bool:
        """
        Pre-computes 24-hour schedule and bootstraps runtime train agents.

        Returns:
            bool: True if simulation started successfully, False if no manifests exist.
        """
        if not train_route_configs:
            return False

        self.reset(train_agents, planned_events)
        day_limit = self.cfg.get("simulation", "day_window_minutes", 1440)
        loop_delay = self.cfg.get("simulation", "loop_restart_delay_ticks", 100)

        for tid, cfg in train_route_configs.items():
            if not cfg.stops:
                continue

            start_node = cfg.stops[0]
            agent = TrainAgent(id=tid, color=cfg.color, current_node=start_node)
            agent.visual_pos = self.graph.get_pos(start_node)
            train_agents[tid] = agent

            # Pre-plan 24-hour cycle for Gantt visualization
            curr_plan_time = cfg.start_delay
            while curr_plan_time < day_limit:
                events, conflicts, dt = self.scheduler.schedule_route(
                    tid, cfg.stops, cfg.color, curr_plan_time, cfg.priority
                )
                if not events:
                    break
                planned_events.extend(events)
                agent.schedule_queue.extend(events)
                self.total_collisions_avoided += conflicts
                self.total_scheduling_time += dt
                self.scheduling_ops += 1
                curr_plan_time = events[-1].end_time + loop_delay

        self.mode = "RUNNING"
        return True

    def schedule_agent_loop(
        self,
        tid: int,
        start_time: int,
        train_agents: Dict[int, TrainAgent],
        train_route_configs: Dict[int, RouteConfig]
    ) -> None:
        """Reschedules a completed train agent for continuous loop simulation."""
        agent = train_agents[tid]
        cfg = train_route_configs[tid]
        events, conflicts, dt = self.scheduler.schedule_route(
            tid, cfg.stops, cfg.color, start_time, cfg.priority
        )
        self.total_collisions_avoided += conflicts
        self.total_scheduling_time += dt
        self.scheduling_ops += 1
        agent.schedule_queue.extend(events)

    def update_tick(
        self,
        train_agents: Dict[int, TrainAgent],
        train_route_configs: Dict[int, RouteConfig]
    ) -> None:
        """Executes a single discrete simulation tick across all train agents."""
        self.sim_time += 1
        cleanup_interval = self.cfg.get("simulation", "cleanup_interval_ticks", 500)
        loop_delay = self.cfg.get("simulation", "loop_restart_delay_ticks", 100)

        if self.sim_time % cleanup_interval == 0:
            self.scheduler.cleanup_old_reservations(self.sim_time)

        for tid, agent in train_agents.items():
            if not agent.current_event and agent.schedule_queue:
                next_evt = agent.schedule_queue[0]
                if self.sim_time >= next_evt.start_time:
                    agent.current_event = agent.schedule_queue.popleft()

            if agent.current_event:
                evt = agent.current_event
                agent.total_journey_time += 1

                if self.sim_time <= evt.end_time:
                    agent.status = "MOVING"
                    dur = evt.end_time - evt.start_time
                    if dur > 0:
                        t = (self.sim_time - evt.start_time) / dur
                        x1, y1 = self.graph.get_pos(evt.source)
                        x2, y2 = self.graph.get_pos(evt.target)
                        agent.visual_pos = (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
                else:
                    agent.status = "WAITING"
                    agent.current_node = evt.target
                    agent.visual_pos = self.graph.get_pos(evt.target)
                    agent.current_event = None
                    agent.trips_completed += 1
            else:
                if agent.schedule_queue:
                    next_start = agent.schedule_queue[0].start_time
                    agent.status = "DELAYED" if next_start > self.sim_time + 15 else "WAITING"
                    agent.total_wait += 1
                else:
                    agent.status = "ARRIVED"
                    self.schedule_agent_loop(
                        tid, self.sim_time + loop_delay, train_agents, train_route_configs
                    )
