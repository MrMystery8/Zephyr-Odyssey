# explosion.py
import pygame
import random
import math


class Explosion(pygame.sprite.Sprite):
    def __init__(self, center_x_world, center_y_world):
        super().__init__()
        self.center_x_world_initial = float(center_x_world)
        self.center_y_world_initial = float(center_y_world)

        self.current_center_x_world = self.center_x_world_initial
        self.current_center_y_world = self.center_y_world_initial

        self.animation_speed_multiplier = 1.0
        self.frame_index = 0
        self.last_update_time = pygame.time.get_ticks()

       
        self.frames_definition = [
       
            ('shards', 60 * self.animation_speed_multiplier, {
                'num_shards': random.randint(5, 8),
                'max_radius': 35,  
                'min_shard_verts': 4, 'max_shard_verts': 6,
                'colors': [(255, 100, 0), (255, 150, 50), (255, 80, 0), (255, 50, 0)],  
                'alpha_start': 255, 'alpha_end': 235,  
                'expand_rate': 1.6 
            }),
            ('shards', 75 * self.animation_speed_multiplier, {
                'num_shards': random.randint(7, 11),
                'max_radius': 65, 
                'min_shard_verts': 4, 'max_shard_verts': 7,
                'colors': [(255, 180, 50), (255, 200, 100), (255, 160, 30), (255, 150, 0)],
                'alpha_start': 215, 'alpha_end': 150,
                'expand_rate': 1.8 
            }),
            ('shards', 85 * self.animation_speed_multiplier, {
                'num_shards': random.randint(6, 9),
                'max_radius': 105,  
                'min_shard_verts': 3, 'max_shard_verts': 6,
                'colors': [(255, 220, 100), (255, 230, 150), (240, 180, 90), (200, 100, 50)],
                'alpha_start': 150, 'alpha_end': 60,
                'expand_rate': 2.6
            }),
            
            ('smoke', 130 * self.animation_speed_multiplier, [  
                {'radius': 60, 'color': (150, 150, 150), 'alpha': 130, 'rise': -0.18,
                 'drift_x': random.uniform(-0.12, 0.12), 'offset_x': random.uniform(-12, 12),
                 'offset_y': random.uniform(-12, 12), 'expand_rate': 0.3, 'aspect_ratio_range': (0.7, 1.3)},
                {'radius': 50, 'color': (140, 140, 140), 'alpha': 120, 'rise': -0.22,
                 'drift_x': random.uniform(-0.18, 0.18), 'offset_x': random.uniform(-18, 18),
                 'offset_y': random.uniform(-18, 18), 'expand_rate': 0.38, 'aspect_ratio_range': (0.6, 1.4)},
                
            ]),
            ('smoke', 160 * self.animation_speed_multiplier, [ 
                {'radius': 85, 'color': (130, 130, 130), 'alpha': 120, 'rise': -0.28,
                 'drift_x': random.uniform(-0.18, 0.18), 'offset_x': random.uniform(-18, 18),
                 'offset_y': random.uniform(-18, 18), 'expand_rate': 0.5, 'aspect_ratio_range': (0.7, 1.3)},
                {'radius': 75, 'color': (120, 120, 120), 'alpha': 80, 'rise': -0.32,
                 'drift_x': random.uniform(-0.22, 0.22), 'offset_x': random.uniform(-22, 22),
                 'offset_y': random.uniform(-22, 22), 'expand_rate': 0.45, 'aspect_ratio_range': (0.6, 1.4)},
            ]),
            ('smoke', 200 * self.animation_speed_multiplier, [ 
                {'radius': 100, 'color': (100, 100, 100), 'alpha': 70, 'rise': -0.35,
                 'drift_x': random.uniform(-0.20, 0.20), 'offset_x': random.uniform(-20, 20),
                 'offset_y': random.uniform(-20, 20), 'expand_rate': 0.55, 'aspect_ratio_range': (0.7, 1.3)},
                
            ]),
            ('smoke', 220 * self.animation_speed_multiplier, [ 
                {'radius': 110, 'color': (80, 80, 80), 'alpha': 35, 'rise': -0.38,
                 'drift_x': random.uniform(-0.25, 0.25), 'offset_x': random.uniform(-25, 25),
                 'offset_y': random.uniform(-25, 25), 'expand_rate': 0.7, 'aspect_ratio_range': (0.7, 1.3)},
            ]),
        ]
        self.num_frames_defined = len(self.frames_definition)

        self.max_dimension = 0
        current_max_radius_overall = 0
        for f_type, _, props in self.frames_definition:
            if f_type == 'shards':
              
                current_max_radius_overall = max(current_max_radius_overall,
                                                 props['max_radius'] * props.get('expand_rate', 1.0) * 1.3)
            elif f_type == 'smoke':
                for smoke_prop in props:
                    current_max_radius_overall = max(current_max_radius_overall,
                                                     smoke_prop['radius'] * 1.6)

        self.max_dimension = int(current_max_radius_overall * 2.0)
        self.max_dimension = max(self.max_dimension, 180)  
        self.max_dimension += 70 

        self.image = pygame.Surface((self.max_dimension, self.max_dimension), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(self.current_center_x_world), int(self.current_center_y_world)))

        self.frame_elements = []
        self.time_in_current_frame_def = 0

        self.generate_frame_elements()
        self.update_image_content()

    def generate_random_convex_polygon(self, center_x, center_y, max_r_base, min_verts, max_verts):
        points = []
        num_vertices = random.randint(min_verts, max_verts)
        angle_step = 360 / num_vertices
        generation_radius_scale = 0.65  

        for i in range(num_vertices):
            angle_rad = math.radians(i * angle_step + random.uniform(-angle_step * 0.45, angle_step * 0.45))
            radius = random.uniform(max_r_base * 0.3,
                                    max_r_base * 0.8) * generation_radius_scale  

            x = center_x + radius * math.cos(angle_rad)
            y = center_y + radius * math.sin(angle_rad)
            points.append((int(x), int(y)))
        return points

    def generate_frame_elements(self):
        if self.frame_index >= self.num_frames_defined: return
        self.frame_elements = []
        frame_type, _, properties = self.frames_definition[self.frame_index]
        center_of_surface_x = self.max_dimension // 2
        center_of_surface_y = self.max_dimension // 2

        if frame_type == 'shards':
            for _ in range(properties['num_shards']):
                polygon_points = self.generate_random_convex_polygon(
                    center_of_surface_x, center_of_surface_y,
                    properties['max_radius'],
                    properties['min_shard_verts'], properties['max_shard_verts']
                )
                color = random.choice(properties['colors'])
                rotation_angle = random.uniform(0, 360)
                self.frame_elements.append(
                    {'type': 'polygon', 'points': polygon_points, 'color': color, 'rotation': rotation_angle})

        elif frame_type == 'smoke':
            for smoke_prop_template in properties:
                self.frame_elements.append({
                    'type': 'smoke_puff',
                    'orig_radius': smoke_prop_template['radius'],
                    'current_radius': smoke_prop_template['radius'] * random.uniform(0.35, 0.65),
                    'color': smoke_prop_template['color'],
                    'orig_alpha': smoke_prop_template['alpha'],
                    'current_alpha': smoke_prop_template['alpha'] * random.uniform(0.85, 1.05),
                    'rise_speed': smoke_prop_template['rise'] * random.uniform(0.8, 1.2),
                    'drift_x_speed': smoke_prop_template['drift_x'] * random.uniform(0.7, 1.3),
                    'base_offset_x': smoke_prop_template.get('offset_x', 0) + random.uniform(
                        -smoke_prop_template['radius'] * 0.35, smoke_prop_template['radius'] * 0.35),
                    'base_offset_y': smoke_prop_template.get('offset_y', 0) + random.uniform(
                        -smoke_prop_template['radius'] * 0.35, smoke_prop_template['radius'] * 0.35),
                    'current_offset_y': 0,
                    'current_offset_x': 0,
                    'expand_rate': smoke_prop_template.get('expand_rate', 0.2) * random.uniform(0.85, 1.15),
                    'aspect_ratio': random.uniform(smoke_prop_template.get('aspect_ratio_range', (0.7, 1.3))[0],
                                                   smoke_prop_template.get('aspect_ratio_range', (0.7, 1.3))[1]),
                    'rotation': random.uniform(0, 60) 
                })

    def rotate_point(self, point, angle_degrees, center_x, center_y):
        angle_rad = math.radians(angle_degrees)
        s, c = math.sin(angle_rad), math.cos(angle_rad)
        px, py = point[0] - center_x, point[1] - center_y
        new_x = px * c - py * s
        new_y = px * s + py * c
        return new_x + center_x, new_y + center_y

    def update_image_content(self):
        if self.frame_index >= self.num_frames_defined: self.kill(); return
        self.image.fill((0, 0, 0, 0))
        frame_type, duration_ms, properties = self.frames_definition[self.frame_index]
        progress = min(1.0, self.time_in_current_frame_def / duration_ms if duration_ms > 0 else 1.0)
        center_of_surface_x = self.max_dimension // 2
        center_of_surface_y = self.max_dimension // 2

        if frame_type == 'shards':
            alpha = properties['alpha_start'] * (1 - progress) + properties['alpha_end'] * progress
            current_expand_factor = 1.0 + (properties.get('expand_rate', 1.5) - 1.0) * progress
            for element in self.frame_elements:
                if element['type'] == 'polygon':
                    scaled_rotated_points = []
                    current_rotation = element['rotation'] * progress * 1.5 
                    for px, py in element['points']:
                        vec_x = px - center_of_surface_x
                        vec_y = py - center_of_surface_y
                        scaled_px = center_of_surface_x + vec_x * current_expand_factor
                        scaled_py = center_of_surface_y + vec_y * current_expand_factor
                        final_px, final_py = self.rotate_point((scaled_px, scaled_py), current_rotation,
                                                               center_of_surface_x, center_of_surface_y)
                        scaled_rotated_points.append((final_px, final_py))
                    final_color = (*element['color'], int(max(0, min(255, alpha))))
                    if len(scaled_rotated_points) >= 3:
                        try:
                            pygame.draw.polygon(self.image, final_color, scaled_rotated_points)
                        except TypeError:
                            pass

        elif frame_type == 'smoke':
            for puff in self.frame_elements:
                if puff['type'] == 'smoke_puff':
                    target_radius_scale = 1.0 + 0.8 * progress  
                    puff['current_radius'] += (puff['orig_radius'] * target_radius_scale - puff[
                        'current_radius']) * 0.08 * puff['expand_rate']

                    puff['current_alpha'] = puff['orig_alpha'] * (1.0 - progress * 0.75)  
                    puff_alpha = int(max(0, min(255, puff['current_alpha'])))

                    puff['current_offset_y'] += puff['rise_speed']
                    puff['current_offset_x'] += puff['drift_x_speed']

                    final_color = (*puff['color'], puff_alpha)
                    pos_x = center_of_surface_x + puff['base_offset_x'] + puff['current_offset_x']
                    pos_y = center_of_surface_y + puff['base_offset_y'] + puff['current_offset_y']

                    current_r = int(puff['current_radius'])
                    if current_r > 1 and puff_alpha > 10:
                        ellipse_w = int(current_r * 2 * puff['aspect_ratio'])
                        ellipse_h = int(current_r * 2 / puff['aspect_ratio'])
                        max_ellipse_dim = max(ellipse_w, ellipse_h)
                        if max_ellipse_dim <= 0: continue  
                        temp_surf = pygame.Surface((max_ellipse_dim, max_ellipse_dim), pygame.SRCALPHA)
                        temp_surf.fill((0, 0, 0, 0))
                        ellipse_rect_on_temp = pygame.Rect(0, 0, ellipse_w, ellipse_h)
                        ellipse_rect_on_temp.center = (max_ellipse_dim // 2, max_ellipse_dim // 2)
                        try:
                            pygame.draw.ellipse(temp_surf, final_color, ellipse_rect_on_temp)
                            rotated_surf = pygame.transform.rotate(temp_surf, puff['rotation'])
                            rotated_rect = rotated_surf.get_rect(center=(int(pos_x), int(pos_y)))
                            self.image.blit(rotated_surf, rotated_rect)
                        except (TypeError, ValueError):
                            pass 

    def update(self, time_delta_seconds, world_scroll_dx):
        if not self.alive(): return
        self.current_center_x_world -= world_scroll_dx
        current_time = pygame.time.get_ticks()
        delta_ms_since_last_major_update = current_time - self.last_update_time
        self.time_in_current_frame_def += delta_ms_since_last_major_update
        self.last_update_time = current_time
        if self.frame_index < self.num_frames_defined:
            _, duration_ms, _ = self.frames_definition[self.frame_index]
            if self.time_in_current_frame_def >= duration_ms:
                self.frame_index += 1
                self.time_in_current_frame_def = 0
                if self.frame_index < self.num_frames_defined:
                    self.generate_frame_elements()
                else:
                    self.kill()
                    return
            if self.alive(): self.update_image_content()
        else:
            self.kill(); return
        if self.rect: self.rect.center = (int(self.current_center_x_world), int(self.current_center_y_world))

    def draw(self, surface, camera_y_offset):
        if self.image and self.rect and self.alive():
            draw_rect = self.rect.copy()
            draw_rect.y -= camera_y_offset
            surface.blit(self.image, draw_rect)