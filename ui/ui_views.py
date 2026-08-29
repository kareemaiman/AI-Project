"""
Smart Rail UI Views & Presentation Pipeline.

Renders graph networks, moving trains, HUD overlays, tab panels, and
cached 24-hour spatial-temporal Gantt charts without magic constants.
"""

from typing import Callable, Dict, List, Optional, Tuple
import pygame
from core.config_manager import ConfigManager
from core.models import RailwayGraph, RouteConfig, ScheduleEvent, TrainAgent


def draw_map_background(
    surface: pygame.Surface,
    width: int,
    height: int,
    zoom: float,
    cam_x: float,
    cam_y: float,
    cfg: ConfigManager
) -> None:
    """Renders the dark Cartesian background grid."""
    grid_size = int(cfg.get("simulation", "grid_size_pixels", 40) * zoom)
    grid_color = cfg.get_color("grid_line")
    ox, oy = int(cam_x % grid_size), int(cam_y % grid_size)

    for x in range(ox, width, grid_size):
        pygame.draw.line(surface, grid_color, (x, 0), (x, height), 1)
    for y in range(oy, height, grid_size):
        pygame.draw.line(surface, grid_color, (0, y), (width, y), 1)


def draw_map(
    surface: pygame.Surface,
    graph: RailwayGraph,
    train_agents: Dict[int, TrainAgent],
    selected_node_for_link: Optional[str],
    zoom: float,
    to_screen_fn: Callable[[float, float], Tuple[int, int]],
    font: pygame.font.Font,
    cfg: ConfigManager
) -> None:
    """Renders track edges, station nodes, and dynamic moving trains."""
    track_color = cfg.get_color("track_default")
    node_color = cfg.get_color("node_default")
    text_color = cfg.get_color("text")
    active_edge_color = cfg.get_color("track_active")

    # 1. Track Edges
    for u, v in graph.get_all_edges():
        p1 = to_screen_fn(*graph.get_pos(u))
        p2 = to_screen_fn(*graph.get_pos(v))
        pygame.draw.line(surface, track_color, p1, p2, max(2, int(4 * zoom)))

    # 2. Moving Trains
    for _, agent in train_agents.items():
        if agent.current_event and agent.status == "MOVING":
            p1 = to_screen_fn(*graph.get_pos(agent.current_event.source))
            p2 = to_screen_fn(*graph.get_pos(agent.current_event.target))
            pygame.draw.line(surface, active_edge_color, p1, p2, max(2, int(5 * zoom)))

        tx, ty = to_screen_fn(*agent.visual_pos)
        rad = max(4, int(9 * zoom))
        pygame.draw.circle(surface, agent.color, (tx, ty), rad)
        pygame.draw.circle(surface, (255, 255, 255), (tx, ty), rad, max(1, int(2 * zoom)))

        lbl = font.render(f"#{agent.id}", True, text_color)
        surface.blit(lbl, (tx - lbl.get_width() // 2, ty - rad - 16))

    # 3. Station Nodes
    for name, (nx_x, nx_y) in graph.cached_pos.items():
        sx, sy = to_screen_fn(nx_x, nx_y)
        rad = max(5, int(10 * zoom))
        col = (255, 215, 0) if name == selected_node_for_link else node_color

        pygame.draw.circle(surface, col, (sx, sy), rad)
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), rad, max(1, int(2 * zoom)))

        lbl = font.render(name, True, text_color)
        surface.blit(lbl, (sx - lbl.get_width() // 2, sy + rad + 4))


def draw_tab_config(
    surface: pygame.Surface,
    panel_x: int,
    header_font: pygame.font.Font,
    font: pygame.font.Font,
    status_font: pygame.font.Font,
    sim_speed: float,
    feedback_message: str,
    cfg: ConfigManager
) -> None:
    """Renders the CONFIG tab controls, editor guides, and feedback banners."""
    text_col = cfg.get_color("text")
    muted_col = cfg.get_color("text_muted")
    warn_col = cfg.get_color("status_waiting")

    # Header & Station Editor
    surface.blit(header_font.render("Station & Track Editor", True, text_col), (panel_x + 15, 48))
    surface.blit(font.render("Station Name:", True, text_col), (panel_x + 15, 70))
    surface.blit(font.render("X Coordinate:", True, text_col), (panel_x + 15, 124))
    surface.blit(font.render("Y Coordinate:", True, text_col), (panel_x + 185, 124))

    # Editor Guides
    surface.blit(status_font.render("• Press ENTER in fields to Add Station", True, muted_col), (panel_x + 15, 180))
    surface.blit(status_font.render("• Left-Click 2 stations to Link Track", True, muted_col), (panel_x + 15, 196))
    surface.blit(status_font.render("• Right-Click node or track to Delete", True, muted_col), (panel_x + 15, 212))

    # Simulation Engine Controls
    surface.blit(header_font.render("Simulation Engine", True, text_col), (panel_x + 15, 236))
    surface.blit(font.render("Deconfliction Algorithm:", True, text_col), (panel_x + 15, 258))
    surface.blit(font.render(f"Simulation Speed: {sim_speed:.1f}x", True, text_col), (panel_x + 15, 316))

    if feedback_message:
        surface.blit(status_font.render(feedback_message, True, warn_col), (panel_x + 15, 530))


def draw_tab_schedules(
    surface: pygame.Surface,
    panel_x: int,
    header_font: pygame.font.Font,
    font: pygame.font.Font,
    status_font: pygame.font.Font,
    train_route_configs: Dict[int, RouteConfig],
    train_list_rects: List[Tuple[pygame.Rect, int]],
    selected_train: Optional[int],
    cfg: ConfigManager
) -> None:
    """Renders the SCHEDULES tab train manifest list, priority tag, and controls."""
    text_col = cfg.get_color("text")
    muted_col = cfg.get_color("text_muted")

    surface.blit(header_font.render("Train Fleet Manifest", True, text_col), (panel_x + 15, 48))
    surface.blit(font.render("ID:", True, text_col), (panel_x + 15, 70))
    surface.blit(font.render("Color (R G B):", True, text_col), (panel_x + 72, 70))
    surface.blit(font.render("Start Delay:", True, text_col), (panel_x + 198, 70))
    surface.blit(font.render("Pri (1-3):", True, text_col), (panel_x + 272, 70))

    surface.blit(status_font.render("Add Stop from Network:", True, muted_col), (panel_x + 15, 148))
    surface.blit(status_font.render("Route Stops Sequence:", True, muted_col), (panel_x + 15, 202))

    surface.blit(header_font.render("Active Fleet Manifests:", True, text_col), (panel_x + 15, 336))

    train_list_rects.clear()
    list_y = 360
    for tid, tcfg in sorted(train_route_configs.items()):
        is_sel = (selected_train == tid)
        rect = pygame.Rect(panel_x + 15, list_y, 320, 26)
        train_list_rects.append((rect, tid))

        bg_col = (50, 70, 100) if is_sel else (30, 35, 48)
        pygame.draw.rect(surface, bg_col, rect, border_radius=4)
        pygame.draw.rect(surface, (80, 90, 110) if is_sel else (50, 55, 70), rect, 1, border_radius=4)

        pygame.draw.circle(surface, tcfg.color, (panel_x + 30, list_y + 13), 6)
        pri_label = "Exp" if tcfg.priority == 1 else ("Std" if tcfg.priority == 2 else "Frg")
        txt = f"#{tid} [{pri_label}] {' -> '.join(tcfg.stops)}"
        surface.blit(status_font.render(txt, True, text_col), (panel_x + 45, list_y + 6))
        list_y += 30


def draw_tab_stats(
    surface: pygame.Surface,
    panel_x: int,
    header_font: pygame.font.Font,
    font: pygame.font.Font,
    status_font: pygame.font.Font,
    total_time: float,
    ops: int,
    conflicts: int,
    train_agents: Dict[int, TrainAgent],
    height: int,
    cfg: ConfigManager
) -> None:
    """Renders the STATS tab computation telemetry, collision avoidance metrics, and train states."""
    text_col = cfg.get_color("text")
    muted_col = cfg.get_color("text_muted")

    surface.blit(header_font.render("Live Fleet Telemetry", True, text_col), (panel_x + 15, 48))
    surface.blit(font.render(f"Computation Time: {total_time:.2f} ms", True, text_col), (panel_x + 15, 78))
    surface.blit(font.render(f"Scheduling Operations: {ops}", True, text_col), (panel_x + 15, 100))
    surface.blit(font.render(f"Conflicts Avoided: {conflicts}", True, text_col), (panel_x + 15, 122))

    surface.blit(header_font.render("Real-Time Train Agents:", True, text_col), (panel_x + 15, 154))

    card_y = 182
    for tid, agent in sorted(train_agents.items()):
        rect = pygame.Rect(panel_x + 15, card_y, 320, 36)
        pygame.draw.rect(surface, (28, 32, 45), rect, border_radius=4)
        pygame.draw.circle(surface, agent.color, (panel_x + 30, card_y + 18), 7)

        status_col = (80, 220, 100) if agent.status == "MOVING" else (240, 180, 60)
        surface.blit(font.render(f"Train #{tid}", True, text_col), (panel_x + 46, card_y + 8))
        surface.blit(status_font.render(f"Status: {agent.status}", True, status_col), (panel_x + 140, card_y + 10))
        surface.blit(status_font.render(f"Trips: {agent.trips_completed}", True, muted_col), (panel_x + 245, card_y + 10))
        card_y += 42


def render_gantt_surface(
    graph: RailwayGraph,
    events: List[ScheduleEvent],
    status_font: pygame.font.Font,
    cfg: ConfigManager
) -> pygame.Surface:
    """Pre-renders the 24-hour spatial-temporal Gantt chart."""
    edges = sorted(graph.get_all_edges())
    row_h = 32
    w, h = 320, max(120, len(edges) * row_h + 30)
    surf = pygame.Surface((w, h))
    surf.fill(cfg.get_color("panel"))

    text_col = cfg.get_color("text")
    border_col = cfg.get_color("panel_border")

    for i, (u, v) in enumerate(edges):
        y = i * row_h
        pygame.draw.line(surf, border_col, (0, y), (w, y), 1)
        surf.blit(status_font.render(f"{u}-{v}", True, text_col), (4, y + 8))

        for evt in events:
            if (evt.source == u and evt.target == v) or (evt.source == v and evt.target == u):
                x1 = int(70 + (evt.start_time % 1440) / 1440.0 * 240)
                x2 = int(70 + (evt.end_time % 1440) / 1440.0 * 240)
                if x2 > x1:
                    pygame.draw.rect(surf, evt.color, (x1, y + 4, max(2, x2 - x1), row_h - 8), border_radius=2)

    return surf


def draw_tab_table(
    surface: pygame.Surface,
    panel_x: int,
    header_font: pygame.font.Font,
    status_font: pygame.font.Font,
    table_surface: Optional[pygame.Surface],
    scroll_y: int,
    sim_time: int,
    height: int,
    cfg: ConfigManager
) -> None:
    """Renders the scrollable Gantt viewport and live time indicator cursor."""
    text_col = cfg.get_color("text")
    surface.blit(header_font.render("24h Spatial-Temporal Gantt", True, text_col), (panel_x + 15, 48))
    surface.blit(status_font.render("Track Block Occupancy [00:00 - 24:00]", True, cfg.get_color("text_muted")), (panel_x + 15, 72))

    if table_surface:
        view_rect = pygame.Rect(panel_x + 15, 96, 320, height - 120)
        surface.blit(table_surface, (panel_x + 15, 96 + scroll_y), area=pygame.Rect(0, -scroll_y, 320, height - 120))
        pygame.draw.rect(surface, cfg.get_color("panel_border"), view_rect, 1)

        # Timeline cursor
        cur_x = panel_x + 15 + int(70 + (sim_time % 1440) / 1440.0 * 240)
        pygame.draw.line(surface, (255, 80, 80), (cur_x, 96), (cur_x, height - 24), 2)


def draw_overlay_info(
    surface: pygame.Surface,
    header_font: pygame.font.Font,
    sim_time: int,
    cfg: ConfigManager
) -> None:
    """Renders the top HUD simulation clock."""
    text_col = cfg.get_color("text")
    hrs = (sim_time // 60) % 24
    mins = sim_time % 60
    clock_str = f"SIMULATION TIME: {hrs:02d}:{mins:02d} (Tick {sim_time})"
    surface.blit(header_font.render(clock_str, True, text_col), (20, 20))
