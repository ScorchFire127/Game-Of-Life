# ui.py
import pygame
from constants import *

class UI:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.left_panel_rect = None # Initialize all rects to None
        self.top_bar_rect = None
        self.bottom_bar_rect = None
        self.play_area_rect = None
        self.settings_button_rect = None
        self.multiplier_display_rect = None
        self.multiplier_click_rect = None
        self._calculate_rects()

        try:
            self.font = pygame.font.SysFont(None, 24)
            self.small_font = pygame.font.SysFont(None, 18)
            self.coord_font = pygame.font.SysFont("monospace", 16)
        except pygame.error as e: print(f"Font Error: {e}"); self.font = self.small_font = self.coord_font = None

        # --- UI State ---
        self.state = UI_STATE_NORMAL
        self.multiplier_input_text = "1"
        self.cell_multiplier = 1

        self.selected_particle_type = "red" # Default placeable particle
        self.selected_tool = "place" # Default tool
        self.tool_editor_particle_type = None

        # --- Define tools including Wall ---
        tool_names = ["Place", "Wall", "Erase", "Attract", "Repel", "Reset"] # Added Wall
        self.tools = [{"name": name, "rect": None} for name in tool_names]

        self.particle_buttons = []
        self.add_particle_button_rect = None

        self._calculate_tool_button_rects()


    def _calculate_rects(self):
        # ... (Calculation logic remains the same as previous version) ...
        if self.screen_height <= (2 * BORDER_WIDTH + BOTTOM_BAR_HEIGHT + TOP_BAR_HEIGHT) or self.screen_width <= (BORDER_WIDTH + LEFT_PANEL_WIDTH + BORDER_WIDTH):
            self.left_panel_rect = pygame.Rect(0,0,0,0); self.top_bar_rect = pygame.Rect(0,0,0,0); self.bottom_bar_rect = pygame.Rect(0,0,0,0); self.play_area_rect = pygame.Rect(0,0,0,0); self.settings_button_rect = pygame.Rect(0,0,0,0)
            return
        self.left_panel_rect = pygame.Rect(BORDER_WIDTH, BORDER_WIDTH, LEFT_PANEL_WIDTH, max(0, self.screen_height - 2 * BORDER_WIDTH - BOTTOM_BAR_HEIGHT))
        self.top_bar_rect = pygame.Rect(self.left_panel_rect.right + BORDER_WIDTH, BORDER_WIDTH, max(0, self.screen_width - self.left_panel_rect.right - 2 * BORDER_WIDTH), TOP_BAR_HEIGHT)
        self.bottom_bar_rect = pygame.Rect(self.left_panel_rect.right + BORDER_WIDTH, max(0, self.screen_height - BORDER_WIDTH - BOTTOM_BAR_HEIGHT), max(0, self.screen_width - self.left_panel_rect.right - 2 * BORDER_WIDTH), BOTTOM_BAR_HEIGHT)
        play_area_top = self.top_bar_rect.bottom + BORDER_WIDTH; play_area_bottom = self.bottom_bar_rect.top - BORDER_WIDTH; play_area_height = max(0, play_area_bottom - play_area_top)
        self.play_area_rect = pygame.Rect(self.left_panel_rect.right + BORDER_WIDTH, play_area_top, max(0, self.screen_width - self.left_panel_rect.right - 2 * BORDER_WIDTH), play_area_height)
        settings_button_width = 90; settings_button_height = max(1, self.top_bar_rect.height - 10)
        self.settings_button_rect = pygame.Rect(max(self.top_bar_rect.left, self.top_bar_rect.right - settings_button_width - BORDER_WIDTH), self.top_bar_rect.top + 5, settings_button_width, settings_button_height)
        self.multiplier_display_rect = pygame.Rect(0,0,0,0); self.multiplier_click_rect = pygame.Rect(0,0,0,0)


    def _calculate_tool_button_rects(self):
        """ Calculates the rects for the tool buttons specifically. """
        if not hasattr(self, 'left_panel_rect') or not self.left_panel_rect or self.left_panel_rect.width <= 0: return

        y_offset = self.left_panel_rect.top + 10; x_start = self.left_panel_rect.left + 10
        panel_width = self.left_panel_rect.width - 20

        num_tools = len(self.tools)
        cols = 2 # Stick to 2 columns
        tool_button_width = max(1, (panel_width - (cols - 1)*10) // cols)
        tool_button_height = 30
        for i, tool_info in enumerate(self.tools):
             col = i % cols
             row = i // cols
             rect = pygame.Rect(x_start + col * (tool_button_width + 10),
                                y_offset + row * (tool_button_height + 5),
                                tool_button_width, tool_button_height)
             tool_info["rect"] = rect

    def draw(self, surface, game_state):
        if not self.font: return # Cannot draw without fonts
        # ... (Unpack game_state variables as before) ...
        camera_zoom = game_state.get('camera_zoom', 1.0); eraser_radius = game_state.get('eraser_radius', ERASER_START_RADIUS)
        tool_strength = game_state.get('tool_strength', DEFAULT_TOOL_STRENGTH); cursor_chunk_coord = game_state.get('cursor_chunk_coord', None)
        particle_definitions = game_state.get('particle_definitions', {})
        particle_enable_states = game_state.get('particle_enable_states', {}); particle_lock_states = game_state.get('particle_lock_states', {})
        is_paused = game_state.get('is_paused', False); game_speed = game_state.get('game_speed', 1.0)

        self._draw_borders(surface)
        self._draw_panels_background(surface)
        self._draw_top_bar_content(surface, camera_zoom, is_paused, game_speed)
        self._draw_bottom_bar_content(surface, cursor_chunk_coord)
        self._draw_left_panel_content(surface, eraser_radius, tool_strength, particle_definitions, particle_enable_states, particle_lock_states)

        if self.state == UI_STATE_SHOW_TOOL_EDITOR:
             self._draw_tool_editor(surface, particle_definitions, particle_enable_states, particle_lock_states)


    def _draw_borders(self, surface):
        # ... (Draw borders as before) ...
        if not surface or self.screen_width <= 0 or self.screen_height <= 0: return
        pygame.draw.rect(surface, BLACK, (0, 0, self.screen_width, self.screen_height), BORDER_WIDTH * 2)
        if self.left_panel_rect: pygame.draw.rect(surface, BLACK, self.left_panel_rect.inflate(BORDER_WIDTH*2, BORDER_WIDTH*2), BORDER_WIDTH)
        if self.top_bar_rect: pygame.draw.rect(surface, BLACK, self.top_bar_rect.inflate(BORDER_WIDTH*2, BORDER_WIDTH*2), BORDER_WIDTH)
        if self.bottom_bar_rect: pygame.draw.rect(surface, BLACK, self.bottom_bar_rect.inflate(BORDER_WIDTH*2, BORDER_WIDTH*2), BORDER_WIDTH)


    def _draw_panels_background(self, surface):
        # ... (Draw backgrounds as before) ...
        if self.left_panel_rect: pygame.draw.rect(surface, DARK_GREY, self.left_panel_rect)
        if self.top_bar_rect: pygame.draw.rect(surface, DARK_GREY, self.top_bar_rect)
        if self.bottom_bar_rect: pygame.draw.rect(surface, DARK_GREY, self.bottom_bar_rect)


    def _draw_top_bar_content(self, surface, camera_zoom, is_paused, game_speed):
        # ... (Draw top bar content as before) ...
        if not self.top_bar_rect or not self.font: return
        display_text = f"Place x{self.cell_multiplier}"; text_color = WHITE
        if self.state == UI_STATE_EDITING_MULTIPLIER: display_text = f"Enter: {self.multiplier_input_text}_"; text_color = YELLOW
        multiplier_text_surf = self.font.render(display_text, True, text_color)
        self.multiplier_display_rect = multiplier_text_surf.get_rect(left = self.top_bar_rect.left + 10, centery = self.top_bar_rect.centery)
        self.multiplier_click_rect = self.multiplier_display_rect.inflate(10, 5)
        if self.state == UI_STATE_EDITING_MULTIPLIER: pygame.draw.rect(surface, LIGHT_GREY, self.multiplier_click_rect, border_radius=3)
        surface.blit(multiplier_text_surf, self.multiplier_display_rect); last_element_right = self.multiplier_click_rect.right
        zoom_text = self.font.render(f"Zoom: {camera_zoom:.2f}x", True, WHITE); zoom_rect = zoom_text.get_rect(left=last_element_right + 20, centery=self.top_bar_rect.centery)
        surface.blit(zoom_text, zoom_rect); last_element_right = zoom_rect.right
        time_status_text = f"Speed: {game_speed:.1f}x"; time_color = WHITE
        if is_paused: time_status_text += " (Paused)"; time_color = YELLOW
        time_text_surf = self.font.render(time_status_text, True, time_color); time_rect = time_text_surf.get_rect(left=last_element_right + 20, centery=self.top_bar_rect.centery)
        surface.blit(time_text_surf, time_rect)
        if self.settings_button_rect:
            pygame.draw.rect(surface, LIGHT_GREY, self.settings_button_rect); settings_text = self.font.render("Settings", True, BLACK)
            surface.blit(settings_text, settings_text.get_rect(center=self.settings_button_rect.center))


    def _draw_bottom_bar_content(self, surface, cursor_chunk_coord):
        # ... (Draw bottom bar content as before) ...
        if not self.bottom_bar_rect or not self.coord_font: return
        coord_text = f"Chunk: ({cursor_chunk_coord[0]}, {cursor_chunk_coord[1]})" if cursor_chunk_coord else "Chunk: (N/A)"
        text_surf = self.coord_font.render(coord_text, True, COORD_TEXT_COLOR)
        text_rect = text_surf.get_rect(right=self.bottom_bar_rect.right - 10, centery=self.bottom_bar_rect.centery)
        if text_rect.left < self.bottom_bar_rect.left: text_rect.left = self.bottom_bar_rect.left
        surface.blit(text_surf, text_rect)


    def _draw_left_panel_content(self, surface, eraser_radius, tool_strength, particle_definitions, particle_enable_states, particle_lock_states):
        if not hasattr(self, 'left_panel_rect') or not self.left_panel_rect or not self.font or not self.small_font:
            print("Warning: UI drawing skipped, panel/fonts not ready.")
            return

        # Tool Selection
        tool_button_height = 30; y_offset = self.left_panel_rect.top + 10
        cols = 2 # Define cols for tool layout calculation
        for tool_info in self.tools:
            tool_name = tool_info["name"]; rect = tool_info["rect"]
            if rect is None: continue
            is_visually_selected = (tool_name == "Wall" and self.state == UI_STATE_DRAWING_WALL) or \
                                 (tool_name != "Wall" and self.selected_tool == tool_name.lower())
            button_color = WHITE if is_visually_selected else LIGHT_GREY; text_color = BLACK
            pygame.draw.rect(surface, button_color, rect)
            text_surf = self.font.render(tool_name, True, text_color)
            surface.blit(text_surf, text_surf.get_rect(center=rect.center))
            display_value = None
            if self.state != UI_STATE_DRAWING_WALL:
                if tool_name == "Erase" and is_visually_selected: display_value = f"R:{eraser_radius}"
                elif tool_name in ["Attract", "Repel"] and is_visually_selected: display_value = f"S:{tool_strength}"
            if display_value:
                value_text = self.small_font.render(display_value, True, BLACK if is_visually_selected else WHITE)
                value_rect = value_text.get_rect(centerx=rect.centerx, bottom=rect.top - 2)
                surface.blit(value_text, value_rect)
        num_tool_rows = (len(self.tools) + cols - 1) // cols
        y_offset += num_tool_rows * (tool_button_height + 5) + 15

        # --- Particle Selection (With Specific Order) ---
        x_start = self.left_panel_rect.left + 10; panel_width = self.left_panel_rect.width - 20
        # Define the desired display order
        display_order = ["red", "blue", "green", "yellow", "anti"]
        # Get available types intersection with desired order + any extras
        available_placeable = [pt for pt in display_order if pt in particle_definitions and pt != 'wall']
        # Add any other defined types not in the order list (excluding wall)
        available_placeable.extend([pt for pt in particle_definitions if pt not in display_order and pt != 'wall'])

        self.particle_buttons.clear()

        # Toggle All Button
        toggle_all_rect = pygame.Rect(x_start, y_offset, panel_width, 20)
        pygame.draw.rect(surface, LIGHT_GREY, toggle_all_rect)
        toggle_text = self.small_font.render("Toggle All (TBD)", True, BLACK)
        surface.blit(toggle_text, toggle_text.get_rect(center=toggle_all_rect.center))
        y_offset += 25

        # Particle Grid Drawing
        particle_button_size = 25; label_height = 15; total_item_height = particle_button_size + label_height; padding = 5
        items_per_row = max(1, (panel_width + padding) // (particle_button_size + padding))
        col_count = 0; x_pos = x_start
        for ptype_name in available_placeable: # Iterate through ordered list
             pdef = particle_definitions.get(ptype_name, {})
             color = pdef.get("color", WHITE)
             is_enabled = particle_enable_states.get(ptype_name, True)
             is_locked = particle_lock_states.get(ptype_name, False)
             particle_rect = pygame.Rect(x_pos, y_offset, particle_button_size, particle_button_size)
             self.particle_buttons.append({"type": ptype_name, "rect": particle_rect})
             outline_rect = particle_rect.inflate(4, 4)
             if self.selected_tool == "place" and self.selected_particle_type == ptype_name: pygame.draw.rect(surface, WHITE, outline_rect, 2)
             draw_color = color if is_enabled else DARK_GREY
             pygame.draw.rect(surface, draw_color, particle_rect)
             label = self.small_font.render(ptype_name.capitalize(), True, WHITE)
             label_rect = label.get_rect(centerx=particle_rect.centerx, top=particle_rect.bottom + 2)
             surface.blit(label, label_rect)
             if is_locked:
                  lock_icon_surf = self.small_font.render("L", True, YELLOW)
                  lock_rect = lock_icon_surf.get_rect(center=particle_rect.center)
                  surface.blit(lock_icon_surf, lock_rect)
             col_count += 1
             if col_count >= items_per_row: col_count = 0; x_pos = x_start; y_offset += total_item_height + padding
             else: x_pos += particle_button_size + padding
        if col_count != 0: y_offset += total_item_height + padding
        y_offset += 10

        # Add Custom Particle Button
        self.add_particle_button_rect = pygame.Rect(x_start, y_offset, panel_width, 30)
        pygame.draw.rect(surface, LIGHT_GREY, self.add_particle_button_rect)
        add_text = self.font.render("Add Particle (TBD)", True, BLACK)
        surface.blit(add_text, add_text.get_rect(center=self.add_particle_button_rect.center))

    def _draw_tool_editor(self, surface, particle_definitions, particle_enable_states, particle_lock_states):
        # ... (Placeholder drawing logic remains the same) ...
        if not self.font: return
        editor_width=300; editor_height=400
        editor_rect = pygame.Rect((self.screen_width - editor_width) // 2, (self.screen_height - editor_height) // 2, editor_width, editor_height)
        bg_surf = pygame.Surface(editor_rect.size, pygame.SRCALPHA); bg_surf.fill((50, 50, 50, 220)); surface.blit(bg_surf, editor_rect.topleft)
        pygame.draw.rect(surface, LIGHT_GREY, editor_rect, 2)
        title = f"Edit {self.tool_editor_particle_type.capitalize()} Targets (TBD)"; title_surf = self.font.render(title, True, WHITE)
        title_rect = title_surf.get_rect(centerx=editor_rect.centerx, top=editor_rect.top + 10); surface.blit(title_surf, title_rect)
        close_rect = pygame.Rect(editor_rect.right - 35, editor_rect.top + 5, 30, 20)
        pygame.draw.rect(surface, RED, close_rect); close_text = self.font.render("X", True, WHITE)
        surface.blit(close_text, close_text.get_rect(center=close_rect.center))

    def handle_event(self, event, current_multiplier_value):
        # ... (handle_event logic remains the same) ...
        if self.state == UI_STATE_EDITING_MULTIPLIER:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    try: new_val = int(self.multiplier_input_text); self.cell_multiplier = max(0, new_val)
                    except ValueError: pass # Keep old value if invalid
                    self.multiplier_input_text = str(self.cell_multiplier)
                    self.state = UI_STATE_NORMAL; return self.cell_multiplier
                elif event.key == pygame.K_BACKSPACE: self.multiplier_input_text = self.multiplier_input_text[:-1]
                elif event.unicode.isdigit() and len(self.multiplier_input_text) < 6: self.multiplier_input_text += event.unicode
                elif event.key == pygame.K_ESCAPE: self.multiplier_input_text = str(self.cell_multiplier); self.state = UI_STATE_NORMAL
                return None # Consume key event
        if event.type == pygame.MOUSEBUTTONDOWN:
             handled, action = self.handle_click(event.pos, event.button)
             if handled: return action
        return None


    def handle_click(self, pos, button):
        # ... (checks for Tool Editor, Multiplier, Settings) ...

        # --- Check Left Panel ---
        if hasattr(self, 'left_panel_rect') and self.left_panel_rect and self.left_panel_rect.collidepoint(pos):
            # Check Tool Buttons
            for tool_info in self.tools:
                 tool_name = tool_info["name"]; rect = tool_info["rect"]
                 if rect and rect.collidepoint(pos):
                      action_to_signal = None
                      if button == 1: # Left Click
                          tool_id = tool_name.lower()
                          if tool_id == "reset":
                              print("Reset button clicked.")
                              action_to_signal = 'reset_simulation' # Signal Game to reset
                          elif tool_id == "wall":
                               # Toggle wall drawing state
                               if self.state == UI_STATE_DRAWING_WALL:
                                    self.state = UI_STATE_NORMAL; action_to_signal = 'cancel_wall_draw'; print("Wall drawing OFF")
                               else:
                                    self.state = UI_STATE_DRAWING_WALL; self.selected_tool = "place"; action_to_signal = 'start_wall_draw'; print("Wall drawing ON")
                          elif self.selected_tool == tool_id: # Click active tool -> deactivate
                               self.selected_tool = "place"; print(f"Tool deactivated (selected Place)")
                               if self.state == UI_STATE_DRAWING_WALL: self.state = UI_STATE_NORMAL; action_to_signal = 'cancel_wall_draw'
                          else: # Click inactive tool -> activate
                               self.selected_tool = tool_id; print(f"Selected tool: {self.selected_tool}")
                               if self.state == UI_STATE_DRAWING_WALL: self.state = UI_STATE_NORMAL; action_to_signal = 'cancel_wall_draw'
                          return True, action_to_signal
                      elif button == 3: # Right Click (Editor/Info)
                           # ... (Right click logic for Attract/Repel/Erase remains same) ...
                           if tool_name in ["Attract", "Repel"]: self.state = UI_STATE_SHOW_TOOL_EDITOR; self.tool_editor_particle_type = tool_name.lower(); action_to_signal = 'show_tool_editor'
                           elif tool_name == "Erase": print(f"RClick Erase. Use [ ] keys."); action_to_signal = 'adjust_eraser'
                           return True, action_to_signal

            # ... (Check Particle Buttons logic remains same) ...
            for button_info in self.particle_buttons:
                 ptype = button_info["type"]; rect = button_info["rect"]
                 if rect and rect.collidepoint(pos):
                      action = None
                      if button == 1:
                           self.selected_particle_type = ptype; self.selected_tool = "place"
                           if self.state == UI_STATE_DRAWING_WALL and ptype != "wall": self.state = UI_STATE_NORMAL; action = 'cancel_wall_draw'
                           print(f"Particle: {ptype} (Tool: Place)")
                           return True, action
                      elif button == 3: action = ('toggle_lock', ptype)
                      return True, action

            # ... (Check Add Particle Button logic remains same) ...
            if self.add_particle_button_rect and self.add_particle_button_rect.collidepoint(pos) and button == 1:
                 print("Add Particle (TBD)"); return True, 'add_custom_particle'


            return True, None # Consume click in panel bg

        # Click outside UI
        return False, None

    def update_dimensions(self, screen_width, screen_height):
        # ... (update_dimensions logic remains the same) ...
        self.screen_width = screen_width; self.screen_height = screen_height
        self._calculate_rects(); self._calculate_tool_button_rects()