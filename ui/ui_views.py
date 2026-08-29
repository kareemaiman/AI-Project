"""
Smart Rail UI Views & Visual Rendering Pipeline.

Draws Cartesian background grids, network topology, train animations,
sidebar tab panels, HUD overlays, and 24-hour spatial-temporal Gantt charts.
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
    cam_offset_x: float,
    cam_offset_y: float,
    cfg: ConfigManager
) -> None:
    """Draws Cartesian grid aligned with camera pan/zoom offsets."""
    panel_w = cfg.get("window", "panel_width", 350)
    grid_col = cfg.get_color("grid")
    spacing = max(20, int(100 * zoom))
    start_x = int(cam_offset_x % spacing)
    start_y = int(cam_offset_y % spacing)

    for x in range(start_x, width - panel_w, spacing):
        pygame.draw.line(surface, grid_col, (x, 0), (x, height), 1)
    for y in range(start_y, height, spacing):
        pygame.draw.line(surface, grid_col, (0, y), (width - panel_w, y), 1)


def draw_map(
    surface: pygame.Surface,
    graph: RailwayGraph,
    train_agents: Dict[int, TrainAgent],
    selected_node_for_link: Optional[str],
    zoom: float,
    to_screen: Callable[[float, float], Tuple[int, int]],
    font: pygame.font.Font,
    cfg: ConfigManager
) -> None:
    """Renders tracks, station nodes, labels, active segments, and train sprites."""
    panel_w = cfg.get("window", "panel_width", 350)
    screen_w, screen_h = surface.get_size()

    # 1. Static tracks
    edge_col = cfg.get_color("edge")
    for u, v in graph.get_all_edges():
        p1 = to_screen(*graph.get_pos(u))
        p2 = to_screen(*graph.get_pos(v))
        pygame.draw.line(surface, edge_col, p1, p2, max(2, int(2 * zoom)))

    # 2. Highlight active occupied tracks
    active_edge_col = cfg.get_color("edge_active")
    for agent in train_agents.values():
        if agent.current_event:
            evt = agent.current_event
            p1 = to_screen(*graph.get_pos(evt.source))
            p2 = to_screen(*graph.get_pos(evt.target))
            pygame.draw.line(surface, active_edge_col, p1, p2, max(3, int(4 * zoom)))

    # 3. Stations
    node_col = cfg.get_color("node")
    sel_node_col = cfg.get_color("node_selected")
    text_col = cfg.get_color("text")
    for node, (x, y) in graph.cached_pos.items():
        col = sel_node_col if node == selected_node_for_link else node_col
        sx, sy = to_screen(x, y)
        if -50 < sx < screen_w - panel_w + 50 and -50 < sy < screen_h + 50:
            r = max(4, int(8 * zoom))
            pygame.draw.circle(surface, col, (sx, sy), r)
            pygame.draw.circle(surface, (20, 20, 25), (sx, sy), r, 2)
            if zoom > 0.55:
                lbl = font.render(node, True, text_col)
                surface.blit(lbl, (sx + 10, sy - 10))

    # 4. Train agents
    delayed_col = cfg.get_color("status_delayed")
    for agent in train_agents.values():
        sx, sy = to_screen(*agent.visual_pos)
        agent_r = max(5, int(9 * zoom))
        if agent.status == "DELAYED":
            pygame.draw.circle(surface, delayed_col, (sx, sy), agent_r + 4, 2)
        elif agent.status == "MOVING":
            pygame.draw.circle(surface, (255, 255, 255), (sx, sy), agent_r + 2, 1)

        pygame.draw.circle(surface, agent.color, (sx, sy), agent_r)
        pygame.draw.circle(surface, (10, 10, 15), (sx, sy), agent_r, 1)


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

    y = 48
    surface.blit(header_font.render("Station & Track Editor", True, text_col), (panel_x + 15, y))
    y += 24
    surface.blit(font.render("Station Name:", True, text_col), (panel_x + 15, y))
    y += 58
    surface.blit(font.render("X Coordinate:", True, text_col), (panel_x + 15, y))
    surface.blit(font.render("Y Coordinate:", True, text_col), (panel_x + 125, y))
    y += 62
    surface.blit(status_font.render("• Press ENTER in fields to Add Station", True, muted_col), (panel_x + 15, y))
    y += 16
    surface.blit(status_font.render("• Left-Click 2 stations to Link Track", True, muted_col), (panel_x + 15, y))
    y += 16
    surface.blit(status_font.render("• Right-Click node or track to Delete", True, muted_col), (panel_x + 15, y))
    y += 25

    surface.blit(header_font.render("Simulation Engine", True, text_col), (panel_x + 15, y))
    y += 24
    surface.blit(font.render("Algorithm Selection:", True, text_col), (panel_x + 15, y))
    y += 55
    surface.blit(font.render(f"Simulation Speed: {sim_speed:.1f}x", True, text_col), (panel_x + 15, y))

    if feedback_message:
        y += 215
        surface.blit(status_font.render(feedback_message, True, warn_col), (panel_x + 15, y))


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

    y = 48
    surface.blit(header_font.render("Train Fleet Manifest", True, text_col), (panel_x + 15, y))
    y += 22
    surface.blit(font.render("ID:", True, text_col), (panel_x + 15, y + 4))
    surface.blit(font.render("Color:", True, text_col), (panel_x + 75, y + 4))
    surface.blit(font.render("Delay:", True, text_col), (panel_x + 185, y + 4))
    surface.blit(font.render("Pri (1-3):", True, text_col), (panel_x + 250, y + 4))
    y += 85
    surface.blit(font.render("Route Stops (Space-Separated):", True, text_col), (panel_x + 15, y))
    y += 24
    surface.blit(status_font.render("Or pick station from dropdown to append:", True, muted_col), (panel_x + 15, y))
    y += 215

    surface.blit(header_font.render("Active Manifests (Click to Edit)", True, text_col), (panel_x + 15, y))
    y += 25

    train_list_rects.clear()
    for tid, tcfg in list(train_route_configs.items())[:11]:
        stops_str = "->".join([s[:3] for s in tcfg.stops])
        pri_tag = "EXP" if tcfg.priority == 1 else ("STD" if tcfg.priority == 2 else "FRT")
        txt = f"#{tid} [{pri_tag}] {stops_str}"
        if len(txt) > 34:
            txt = txt[:31] + "..."

        row_rect = pygame.Rect(panel_x + 15, y, 320, 22)
        train_list_rects.append((row_rect, tid))

        mx, my = pygame.mouse.get_pos()
        if row_rect.collidepoint(mx, my) or tid == selected_train:
            pygame.draw.rect(surface, (60, 60, 75), row_rect, border_radius=3)

        pygame.draw.rect(surface, tcfg.color, (panel_x + 18, y + 5, 12, 12), border_radius=2)
        surface.blit(status_font.render(txt, True, text_col), (panel_x + 36, y + 3))
        y += 25


def draw_tab_stats(
    surface: pygame.Surface,
    panel_x: int,
    header_font: pygame.font.Font,
    font: pygame.font.Font,
    status_font: pygame.font.Font,
    total_scheduling_time: float,
    scheduling_ops: int,
    total_collisions_avoided: int,
    train_agents: Dict[int, TrainAgent],
    screen_height: int,
    cfg: ConfigManager
) -> None:
    """Renders the STATS live telemetry metrics and individual train journey stats."""
    text_col = cfg.get_color("text")
    muted_col = cfg.get_color("text_muted")
    moving_col = cfg.get_color("status_moving")
    waiting_col = cfg.get_color("status_waiting")
    delayed_col = cfg.get_color("status_delayed")

    y = 48
    surface.blit(header_font.render("System Performance", True, text_col), (panel_x + 15, y))
    y += 28

    avg_lat = (total_scheduling_time / scheduling_ops) if scheduling_ops > 0 else 0.0
    surface.blit(font.render(f"Avg Calculation: {avg_lat:.2f} ms", True, (130, 240, 160)), (panel_x + 20, y))
    y += 20
    surface.blit(font.render(f"Conflicts Avoided: {total_collisions_avoided}", True, (255, 110, 110)), (panel_x + 20, y))
    y += 34

    surface.blit(header_font.render("Live Train Telemetry", True, text_col), (panel_x + 15, y))
    y += 26

    if not train_agents:
        surface.blit(status_font.render("Simulation is currently stopped.", True, muted_col), (panel_x + 20, y))
        return

    for agent in list(train_agents.values())[:10]:
        if y > screen_height - 35:
            break
        total_min = agent.total_journey_time + agent.total_wait
        w_min = agent.total_wait
        next_dest = agent.current_event.target if agent.current_event else (agent.schedule_queue[0].target if agent.schedule_queue else "Arrived")

        st_col = delayed_col if agent.status == "DELAYED" else (moving_col if agent.status == "MOVING" else waiting_col)
        line1 = f"Train #{agent.id} [{agent.status}] -> {next_dest}"
        line2 = f"Travel: {total_min//60}h {total_min%60}m | Delay: {w_min//60}h {w_min%60}m"
        surface.blit(status_font.render(line1, True, st_col), (panel_x + 20, y))
        surface.blit(status_font.render(line2, True, muted_col), (panel_x + 20, y + 15))
        y += 36


def render_gantt_surface(
    graph: RailwayGraph,
    planned_events: List[ScheduleEvent],
    status_font: pygame.font.Font,
    cfg: ConfigManager
) -> pygame.Surface:
    """Builds and caches the static 24-hour spatial-temporal Gantt chart surface."""
    edges = sorted(graph.get_all_edges(), key=lambda e: (e[0], e[1]))
    h = max(600, len(edges) * 32 + 60)
    surf = pygame.Surface((340, h))
    surf.fill(cfg.get_color("panel"))

    window_size = cfg.get("simulation", "day_window_minutes", 1440)
    graph_w = 250
    x_offset = 75
    text_col = cfg.get_color("text")
    muted_col = cfg.get_color("text_muted")
    grid_col = cfg.get_color("timeline_grid")

    for hr in range(0, 25, 4):
        tx = x_offset + (hr * 60 / window_size) * graph_w
        pygame.draw.line(surf, grid_col, (tx, 0), (tx, h), 1)
        surf.blit(status_font.render(f"{hr:02d}h", True, muted_col), (tx - 8, 2))

    ty = 25
    for u, v in edges:
        lbl = status_font.render(f"{u[:3]}-{v[:3]}", True, text_col)
        surf.blit(lbl, (5, ty + 1))

        for evt in planned_events:
            if (evt.source == u and evt.target == v) or (evt.source == v and evt.target == u):
                s_wrap = evt.start_time % window_size
                e_wrap = evt.end_time % window_size

                if evt.end_time - evt.start_time >= window_size:
                    pygame.draw.rect(surf, evt.color, (x_offset, ty, graph_w, 16), border_radius=2)
                elif e_wrap < s_wrap:
                    rw1 = ((window_size - s_wrap) / window_size) * graph_w
                    pygame.draw.rect(surf, evt.color, (x_offset + (s_wrap / window_size) * graph_w, ty, max(2, int(rw1)), 16), border_radius=2)
                    rw2 = (e_wrap / window_size) * graph_w
                    pygame.draw.rect(surf, evt.color, (x_offset, ty, max(2, int(rw2)), 16), border_radius=2)
                else:
                    rw = ((e_wrap - s_wrap) / window_size) * graph_w
                    pygame.draw.rect(surf, evt.color, (x_offset + (s_wrap / window_size) * graph_w, ty, max(2, int(rw)), 16), border_radius=2)

        pygame.draw.line(surf, (55, 55, 65), (0, ty + 22), (340, ty + 22), 1)
        ty += 32

    return surf


def draw_tab_table(
    surface: pygame.Surface,
    panel_x: int,
    header_font: pygame.font.Font,
    status_font: pygame.font.Font,
    gantt_surface: Optional[pygame.Surface],
    table_scroll_y: int,
    sim_time: int,
    screen_height: int,
    cfg: ConfigManager
) -> None:
    """Renders the TABLE tab displaying the spatial-temporal track usage Gantt chart."""
    text_col = cfg.get_color("text")
    day_limit = cfg.get("simulation", "day_window_minutes", 1440)

    y = 48
    surface.blit(header_font.render("24h Track Usage (Gantt)", True, text_col), (panel_x + 15, y))
    y += 32

    clip_rect = pygame.Rect(panel_x + 5, y, 340, screen_height - y - 10)
    surface.set_clip(clip_rect)

    if gantt_surface:
        surface.blit(gantt_surface, (panel_x + 5, y + table_scroll_y))
        curr_day_ticks = sim_time % day_limit
        needle_x = (panel_x + 5) + 75 + (curr_day_ticks / day_limit) * 250
        pygame.draw.line(surface, (255, 255, 255), (needle_x, y), (needle_x, screen_height), 2)

    surface.set_clip(None)


def draw_overlay_info(surface: pygame.Surface, header_font: pygame.font.Font, sim_time: int, cfg: ConfigManager) -> None:
    """Renders top-left simulation clock overlay (Day & 24h Time)."""
    day_limit = cfg.get("simulation", "day_window_minutes", 1440)
    day = (sim_time // day_limit) + 1
    mins_rem = sim_time % day_limit
    hrs = mins_rem // 60
    mns = mins_rem % 60

    text = f"Day {day:02d} - {hrs:02d}:{mns:02d}"
    txt_surf = header_font.render(text, True, (255, 255, 255))
    bg_rect = pygame.Rect(20, 20, txt_surf.get_width() + 24, 38)
    pygame.draw.rect(surface, (20, 20, 26), bg_rect, border_radius=6)
    pygame.draw.rect(surface, (50, 50, 65), bg_rect, 1, border_radius=6)
    surface.blit(txt_surf, (32, 27))
