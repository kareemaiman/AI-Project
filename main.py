import networkx as nx
import pygame
import sys
G = nx.Graph()
tracks = [
    ("Highpoint", "Aethelgard", 55),
    ("Highpoint", "Deepwood", 75),
    ("Deepwood", "Ironhaven", 55),
    ("Westgate", "Aethelgard", 50),
    ("Westgate", "Rivermouth", 75),
    ("Rivermouth", "Suncrest", 50),
    ("Aethelgard", "Suncrest", 75),
    ("Aethelgard", "Ironhaven", 75),
    ("Ironhaven", "Suncrest", 75),
    ("Ironhaven", "Eastport", 50)
]
G.add_weighted_edges_from(tracks)

# --- CONFIGURATION ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
background_image = pygame.image.load("C:/Users/karee/PycharmProjects/pythonProject4/Gemini_Generated_Image_ognwt2ognwt2ognw.png")
#  colors
BG_COLOR = (245, 245, 220)  # Beige/Map color
TRACK_COLOR = (50, 50, 50)
STATION_COLOR = (139, 69, 19)
TEXT_COLOR = (0, 0, 0)
TRAIN_COLORS = {
    'T1': (200, 0, 0),  # Red
    'T2': (0, 0, 200),  # Blue
    'T3': (0, 150, 0)  # Green
}

# --- CITY COORDINATES (Topology matches your fictional map) ---
CITY_COORDS = {
    "Highpoint": (500, 100),
    "Deepwood": (800, 150),
    "Westgate": (150, 300),
    "Aethelgard": (500, 300),
    "Ironhaven": (750, 300),
    "Eastport": (950, 300),
    "Rivermouth": (250, 550),
    "Suncrest": (600, 550)
}

# --- CONNECTIVITY (For drawing lines) ---
TRACKS = [
    ("Highpoint", "Aethelgard"), ("Highpoint", "Deepwood"),
    ("Deepwood", "Ironhaven"), ("Westgate", "Aethelgard"),
    ("Westgate", "Rivermouth"), ("Rivermouth", "Suncrest"),
    ("Aethelgard", "Suncrest"), ("Aethelgard", "Ironhaven"),
    ("Ironhaven", "Suncrest"), ("Ironhaven", "Eastport")
]


class RailwayVisualizer:
    def __init__(self, schedule_data):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AI Train Scheduler - Simulation")
        self.font = pygame.font.SysFont('Arial', 16, bold=True)
        self.clock = pygame.time.Clock()

        # Schedule Data: Format from Step 3/4
        # expected format: {'T1': {'segments': [{'edge': ('A','B'), 'start_time': 0, 'end_time': 50}, ...]}, ...}
        self.schedule = schedule_data

        # Simulation Time (starts at 0 minutes)
        self.sim_time = 0
        self.time_speed = 0.5  # How fast simulation minutes pass per frame

    def draw_map(self):
        global background_image
        global SCREEN_WIDTH
        global SCREEN_HEIGHT
        background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen.blit(background_image, (0, 0))

        # 1. Draw Tracks
        for city_a, city_b in TRACKS:
            start_pos = CITY_COORDS[city_a]
            end_pos = CITY_COORDS[city_b]
            pygame.draw.line(self.screen, TRACK_COLOR, start_pos, end_pos, 5)

        # 2. Draw Stations
        for city, (x, y) in CITY_COORDS.items():
            pygame.draw.circle(self.screen, STATION_COLOR, (x, y), 5)
            # Draw Label
            label = self.font.render(city, True, TEXT_COLOR)
            self.screen.blit(label, (x - 20, y - 35))

    def get_train_position(self, segments, current_time):
        for seg in segments:
            t_start = seg['start_time']
            t_end = seg['end_time']

            if t_start <= current_time <= t_end:
                # Interpolation Math
                u, v = seg['edge']
                start_x, start_y = CITY_COORDS[u]
                end_x, end_y = CITY_COORDS[v]

                # Progress ratio (0.0 to 1.0)
                if t_end - t_start == 0:
                    ratio = 1
                else:
                    ratio = (current_time - t_start) / (t_end - t_start)

                cur_x = start_x + (end_x - start_x) * ratio
                cur_y = start_y + (end_y - start_y) * ratio
                return (cur_x, cur_y)

        return None

    def run(self):
        running = True
        while running:
            # Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Draw Static Elements
            self.draw_map()

            # Update & Draw Trains
            active_trains = False

            for train_id, data in self.schedule.items():
                # Get position based on current simulation time
                pos = self.get_train_position(data['segments'], self.sim_time)

                if pos:
                    active_trains = True
                    (tx, ty) = pos
                    color = TRAIN_COLORS.get(train_id, (0, 0, 0))

                    # Draw Train Body
                    pygame.draw.circle(self.screen, color, (int(tx), int(ty)), 12)
                    # Draw Train ID
                    id_text = self.font.render(train_id, True, (255, 255, 255))
                    self.screen.blit(id_text, (int(tx) - 8, int(ty) - 8))

            # Draw Time HUD
            time_surf = self.font.render(f"Sim Time: {int(self.sim_time)} min", True, (0, 0, 0))
            self.screen.blit(time_surf, (10, 10))

            # Update Display
            pygame.display.flip()

            # Increment Time
            self.sim_time += self.time_speed
            self.clock.tick(60)  # 60 FPS

        pygame.quit()
        sys.exit()


# --- DUMMY DATA FOR TESTING (Run this file directly) ---
if __name__ == "__main__":
    # This mocks the output from your CSP/Greedy logic
    mock_schedule = {
        'T1': {
            'segments': [
                {'edge': ('Westgate', 'Aethelgard'), 'start_time': 0, 'end_time': 50},
                {'edge': ('Aethelgard', 'Ironhaven'), 'start_time': 50, 'end_time': 125},
                {'edge': ('Ironhaven', 'Eastport'), 'start_time': 125, 'end_time': 175}
            ]
        },
        'T2': {
            'segments': [
                {'edge': ('Deepwood', 'Ironhaven'), 'start_time': 10, 'end_time': 65},
                {'edge': ('Ironhaven', 'Suncrest'), 'start_time': 65, 'end_time': 140}
            ]
        },
        'T3': {
            'segments': [
                {'edge': ('Ironhaven', 'Aethelgard'), 'start_time': 0, 'end_time': 75},
                {'edge': ('Aethelgard', 'Highpoint'), 'start_time': 75, 'end_time': 130}
            ]
        }
    }

    app = RailwayVisualizer(mock_schedule)
    app.run()

