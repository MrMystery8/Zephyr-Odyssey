# debris_effect.py
import pygame
import random
import math


class DebrisEffect(pygame.sprite.Sprite):
    def __init__(self, center_x, center_y, material_type, intensity=1.0):
        super().__init__()
        self.center_x_world = float(center_x)
        self.center_y_world = float(center_y)
        self.material_type = material_type
        self.intensity = intensity

        self.particles = []
        self._generate_particles()

        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(center_x), int(center_y)))
        self.time_since_creation = 0

    def _generate_particles(self):
        num_particles = 0
        
        particle_properties_template = {}

        if self.material_type == "mirror":
            num_particles = int(random.randint(12, 20) * self.intensity)
            particle_properties_template = {
                'color_list': [(190, 195, 205), (210, 215, 225), (170, 175, 185), (220, 225, 230)],
                'size_range': (3, 8),
                'speed_range': (3.0, 7.0),
                'life_range': (0.6, 1.2),
                'gravity': 0.18,
                'shape': 'polygon_sharp'
            }
        elif self.material_type == "machinery":
            num_particles = int(random.randint(15, 25) * self.intensity)
            particle_properties_template = {
                'color_list': [(70, 70, 80), (90, 90, 100), (50, 50, 60)],
                'size_range': (4, 10),
                'speed_range': (1.8, 4.5),
                'life_range': (0.7, 1.4),
                'gravity': 0.25,
                'shape': 'rect_chunky'
            }
            for _ in range(random.randint(5, 10)):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(5.0, 8.5) * self.intensity
                self.particles.append(
                    {'x': self.center_x_world, 'y': self.center_y_world, 'vx': math.cos(angle) * speed,
                     'vy': math.sin(angle) * speed, 'size': random.randint(1, 4),
                     'color': random.choice([(255, 180, 50), (255, 220, 100)]), 'alpha': 255.0, 'max_alpha': 255.0,
                     'life': random.uniform(0.2, 0.45), 'max_life': random.uniform(0.2, 0.45), 'gravity': 0.15,
                     'shape': 'spark_line'})
        elif self.material_type == "ice":
            num_particles = int(random.randint(40, 70) * self.intensity)
            particle_properties_template = {
                'color_list': [(200, 220, 255), (220, 235, 255, 230), (190, 210, 245, 210), (230, 240, 255, 190)],
                'size_range': (4, 12), 'speed_range': (3.5, 8.0), 'life_range': (0.6, 1.5), 'gravity': 0.18,
                'shape': 'triangle_ice_sharp'}
            for _ in range(int(25 * self.intensity)):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(1.5, 3.5) * self.intensity
                life_mist = random.uniform(0.4, 0.7)
                self.particles.append(
                    {'x': self.center_x_world, 'y': self.center_y_world, 'vx': math.cos(angle) * speed,
                     'vy': math.sin(angle) * speed - random.uniform(0.8, 2.0), 'size': random.randint(1, 4),
                     'color': (230, 240, 255), 'alpha': random.uniform(120, 200), 'max_alpha': random.uniform(120, 200),
                     'life': life_mist, 'max_life': life_mist, 'gravity': 0.04, 'shape': 'circle'})
        elif self.material_type == "rock":
            num_particles = int(random.randint(10, 18) * self.intensity)
            particle_properties_template = {'color_list': [(100, 90, 80), (120, 110, 100), (80, 70, 60)],
                                            'size_range': (4, 9), 'speed_range': (1.0, 3.5), 'life_range': (0.7, 1.5),
                                            'gravity': 0.25, 'shape': 'rect_chunky'}
        elif self.material_type == "snow_puff":
            num_particles = int(random.randint(15, 25) * self.intensity)
            particle_properties_template = {'color_list': [(235, 235, 240), (220, 220, 225), (240, 240, 248)],
                                            'size_range': (3, 7), 'speed_range': (0.5, 2.5), 'life_range': (0.8, 1.5),
                                            'gravity': 0.05, 'shape': 'circle_soft'}
        elif self.material_type == "bug_flesh": 
            num_particles = int(random.randint(35, 55) * self.intensity) 
            particle_properties_template = {
                'color_list': [
                    (160, 10, 10),    
                    (190, 30, 30),    
                    (210, 50, 50),    
                    (230, 70, 70),    
                    (200, 40, 40, 210),
                    (170, 25, 25, 180) 
                ],
                'size_range': (4, 15), 
                'speed_range': (1.8, 5.0), 
                'life_range': (0.9, 1.8), 
                'gravity': 0.30, 
                'shape': 'polygon_sharp' 
            }
        

        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            initial_vy_offset = 0
            speed_base = particle_properties_template.get('speed_range', (1.0, 3.0))
            speed = random.uniform(speed_base[0], speed_base[1]) * self.intensity
            if self.material_type == "snow_puff":
                initial_vy_offset = -random.uniform(0.5, 2.0) * self.intensity
            elif self.material_type == "ice":
                initial_vy_offset = -random.uniform(0, speed * 0.4)
            elif self.material_type == "bug_flesh":
                initial_vy_offset = -random.uniform(0.3, 2.0) * self.intensity


            life_base = particle_properties_template.get('life_range', (0.5, 1.0))
            life = random.uniform(life_base[0], life_base[1])
            size_base = particle_properties_template.get('size_range', (2, 5))
            size_val = random.randint(size_base[0], size_base[1])
            start_alpha = 255.0

            self.particles.append({
                'x': self.center_x_world + random.uniform(-self.intensity * 5,
                                                          self.intensity * 5) if self.material_type == "snow_puff" else self.center_x_world + random.uniform(
                    -self.intensity * 2, self.intensity * 2),
                'y': self.center_y_world + random.uniform(-self.intensity * 5,
                                                          self.intensity * 5) if self.material_type == "snow_puff" else self.center_y_world + random.uniform(
                    -self.intensity * 2, self.intensity * 2),
                'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed + initial_vy_offset,
                'size': size_val,
                'color': random.choice(particle_properties_template.get('color_list', [(200, 200, 200)])),
                'alpha': start_alpha, 'max_alpha': start_alpha,
                'life': life, 'max_life': life,
                'gravity': particle_properties_template.get('gravity', 0.1),
                'shape': particle_properties_template.get('shape', 'rect_chunky'),
                'rotation': random.uniform(0, 360), 'angular_velocity': random.uniform(-300, 300)
            })

    def update(self, time_delta_seconds, world_scroll_dx):
        self.center_x_world -= world_scroll_dx
        self.time_since_creation += time_delta_seconds
        active_particles = []
        for p in self.particles:
            p['vx'] *= (1 - 0.2 * time_delta_seconds)
            p['vy'] *= (1 - 0.1 * time_delta_seconds)
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += p['gravity'] * (60 * time_delta_seconds)
            p['x'] -= world_scroll_dx
            p['life'] -= time_delta_seconds

            if p['max_life'] > 0 and p['life'] > 0:
                life_ratio = p['life'] / p['max_life']
                p['alpha'] = p['max_alpha'] * (life_ratio ** 0.5)
            elif p['life'] <= 0:
                p['alpha'] -= 400 * time_delta_seconds

            p['alpha'] = max(0, p['alpha'])
            if 'rotation' in p: p['rotation'] = (p['rotation'] + p['angular_velocity'] * time_delta_seconds) % 360
            if p['alpha'] > 5: active_particles.append(p)

        self.particles = active_particles
        if not self.particles and self.time_since_creation > 0.2:
            self.kill()
        elif self.time_since_creation > 7.0:
            self.kill()
        self.rect.center = (int(self.center_x_world), int(self.center_y_world))

    def _rotate_points(self, points, angle_degrees, center_x, center_y):
        angle_rad = math.radians(angle_degrees)
        s, c = math.sin(angle_rad), math.cos(angle_rad)
        rotated_points = []
        for px, py in points: translated_x, translated_y = px - center_x, py - center_y; new_x = translated_x * c - translated_y * s; new_y = translated_x * s + translated_y * c; rotated_points.append(
            (new_x + center_x, new_y + center_y))
        return rotated_points

    def draw(self, surface, camera_y_offset):
        for p in self.particles:
            if p['alpha'] <= 5: continue
            draw_x_center = p['x']
            draw_y_center = p['y'] - camera_y_offset
            base_color = p['color']
            current_alpha = int(p['alpha'])
            if len(base_color) == 4:
                final_color = (base_color[0], base_color[1], base_color[2], int(min(current_alpha, base_color[3])))
            else:
                final_color = (*base_color, current_alpha)
            size = int(p['size'])
            if size <= 0: continue
            try:
                if p['shape'] == 'polygon_sharp':
                    num_points = random.randint(4, 6); 
                    points_orig = []
                    for i in range(num_points):
                        angle_rad = (2 * math.pi / num_points) * i + random.uniform(-0.2, 0.2) 
                        
                        r_scale = random.uniform(0.4, 1.0) if i % 2 == 0 else random.uniform(0.7, 1.3)
                        px_rel = size * math.cos(angle_rad) * r_scale
                        py_rel = size * math.sin(angle_rad) * r_scale
                        points_orig.append((px_rel, py_rel))
                    rotated_points = self._rotate_points(points_orig, p.get('rotation', 0), 0, 0)
                    screen_points = [(int(draw_x_center + rp[0]), int(draw_y_center + rp[1])) for rp in rotated_points]
                    if len(screen_points) >= 3: pygame.draw.polygon(surface, final_color, screen_points)
                elif p['shape'] == 'triangle_ice_sharp':
                    half_s = size * random.uniform(0.8, 1.2)
                    height_factor = random.uniform(1.2, 2.0)
                    base_width_factor = random.uniform(0.2, 0.6)
                    points_orig = [(0, -half_s * height_factor / 2.0),
                                   (-half_s * base_width_factor / 2.0, half_s * height_factor / 2.0),
                                   (half_s * base_width_factor / 2.0, half_s * height_factor / 2.0)]
                    rotated_points = self._rotate_points(points_orig, p.get('rotation', random.uniform(0, 360)), 0, 0)
                    screen_points = [(int(draw_x_center + rp[0]), int(draw_y_center + rp[1])) for rp in rotated_points]
                    if len(screen_points) >= 3: pygame.draw.polygon(surface, final_color, screen_points)
                elif p['shape'] == 'rect_chunky' or p['shape'] == 'rect_varied_rock':
                    w = size * random.uniform(0.6, 1.5)
                    h = size * random.uniform(0.6, 1.5)
                    points_orig = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
                    rotated_points = self._rotate_points(points_orig, p.get('rotation', random.uniform(0, 90)), 0, 0)
                    screen_points = [(int(draw_x_center + rp[0]), int(draw_y_center + rp[1])) for rp in rotated_points]
                    if len(screen_points) >= 3: pygame.draw.polygon(surface, final_color, screen_points)
                elif p['shape'] == 'spark_line':
                    angle_rad = math.atan2(p['vy'], p['vx'])
                    length = max(3, size * 2.0)
                    end_x = draw_x_center + length * math.cos(angle_rad)
                    end_y = draw_y_center + length * math.sin(angle_rad)
                    pygame.draw.line(surface, final_color, (int(draw_x_center), int(draw_y_center)),
                                     (int(end_x), int(end_y)), max(1, size // 2 + 1))
                elif p['shape'] == 'circle_soft' or p['shape'] == 'circle':
                    if p['shape'] == 'circle_soft':
                        for i_soft in range(2, 0, -1):
                            s_alpha = current_alpha // (2 - i_soft + 1)
                            s_size = size * (i_soft / 2.0)
                            if s_size >= 1: pygame.draw.circle(surface, (final_color[0], final_color[1], final_color[2],
                                                                         int(s_alpha * 0.7)),
                                                               (int(draw_x_center), int(draw_y_center)), int(s_size))
                    else:
                        pygame.draw.circle(surface, final_color, (int(draw_x_center), int(draw_y_center)), size)
                
                    pygame.draw.circle(surface, final_color, (int(draw_x_center), int(draw_y_center)), size)
            except (TypeError, ValueError):
                pass