# main.py
import pygame
import sys
import random
import math
import time
from collections import defaultdict

# Import constants AFTER they are correctly defined
from constants import *
from particle import Particle
from camera import Camera
from ui import UI

class Game:
    def __init__(self):
        pygame.init()
        self.screen_flags = pygame.RESIZABLE
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), self.screen_flags)
        pygame.display.set_caption("Particle Sim")
        self.clock = pygame.time.Clock()
        self.running = True; self.fullscreen = False; self.is_paused = False
        self.particles = []; self.chunks = defaultdict(list)
        self.particle_definitions = BASE_PARTICLE_DEFINITIONS.copy()
        self.particle_definitions["wall"] = WALL_PARTICLE_DEFINITION
        self.particle_enable_states = {ptype: True for ptype in self.particle_definitions}
        self.particle_lock_states = {ptype: (ptype == "wall") for ptype in self.particle_definitions}
        current_w, current_h = self.screen.get_size()
        self.camera = Camera(current_w, current_h)
        self.ui = UI(current_w, current_h)
        self.is_panning = False; self.pan_start_pos = None
        self.is_applying_tool_continuously = False
        self.eraser_radius = ERASER_START_RADIUS; self.tool_strength = DEFAULT_TOOL_STRENGTH
        self.cursor_chunk_coord = None; self.wall_draw_start_pos = None
        self.game_speed_multiplier = 1.0; self.min_speed = MIN_SPEED
        self.max_speed = MAX_SPEED; self.speed_increment = SPEED_INCREMENT
        if hasattr(self, 'ui') and self.ui: self.ui.update_dimensions(current_w, current_h)
        else: print("CRITICAL ERROR: UI init failed"); self.running = False

    def run(self):
        while self.running:
            dt_real = self.clock.tick(FPS) / 1000.0; dt_real = min(dt_real, 0.1)
            effective_dt = dt_real * self.game_speed_multiplier if not self.is_paused else 0.0
            mouse_pos = pygame.mouse.get_pos()
            if hasattr(self.ui, 'play_area_rect') and self.ui.play_area_rect and self.ui.play_area_rect.collidepoint(mouse_pos):
                 if hasattr(self, 'camera') and self.camera:
                      world_pos = self.camera.screen_to_world(mouse_pos); self.cursor_chunk_coord = (int(world_pos.x // CHUNK_SIZE), int(world_pos.y // CHUNK_SIZE))
                 else: self.cursor_chunk_coord = None
            else: self.cursor_chunk_coord = None
            self.handle_events(mouse_pos)
            self.update(effective_dt)
            self.draw()
        pygame.quit(); sys.exit()

    def handle_events(self, mouse_pos):
        if not hasattr(self, 'ui') or not self.ui: return
        mouse_buttons = pygame.mouse.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False; return
            if event.type == pygame.VIDEORESIZE: self._resize_screen(event.w, event.h)
            ui_action = self.ui.handle_event(event, self.ui.cell_multiplier); ui_handled_event = False
            if ui_action is not None:
                 ui_handled_event = True
                 if isinstance(ui_action, tuple):
                      action_type, action_payload = ui_action
                      if action_type == 'toggle_lock':
                           ptype = action_payload
                           if ptype in self.particle_lock_states: self.particle_lock_states[ptype] = not self.particle_lock_states[ptype]; print(f"{ptype} lock: {self.particle_lock_states[ptype]}")
                 elif isinstance(ui_action, str):
                      if ui_action == 'reset_simulation': self.reset_simulation(); return
                      elif ui_action == 'cancel_wall_draw' or ui_action == 'start_wall_draw':
                           self.wall_draw_start_pos = None
                           if ui_action == 'start_wall_draw': print("Wall drawing mode ON.")
                           else: print("Wall drawing mode OFF.")
            if not ui_handled_event:
                if event.type == pygame.KEYDOWN:
                     if self.ui.state != UI_STATE_EDITING_MULTIPLIER: self._handle_keydown(event.key)
                if event.type == pygame.MOUSEWHEEL:
                     if self.ui.play_area_rect and self.ui.play_area_rect.collidepoint(mouse_pos):
                          if self.ui.state == UI_STATE_NORMAL: factor = ZOOM_FACTOR if event.y > 0 else 1 / ZOOM_FACTOR; self.camera.zoom_at(mouse_pos, factor)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    button = event.button
                    if self.ui.play_area_rect and self.ui.play_area_rect.collidepoint(mouse_pos):
                        if self.ui.state == UI_STATE_DRAWING_WALL and button == 1: world_pos = self.camera.screen_to_world(mouse_pos); self._place_wall_segment(self.wall_draw_start_pos, world_pos) if self.wall_draw_start_pos else None; self.wall_draw_start_pos = world_pos; continue
                        elif self.ui.state == UI_STATE_DRAWING_WALL and button == 3: self.ui.state = UI_STATE_NORMAL; self.wall_draw_start_pos = None; continue
                        elif button == 3 and self.ui.state != UI_STATE_DRAWING_WALL: self.is_panning = True; self.pan_start_pos = mouse_pos
                        elif button == 1 and self.ui.state == UI_STATE_NORMAL:
                             if self.ui.selected_tool == "place": self._place_particles(mouse_pos)
                             else: self.is_applying_tool_continuously = True; self._apply_tool(mouse_pos)
                if event.type == pygame.MOUSEBUTTONUP:
                    button = event.button
                    if button == 3: self.is_panning = False
                    if button == 1: self.is_applying_tool_continuously = False
        if self.is_panning and mouse_buttons[2]:
            if self.pan_start_pos: dx = self.pan_start_pos[0] - mouse_pos[0]; dy = self.pan_start_pos[1] - mouse_pos[1]; self.camera.apply_pan(dx, dy); self.pan_start_pos = mouse_pos
        if self.is_applying_tool_continuously and mouse_buttons[0] and self.ui.state == UI_STATE_NORMAL:
             if self.ui.play_area_rect and self.ui.play_area_rect.collidepoint(mouse_pos):
                  if self.ui.selected_tool != "place": self._apply_tool(mouse_pos)

    def _handle_keydown(self, key):
        if not hasattr(self, 'ui') or not self.ui: return
        if key == pygame.K_ESCAPE:
             if self.ui.state == UI_STATE_DRAWING_WALL: print("Cancel wall draw (ESC)"); self.ui.state = UI_STATE_NORMAL; self.wall_draw_start_pos = None
             elif self.ui.state == UI_STATE_SHOW_TOOL_EDITOR: print("Close tool editor (ESC)"); self.ui.state = UI_STATE_NORMAL; self.ui.tool_editor_particle_type = None
             elif self.ui.state == UI_STATE_EDITING_MULTIPLIER: print("Cancel multiplier edit (ESC)"); self.ui.state = UI_STATE_NORMAL; self.ui.multiplier_input_text = str(self.ui.cell_multiplier)
             else: self.running = False
        elif key == pygame.K_f:
            self.fullscreen = not self.fullscreen
            if self.fullscreen:
                try: info = pygame.display.Info(); self.screen_flags = pygame.FULLSCREEN | pygame.SCALED; self._resize_screen(info.current_w, info.current_h)
                except pygame.error as e: print(f"FS Error: {e}"); self.fullscreen = False; self.screen_flags = pygame.RESIZABLE
            else: self.screen_flags = pygame.RESIZABLE; self._resize_screen(SCREEN_WIDTH, SCREEN_HEIGHT)
        elif key == pygame.K_p: self.is_paused = not self.is_paused; print(f"Game {'Paused' if self.is_paused else 'Resumed'}")
        elif key == pygame.K_EQUALS or key == pygame.K_PLUS or key == pygame.K_KP_PLUS: self.game_speed_multiplier = min(self.max_speed, round(self.game_speed_multiplier + self.speed_increment, 2)); print(f"Speed: {self.game_speed_multiplier:.2f}x")
        elif key == pygame.K_MINUS or key == pygame.K_KP_MINUS: self.game_speed_multiplier = max(self.min_speed, round(self.game_speed_multiplier - self.speed_increment, 2)); print(f"Speed: {self.game_speed_multiplier:.2f}x")
        elif key == pygame.K_UP: new_mult = min(1000, self.ui.cell_multiplier * 2 if self.ui.cell_multiplier > 1 else 2); self.ui.cell_multiplier = new_mult; self.ui.multiplier_input_text = str(self.ui.cell_multiplier); print(f"Multiplier: {self.ui.cell_multiplier}")
        elif key == pygame.K_DOWN: new_mult = max(1, self.ui.cell_multiplier // 2); self.ui.cell_multiplier = new_mult; self.ui.multiplier_input_text = str(self.ui.cell_multiplier); print(f"Multiplier: {self.ui.cell_multiplier}")
        else:
             mods = pygame.key.get_mods(); adjust_strength = mods & pygame.KMOD_SHIFT
             if key == pygame.K_LEFTBRACKET:
                  if adjust_strength and self.ui.selected_tool in ['attract', 'repel']: new_strength = max(MIN_TOOL_STRENGTH, self.tool_strength - TOOL_STRENGTH_STEP); self.tool_strength = new_strength; print(f"Strength: {self.tool_strength}")
                  elif not adjust_strength and self.ui.selected_tool == 'erase': new_radius = max(MIN_ERASER_RADIUS, self.eraser_radius - ERASER_RADIUS_STEP); self.eraser_radius = new_radius; print(f"Radius: {self.eraser_radius}")
             elif key == pygame.K_RIGHTBRACKET:
                  if adjust_strength and self.ui.selected_tool in ['attract', 'repel']: new_strength = min(MAX_TOOL_STRENGTH, self.tool_strength + TOOL_STRENGTH_STEP); self.tool_strength = new_strength; print(f"Strength: {self.tool_strength}")
                  elif not adjust_strength and self.ui.selected_tool == 'erase': new_radius = min(MAX_ERASER_RADIUS, self.eraser_radius + ERASER_RADIUS_STEP); self.eraser_radius = new_radius; print(f"Radius: {self.eraser_radius}")

    def _place_particles(self, screen_pos):
        if not hasattr(self, 'ui') or not self.ui: return
        world_pos = self.camera.screen_to_world(screen_pos); ptype = self.ui.selected_particle_type
        if ptype == "wall" or ptype not in self.particle_definitions or not self.particle_enable_states.get(ptype, True): return
        pdef = self.particle_definitions[ptype]
        for _ in range(self.ui.cell_multiplier):
            offset = pygame.math.Vector2(random.uniform(-2, 2), random.uniform(-2, 2)) * (self.ui.cell_multiplier > 1)
            new_particle = Particle(world_pos.x + offset.x, world_pos.y + offset.y, pdef, name=ptype)
            self.particles.append(new_particle); new_particle.chunk_coord = new_particle.get_chunk_coord(); self.chunks[new_particle.chunk_coord].append(new_particle)

    def _place_wall_segment(self, world_start, world_end):
        if "wall" not in self.particle_definitions: print("Error: Wall definition missing."); return
        pdef = self.particle_definitions["wall"]; wall_size = pdef.get("size", DEFAULT_PARTICLE_SIZE); spacing = wall_size * 1.2
        try:
            distance = world_start.distance_to(world_end)
            if distance < 1.0 : return
            direction = (world_end - world_start).normalize()
            num_steps = int(distance / spacing) if spacing > 1e-6 else 0
            for i in range(num_steps + 1):
                current_pos = world_start + direction * i * spacing
                new_particle = Particle(current_pos.x, current_pos.y, pdef, name="wall")
                self.particles.append(new_particle); new_particle.chunk_coord = new_particle.get_chunk_coord(); self.chunks[new_particle.chunk_coord].append(new_particle)
        except (ValueError, ZeroDivisionError) as e: print(f"Wall placement error: {e}")

    def _apply_tool(self, screen_pos):
        if not hasattr(self, 'ui') or not self.ui: return
        world_pos_vec = self.camera.screen_to_world(screen_pos); active_tool = self.ui.selected_tool
        if active_tool == "erase":
            tool_radius = self.eraser_radius; tool_radius_sq = tool_radius * tool_radius; particles_to_remove = set()
            chunk_search_radius = math.ceil(tool_radius / CHUNK_SIZE); center_chunk_x = int(world_pos_vec.x // CHUNK_SIZE); center_chunk_y = int(world_pos_vec.y // CHUNK_SIZE)
            for dx in range(-chunk_search_radius, chunk_search_radius + 1):
                for dy in range(-chunk_search_radius, chunk_search_radius + 1):
                    check_coord = (center_chunk_x + dx, center_chunk_y + dy)
                    if check_coord in self.chunks:
                        indices_to_remove_from_chunk = []
                        for idx, p in enumerate(self.chunks[check_coord]):
                            if not self.particle_lock_states.get(p.type, False) and p not in particles_to_remove and p.pos.distance_squared_to(world_pos_vec) < tool_radius_sq:
                                particles_to_remove.add(p); indices_to_remove_from_chunk.append(idx)
                        if indices_to_remove_from_chunk:
                            for idx in sorted(indices_to_remove_from_chunk, reverse=True): del self.chunks[check_coord][idx]
            if particles_to_remove: self.particles = [p for p in self.particles if p not in particles_to_remove]; print(f"Erased {len(particles_to_remove)} particles.") if len(particles_to_remove) > 0 else None
        elif active_tool in ["attract", "repel"]:
            tool_radius = TOOL_RADIUS; tool_radius_sq = tool_radius * tool_radius; strength = self.tool_strength if active_tool == "attract" else -self.tool_strength
            chunk_search_radius = math.ceil(tool_radius / CHUNK_SIZE); center_chunk_x = int(world_pos_vec.x // CHUNK_SIZE); center_chunk_y = int(world_pos_vec.y // CHUNK_SIZE)
            for dx in range(-chunk_search_radius, chunk_search_radius + 1):
                 for dy in range(-chunk_search_radius, chunk_search_radius + 1):
                      check_coord = (center_chunk_x + dx, center_chunk_y + dy)
                      if check_coord in self.chunks:
                           for p in self.chunks[check_coord]:
                                if self.particle_enable_states.get(p.type, True) and p.is_movable:
                                     dist_sq = p.pos.distance_squared_to(world_pos_vec)
                                     if 0 < dist_sq < tool_radius_sq:
                                          direction = world_pos_vec - p.pos; dist = direction.length()
                                          if dist > 1e-6: direction.normalize_ip(); falloff = ((tool_radius - dist) / tool_radius)**2; force = direction * strength * falloff; p.apply_force(force)

    def _get_active_chunks_coords(self):
        visible_rect = self.camera.get_visible_world_rect(); buffer = CHUNK_LOAD_BUFFER * CHUNK_SIZE; start_chunk_x = int((visible_rect.left - buffer) // CHUNK_SIZE); end_chunk_x = int((visible_rect.right + buffer) // CHUNK_SIZE); start_chunk_y = int((visible_rect.top - buffer) // CHUNK_SIZE); end_chunk_y = int((visible_rect.bottom + buffer) // CHUNK_SIZE); active_coords = set((cx, cy) for cx in range(start_chunk_x, end_chunk_x + 1) for cy in range(start_chunk_y, end_chunk_y + 1)); return active_coords

    def _update_chunk_assignments(self):
        self.chunks.clear(); [self.chunks[p.get_chunk_coord()].append(p) for p in self.particles]

    def _calculate_decayed_force(self, base_force, dist_chunks):
        if dist_chunks <= 1.0: return base_force
        elif dist_chunks <= GENERAL_ATTRACTION_MAX_CHUNKS: return base_force * (0.5 ** (dist_chunks - 1.0))
        else: return 0.0

    # REPLACEMENT for _calculate_interactions (Additive, Symmetric, Rule-Based)
    def _calculate_interactions(self, dt):
        """ Calculates forces based on additive pairwise rules with symmetry. """
        num_particles = len(self.particles)
        origin = pygame.math.Vector2(0, 0)

        # --- Apply Green Center Attraction First ---
        for p_a in self.particles: # Iterate through all particles for this effect
            if p_a.type == "green" and p_a.is_movable and self.particle_enable_states.get(p_a.type, True):
                 dist_vec_origin = origin - p_a.pos; dist_sq_origin = dist_vec_origin.length_squared()
                 if dist_sq_origin > 1e-6:
                      dist_origin = math.sqrt(dist_sq_origin); dist_chunks_origin = dist_origin / CHUNK_SIZE
                      force_mag = self._calculate_decayed_force(GREEN_CENTER_ATTRACT_FORCE, dist_chunks_origin)
                      if force_mag > 0:
                           center_force = dist_vec_origin.normalize() * force_mag
                           if center_force.length_squared() > MIN_FORCE_THRESHOLD_SQ: p_a.apply_force(center_force)

        # --- Pairwise Interactions ---
        for i in range(num_particles):
            p_a = self.particles[i]
            # Skip walls, disabled for force calculation origin
            if not self.particle_enable_states.get(p_a.type, True) or p_a.type == "wall": continue

            for j in range(i + 1, num_particles):
                p_b = self.particles[j]
                # Skip walls, disabled for force calculation target
                if not self.particle_enable_states.get(p_b.type, True) or p_b.type == "wall": continue

                dist_vec = p_b.pos - p_a.pos; dist_sq = dist_vec.length_squared()
                if dist_sq < 1e-9: continue # Skip overlapping

                dist = math.sqrt(dist_sq); direction_a_to_b = dist_vec / dist; dist_chunks = dist / CHUNK_SIZE

                # Calculate net force contributions for this pair
                net_force_a = pygame.math.Vector2(0,0)
                net_force_b = pygame.math.Vector2(0,0)
                type_a = p_a.type; type_b = p_b.type;
                types = {type_a, type_b}

                # --- Determine Force Magnitude & Type (+1 Attract / -1 Repel) ---
                force_magnitude = 0
                force_type = 0 # 0 = No base interaction from rules below

                # Rule 1: Yellow repels everything
                if "yellow" in types:
                    force_type = -1
                    force_magnitude = YELLOW_REPEL_FORCE
                # Rule 2: Anti attracts everything (except Yellow, Anti)
                elif "anti" in types:
                    if type_a != type_b: # Exclude Anti-Anti
                         force_type = 1
                         force_magnitude = ANTI_UNIVERSAL_ATTRACT
                # Rule 3: Green attracts everything (except Yellow, Anti)
                elif "green" in types:
                     # This now covers G-G, G-R, G-B
                     force_type = 1
                     force_magnitude = GREEN_UNIVERSAL_ATTRACT
                # Rule 4: Red/Blue specifics
                elif types == {"red", "blue"}:
                     force_type = 1
                     force_magnitude = RED_BLUE_ATTRACT
                elif type_a == "red" and type_b == "red":
                     force_type = -1
                     force_magnitude = RED_SELF_REPEL
                elif type_a == "blue" and type_b == "blue":
                     force_type = -1
                     force_magnitude = BLUE_SELF_REPEL

                # --- Calculate Final Pair Force Vector ---
                if force_magnitude > 0 and force_type != 0:
                    decayed_magnitude = self._calculate_decayed_force(force_magnitude, dist_chunks)
                    if decayed_magnitude > 0:
                        base_force_vector = direction_a_to_b * decayed_magnitude
                        # Apply symmetrically based on force type
                        net_force_a = base_force_vector * force_type
                        net_force_b = -base_force_vector * force_type

                        # --- Apply Pair Forces (Threshold and Limit) ---
                        if p_a.is_movable:
                            if net_force_a.length_squared() > MIN_FORCE_THRESHOLD_SQ:
                                if net_force_a.length_squared() > MAX_INTERACTION_FORCE**2: net_force_a.scale_to_length(MAX_INTERACTION_FORCE)
                                p_a.apply_force(net_force_a) # Add this pair's force to A's total acc

                        if p_b.is_movable:
                            if net_force_b.length_squared() > MIN_FORCE_THRESHOLD_SQ:
                                if net_force_b.length_squared() > MAX_INTERACTION_FORCE**2: net_force_b.scale_to_length(MAX_INTERACTION_FORCE)
                                p_b.apply_force(net_force_b) # Add this pair's force to B's total acc


    # REPLACEMENT for _handle_collisions
    def _handle_collisions(self):
        """ Detects and resolves collisions: overlap push, elastic exchange, wall bounce, annihilation. """
        particles_to_remove = set(); active_chunk_coords = self._get_active_chunks_coords()
        needs_rebuild = False

        for _ in range(COLLISION_ITERATIONS):
             processed_pairs = set(); needs_another_pass = False
             for chunk_coord in active_chunk_coords:
                 if chunk_coord not in self.chunks or not self.chunks[chunk_coord]: continue
                 particles_in_chunk = self.chunks[chunk_coord]
                 neighbor_coords_to_check = set(); cx, cy = chunk_coord
                 for dx in range(-1, 2):
                      for dy in range(-1, 2):
                           check_coord = (cx + dx, cy + dy)
                           if check_coord in active_chunk_coords: neighbor_coords_to_check.add(check_coord)
                 potential_partners = []
                 for neighbor_coord in neighbor_coords_to_check:
                      if neighbor_coord in self.chunks and neighbor_coord != chunk_coord: potential_partners.extend(self.chunks[neighbor_coord])
                 all_potential_partners = particles_in_chunk + potential_partners

                 for i, p_a in enumerate(particles_in_chunk):
                      if p_a in particles_to_remove: continue
                      for j in range(i + 1, len(all_potential_partners)):
                           p_b = all_potential_partners[j]
                           pair = tuple(sorted((id(p_a), id(p_b))))
                           if pair in processed_pairs or p_b in particles_to_remove: continue

                           dist_vec = p_b.pos - p_a.pos; dist_sq = dist_vec.length_squared()
                           min_dist = p_a.size + p_b.size; min_dist_sq = min_dist * min_dist
                           if 0 < dist_sq < min_dist_sq:
                                processed_pairs.add(pair)
                                is_a_anti = p_a.is_anti_particle; is_b_anti = p_b.is_anti_particle
                                if is_a_anti != is_b_anti:
                                     if not self.particle_lock_states.get(p_a.type, False): particles_to_remove.add(p_a)
                                     if not self.particle_lock_states.get(p_b.type, False): particles_to_remove.add(p_b)
                                     needs_rebuild = True; continue

                                needs_another_pass = True; dist = math.sqrt(dist_sq); overlap = min_dist - dist
                                try: normal = dist_vec.normalize()
                                except ValueError: normal = pygame.math.Vector2(random.uniform(-1,1), random.uniform(-1,1)).normalize()
                                is_a_wall = not p_a.is_movable; is_b_wall = not p_b.is_movable
                                mass_a = p_a.mass if p_a.is_movable else float('inf'); mass_b = p_b.mass if p_b.is_movable else float('inf')
                                total_mass = mass_a + mass_b

                                # Overlap Resolution Push
                                if total_mass > 1e-9 and total_mass != float('inf'): push_a = mass_b / total_mass; push_b = mass_a / total_mass; p_a.pos -= normal * overlap * push_a * COLLISION_PUSH_FACTOR; p_b.pos += normal * overlap * push_b * COLLISION_PUSH_FACTOR
                                elif mass_a != float('inf'): p_a.pos -= normal * overlap
                                elif mass_b != float('inf'): p_b.pos += normal * overlap

                                # Collision Response (Velocity)
                                v_rel = p_a.vel - p_b.vel; vel_along_normal = v_rel.dot(normal)
                                if vel_along_normal < 0: # Moving towards each other
                                    if is_a_wall and not is_b_wall: p_b.vel.reflect_ip(normal); p_b.vel *= WALL_BOUNCE_FACTOR
                                    elif is_b_wall and not is_a_wall: p_a.vel.reflect_ip(normal); p_a.vel *= WALL_BOUNCE_FACTOR # Use same normal for reflect_ip
                                    elif p_a.is_movable and p_b.is_movable and total_mass > 1e-9:
                                        e = PARTICLE_COLLISION_ELASTICITY; j = -(1 + e) * vel_along_normal; j /= (1 / mass_a) + (1 / mass_b)
                                        impulse_vec = normal * j; p_a.vel += impulse_vec / mass_a; p_b.vel -= impulse_vec / mass_b

             if not needs_another_pass: break

        if particles_to_remove:
             self.particles = [p for p in self.particles if p not in particles_to_remove]
             print(f"Annihilated {len(particles_to_remove)} particles.")

        return needs_rebuild


    def update(self, effective_dt):
        if effective_dt <= 0: return
        self._calculate_interactions(effective_dt) # Apply forces to acc
        needs_rebuild_collision = self._handle_collisions() # Resolve positions/velocities, get removal flag
        needs_rebuild_movement = False
        for p in list(self.particles):
            if p in self.particles:
                 if p.update(effective_dt): # Update using acc, move, check chunk change
                    needs_rebuild_movement = True
        if needs_rebuild_collision or needs_rebuild_movement: self._update_chunk_assignments()


    def draw(self):
        self.screen.fill(BLACK); self._draw_chunk_grid()
        active_chunk_coords = self._get_active_chunks_coords()
        for chunk_coord in active_chunk_coords:
             if chunk_coord in self.chunks:
                  for p in self.chunks[chunk_coord]:
                       if self.particle_enable_states.get(p.type, True): p.draw(self.screen, self.camera)
        self._draw_tool_visuals()
        game_state_for_ui = { 'camera_zoom': self.camera.zoom, 'eraser_radius': self.eraser_radius, 'tool_strength': self.tool_strength, 'cursor_chunk_coord': self.cursor_chunk_coord, 'particle_definitions': self.particle_definitions, 'particle_enable_states': self.particle_enable_states, 'particle_lock_states': self.particle_lock_states, 'is_paused': self.is_paused, 'game_speed': self.game_speed_multiplier, }
        if hasattr(self, 'ui') and self.ui: self.ui.draw(self.screen, game_state_for_ui)
        pygame.display.flip()


    def _draw_tool_visuals(self):
         if not hasattr(self, 'ui') or not self.ui: return
         original_clip = self.screen.get_clip()
         if self.ui.play_area_rect: self.screen.set_clip(self.ui.play_area_rect)
         else: return
         mouse_pos = pygame.mouse.get_pos()
         if self.ui.play_area_rect.collidepoint(mouse_pos):
             if self.ui.state == UI_STATE_DRAWING_WALL and self.wall_draw_start_pos:
                  start_screen_pos = self.camera.world_to_screen(self.wall_draw_start_pos); end_screen_pos = mouse_pos
                  try: pygame.draw.line(self.screen, WALL_DRAW_LINE_COLOR, start_screen_pos, end_screen_pos, 3)
                  except TypeError as e: print(f"Warn: Wall line draw error: {e}")
             elif self.ui.selected_tool == 'erase': screen_radius = int(self.eraser_radius * self.camera.zoom); pygame.draw.circle(self.screen, ERASER_COLOR, mouse_pos, screen_radius, 1) if screen_radius >= 1 else None
             elif self.ui.selected_tool in ['attract', 'repel']: screen_radius = int(TOOL_RADIUS * self.camera.zoom); color = BLUE if self.ui.selected_tool == 'attract' else RED; pygame.draw.circle(self.screen, color, mouse_pos, screen_radius, 1) if screen_radius >= 1 else None
         self.screen.set_clip(original_clip)


    def _draw_chunk_grid(self):
        if not hasattr(self, 'ui') or not self.ui.play_area_rect: return
        grid_color = DARK_GREY; visible_world_rect = self.camera.get_visible_world_rect(); start_x = math.floor(visible_world_rect.left / CHUNK_SIZE) * CHUNK_SIZE; end_x = math.ceil(visible_world_rect.right / CHUNK_SIZE) * CHUNK_SIZE; start_y = math.floor(visible_world_rect.top / CHUNK_SIZE) * CHUNK_SIZE; end_y = math.ceil(visible_world_rect.bottom / CHUNK_SIZE) * CHUNK_SIZE; original_clip = self.screen.get_clip(); self.screen.set_clip(self.ui.play_area_rect); step = CHUNK_SIZE
        world_coord = start_x;
        while world_coord < end_x: p1 = self.camera.world_to_screen((world_coord, visible_world_rect.top)); p2 = self.camera.world_to_screen((world_coord, visible_world_rect.bottom)); pygame.draw.line(self.screen, grid_color, p1, p2, 1); world_coord += step
        world_coord = start_y;
        while world_coord < end_y: p1 = self.camera.world_to_screen((visible_world_rect.left, world_coord)); p2 = self.camera.world_to_screen((visible_world_rect.right, world_coord)); pygame.draw.line(self.screen, grid_color, p1, p2, 1); world_coord += step
        self.screen.set_clip(original_clip)


    def _resize_screen(self, w, h):
        min_w, min_h = 400, 300; w, h = max(w, min_w), max(h, min_h)
        if not self.fullscreen: pass
        try:
            self.screen = pygame.display.set_mode((w, h), self.screen_flags)
            if hasattr(self, 'camera') and self.camera: self.camera.update_screen_size(w, h)
            if hasattr(self, 'ui') and self.ui: self.ui.update_dimensions(w, h)
            print(f"Resized {w}x{h} FS:{self.fullscreen}")
        except pygame.error as e: print(f"Resize Error: {e}")

    # ADD this new method
    def reset_simulation(self):
        """ Clears all particles and resets relevant game state. """
        print("Resetting simulation...")
        self.particles.clear()
        self.chunks.clear()
        self.wall_draw_start_pos = None
        # Optional: Reset camera/zoom?
        # self.camera.camera_offset = pygame.math.Vector2(0, 0)
        # self.camera.zoom = 1.0
        if hasattr(self, 'ui') and self.ui: # Reset UI state if it exists
             self.ui.state = UI_STATE_NORMAL
             self.ui.selected_tool = "place"
             self.ui.selected_particle_type = "red"
        print("Simulation reset.")

# --- Main Execution ---
if __name__ == '__main__':
    try:
        game = Game()
        if game.running: game.run() # Check if init succeeded
    except Exception as e:
        print("\n--- AN ERROR OCCURRED ---")
        import traceback
        traceback.print_exc()
        pygame.quit()
        input("Press Enter to exit...")
        sys.exit()