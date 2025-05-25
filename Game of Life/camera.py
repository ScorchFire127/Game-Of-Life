# camera.py
# Description: Defines the Camera class for handling view panning/zooming and coordinate conversion.

import pygame
from constants import MIN_ZOOM, MAX_ZOOM, CHUNK_SIZE # Import zoom limits

class Camera:
    """ Handles the view offset (panning), zoom, and coordinate transformations. """
    def __init__(self, width, height):
        # World position of the top-left corner of the screen at zoom=1
        self.camera_offset = pygame.math.Vector2(0, 0)
        self.screen_width = width
        self.screen_height = height
        self.zoom = 1.0
        self.min_zoom = MIN_ZOOM
        self.max_zoom = MAX_ZOOM

    def apply_pan(self, dx_screen, dy_screen):
        """ Pans the camera view based on screen pixel movement. """
        # Adjust pan distance based on current zoom level
        self.camera_offset.x += dx_screen / self.zoom
        self.camera_offset.y += dy_screen / self.zoom

    def zoom_at(self, screen_pos, zoom_change_factor):
        """
        Zooms the camera view in or out, keeping the point under screen_pos stationary.
        Args:
            screen_pos (tuple): The (x, y) screen coordinate to zoom towards/away from.
            zoom_change_factor (float): Multiplier for zoom (e.g., 1.1 for zoom in, 1/1.1 for zoom out).
        """
        if not (self.min_zoom <= self.zoom * zoom_change_factor <= self.max_zoom):
             return # Don't zoom if it exceeds limits

        world_pos_before_zoom = self.screen_to_world(screen_pos)

        self.zoom *= zoom_change_factor

        world_pos_after_zoom = self.screen_to_world(screen_pos)

        # Calculate the difference in world coordinates caused by the zoom shift
        delta_world = world_pos_before_zoom - world_pos_after_zoom

        # Adjust the offset to counteract the shift, keeping the target point fixed
        self.camera_offset += delta_world


    def world_to_screen(self, world_pos):
        """ Converts world coordinates (Vector2 or tuple) to screen coordinates (tuple). """
        # Calculate position relative to the camera's world offset, then scale by zoom
        relative_x = (world_pos[0] - self.camera_offset.x) * self.zoom
        relative_y = (world_pos[1] - self.camera_offset.y) * self.zoom
        # The final screen position is relative to the screen's top-left (0,0)
        # If zooming around center: add screen_center. For top-left zoom: no addition needed.
        # Since zoom_at handles offset adjustment, this direct calculation works.
        screen_x = int(relative_x)
        screen_y = int(relative_y)
        return screen_x, screen_y

    def screen_to_world(self, screen_pos):
        """ Converts screen coordinates (tuple) to world coordinates (tuple/Vector2). """
        # Convert screen position to position relative to camera origin in world space (scaled by zoom)
        relative_world_x = screen_pos[0] / self.zoom
        relative_world_y = screen_pos[1] / self.zoom
        # Add the camera's world offset to get the absolute world position
        world_x = relative_world_x + self.camera_offset.x
        world_y = relative_world_y + self.camera_offset.y
        return pygame.math.Vector2(world_x, world_y) # Return Vector2 for easier math

    def get_visible_world_rect(self):
        """
        Returns a pygame.Rect representing the visible area in world coordinates,
        accounting for zoom.
        """
        # Calculate the width and height of the view in world units
        world_view_width = self.screen_width / self.zoom
        world_view_height = self.screen_height / self.zoom

        # The top-left corner is simply the camera offset
        return pygame.Rect(self.camera_offset.x, self.camera_offset.y, world_view_width, world_view_height)

    def update_screen_size(self, width, height):
         """ Updates screen dimensions, useful on resize. """
         self.screen_width = width
         self.screen_height = height