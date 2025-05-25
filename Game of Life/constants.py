# constants.py
import pygame

# --- Screen & Display ---
SCREEN_WIDTH = 1280; SCREEN_HEIGHT = 720; FPS = 60; BORDER_WIDTH = 5

# --- Colors ---
BLACK = (0, 0, 0); WHITE = (255, 255, 255); DARK_GREY = (40, 40, 40)
LIGHT_GREY = (100, 100, 100); RED = (255, 0, 0); GREEN = (0, 255, 0)
BLUE = (0, 0, 255); YELLOW = (255, 255, 0)
WALL_COLOR = (150, 150, 150); ANTI_PARTICLE_COLOR = (150, 0, 150) # Purple
ERASER_COLOR = WHITE; COORD_TEXT_COLOR = (200, 200, 200)
WALL_DRAW_LINE_COLOR = (200, 200, 200, 150)

# --- Game Mechanics ---
CHUNK_SIZE = 100; CHUNK_LOAD_BUFFER = 1; DEFAULT_PARTICLE_SIZE = 3
MIN_PARTICLE_SIZE = 1; MAX_PARTICLE_SIZE = 50; COLLISION_ITERATIONS = 3
COLLISION_PUSH_FACTOR = 0.4; WALL_BOUNCE_FACTOR = 0.6
PARTICLE_COLLISION_ELASTICITY = 0.9

# --- UI Dimensions ---
LEFT_PANEL_WIDTH = 200; TOP_BAR_HEIGHT = 40; BOTTOM_BAR_HEIGHT = 25

# --- Tools ---
ERASER_START_RADIUS = 30; ERASER_RADIUS_STEP = 5; MIN_ERASER_RADIUS = 5; MAX_ERASER_RADIUS = 150
TOOL_RADIUS = 50; TOOL_STRENGTH_STEP = 5; MIN_TOOL_STRENGTH = 5; MAX_TOOL_STRENGTH = 200
DEFAULT_TOOL_STRENGTH = 50

# --- Zoom ---
MIN_ZOOM = 0.1; MAX_ZOOM = 5.0; ZOOM_FACTOR = 1.1

# --- Physics/Interaction (Tune these!) ---
# Define MAGNITUDES for different interaction types
ATTRACT_FORCE = 150.0  # Base attraction (e.g., R<->G, G<->Other)
REPEL_FORCE = 200.0    # Base repulsion (e.g., R<->R, B<->B)
# Specific forces for unique interactions
ANTI_PARTICLE_ATTRACT_FORCE = 250.0 # Anti attracts others
YELLOW_REPEL_FORCE = 220.0   # <<< THIS IS DEFINED HERE
GREEN_ATTRACT_FORCE = 120.0 # Green general attraction base
RED_BLUE_ATTRACT_FORCE = ATTRACT_FORCE * 1.5 # <<< THIS IS DEFINED HERE
RED_SELF_REPEL          = REPEL_FORCE * 0.5 # Specific R/R repulsion based on REPEL_FORCE
BLUE_SELF_REPEL         = REPEL_FORCE * 0.5 # Specific B/B repulsion based on REPEL_FORCE

GREEN_CENTER_ATTRACT_FORCE = 50.0 # Green specific behavior towards center
GENERAL_ATTRACTION_MAX_CHUNKS = 8 # Still used for decay function limit
MAX_INTERACTION_FORCE = 1000 # Limit TOTAL applied force magnitude per particle pair
MIN_FORCE_THRESHOLD_SQ = 1e-4 # Ignore tiny forces

# --- UI States ---
UI_STATE_NORMAL = 0; UI_STATE_EDITING_MULTIPLIER = 1
UI_STATE_SHOW_TOOL_EDITOR = 2; UI_STATE_DRAWING_WALL = 3

# --- Particle Types ---
PARTICLE_TYPES = ["red", "green", "blue", "yellow", "anti"] # Placeable types

# --- Particle Colors ---
PARTICLE_COLORS = { "red": RED, "green": GREEN, "blue": BLUE, "yellow": YELLOW, "wall": WALL_COLOR, "anti": ANTI_PARTICLE_COLOR }

# --- Base Particle Definitions ---
BASE_PARTICLE_DEFINITIONS = {
    ptype: {
        "color": PARTICLE_COLORS.get(ptype, WHITE), "size": DEFAULT_PARTICLE_SIZE,
        "is_movable": True, "is_anti_particle": ptype == "anti",
        "attracts": {}, "repels": {}
    } for ptype in PARTICLE_TYPES
}

# --- Wall Definition ---
WALL_PARTICLE_DEFINITION = {
    "color": WALL_COLOR, "size": DEFAULT_PARTICLE_SIZE + 1,
    "is_movable": False, "is_anti_particle": False,
    "attracts": {}, "repels": {}
}

# --- Time Control Constants ---
MIN_SPEED = 0.1; MAX_SPEED = 8.0; SPEED_INCREMENT = 0.1