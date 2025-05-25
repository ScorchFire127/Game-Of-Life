# particle.py
import pygame
import random
import math
from constants import CHUNK_SIZE, DEFAULT_PARTICLE_SIZE

class Particle:
    """ Represents a single particle in the simulation. """
    def __init__(self, x, y, particle_def, name=None):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)) if particle_def.get("is_movable", True) else pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)

        # --- Attributes from definition ---
        self.type = name if name else "unknown"
        self.definition = particle_def
        self.color = particle_def.get("color", (255, 255, 255))
        self.size = particle_def.get("size", DEFAULT_PARTICLE_SIZE)
        self.is_movable = particle_def.get("is_movable", True)
        self.is_anti_particle = particle_def.get("is_anti_particle", False)
        # self.force_value = particle_def.get("force_value", 0.0) # REMOVED this line
        self.mass = max(1.0, math.pi * self.size**2)

        # --- State ---
        self.chunk_coord = self.get_chunk_coord()
        self.name = name if name else self.type

    def get_chunk_coord(self):
        """ Calculates the chunk coordinates (cx, cy) based on position. """
        return (int(self.pos.x // CHUNK_SIZE), int(self.pos.y // CHUNK_SIZE))

    def apply_force(self, force):
        """ Adds a force vector to the particle's acceleration, if movable. """
        if self.is_movable:
             # Consider dividing force by mass here if implementing F=ma
             # effective_force = force / self.mass if self.mass > 0 else force
             self.acc += force

    def update(self, dt):
        """ Updates the particle's state (position, velocity). No Damping. """
        if not self.is_movable:
            self.vel = pygame.math.Vector2(0, 0)
            self.acc = pygame.math.Vector2(0, 0)
            return False # No chunk change if not moving

        # Physics integration (Velocity changes ONLY due to acceleration)
        self.vel += self.acc * dt
        self.pos += self.vel * dt

        # --- DAMPING REMOVED ---
        # self.vel *= 0.995 # <--- REMOVED THIS LINE

        # --- Speed Limiting (Still Recommended as a Safety) ---
        max_speed = CHUNK_SIZE * 5 # Increased limit further? Tune as needed.
        speed_sq = self.vel.length_squared()
        if speed_sq > max_speed * max_speed:
            try: self.vel.scale_to_length(max_speed)
            except ValueError: self.vel = pygame.math.Vector2(0,0) # Handle zero vector case

        # Reset acceleration for the next frame (Forces apply each frame)
        self.acc = pygame.math.Vector2(0, 0)

        # Check for chunk change
        new_chunk_coord = self.get_chunk_coord()
        moved_chunk = new_chunk_coord != self.chunk_coord
        self.chunk_coord = new_chunk_coord
        return moved_chunk

    def draw(self, surface, camera):
        """ Draws the particle onto the screen surface relative to the camera. """
        screen_pos = camera.world_to_screen(self.pos)
        screen_radius = max(1, int(self.size * camera.zoom)) # Use particle size, scale with zoom

        # Culling check (more efficient than checking every pixel)
        if screen_pos[0] + screen_radius < 0 or \
           screen_pos[0] - screen_radius > camera.screen_width or \
           screen_pos[1] + screen_radius < 0 or \
           screen_pos[1] - screen_radius > camera.screen_height:
            return # Particle is completely off-screen

        # Draw as a circle
        pygame.draw.circle(surface, self.color, screen_pos, screen_radius)
        # Optional: Draw outline or name if zoomed in?
        # if camera.zoom > SOME_THRESHOLD:
        #    pygame.draw.circle(surface, WHITE, screen_pos, screen_radius, 1)