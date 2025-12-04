# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================

INITIAL_SCREEN_WIDTH = 1280
INITIAL_SCREEN_HEIGHT = 720

# Color Palette for UI and Elements
COLORS = {
    "bg": (30, 30, 35),            # Dark background for the map
    "grid": (45, 45, 50),          # Cartesian Grid Lines
    "node": (100, 200, 255),       # Stations
    "node_selected": (255, 215, 0),# Highlighted station
    "node_hover": (150, 230, 255), # Hovered station
    "edge": (60, 60, 60),          # Tracks
    "edge_active": (100, 100, 100),# Tracks with active trains
    "text": (230, 230, 230),       # Standard text
    "panel": (45, 45, 50),         # Right-hand side UI panel
    "input_bg": (25, 25, 30),      # Input fields
    "btn_active": (70, 160, 100),  # Green buttons
    "btn_inactive": (180, 60, 60), # Red/Pause buttons
    "btn_neutral": (80, 80, 100),  # Standard buttons
    "tab_active": (100, 100, 120), # Active tab header
    "tab_inactive": (50, 50, 60),  # Inactive tab header
    "timeline_bar": (100, 200, 150),# Gantt chart bars
    "status_waiting": (255, 200, 80),# Status text for waiting trains
    "status_moving": (80, 255, 80),  # Status text for moving trains
    "status_delayed": (255, 80, 80)  # Status text for delayed trains
}

FONT_SIZE = 16
HEADER_FONT_SIZE = 22