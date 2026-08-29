"""
Smart Rail Mouse & Keyboard Interaction Event Handler.

Encapsulates map-level interactions: station selection, track linking,
right-click deletion of graph nodes and segments, and train manifest picking.
"""

import math
from typing import Optional, Tuple
import pygame
from core.models import RailwayGraph


class MapInteractionHandler:
    """Handles canvas clicks, drag panning, zoom adjustments, and station/track editing."""

    def __init__(self):
        """Initializes interaction state variables."""
        self.selected_node_for_link: Optional[str] = None
        self.is_dragging_map = False
        self.last_mouse_pos: Tuple[int, int] = (0, 0)

    def handle_map_click(
        self,
        event: pygame.event.Event,
        graph: RailwayGraph,
        is_editor_mode: bool,
        zoom: float,
        to_world_fn
    ) -> Tuple[Optional[str], bool, str]:
        """
        Processes map click for station linking or right-click deletion.

        Returns:
            Tuple: (Selected node for link, Graph modified flag, Feedback message)
        """
        wx, wy = to_world_fn(*event.pos)
        feedback = ""
        modified = False

        # Right-Click: Delete Station or Track
        if event.button == 3 and is_editor_mode:
            clicked_node = None
            for n, (nx_x, nx_y) in graph.cached_pos.items():
                if math.hypot(wx - nx_x, wy - nx_y) < (20 / zoom):
                    clicked_node = n
                    break

            if clicked_node:
                graph.remove_station(clicked_node)
                feedback = f"Deleted Station '{clicked_node}'."
                modified = True
            else:
                for u, v in graph.get_all_edges():
                    x1, y1 = graph.get_pos(u)
                    x2, y2 = graph.get_pos(v)
                    l2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
                    if l2 == 0:
                        continue
                    t = max(0, min(1, ((wx - x1) * (x2 - x1) + (wy - y1) * (y2 - y1)) / l2))
                    px, py = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
                    if math.hypot(wx - px, wy - py) < (10 / zoom):
                        graph.remove_track(u, v)
                        feedback = f"Deleted Track ({u} - {v})."
                        modified = True
                        break

        # Left-Click: Station Linking or Drag Start
        elif event.button == 1:
            clicked = None
            for n, (nx_x, nx_y) in graph.cached_pos.items():
                if math.hypot(wx - nx_x, wy - nx_y) < (20 / zoom):
                    clicked = n
                    break

            if clicked and is_editor_mode:
                if self.selected_node_for_link is None:
                    self.selected_node_for_link = clicked
                    feedback = f"Selected '{clicked}'. Click 2nd station to link."
                elif self.selected_node_for_link != clicked:
                    graph.add_track(self.selected_node_for_link, clicked)
                    feedback = f"Linked Track ({self.selected_node_for_link} - {clicked})."
                    self.selected_node_for_link = None
                    modified = True
                else:
                    self.selected_node_for_link = None
            elif not clicked:
                self.is_dragging_map = True
                self.last_mouse_pos = event.pos

        return self.selected_node_for_link, modified, feedback
