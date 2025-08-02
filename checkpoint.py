# checkpoint.py
import pygame
import random
import math
import os
import sys
from config import WIDTH, HEIGHT  


TARGET_BEACON_WIDTH = 100  
TARGET_BEACON_HEIGHT = 120  
BEACON_FLOATING_OFFSET_Y = 8  


class Beacon(pygame.sprite.Sprite):
    def __init__(self, screen_spawn_x, terrain_obj):
        super().__init__()
        self.terrain = terrain_obj

        self.is_collected = False
        self.collection_animation_active = False

        self.animation_phase = "idle"
        self.animation_timer_start = 0
        self.phase_duration = 0

        self.beacon_fly_speed = 35
        self.beacon_pulse_magnitude = 0

        self.ground_shockwave_radius = 0
        self.max_ground_shockwave_radius = 0
        self.ground_shockwave_alpha = 0
        self.intake_particles = []

        self.ignition_blast_radius = 0
        self.ignition_blast_alpha = 0
        self.ignition_colors = [(220, 255, 255), (200, 240, 255), (240, 255, 240)]

        self.ray_origin_y_world = 0
        self.ray_current_top_y_world = 0
        self.ray_max_reach_y_world = -HEIGHT * 1.0
        self.ray_speed = 90

        self.ray_core_color = (220, 255, 220)
        self.ray_primary_beam_color = (100, 255, 100)
        self.ray_aura_color = (50, 200, 50)

        self.ray_core_thickness = 4
        self.ray_primary_thickness = 12

        self.current_ray_alpha = 0
        self.max_ray_core_alpha = 255

        self.ray_fade_speed = 25
        self.ray_tip_flare_radius = 0

        self.ray_tip_sparkles = []
        self.max_ray_tip_sparkles = 10
        self.ray_tip_sparkle_spawn_chance = 0.6

        self.activation_elements = []
        self.activation_duration_ms = 350
        self.activation_colors = [(100, 255, 100), (150, 255, 150), (200, 255, 200)]

        self.trailing_exhaust_particles = []
        self.max_trailing_exhaust = 30
        self.last_exhaust_spawn = 0
        self.trailing_particle_spawn_interval = 30
        self.trailing_particle_color_start = (100, 255, 100)
        self.trailing_particle_color_end = (50, 200, 50)

        self.sky_burst_elements = []
        self.sky_burst_active = False

        self.image_red_asset_orig = None
        self.image_green_asset_orig = None

        try:
            main_script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            path_red = os.path.join(main_script_dir, "assets", "BeconRed.png")
            path_green = os.path.join(main_script_dir, "assets", "BeconGreen.png")

            if os.path.exists(path_red):
                self.image_red_asset_orig = pygame.image.load(path_red).convert_alpha()
            else:
                print(f"ERROR: BeconRed.png not found at {path_red}")
                self.image_red_asset_orig = pygame.Surface((28, 56), pygame.SRCALPHA)
                self.image_red_asset_orig.fill((255, 0, 0, 200))

            if os.path.exists(path_green):
                self.image_green_asset_orig = pygame.image.load(path_green).convert_alpha()
            else:
                print(f"ERROR: BeconGreen.png not found at {path_green}")
                self.image_green_asset_orig = pygame.Surface((28, 56), pygame.SRCALPHA)
                self.image_green_asset_orig.fill((0, 255, 0, 200))
        except Exception as e:
            print(f"Error loading beacon images: {e}")
            if not self.image_red_asset_orig:
                self.image_red_asset_orig = pygame.Surface((28, 56), pygame.SRCALPHA)
                self.image_red_asset_orig.fill((255, 0, 0, 200))
            if not self.image_green_asset_orig:
                self.image_green_asset_orig = pygame.Surface((28, 56), pygame.SRCALPHA)
                self.image_green_asset_orig.fill((0, 255, 0, 200))

        self.image_red_asset = pygame.transform.smoothscale(self.image_red_asset_orig,
                                                            (TARGET_BEACON_WIDTH, TARGET_BEACON_HEIGHT))
        self.image_green_asset = pygame.transform.smoothscale(self.image_green_asset_orig,
                                                              (TARGET_BEACON_WIDTH, TARGET_BEACON_HEIGHT))

        self.image = self.image_red_asset
        self.width, self.height = self.image.get_size()
        self.rect = self.image.get_rect()

        self.max_ground_shockwave_radius = self.width * 4

        initial_terrain_y = self.terrain.height_at(screen_spawn_x)
        self.rect.midbottom = (screen_spawn_x, initial_terrain_y - BEACON_FLOATING_OFFSET_Y)
        self.world_x = float(self.rect.centerx)  
        self.screen_x_on_collect = 0  
        self.world_y = float(self.rect.centery)

    def _set_phase(self, new_phase, duration_ms):
        self.animation_phase = new_phase
        self.animation_timer_start = pygame.time.get_ticks()
        self.phase_duration = duration_ms

    def _get_phase_progress(self):
        if self.phase_duration <= 0: return 1.0
        elapsed = pygame.time.get_ticks() - self.animation_timer_start
        return min(1.0, max(0.0, elapsed / self.phase_duration))

    def collect(self):
        if not self.is_collected:
            self.is_collected = True
            self.collection_animation_active = True

            
            self.screen_x_on_collect = self.rect.x

            old_midbottom = self.rect.midbottom
            self.image = self.image_green_asset
            self.rect = self.image.get_rect(midbottom=old_midbottom)

            self._set_phase("charging", self.activation_duration_ms)
            self.ray_origin_y_world = self.world_y
            self.ray_current_top_y_world = self.world_y
            self.current_ray_alpha = 0
            self.last_trailing_exhaust_spawn = pygame.time.get_ticks()
            self._generate_activation_elements()
            return True
        return False

    def _generate_activation_elements(self):
        self.activation_elements = []
        num_rings = 3
        for i in range(num_rings):
            self.activation_elements.append(
                {'type': 'ring', 'max_radius': self.width * (1.5 + i * 0.8), 'current_radius': 0, 'alpha': 255,
                 'thickness': random.randint(2, 4), 'color': random.choice(self.activation_colors),
                 'rotation_speed': random.uniform(-2, 2) * (1 if i % 2 == 0 else -1),
                 'current_angle': random.uniform(0, 360), 'expand_progress': 0, 'delay_factor': i * 0.15})

    def _update_activation_effect(self, time_delta_seconds):
        phase_progress = self._get_phase_progress()
        if phase_progress >= 1.0: self.activation_elements = []; self._set_phase("ignition_blast", 150); return
        for element in self.activation_elements:
            element_progress = max(0, min(1, (phase_progress - element['delay_factor']) / (
                    1.0 - element['delay_factor']) if (1.0 - element['delay_factor']) > 0 else 1.0))
            if element_progress > 0: element['current_radius'] = element['max_radius'] * math.sin(
                element_progress * math.pi * 0.5); element['alpha'] = 255 * (1.0 - element_progress ** 2); element[
                'current_angle'] = (element['current_angle'] + element['rotation_speed'] * (
                    60 * time_delta_seconds)) % 360

    def _update_ignition_blast(self, time_delta_seconds, progress):
        self.ignition_blast_radius = (self.width * 3.5) * math.sin(progress * math.pi)
        self.ignition_blast_alpha = 255 * math.sin(progress * math.pi)
        self.beacon_pulse_magnitude = 1.0

    def _simple_particle_update(self, particle_list, time_delta_seconds, time_factor, gravity=0.1, alpha_decay_rate=5,
                                fixed_x_screen=None):
        active_particles = []
        for p in particle_list:
            p['y_world'] += p['vy'] * time_factor
            p['vy'] += gravity * time_factor
            if 'vx' in p:
                if fixed_x_screen is None:  
                    p['x_offset'] += p['vx'] * time_factor
                p['vx'] *= 0.98

            p['life'] -= time_delta_seconds
            p['alpha'] -= alpha_decay_rate * time_factor
            if p['life'] > 0 and p['alpha'] > 10:
                active_particles.append(p)
        return active_particles

    def _update_ray_and_associated_particles(self, time_delta_seconds):
        time_factor = 60 * time_delta_seconds
        self.ray_current_top_y_world -= self.ray_speed * time_factor

        self.world_y -= self.beacon_fly_speed * time_factor


        self.beacon_pulse_magnitude = (math.sin(pygame.time.get_ticks() * 0.025) + 1) / 2
        self.ray_tip_flare_radius = (self.ray_core_thickness * 2.0) * (
                1 + 0.8 * math.sin(pygame.time.get_ticks() * 0.06))

        if len(self.ray_tip_sparkles) < self.max_ray_tip_sparkles and random.random() < self.ray_tip_sparkle_spawn_chance:
            self.ray_tip_sparkles.append(
                {'x_offset': random.uniform(-self.ray_core_thickness * 0.7, self.ray_core_thickness * 0.7),
                 'y_world': self.ray_current_top_y_world + random.uniform(-25, 15), 
                 'vy': -random.uniform(self.ray_speed * 0.15, self.ray_speed * 0.4),
                 'life': random.uniform(0.2, 0.45), 'alpha': random.randint(230, 255), 'size': random.randint(2, 5)})
        
        self.ray_tip_sparkles = self._simple_particle_update(self.ray_tip_sparkles, time_delta_seconds, time_factor,
                                                             gravity=0.15, alpha_decay_rate=12, fixed_x_screen=True)

        current_ticks = pygame.time.get_ticks()
        if current_ticks - self.last_exhaust_spawn > self.trailing_particle_spawn_interval and len(
                self.trailing_exhaust_particles) < self.max_trailing_exhaust:
            self.last_exhaust_spawn = current_ticks
            spawn_y_exhaust = self.world_y + self.height * 0.5
            self.trailing_exhaust_particles.append({'x_offset': random.uniform(-self.width * 0.2, self.width * 0.2),
                                                    'y_world': spawn_y_exhaust, 
                                                    'vy': self.beacon_fly_speed * random.uniform(0.1,
                                                                                                 0.4) * 0.15 - random.uniform(
                                                        0.8, 2.0),
                                                    'vx': random.uniform(-1.0, 1.0), 'life': random.uniform(0.6, 1.2),
                                                    'alpha': random.randint(150, 220), 'size': random.randint(3, 6)})
        
        self.trailing_exhaust_particles = self._simple_particle_update(self.trailing_exhaust_particles,
                                                                       time_delta_seconds, time_factor, gravity=-0.03,
                                                                       alpha_decay_rate=2.5, fixed_x_screen=True)

    def _update_sky_burst(self, time_delta_seconds, progress):
        if not self.sky_burst_active:
            self.sky_burst_active = True
            self.sky_burst_elements = []
            num_burst_rays = 12
            for i in range(num_burst_rays):
                angle = (360 / num_burst_rays) * i + random.uniform(-10, 10)
                self.sky_burst_elements.append(
                    {'angle': angle, 'length': 0, 'max_length': random.uniform(self.width * 2.5, self.width * 4.5),
                     'alpha': 255, 'thickness': random.randint(3, 6),
                     'color': random.choice([(200, 255, 200), (220, 255, 220), (240, 255, 240)])})
        for ray_el in self.sky_burst_elements:
            ray_el['length'] = ray_el['max_length'] * math.sin(progress * math.pi)
            ray_el['alpha'] = 255 * (1.0 - progress ** 0.5)

    def update(self, dx_world_scroll, time_delta_seconds):
        if time_delta_seconds <= 0: time_delta_seconds = 1.0 / 60.0

        if not self.collection_animation_active:
            
            self.world_x -= dx_world_scroll
            self.rect.centerx = int(self.world_x)

            if 0 <= self.rect.centerx < WIDTH:
                mid_bottom_y_terrain = self.terrain.height_at(self.rect.centerx)
                self.world_y = (mid_bottom_y_terrain - BEACON_FLOATING_OFFSET_Y) - self.height / 2.0
                self.rect.centery = int(self.world_y)

            if self.rect.right < 0 and not self.is_collected: self.kill()
        else:
            
            self.rect.x = self.screen_x_on_collect
         

            progress = self._get_phase_progress()

            if self.animation_phase == "charging":
                self._update_activation_effect(time_delta_seconds)
                self.world_y -= self.beacon_fly_speed * 0.05 * (60 * time_delta_seconds)
            elif self.animation_phase == "ignition_blast":
                self._update_ignition_blast(time_delta_seconds, progress)
                if progress >= 1.0:
                    self._set_phase("ray_shooting", 800)
                    self.current_ray_alpha = self.max_ray_core_alpha
            elif self.animation_phase == "ray_shooting":
                self._update_ray_and_associated_particles(time_delta_seconds)
                if self.ray_current_top_y_world <= self.ray_max_reach_y_world or progress >= 1.0:
                    self._set_phase("sky_connection_burst", 250)
            elif self.animation_phase == "sky_connection_burst":
                self._update_sky_burst(time_delta_seconds, progress)
                self.current_ray_alpha = self.max_ray_core_alpha * (1.0 - progress * 0.9)
                self.world_y -= self.beacon_fly_speed * 0.4 * (60 * time_delta_seconds)
            elif self.animation_phase == "fading_out":
                self.current_ray_alpha = max(0, self.current_ray_alpha - self.ray_fade_speed * (
                        60 * time_delta_seconds) * 0.35)
                self.world_y -= self.beacon_fly_speed * 0.2 * (60 * time_delta_seconds)
                self.ray_tip_sparkles = self._simple_particle_update(self.ray_tip_sparkles, time_delta_seconds,
                                                                     (60 * time_delta_seconds), gravity=0.15,
                                                                     alpha_decay_rate=15, fixed_x_screen=True)
                self.trailing_exhaust_particles = self._simple_particle_update(self.trailing_exhaust_particles,
                                                                               time_delta_seconds,
                                                                               (60 * time_delta_seconds), gravity=-0.03,
                                                                               alpha_decay_rate=3, fixed_x_screen=True)
                if progress >= 1.0 and self.current_ray_alpha <= 0 and \
                        not self.ray_tip_sparkles and not self.trailing_exhaust_particles and \
                        (not self.sky_burst_active or not self.sky_burst_elements):
                    self.collection_animation_active = False
                    self.kill()

      
            self.rect.centery = int(self.world_y)
            if self.rect.bottom < -self.height * 5: self.kill()

    def draw_animated_effects(self, surface, camera_y_offset):
        if not self.collection_animation_active: return
        current_ticks = pygame.time.get_ticks()

      
      
        draw_x_effects_center = self.rect.centerx  
        draw_y_beacon_current_center = self.world_y

        if self.animation_phase == "charging":
            for el in self.activation_elements:
                if el['alpha'] > 10:
                    ring_color_with_alpha = (*el['color'], int(el['alpha']))
                    if el['current_radius'] > 1:
                        try:
                            pygame.draw.circle(surface, ring_color_with_alpha,
                                               (int(draw_x_effects_center),
                                                int(draw_y_beacon_current_center - camera_y_offset)),
                                               int(el['current_radius']), el['thickness'])
                        except TypeError:
                            pass
            if self.ground_shockwave_alpha > 10 and self.ground_shockwave_radius > 1:
                shock_color = (180, 220, 255, int(self.ground_shockwave_alpha))
                try:
                  
                    pygame.draw.circle(surface, shock_color,
                                       (int(self.screen_x_on_collect + self.width / 2),
                                        int(self.ray_origin_y_world - camera_y_offset)),
                                       int(self.ground_shockwave_radius), random.randint(2, 4))
                except TypeError:
                    pass
            for p in self.intake_particles:
                if p['alpha'] > 10:
                 
                    p_x = draw_x_effects_center + p['x_off']
                    p_y = (draw_y_beacon_current_center + p['y_off']) - camera_y_offset
                    try:
                        pygame.draw.line(surface, (*p['color'], int(p['alpha'])), (int(p_x), int(p_y)),
                                         (int(draw_x_effects_center),
                                          int(draw_y_beacon_current_center - camera_y_offset)), p['size'] // 2 + 1)
                    except TypeError:
                        pass

        if self.animation_phase == "ignition_blast" and self.ignition_blast_alpha > 10:
            ignition_center_y = draw_y_beacon_current_center - self.height * 0.4 - camera_y_offset
            for i in range(random.randint(4, 7)):
                radius = self.ignition_blast_radius * (1.0 - i * 0.15) * random.uniform(0.8, 1.2)
                alpha = self.ignition_blast_alpha * (1.0 - i * 0.20) * random.uniform(0.7, 1.0)
                if radius > 1 and alpha > 10:
                    try:
                        pygame.draw.circle(surface, (*random.choice(self.ignition_colors), int(alpha)),
                                           (int(draw_x_effects_center + random.uniform(-5, 5)),
                                            int(ignition_center_y + random.uniform(-5, 5))), int(radius))
                    except TypeError:
                        pass

        effective_ray_alpha = self.current_ray_alpha
        if effective_ray_alpha > 5 and \
                (self.animation_phase == "ray_shooting" or \
                 self.animation_phase == "sky_connection_burst" or \
                 (self.animation_phase == "fading_out" and effective_ray_alpha > 5)):
            ray_tip_y_screen = self.ray_current_top_y_world - camera_y_offset
            ray_base_y_screen = self.ray_origin_y_world - camera_y_offset
            pulse_main = (math.sin(current_ticks * 0.025) + 1) / 2
            pulse_secondary = (math.sin(current_ticks * 0.045 + math.pi / 1.5) + 1) / 2
            if effective_ray_alpha > 0:
                beam_alpha_val = int(effective_ray_alpha * (0.6 + 0.4 * pulse_secondary))
                beam_thick = int(self.ray_primary_thickness * (0.65 + 0.35 * pulse_main))
                if beam_alpha_val > 10 and beam_thick > 1 and ray_tip_y_screen < ray_base_y_screen:
                    try: 
                        pygame.draw.line(surface, (*self.ray_primary_beam_color, beam_alpha_val),
                                         (draw_x_effects_center, ray_base_y_screen),
                                         (draw_x_effects_center, ray_tip_y_screen), beam_thick)
                    except TypeError:
                        pass
                core_alpha_val_main = int(effective_ray_alpha)
                core_thick_main = int(self.ray_core_thickness * (0.8 + 0.2 * pulse_secondary))
                if pulse_main > 0.6 and core_alpha_val_main > 30:
                    pygame.draw.line(surface, (240, 255, 240, int(core_alpha_val_main * 0.95)),
                                     (draw_x_effects_center, ray_base_y_screen),
                                     (draw_x_effects_center, ray_tip_y_screen),
                                     max(1, core_thick_main // 2 + 2))
                if core_alpha_val_main > 10 and core_thick_main > 0 and ray_tip_y_screen < ray_base_y_screen:
                    try:
                        pygame.draw.line(surface, (*self.ray_core_color, core_alpha_val_main),
                                         (draw_x_effects_center, ray_base_y_screen),
                                         (draw_x_effects_center, ray_tip_y_screen), core_thick_main)
                    except TypeError:
                        pass
            if self.animation_phase == "ray_shooting" and self.ray_tip_flare_radius > 1 and effective_ray_alpha > 80:
                tip_flare_alpha_val = int(effective_ray_alpha * 0.7 * ((math.sin(current_ticks * 0.05) + 1) / 2))
                tip_flare_color_val = (220, 255, 230, tip_flare_alpha_val)
                tip_radius = int(self.ray_tip_flare_radius * 1.3)
                try:
                    pygame.draw.circle(surface, tip_flare_color_val,
                                       (int(draw_x_effects_center), int(ray_tip_y_screen)), tip_radius)
                except TypeError:
                    pass

        for s in self.ray_tip_sparkles:
            if s['alpha'] > 10:
                sx = draw_x_effects_center + s['x_offset']
                sy = s['y_world'] - camera_y_offset
                s_color = (230, 255, 230, int(max(0, min(255, s['alpha']))))
                try:
                    pygame.draw.circle(surface, s_color, (int(sx), int(sy)), s['size'])
                except TypeError:
                    pass

        for p in self.trailing_exhaust_particles:
            if p['alpha'] > 10:
                px = draw_x_effects_center + p['x_offset']
                py = p['y_world'] - camera_y_offset
                life_prog = max(0, p['life'] / (1.0 if p['life'] > 0.001 else 1))
                r = max(0, min(255, int(
                    self.trailing_particle_color_start[0] * life_prog + self.trailing_particle_color_end[0] * (
                                1 - life_prog))))
                g = max(0, min(255, int(
                    self.trailing_particle_color_start[1] * life_prog + self.trailing_particle_color_end[1] * (
                                1 - life_prog))))
                b = max(0, min(255, int(
                    self.trailing_particle_color_start[2] * life_prog + self.trailing_particle_color_end[2] * (
                                1 - life_prog))))
                p_alpha = int(max(0, min(255, p['alpha'])))
                p_color = (r, g, b, p_alpha)
                end_px = px + p['vx'] * -2.5
                end_py = py + p['vy'] * -2.5
                try:
                    pygame.draw.line(surface, p_color, (int(px), int(py)), (int(end_px), int(end_py)),
                                     p['size'] // 2 + 1)
                except TypeError:
                    pass

        if self.animation_phase == "sky_connection_burst" or (
                self.animation_phase == "fading_out" and self.sky_burst_active):
            burst_center_x = draw_x_effects_center
            burst_center_y = self.ray_max_reach_y_world - camera_y_offset
            fade_progress_overall = 0
            if self.animation_phase == "fading_out":
                fade_duration_sky_burst = self.phase_duration / 1000.0 if self.phase_duration > 0 else 0.6
                elapsed_sky_burst_fade = (pygame.time.get_ticks() - self.animation_timer_start) / 1000.0
                if fade_duration_sky_burst > 0: fade_progress_overall = min(1.0,
                                                                            elapsed_sky_burst_fade / fade_duration_sky_burst)
            for ray_el in self.sky_burst_elements:
                current_alpha = ray_el['alpha']
                if self.animation_phase == "fading_out": current_alpha *= (1.0 - fade_progress_overall)
                current_length = ray_el['length'] * (1.0 - fade_progress_overall * 0.3)
                if current_alpha > 10 and current_length > 1:
                    angle_rad = math.radians(ray_el['angle'])
                    end_x = burst_center_x + current_length * math.cos(angle_rad)
                    end_y = burst_center_y + current_length * math.sin(angle_rad)
                    try:
                        pygame.draw.line(surface, (*ray_el['color'], int(current_alpha)),
                                         (int(burst_center_x), int(burst_center_y)), (int(end_x), int(end_y)),
                                         ray_el['thickness'])
                    except TypeError:
                        pass
            if self.animation_phase == "fading_out" and fade_progress_overall >= 1.0: self.sky_burst_active = False

    def draw(self, surface, camera_y_offset):
        if self.alive():
         
            draw_rect = self.image.get_rect()  
            if self.collection_animation_active:
                draw_rect.topleft = (self.screen_x_on_collect, self.rect.top)  
            else:
                draw_rect.topleft = (self.rect.left, self.rect.top) 


            final_draw_rect_y = draw_rect.top - camera_y_offset

            surface.blit(self.image, (draw_rect.left, final_draw_rect_y))

            if self.collection_animation_active:
                self.draw_animated_effects(surface, camera_y_offset)