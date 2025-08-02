# terrain.py
import pygame
import math
import random
import os
import sys
from config import (WIDTH, HEIGHT, CHUNK, GROUND_Y, DOWNHILL_SLOPE_FACTOR,
                    FINAL_RAMP_HEIGHT_RISE, TREE_LINE_WORLD_Y_OFFSET)
import game_state as gs
import config 

LEVEL2_CEILING_Y = 60.0 
DEFAULT_TERRAIN_COLOR = (235, 235, 240)
DEFAULT_CLUMP_COLOR_MIN = 248
DEFAULT_CLUMP_COLOR_MAX = 255



def lerp_color(color1, color2, t):
    t = max(0.0, min(1.0, t))
    r = int(color1[0] * (1.0 - t) + color2[0] * t)
    g = int(color1[1] * (1.0 - t) + color2[1] * t)
    b = int(color1[2] * (1.0 - t) + color2[2] * t)
    return (r, g, b)


class Terrain:
    def __init__(self, is_tutorial=False):
        self.scroll_fractional_offset = 0.0
        self.world_start_chunk_index = 0
        self.num_height_points = WIDTH // CHUNK + 3 
        self.is_tutorial_terrain = is_tutorial
       
        self.heights = [self._sample(float(i)) for i in range(self.num_height_points)] 
        self.lava_surface_particles = []
        self.rock_texture_noise_seed = random.randint(0, 10000)

        self.l2_ground_smoke_particles = []
        self.last_l2_smoke_spawn_time = 0

        self.l2_lava_smoke_particles = []
        self.last_l2_lava_smoke_spawn_time = 0

    def _sample(self, world_chunk_idx_float): 
        if self.is_tutorial_terrain:
            return float(GROUND_Y) 
        
        return float(GROUND_Y + world_chunk_idx_float * DOWNHILL_SLOPE_FACTOR + \
                   50.0 * math.sin(world_chunk_idx_float * 0.035) + \
                   25.0 * math.sin(world_chunk_idx_float * 0.09))

    def update(self, dx_pixels_scrolled):
        if self.is_tutorial_terrain:
            return

        current_time_ms = pygame.time.get_ticks()
       
        time_delta_seconds = 1.0 / config.FPS if config.FPS > 0 else 1.0/60.0


        self.scroll_fractional_offset += dx_pixels_scrolled / float(CHUNK) 
        while self.scroll_fractional_offset >= 1.0:
            self.heights.pop(0)
            self.world_start_chunk_index += 1
            new_point_world_index = float(self.world_start_chunk_index + len(self.heights)) 
            self.heights.append(self._sample(new_point_world_index)) 
            self.scroll_fractional_offset -= 1.0

      
        if gs.is_level_2_simple_mode and config.LAVA_SURFACE_PARTICLES_ENABLED:
            active_particles = []
            if len(self.lava_surface_particles) < config.LAVA_MAX_SURFACE_PARTICLES:
                for _ in range(config.LAVA_PARTICLES_PER_FRAME_SPAWN):
                    spawn_screen_x = random.uniform(float(CHUNK), float(WIDTH - CHUNK))
                    y_platform_top_world = self.height_at(spawn_screen_x) 
                    base_lava_y_world = y_platform_top_world + config.L2_BLACK_PLATFORM_THICKNESS + config.LAVA_START_OFFSET_BELOW_PLATFORM

                    spawn_world_y = base_lava_y_world + random.uniform(-config.LAVA_WAVE_AMPLITUDE / 2.0,
                                                                       config.LAVA_WAVE_AMPLITUDE / 2.0)
                    life = random.uniform(config.LAVA_SURFACE_PARTICLE_LIFE_MS[0],
                                          config.LAVA_SURFACE_PARTICLE_LIFE_MS[1])
                    start_size = random.uniform(config.LAVA_SURFACE_PARTICLE_SIZE_RANGE[0],
                                                config.LAVA_SURFACE_PARTICLE_SIZE_RANGE[1])
                    self.lava_surface_particles.append({
                        'x': spawn_screen_x, 'y': spawn_world_y,
                        'vy': random.uniform(config.LAVA_SURFACE_PARTICLE_RISE_SPEED_MIN,
                                             config.LAVA_SURFACE_PARTICLE_RISE_SPEED_MAX),
                        'life_ms': life, 'max_life_ms': life, 'start_size': start_size, 'size': start_size,
                        'current_color': config.LAVA_SURFACE_PARTICLE_COLOR_START,
                        'start_color': config.LAVA_SURFACE_PARTICLE_COLOR_START,
                        'end_color': config.LAVA_SURFACE_PARTICLE_COLOR_END, 'alpha': 255.0
                    })
            for p in self.lava_surface_particles:
                p['x'] -= dx_pixels_scrolled
                p['y'] += p['vy'] * (60.0 * time_delta_seconds) 
                p['life_ms'] -= time_delta_seconds * 1000.0
                if p['life_ms'] > 0 and p['max_life_ms'] > 0:
                    life_ratio = p['life_ms'] / p['max_life_ms']
                    p['alpha'] = 255.0 * (life_ratio ** config.LAVA_SURFACE_PARTICLE_FADE_POWER)
                    r = p['start_color'][0] * life_ratio + p['end_color'][0] * (1.0 - life_ratio)
                    g = p['start_color'][1] * life_ratio + p['end_color'][1] * (1.0 - life_ratio)
                    b = p['start_color'][2] * life_ratio + p['end_color'][2] * (1.0 - life_ratio)
                    p['current_color'] = (int(r), int(g), int(b))
                    p['size'] = p['start_size'] * (life_ratio ** 0.5)
                    if p['alpha'] > 10 and p['size'] >= 1 and \
                       p['x'] > -p['size'] and p['x'] < float(WIDTH) + p['size']:
                        active_particles.append(p)
            self.lava_surface_particles = active_particles

      
        if gs.is_level_2_simple_mode and config.L2_GROUND_SMOKE_ENABLED:
            if current_time_ms - self.last_l2_smoke_spawn_time > config.L2_GROUND_SMOKE_SPAWN_INTERVAL_MS:
                self.last_l2_smoke_spawn_time = current_time_ms
                if len(self.l2_ground_smoke_particles) < config.L2_GROUND_SMOKE_MAX_PARTICLES:
                    for _ in range(config.L2_GROUND_SMOKE_PARTICLES_PER_SPAWN):
                        spawn_screen_x = random.uniform(float(CHUNK), float(WIDTH - CHUNK))
                        spawn_world_y_platform_top = self.height_at(spawn_screen_x) 
                        life = random.uniform(config.L2_GROUND_SMOKE_LIFE_MS[0], config.L2_GROUND_SMOKE_LIFE_MS[1])
                        start_size = random.uniform(config.L2_GROUND_SMOKE_SIZE_RANGE[0], config.L2_GROUND_SMOKE_SIZE_RANGE[1])
                        self.l2_ground_smoke_particles.append({
                            'current_screen_x': spawn_screen_x, 'world_y_start': spawn_world_y_platform_top, 'y_offset': 0.0,
                            'vx_drift': random.uniform(config.L2_GROUND_SMOKE_DRIFT_SPEED_MIN, config.L2_GROUND_SMOKE_DRIFT_SPEED_MAX),
                            'vy_rise': random.uniform(config.L2_GROUND_SMOKE_RISE_SPEED_MIN, config.L2_GROUND_SMOKE_RISE_SPEED_MAX),
                            'life_ms': life, 'max_life_ms': life, 'start_size': start_size, 'size': start_size,
                            'current_color': config.L2_GROUND_SMOKE_COLOR_START[:3],
                            'alpha': float(config.L2_GROUND_SMOKE_COLOR_START[3]),
                            'start_alpha': float(config.L2_GROUND_SMOKE_COLOR_START[3])
                        })
            active_smoke = []
            for p in self.l2_ground_smoke_particles:
                p['current_screen_x'] += p['vx_drift'] * (60.0 * time_delta_seconds)
                p['current_screen_x'] -= dx_pixels_scrolled
                p['y_offset'] += p['vy_rise'] * (60.0 * time_delta_seconds)
                p['life_ms'] -= time_delta_seconds * 1000.0
                if p['life_ms'] > 0 and p['max_life_ms'] > 0:
                    life_ratio = p['life_ms'] / p['max_life_ms']
                    p['alpha'] = p['start_alpha'] * (life_ratio ** config.L2_GROUND_SMOKE_FADE_POWER)
                    p['size'] = p['start_size'] * (0.5 + 0.5 * life_ratio)
                    if p['current_screen_x'] < -p['size'] or p['current_screen_x'] > float(WIDTH) + p['size']: p['alpha'] = 0.0
                    if p['alpha'] > 5 and p['size'] >= 1: active_smoke.append(p)
            self.l2_ground_smoke_particles = active_smoke

     
        if gs.is_level_2_simple_mode and config.L2_LAVA_SMOKE_ENABLED:
            if current_time_ms - self.last_l2_lava_smoke_spawn_time > config.L2_LAVA_SMOKE_SPAWN_INTERVAL_MS:
                self.last_l2_lava_smoke_spawn_time = current_time_ms
                if len(self.l2_lava_smoke_particles) < config.L2_LAVA_SMOKE_MAX_PARTICLES:
                    for _ in range(config.L2_LAVA_SMOKE_PARTICLES_PER_SPAWN):
                        spawn_screen_x = random.uniform(float(CHUNK), float(WIDTH - CHUNK))
                        spawn_world_y_platform_top = self.height_at(spawn_screen_x) 
                        spawn_world_y_lava_approx = (spawn_world_y_platform_top +
                                                     config.L2_BLACK_PLATFORM_THICKNESS +
                                                     config.LAVA_START_OFFSET_BELOW_PLATFORM +
                                                     config.L2_LAVA_SMOKE_Y_OFFSET_FROM_LAVA_SURFACE)
                        life = random.uniform(config.L2_LAVA_SMOKE_LIFE_MS[0], config.L2_LAVA_SMOKE_LIFE_MS[1])
                        start_size = random.uniform(config.L2_LAVA_SMOKE_SIZE_RANGE[0], config.L2_LAVA_SMOKE_SIZE_RANGE[1])
                        self.l2_lava_smoke_particles.append({
                            'current_screen_x': spawn_screen_x, 'world_y_start': spawn_world_y_lava_approx, 'y_offset': 0.0,
                            'vx_drift': random.uniform(config.L2_LAVA_SMOKE_DRIFT_SPEED_MIN, config.L2_LAVA_SMOKE_DRIFT_SPEED_MAX),
                            'vy_rise': random.uniform(config.L2_LAVA_SMOKE_RISE_SPEED_MIN, config.L2_LAVA_SMOKE_RISE_SPEED_MAX),
                            'life_ms': life, 'max_life_ms': life, 'start_size': start_size, 'size': start_size,
                            'current_color': config.L2_LAVA_SMOKE_COLOR_START[:3],
                            'alpha': float(config.L2_LAVA_SMOKE_COLOR_START[3]),
                            'start_alpha': float(config.L2_LAVA_SMOKE_COLOR_START[3])
                        })
            active_lava_smoke = []
            for p in self.l2_lava_smoke_particles:
                p['current_screen_x'] += p['vx_drift'] * (60.0 * time_delta_seconds)
                p['current_screen_x'] -= dx_pixels_scrolled
                p['y_offset'] += p['vy_rise'] * (60.0 * time_delta_seconds)
                p['life_ms'] -= time_delta_seconds * 1000.0
                if p['life_ms'] > 0 and p['max_life_ms'] > 0:
                    life_ratio = p['life_ms'] / p['max_life_ms']
                    p['alpha'] = p['start_alpha'] * (life_ratio ** config.L2_LAVA_SMOKE_FADE_POWER)
                    p['size'] = p['start_size'] * (0.5 + 0.5 * life_ratio)
                    if p['current_screen_x'] < -p['size'] or p['current_screen_x'] > float(WIDTH) + p['size']: p['alpha'] = 0.0
                    if p['alpha'] > 5 and p['size'] >= 1: active_lava_smoke.append(p)
            self.l2_lava_smoke_particles = active_lava_smoke


    def height_at(self, screen_x_pos_float): 
        if self.is_tutorial_terrain: return float(GROUND_Y)
        index_float = (screen_x_pos_float / float(CHUNK)) + self.scroll_fractional_offset
        index0 = math.floor(index_float)
        interpolation_factor = index_float - index0 

        if index0 < 0 or index0 + 1 >= len(self.heights):
            if not self.heights: return float(HEIGHT * 2)
           
            safe_idx = max(0, min(index0, len(self.heights) - 1))
            if index0 < 0 : safe_idx = 0
            if index0 + 1 >= len(self.heights): safe_idx = len(self.heights) -1
            return float(self.heights[safe_idx])

        h0 = self.heights[index0]     
        h1 = self.heights[index0 + 1] 
        return float(h0 * (1.0 - interpolation_factor) + h1 * interpolation_factor)

    def ceiling_height_at(self, screen_x_pos_float): 
        if self.is_tutorial_terrain or not gs.is_level_2_simple_mode: return float(-HEIGHT * 2.0)

        if not math.isfinite(screen_x_pos_float):
          
            return float(-HEIGHT * 2.0)

        index_float = (screen_x_pos_float / float(CHUNK)) + self.scroll_fractional_offset

        if not math.isfinite(index_float):
          
            return float(-HEIGHT * 2.0)

        index0 = math.floor(index_float)
        interpolation_factor = index_float - index0

        if not math.isfinite(interpolation_factor): 
            interpolation_factor = 0.0

        if index0 < 0 or index0 + 1 >= len(self.heights):
            if not self.heights: return float(-HEIGHT * 2.0)
            
            idx_to_use = 0
            if index0 < 0 : idx_to_use = 0
            elif index0 + 1 >= len(self.heights): idx_to_use = len(self.heights) -1
            else: 
                  
                  idx_to_use = index0

            h_bottom_world = self.heights[idx_to_use] 
            world_chunk_idx = float(self.world_start_chunk_index + idx_to_use) 
            base_y_bottom_slope = float(GROUND_Y + world_chunk_idx * DOWNHILL_SLOPE_FACTOR)
            deviation_bottom = h_bottom_world - base_y_bottom_slope
            base_y_top_slope = float(LEVEL2_CEILING_Y + world_chunk_idx * DOWNHILL_SLOPE_FACTOR)
            return float(base_y_top_slope - deviation_bottom)

        h0_bw = self.heights[index0] 
        h1_bw = self.heights[index0 + 1] 
        wc_idx0 = float(self.world_start_chunk_index + index0) 
        wc_idx1 = float(self.world_start_chunk_index + index0 + 1) 

        b_y_bs0 = float(GROUND_Y + wc_idx0 * DOWNHILL_SLOPE_FACTOR)
        dev0 = h0_bw - b_y_bs0
        b_y_ts0 = float(LEVEL2_CEILING_Y + wc_idx0 * DOWNHILL_SLOPE_FACTOR)
        top_w0 = b_y_ts0 - dev0

        b_y_bs1 = float(GROUND_Y + wc_idx1 * DOWNHILL_SLOPE_FACTOR)
        dev1 = h1_bw - b_y_bs1
        b_y_ts1 = float(LEVEL2_CEILING_Y + wc_idx1 * DOWNHILL_SLOPE_FACTOR)
        top_w1 = b_y_ts1 - dev1

        return float(top_w0 * (1.0 - interpolation_factor) + top_w1 * interpolation_factor)


    def _draw_distant_mountains(self, surface, camera_y_offset): 
        pass

    def _draw_clumps_on_surface(self, surface, terrain_points_on_screen,
                                clump_color_min_default, clump_color_max_default,
                                is_ceiling=False): 
        if not terrain_points_on_screen: return
        if gs.is_level_2_simple_mode and is_ceiling: return

        clump_width_base = float(CHUNK) * 0.8
        for i in range(len(terrain_points_on_screen) - 1):
            p1, p2 = terrain_points_on_screen[i], terrain_points_on_screen[i + 1]
            seg_len = abs(p2[0] - p1[0])
            num_clumps = max(1, int(seg_len / (clump_width_base * 0.4)))
            for _ in range(num_clumps):
                t = random.uniform(0.1, 0.9)
                ccx = p1[0] * (1.0 - t) + p2[0] * t
                ccy = p1[1] * (1.0 - t) + p2[1] * t
                if not (0 <= ccx <= float(WIDTH)): continue
                cl_w = random.randint(int(clump_width_base * 0.6), int(clump_width_base * 1.4))
                cl_h = random.randint(int(cl_w * 0.25), int(cl_w * 0.55))
                cl_h, cl_w = max(3, cl_h), max(3, cl_w)
                r_ellipse = pygame.Rect(0, 0, cl_w, cl_h)
                r_ellipse.center = (int(ccx), int(ccy + cl_h * 0.3 * (-1.0 if not is_ceiling else 1.0)))

                cl_c_val = random.randint(clump_color_min_default, clump_color_max_default)
                cl_c = (cl_c_val, cl_c_val, cl_c_val)
                try:
                    pygame.draw.ellipse(surface, cl_c, r_ellipse)
                except TypeError: pass 

    def draw_background_elements(self, surface, camera_y_offset): 
        self._draw_distant_mountains(surface, camera_y_offset)

    def _draw_rocky_texture(self, surface, platform_poly_points, base_color, highlight_color): 
        if not platform_poly_points or len(platform_poly_points) < 3: return
        min_x = min(p[0] for p in platform_poly_points)
        max_x = max(p[0] for p in platform_poly_points)
        min_y = min(p[1] for p in platform_poly_points)
        max_y = max(p[1] for p in platform_poly_points)
        tex_width = max(1, int(max_x - min_x))
        tex_height = max(1, int(max_y - min_y))
        if tex_width < 5 or tex_height < 5: pygame.draw.polygon(surface, base_color, platform_poly_points); return
        texture_surf = pygame.Surface((tex_width, tex_height), pygame.SRCALPHA); texture_surf.fill((0,0,0,0))
        local_poly_points = [(p[0] - min_x, p[1] - min_y) for p in platform_poly_points]
        pygame.draw.polygon(texture_surf, base_color, local_poly_points)
        num_lines = int(tex_width * tex_height / 800.0) 
        seed_offset = int(self.world_start_chunk_index + self.scroll_fractional_offset)
        current_seed = self.rock_texture_noise_seed + seed_offset
        rng = random.Random(current_seed)
        for _ in range(num_lines):
            start_x = rng.uniform(0, tex_width); start_y = rng.uniform(0, tex_height)
            angle = rng.uniform(0, 2.0 * math.pi); length = rng.uniform(float(CHUNK) * 0.5, float(CHUNK) * 2.0)
            end_x = start_x + length * math.cos(angle); end_y = start_y + length * math.sin(angle)
            line_thickness = rng.randint(1, 2)
            try: pygame.draw.line(texture_surf, highlight_color, (start_x, start_y), (end_x, end_y), line_thickness)
            except TypeError: pass
        mask = pygame.Surface((tex_width, tex_height), pygame.SRCALPHA); mask.fill((0,0,0,0))
        pygame.draw.polygon(mask, (255,255,255,255), local_poly_points)
        texture_surf.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(texture_surf, (min_x, min_y))

    def draw_snow_platform_and_clumps(self, surface, camera_y_offset): 
        is_l2_simple = gs.is_level_2_simple_mode
        current_time_ms = pygame.time.get_ticks()
        clump_c_min_default, clump_c_max_default = DEFAULT_CLUMP_COLOR_MIN, DEFAULT_CLUMP_COLOR_MAX

        pts_platform_top_surface_on_screen = []
        csx_initial = -self.scroll_fractional_offset * float(CHUNK) 
        for k_idx in range(len(self.heights)):
            platform_top_y_world = self.heights[k_idx] 
            screen_x = csx_initial + k_idx * float(CHUNK)
            y_on_screen = platform_top_y_world - camera_y_offset
            pts_platform_top_surface_on_screen.append((screen_x, y_on_screen))

        
        if is_l2_simple and len(pts_platform_top_surface_on_screen) >= 2:
            pulse_factor = (math.sin(current_time_ms * config.LAVA_PULSE_SPEED_HZ * 2.0 * math.pi / 1000.0) + 1.0) / 2.0
            lava_overlap_allowance = float(config.LAVA_WAVE_AMPLITUDE + 2)
            lava_visual_top_points_wavy_on_screen = []
            for screen_x, y_platform_top_on_screen in pts_platform_top_surface_on_screen:
                base_lava_y = y_platform_top_on_screen + config.L2_BLACK_PLATFORM_THICKNESS + config.LAVA_START_OFFSET_BELOW_PLATFORM
                wave_offset = float(config.LAVA_WAVE_AMPLITUDE) * math.sin(
                    screen_x * config.LAVA_WAVE_FREQUENCY_SPATIAL + current_time_ms * config.LAVA_WAVE_FREQUENCY_TEMPORAL)
                wavy_lava_y = base_lava_y + wave_offset - lava_overlap_allowance
                lava_visual_top_points_wavy_on_screen.append((screen_x, wavy_lava_y))
            if len(lava_visual_top_points_wavy_on_screen) >= 2:
                num_grad_layers = config.LAVA_NUM_GRADIENT_LAYERS
                layer_thick_individual = (float(config.LAVA_LAYER_THICKNESS) + lava_overlap_allowance) / float(num_grad_layers) if num_grad_layers > 0 else 0
                for layer_idx in range(num_grad_layers):
                    interp_factor = (float(num_grad_layers) - 1.0 - float(layer_idx)) / (float(num_grad_layers) - 1.0) if num_grad_layers > 1 else 1.0
                    r_base = config.LAVA_GRADIENT_COLOR_BOTTOM[0] * interp_factor + config.LAVA_GRADIENT_COLOR_TOP[0] * (1.0 - interp_factor)
                    
                    g_base = config.LAVA_GRADIENT_COLOR_BOTTOM[1] * interp_factor + config.LAVA_GRADIENT_COLOR_TOP[
                        1] * (1 - interp_factor)
                    b_base = config.LAVA_GRADIENT_COLOR_BOTTOM[2] * interp_factor + config.LAVA_GRADIENT_COLOR_TOP[
                        2] * (1 - interp_factor)
                    pulse_intensity_factor = (1 - (layer_idx / num_grad_layers) * 0.7)
                    r_pulse = (pulse_factor - 0.5) * 2 * config.LAVA_PULSE_MAGNITUDE_RGB[0] * pulse_intensity_factor
                    g_pulse = (pulse_factor - 0.5) * 2 * config.LAVA_PULSE_MAGNITUDE_RGB[1] * pulse_intensity_factor
                    b_pulse = (pulse_factor - 0.5) * 2 * config.LAVA_PULSE_MAGNITUDE_RGB[2] * pulse_intensity_factor
                    pulsed_color = (max(0, min(255, int(r_base + r_pulse))),
                                    max(0, min(255, int(g_base + g_pulse))),
                                    max(0, min(255, int(b_base + b_pulse))))
                    lava_layer_poly = []
                    for x, y_wavy_lava_top_overlapped in lava_visual_top_points_wavy_on_screen:
                        lava_layer_poly.append((x, y_wavy_lava_top_overlapped + layer_idx * layer_thick_individual))
                    bottom_edge_temp = []
                    for x, y_wavy_lava_top_overlapped in reversed(lava_visual_top_points_wavy_on_screen):
                        bottom_edge_temp.append(
                            (x, y_wavy_lava_top_overlapped + (layer_idx + 1) * layer_thick_individual))
                    lava_layer_poly.extend(bottom_edge_temp)
                    if len(lava_layer_poly) >= 3:
                        pygame.draw.polygon(surface, pulsed_color, lava_layer_poly)
            if config.LAVA_SURFACE_PARTICLES_ENABLED: 
                for p in self.lava_surface_particles:
                    if p['alpha'] > 10 and p['size'] >= 1:
                        draw_y = p['y'] - camera_y_offset
                        pygame.draw.circle(surface, (*p['current_color'], int(p['alpha'])), (int(p['x']), int(draw_y)), int(p['size']))
            if config.L2_LAVA_SMOKE_ENABLED: 
                for p in self.l2_lava_smoke_particles:
                    if p['alpha'] > 5 and p['size'] >= 1:
                        draw_x, draw_y = p['current_screen_x'], (p['world_y_start'] + p['y_offset']) - camera_y_offset
                        s = int(p['size']); smoke_color_with_alpha = (*config.L2_LAVA_SMOKE_COLOR_START[:3], int(p['alpha']))
                        if s > 0: temp_smoke_surf = pygame.Surface((s*2,s*2),pygame.SRCALPHA); pygame.draw.circle(temp_smoke_surf,smoke_color_with_alpha,(s,s),s); surface.blit(temp_smoke_surf,(draw_x-s,draw_y-s))

        
        if len(pts_platform_top_surface_on_screen) >= 2:
            if is_l2_simple:
                num_strips, platform_thickness = config.LEVEL2_TERRAIN_GRADIENT_STRIPS, float(config.L2_BLACK_PLATFORM_THICKNESS)
                light_color, dark_color = config.LEVEL2_TERRAIN_GRADIENT_LIGHT_BLUE, config.LEVEL2_TERRAIN_COLOR_OVERRIDE
                for j in range(num_strips):
                    t_color = float(j) / (float(num_strips) - 1.0) if num_strips > 1 else 0.5
                    current_strip_color = lerp_color(light_color, dark_color, t_color)
                    strip_poly_points = []
                    for x_coord, y_platform_top_on_screen in pts_platform_top_surface_on_screen:
                        strip_poly_points.append((x_coord, y_platform_top_on_screen + (float(j)/float(num_strips))*platform_thickness))
                    for x_coord, y_platform_top_on_screen in reversed(pts_platform_top_surface_on_screen):
                        strip_poly_points.append((x_coord, y_platform_top_on_screen + (float(j+1)/float(num_strips))*platform_thickness))
                    if len(strip_poly_points) >= 3: pygame.draw.polygon(surface, current_strip_color, strip_poly_points)
            else:
                platform_poly_for_drawing = list(pts_platform_top_surface_on_screen)
                current_platform_color = DEFAULT_TERRAIN_COLOR
                bottom_fill_y = float(HEIGHT + 100)
                platform_poly_for_drawing.append((pts_platform_top_surface_on_screen[-1][0], bottom_fill_y))
                platform_poly_for_drawing.append((pts_platform_top_surface_on_screen[0][0], bottom_fill_y))
                pygame.draw.polygon(surface, current_platform_color, platform_poly_for_drawing)

        if is_l2_simple and config.L2_GROUND_SMOKE_ENABLED: 
            for p in self.l2_ground_smoke_particles:
                if p['alpha'] > 5 and p['size'] >= 1:
                    draw_x, draw_y = p['current_screen_x'], (p['world_y_start'] + p['y_offset']) - camera_y_offset
                    s = int(p['size']); smoke_color_with_alpha = (*p['current_color'], int(p['alpha']))
                    if s > 0: temp_smoke_surf = pygame.Surface((s*2,s*2),pygame.SRCALPHA); pygame.draw.circle(temp_smoke_surf,smoke_color_with_alpha,(s,s),s); surface.blit(temp_smoke_surf,(draw_x-s,draw_y-s))

        self._draw_clumps_on_surface(surface, pts_platform_top_surface_on_screen,
                                     clump_c_min_default, clump_c_max_default, False)

        
        if is_l2_simple:
            pts_ceiling_bottom_surface_on_screen = []
            csx_initial_ceil = -self.scroll_fractional_offset * float(CHUNK)
            for k_idx in range(len(self.heights)):
                screen_x_for_ceil = csx_initial_ceil + k_idx * float(CHUNK)
                ceiling_bottom_y_world = self.ceiling_height_at(screen_x_for_ceil)
                y_on_screen = ceiling_bottom_y_world - camera_y_offset
                pts_ceiling_bottom_surface_on_screen.append((screen_x_for_ceil, y_on_screen))

            if len(pts_ceiling_bottom_surface_on_screen) >= 2:
                num_strips, ceiling_thickness = config.LEVEL2_TERRAIN_GRADIENT_STRIPS, float(config.L2_BLACK_PLATFORM_THICKNESS)
                start_color, end_color = config.LEVEL2_TERRAIN_GRADIENT_LIGHT_BLUE, config.LEVEL2_TERRAIN_COLOR_OVERRIDE
                for j in range(num_strips):
                    t_color = float(j) / (float(num_strips) - 1.0) if num_strips > 1 else 0.0
                    current_strip_color = lerp_color(start_color, end_color, t_color)
                    strip_poly = []
                    for x,y_ceil_bot in pts_ceiling_bottom_surface_on_screen: strip_poly.append((x, y_ceil_bot - (float(j)/float(num_strips))*ceiling_thickness))
                    for x,y_ceil_bot in reversed(pts_ceiling_bottom_surface_on_screen): strip_poly.append((x, y_ceil_bot - (float(j+1)/float(num_strips))*ceiling_thickness))
                    if len(strip_poly) >= 3: pygame.draw.polygon(surface, current_strip_color, strip_poly)

                top_grad_pts = [(x, y_ceil_bot - ceiling_thickness) for x, y_ceil_bot in pts_ceiling_bottom_surface_on_screen]
                if len(top_grad_pts) >= 2: 
                    fill_poly_top = list(top_grad_pts); fill_poly_top.append((top_grad_pts[-1][0], -10.0)); fill_poly_top.append((top_grad_pts[0][0], -10.0))
                    if len(fill_poly_top) >= 3: pygame.draw.polygon(surface, config.LEVEL2_TERRAIN_COLOR_OVERRIDE, fill_poly_top)
            
            
                if config.L2_ROPE_LIGHTS_ENABLED:
                    time_for_pulse_rope = current_time_ms * config.L2_ROPE_LIGHT_PULSE_SPEED_HZ * 2 * math.pi / 1000.0
                    time_for_flicker_rope = current_time_ms * config.L2_ROPE_LIGHT_FLICKER_SPEED_HZ * 2 * math.pi / 1000.0
                    time_for_sway_rope = current_time_ms * config.L2_ROPE_LIGHT_SWAY_SPEED_HZ * 2 * math.pi / 1000.0
                    for i in range(len(pts_ceiling_bottom_surface_on_screen) - 1):
                        p1 = pts_ceiling_bottom_surface_on_screen[i]
                        p2 = pts_ceiling_bottom_surface_on_screen[i + 1]
                        dx_seg, dy_seg = p2[0] - p1[0], p2[1] - p1[1]
                        segment_length = math.hypot(dx_seg, dy_seg)
                        if segment_length < 1: continue
                        ux_seg, uy_seg = dx_seg / segment_length, dy_seg / segment_length
                        effective_spacing = max(1.0, float(config.L2_ROPE_LIGHT_SPACING))
                        j_light_index = 0
                        current_offset_along_segment = 0.0
                        epsilon = 0.01
                        while current_offset_along_segment <= segment_length + epsilon:
                            dist_along_segment = current_offset_along_segment
                            if j_light_index > 0 and (segment_length - dist_along_segment) < (
                                    effective_spacing * 0.5) and (segment_length - dist_along_segment) > -epsilon:
                                dist_along_segment = segment_length
                            light_x_on_edge_anchor = p1[0] + dist_along_segment * ux_seg
                            light_y_on_edge = p1[1] + dist_along_segment * uy_seg
                            light_unique_id_rope = (i * 10000) + j_light_index
                            swayed_light_x = light_x_on_edge_anchor
                            if config.L2_ROPE_LIGHT_SWAY_ENABLED:
                                sway_phase_offset_rope = (
                                                                 light_unique_id_rope * 19) % config.L2_ROPE_LIGHT_SWAY_PHASE_OFFSET_MAX_RAD
                                sway_val_rope = math.sin(time_for_sway_rope + sway_phase_offset_rope)
                                swayed_light_x += sway_val_rope * config.L2_ROPE_LIGHT_SWAY_AMPLITUDE_X
                            light_y = light_y_on_edge + config.L2_ROPE_LIGHT_Y_OFFSET
                            effective_rope_light_radius = config.L2_ROPE_LIGHT_RADIUS * 2.2
                            if -effective_rope_light_radius * 3 < swayed_light_x < WIDTH + effective_rope_light_radius * 3 and \
                                    -effective_rope_light_radius * 3 < light_y < HEIGHT + effective_rope_light_radius * 3:
                                if config.L2_ROPE_LIGHT_SWAY_ENABLED:
                                    pygame.draw.line(surface, config.L2_ROPE_LIGHT_HANGING_LINE_COLOR,
                                                     (int(light_x_on_edge_anchor), int(light_y_on_edge)),
                                                     (int(swayed_light_x), int(light_y)), 1)
                                pulse_phase_offset_rope = (
                                                                  light_unique_id_rope * 7) % config.L2_ROPE_LIGHT_PULSE_PHASE_OFFSET_MAX_RAD
                                pulse_val_rope = (math.sin(time_for_pulse_rope + pulse_phase_offset_rope) + 1) / 2.0
                                base_brightness_factor = config.L2_ROPE_LIGHT_PULSE_MIN_BRIGHTNESS_FACTOR + \
                                                         pulse_val_rope * (
                                                                 1.0 - config.L2_ROPE_LIGHT_PULSE_MIN_BRIGHTNESS_FACTOR)
                                flicker_phase_offset_rope = (
                                                                    light_unique_id_rope * 13) % config.L2_ROPE_LIGHT_FLICKER_PHASE_OFFSET_MAX_RAD
                                flicker_val_rope = (math.sin(
                                    time_for_flicker_rope + flicker_phase_offset_rope) + 1) / 2.0
                                flicker_modulation_rope = (
                                                                  flicker_val_rope * 2.0 - 1.0) * config.L2_ROPE_LIGHT_FLICKER_MAGNITUDE
                                current_brightness_factor = base_brightness_factor + flicker_modulation_rope
                                current_brightness_factor = max(config.L2_ROPE_LIGHT_PULSE_MIN_BRIGHTNESS_FACTOR * 0.4,
                                                                min(1.0 + config.L2_ROPE_LIGHT_FLICKER_MAGNITUDE * 1.2,
                                                                    current_brightness_factor))
                                r_base, g_base, b_base = config.L2_ROPE_LIGHT_BASE_COLOR
                                pulsed_r = max(0, min(255, int(r_base * current_brightness_factor * 1.15)))
                                pulsed_g = max(0, min(255, int(g_base * current_brightness_factor * 1.15)))
                                pulsed_b = max(0, min(255, int(b_base * current_brightness_factor * 1.15)))
                                current_main_light_color = (pulsed_r, pulsed_g, pulsed_b)
                                if config.L2_ROPE_LIGHT_GLOW_ENABLED:
                                    effective_glow_radius_rope = int(
                                        effective_rope_light_radius * config.L2_ROPE_LIGHT_GLOW_RADIUS_FACTOR * 1.2)
                                    glow_flicker_val_rope = (math.sin(
                                        time_for_flicker_rope * 1.15 + flicker_phase_offset_rope + 0.7) + 1) / 2.0
                                    glow_flicker_modulation = (
                                                                      glow_flicker_val_rope * 2.0 - 1.0) * config.L2_ROPE_LIGHT_FLICKER_MAGNITUDE * 0.6
                                    glow_pulse_factor = (math.sin(
                                        time_for_pulse_rope + pulse_phase_offset_rope + math.pi / 2.2) + 1) / 2.0
                                    base_glow_alpha = config.L2_ROPE_LIGHT_GLOW_BASE_ALPHA * 1.4
                                    glow_alpha_dynamic = int(base_glow_alpha * (0.5 + 0.5 * glow_pulse_factor) * (
                                            1.0 + glow_flicker_modulation))
                                    glow_alpha_dynamic = max(25, min(int(base_glow_alpha * 1.15), glow_alpha_dynamic))
                                    glow_base_tint_r, glow_base_tint_g, glow_base_tint_b = config.L2_ROPE_LIGHT_BASE_COLOR
                                    glow_outer_tint_r_factor, glow_outer_tint_g_factor, glow_outer_tint_b_factor = 1.1, 0.95, 0.8
                                    for k_glow in range(3, 0, -1):
                                        current_glow_layer_radius = int(effective_glow_radius_rope * (k_glow / 3.0))
                                        tint_interp = (3 - k_glow) / 2.0
                                        eff_tint_r = int(
                                            glow_base_tint_r * (1.0 - tint_interp * (1.0 - glow_outer_tint_r_factor)))
                                        eff_tint_g = int(
                                            glow_base_tint_g * (1.0 - tint_interp * (1.0 - glow_outer_tint_g_factor)))
                                        eff_tint_b = int(
                                            glow_base_tint_b * (1.0 - tint_interp * (1.0 - glow_outer_tint_b_factor)))
                                        current_glow_color_rgb_tinted = (min(255, max(0, eff_tint_r) + 15),
                                                                         min(255, max(0, eff_tint_g) + 15),
                                                                         min(255, max(0, eff_tint_b) + 10))
                                        current_glow_layer_alpha = int(
                                            glow_alpha_dynamic * (0.8 * ((4 - k_glow) / 3.0)) ** 1.4)
                                        current_glow_layer_alpha = max(0, min(255, current_glow_layer_alpha))
                                        if current_glow_layer_radius > 0 and current_glow_layer_alpha > 5:
                                            glow_surf = pygame.Surface(
                                                (current_glow_layer_radius * 2, current_glow_layer_radius * 2),
                                                pygame.SRCALPHA)
                                            pygame.draw.circle(glow_surf, (*current_glow_color_rgb_tinted,
                                                                           current_glow_layer_alpha),
                                                               (current_glow_layer_radius, current_glow_layer_radius),
                                                               current_glow_layer_radius)
                                            surface.blit(glow_surf, (int(swayed_light_x - current_glow_layer_radius),
                                                                     int(light_y - current_glow_layer_radius)))
                                pygame.draw.circle(surface, current_main_light_color,
                                                   (int(swayed_light_x), int(light_y)),
                                                   int(effective_rope_light_radius))
                                core_radius = max(1, int(effective_rope_light_radius * 0.35))
                                core_brightness_factor = current_brightness_factor * 1.7 + 0.6
                                core_r = min(255, int(r_base * core_brightness_factor + 120))
                                core_g = min(255, int(g_base * core_brightness_factor + 120))
                                core_b = min(255, int(b_base * core_brightness_factor + 100))
                                core_color = (core_r, core_g, core_b)
                                pygame.draw.circle(surface, core_color, (int(swayed_light_x), int(light_y)),
                                                   core_radius)
                            j_light_index += 1
                            if effective_spacing <= 0: break
                            current_offset_along_segment += effective_spacing
                            if segment_length < effective_spacing and j_light_index == 1: break
                            if abs(dist_along_segment - segment_length) < epsilon: break
                time_for_pulse_particle = current_time_ms * config.L2_PARTICLE_LIGHT_PULSE_SPEED_HZ * 2 * math.pi / 1000.0
                time_for_flicker_particle = current_time_ms * config.L2_PARTICLE_LIGHT_FLICKER_SPEED_HZ * 2 * math.pi / 1000.0
                for i in range(len(pts_ceiling_bottom_surface_on_screen) - 1):
                    p1_s = pts_ceiling_bottom_surface_on_screen[i]
                    p2_s = pts_ceiling_bottom_surface_on_screen[i + 1]
                    dx, dy = p2_s[0] - p1_s[0], p2_s[1] - p1_s[1]
                    seg_len = math.hypot(dx, dy)
                    if seg_len < config.LEVEL2_CEILING_LIGHT_SPACING / 2: continue
                    num_l = int(seg_len / config.LEVEL2_CEILING_LIGHT_SPACING)
                    if num_l == 0 and seg_len > config.LEVEL2_CEILING_LIGHT_SPACING / 4: num_l = 1
                    for j in range(num_l):
                        t = (j + 0.5) / num_l if num_l > 0 else 0.5
                        if num_l == 1: t = 0.5
                        fx, fy_edge = p1_s[0] + t * dx, p1_s[1] + t * dy
                        fy = fy_edge + config.LEVEL2_CEILING_LIGHT_Y_OFFSET
                        s_spread = config.LEVEL2_CEILING_LIGHT_PARTICLE_SPREAD
                        r_max_base = config.LEVEL2_CEILING_LIGHT_PARTICLE_RADIUS_MAX
                        effective_particle_radius_max = r_max_base * 1.8
                        effective_particle_radius_min = config.LEVEL2_CEILING_LIGHT_PARTICLE_RADIUS_MIN * 1.5
                        effective_particle_radius_min = max(1, effective_particle_radius_min)
                        if -s_spread - effective_particle_radius_max < fx < WIDTH + s_spread + effective_particle_radius_max and \
                                -s_spread - effective_particle_radius_max < fy < HEIGHT + s_spread + effective_particle_radius_max:
                            cluster_unique_id_particle = (i * 1000) + j
                            pulse_phase_offset_particle = (
                                                                  cluster_unique_id_particle * 11) % config.L2_PARTICLE_LIGHT_PULSE_PHASE_OFFSET_MAX_RAD
                            pulse_val_particle = (math.sin(
                                time_for_pulse_particle + pulse_phase_offset_particle) + 1) / 2.0
                            flicker_phase_offset_particle = (
                                                                    cluster_unique_id_particle * 17) % config.L2_PARTICLE_LIGHT_FLICKER_PHASE_OFFSET_MAX_RAD
                            flicker_val_particle = (math.sin(
                                time_for_flicker_particle + flicker_phase_offset_particle) + 1) / 2.0
                            flicker_modulation_particle = (
                                                                  flicker_val_particle * 2.0 - 1.0) * config.L2_PARTICLE_LIGHT_FLICKER_MAGNITUDE
                            cluster_base_brightness = (0.6 + 0.4 * pulse_val_particle) + flicker_modulation_particle
                            cluster_base_brightness = max(0.25, min(1.0 + config.L2_PARTICLE_LIGHT_FLICKER_MAGNITUDE,
                                                                    cluster_base_brightness))
                            for _ in range(config.LEVEL2_CEILING_LIGHT_NUM_PARTICLES):
                                px = fx + random.uniform(-s_spread, s_spread)
                                py = fy + random.uniform(-s_spread, s_spread)
                                pr_current_base = random.uniform(effective_particle_radius_min,
                                                                 effective_particle_radius_max)
                                pr_final = pr_current_base * random.uniform(0.9, 1.1)
                                pr_final = max(1, int(pr_final))
                                pc_base_rgb = random.choice(config.LEVEL2_CEILING_LIGHT_PARTICLE_COLORS)
                                base_alpha_particle = 250
                                current_particle_alpha = int(
                                    base_alpha_particle * cluster_base_brightness * random.uniform(0.95, 1.08))
                                current_particle_alpha = max(40, min(255, current_particle_alpha))
                                bright_r = min(255, pc_base_rgb[0] + 20)
                                bright_g = min(255, pc_base_rgb[1] + 20)
                                bright_b = min(255, pc_base_rgb[2] + 20)
                                pc_final_color_alpha = (bright_r, bright_g, bright_b, current_particle_alpha)
                                if pr_final > 0:
                                    glow_radius_particle_eff = pr_final * 3.0
                                    glow_alpha_particle_eff = int(
                                        100 * cluster_base_brightness * random.uniform(0.85, 1.15))
                                    glow_alpha_particle_eff = max(20, min(150, glow_alpha_particle_eff))
                                    glow_particle_base_tint_r, glow_particle_base_tint_g, glow_particle_base_tint_b = pc_base_rgb
                                    glow_particle_outer_tint_r_factor, glow_particle_outer_tint_g_factor, glow_particle_outer_tint_b_factor = 1.05, 0.98, 0.85
                                    eff_particle_glow_tint_r = int(
                                        glow_particle_base_tint_r * glow_particle_outer_tint_r_factor)
                                    eff_particle_glow_tint_g = int(
                                        glow_particle_base_tint_g * glow_particle_outer_tint_g_factor)
                                    eff_particle_glow_tint_b = int(
                                        glow_particle_base_tint_b * glow_particle_outer_tint_b_factor)
                                    eff_particle_glow_tint_r = max(0, min(255, eff_particle_glow_tint_r + 10))
                                    eff_particle_glow_tint_g = max(0, min(255, eff_particle_glow_tint_g + 10))
                                    eff_particle_glow_tint_b = max(0, min(255, eff_particle_glow_tint_b + 5))
                                    glow_color_particle_eff_tinted = (
                                        *(eff_particle_glow_tint_r, eff_particle_glow_tint_g, eff_particle_glow_tint_b),
                                        glow_alpha_particle_eff)
                                    if glow_radius_particle_eff > 0 and glow_alpha_particle_eff > 5:
                                        glow_particle_surf = pygame.Surface(
                                            (int(glow_radius_particle_eff * 2), int(glow_radius_particle_eff * 2)),
                                            pygame.SRCALPHA)
                                        pygame.draw.circle(glow_particle_surf, glow_color_particle_eff_tinted,
                                                           (int(glow_radius_particle_eff),
                                                            int(glow_radius_particle_eff)),
                                                           int(glow_radius_particle_eff))
                                        surface.blit(glow_particle_surf, (int(px - glow_radius_particle_eff),
                                                                          int(py - glow_radius_particle_eff)))
                                    pygame.draw.circle(surface, pc_final_color_alpha, (int(px), int(py)), pr_final)
                                    if pr_final > effective_particle_radius_min * 1.35:
                                        core_rad_particle = max(1, int(pr_final * 0.25))
                                        core_col_particle = (255, 255, 250, max(200, current_particle_alpha))
                                        pygame.draw.circle(surface, core_col_particle, (int(px), int(py)),
                                                           core_rad_particle)

    def draw_tutorial_snow_platform(self, surface, camera_y_offset): 
        self.draw_snow_platform_and_clumps(surface, camera_y_offset)


class Ramp:
    def __init__(self, screen_spawn_x, terrain_obj, is_final_ramp=False):
        self.screen_spawn_x = float(screen_spawn_x)
        self.length = 350.0 
        self.height_rise = float(FINAL_RAMP_HEIGHT_RISE if is_final_ramp else 250)
        self.terrain = terrain_obj
        self.base_y_at_start = self.terrain.height_at(self.screen_spawn_x)
        self.end_x_screen = self.screen_spawn_x + self.length
        self.is_final = is_final_ramp
        self.thickness = 5.0 
        self.ramp_overlay_texture = None
        if self.is_final:
            try:
                main_script_dir = os.path.dirname(
                    os.path.abspath(sys.argv[0] if hasattr(sys, 'argv') and sys.argv else __file__))
                assets_dir = os.path.join(main_script_dir, "assets")
                if not os.path.isdir(assets_dir):
                    parent_dir = os.path.dirname(main_script_dir)
                    assets_dir = os.path.join(parent_dir, "assets")
                image_path = os.path.join(assets_dir, "ramp.png")
                if os.path.exists(image_path):
                    loaded_image = pygame.image.load(image_path).convert_alpha()
                    target_w = max(1, int(self.length))
                    target_h = max(1, int(self.height_rise + self.thickness))
                    self.ramp_overlay_texture = pygame.transform.smoothscale(loaded_image, (target_w, target_h))
                else:
                    print(f"WARNING: ramp.png not found at {image_path}. Final ramp will use polygon.")
            except Exception as e:
                print(f"ERROR loading or scaling ramp.png: {e}")

    def update(self, dx_world_scroll):
        self.screen_spawn_x -= dx_world_scroll
        self.end_x_screen -= dx_world_scroll
       
        self.base_y_at_start = self.terrain.height_at(self.screen_spawn_x) 


    def draw(self, surface, camera_y_offset):
        y_top_start_screen = self.base_y_at_start - camera_y_offset
        y_top_end_screen = (self.base_y_at_start - self.height_rise) - camera_y_offset 
        if self.end_x_screen > 0 and self.screen_spawn_x < float(WIDTH):
            if self.is_final and self.ramp_overlay_texture:
                blit_x = self.screen_spawn_x
                blit_y = y_top_end_screen 
                surface.blit(self.ramp_overlay_texture, (blit_x, blit_y))
            else:
                p1 = (self.screen_spawn_x, y_top_start_screen)
                p2 = (self.end_x_screen, y_top_end_screen)
                p3 = (self.end_x_screen, y_top_end_screen + self.thickness)
                p4 = (self.screen_spawn_x, y_top_start_screen + self.thickness)
                pygame.draw.polygon(surface, (180, 180, 190), [p1, p2, p3, p4])

    def on_ramp(self, player_x_pos_float):
        if self.screen_spawn_x <= player_x_pos_float <= self.end_x_screen:
            if self.length == 0.0: return float(self.base_y_at_start)
            progression = (player_x_pos_float - self.screen_spawn_x) / self.length
            return self.base_y_at_start - (progression * self.height_rise)
        return None