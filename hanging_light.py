# hanging_light.py
import pygame
import math
import random 
import config 


class HangingLight(pygame.sprite.Sprite):
    def __init__(self, image_surface, world_x_spawn_pos,
                 initial_ceiling_y_at_spawn_x,
                 y_offset_from_ceiling,
                 terrain_obj):
        super().__init__()

        self.original_image = image_surface
        self.image = self.original_image
        self.terrain = terrain_obj
        self.y_offset_from_ceiling = y_offset_from_ceiling
        self.world_x_anchor = float(world_x_spawn_pos)
        self.rect = self.image.get_rect()
        self.initial_sprite_height = self.original_image.get_height()
        self.initial_sprite_width = self.original_image.get_width()

        self.rect.midtop = (int(self.world_x_anchor),
                            int(initial_ceiling_y_at_spawn_x + self.y_offset_from_ceiling))

        self.swing_angle = 0.0
        self.swing_timer = random.uniform(0, 2 * math.pi)
        self.max_angle = config.L2_HANGING_LIGHT_MAX_SWING_ANGLE
        self.swing_frequency = config.L2_HANGING_LIGHT_SWING_FREQUENCY
        self.last_valid_pivot_y = initial_ceiling_y_at_spawn_x + self.y_offset_from_ceiling

       
        self.glow_color = (140, 140, 100, 0)  

        self.glow_top_width_factor = 0.7
        self.glow_bottom_width_factor = 3.5
        

    def _lerp_component(self, c1_comp, c2_comp, t):
        """Linearly interpolates a single color component."""
        return int(c1_comp * (1.0 - t) + c2_comp * t)

    def _lerp_rgb_color(self, color1_rgb, color2_rgb, t):
        """Linearly interpolates between two RGB colors."""
        r = self._lerp_component(color1_rgb[0], color2_rgb[0], t)
        g = self._lerp_component(color1_rgb[1], color2_rgb[1], t)
        b = self._lerp_component(color1_rgb[2], color2_rgb[2], t)
        return (r, g, b)

    def update(self, dx_world_scroll):
        self.world_x_anchor -= dx_world_scroll
        self.swing_timer += 0.05
        self.swing_angle = math.sin(self.swing_timer * self.swing_frequency) * self.max_angle
        self.image = pygame.transform.rotate(self.original_image, self.swing_angle)
        current_world_y_ceiling_bottom_edge = self.terrain.ceiling_height_at(self.world_x_anchor)
        pivot_y_world = 0
        if not math.isfinite(current_world_y_ceiling_bottom_edge):
            pivot_y_world = self.last_valid_pivot_y
        else:
            pivot_y_world = current_world_y_ceiling_bottom_edge + self.y_offset_from_ceiling
            self.last_valid_pivot_y = pivot_y_world
        
     
        self.rect = self.image.get_rect(
            center=(int(self.world_x_anchor), int(pivot_y_world + self.initial_sprite_height / 2)))
        
        if self.rect.right < -self.initial_sprite_width - 50:
            self.kill()

    def draw(self, surface, camera_y_offset, player_obj=None):
        if self.image and self.rect:
            draw_rect_sprite = self.rect.copy()
            draw_rect_sprite.y -= camera_y_offset

            
            glow_origin_x_screen = self.rect.centerx
            glow_origin_y_world = self.rect.bottom 
            glow_origin_y_screen = glow_origin_y_world - camera_y_offset
            
            glow_top_width_screen = self.initial_sprite_width * self.glow_top_width_factor
            glow_bottom_width_screen = self.initial_sprite_width * self.glow_bottom_width_factor
            
            p1_screen = (glow_origin_x_screen - glow_top_width_screen / 2, glow_origin_y_screen)
            p2_screen = (glow_origin_x_screen + glow_top_width_screen / 2, glow_origin_y_screen)
            
            terrain_y_world_under_bulb = self.terrain.height_at(glow_origin_x_screen) 
            terrain_y_screen_under_bulb = terrain_y_world_under_bulb - camera_y_offset
            
            h_to_terrain = max(1.0, terrain_y_screen_under_bulb - glow_origin_y_screen)
            
            swing_angle_rad = math.radians(self.swing_angle)
            horizontal_projection_shift = h_to_terrain * math.tan(swing_angle_rad)
            projected_glow_base_center_x_screen = glow_origin_x_screen + horizontal_projection_shift
            
            p4x_screen = projected_glow_base_center_x_screen - glow_bottom_width_screen / 2
            
            terrain_y_at_p4x_world = self.terrain.height_at(p4x_screen) 
            p4y_screen = max(glow_origin_y_screen + 1, terrain_y_at_p4x_world - camera_y_offset)
            
            p3x_screen = projected_glow_base_center_x_screen + glow_bottom_width_screen / 2
            
            terrain_y_at_p3x_world = self.terrain.height_at(p3x_screen) 
            p3y_screen = max(glow_origin_y_screen + 1, terrain_y_at_p3x_world - camera_y_offset)
            
            glow_points_screen = [p1_screen, p2_screen, (p3x_screen, p3y_screen), (p4x_screen, p4y_screen)]

            try:
                if all(math.isfinite(coord) for point in glow_points_screen for coord in point) and \
                   (p3y_screen >= glow_origin_y_screen and p4y_screen >= glow_origin_y_screen):
                    if len(glow_points_screen) >= 3:
                        min_x_glow = min(p[0] for p in glow_points_screen)
                        max_x_glow = max(p[0] for p in glow_points_screen)
                        min_y_glow = min(p[1] for p in glow_points_screen)
                        max_y_glow = max(p[1] for p in glow_points_screen)
                        
                        glow_bbox_width = int(max_x_glow - min_x_glow)
                        glow_bbox_height = int(max_y_glow - min_y_glow)

                        if glow_bbox_width > 0 and glow_bbox_height > 0:
                           
                           
                            color_edge = (50, 50, 10)
                            color_mid = self.glow_color[:3] 
                            glow_alpha = self.glow_color[3] 

                            
                            
                            gradient_rect_surface = pygame.Surface((glow_bbox_width, glow_bbox_height), pygame.SRCALPHA)
                            gradient_rect_surface.fill((0, 0, 0, 0)) 

                            
                            for x_local in range(glow_bbox_width):
                                if glow_bbox_width == 1:
                                    t_gradient = 0.5 
                                else:
                                    t_gradient = x_local / (glow_bbox_width - 1.0)
                                
                                current_rgb = ()
                                if t_gradient <= 0.5:
                                    interp_t = t_gradient * 2.0 
                                    current_rgb = self._lerp_rgb_color(color_edge, color_mid, interp_t)
                                else:
                                    interp_t = (t_gradient - 0.5) * 2.0
                                    current_rgb = self._lerp_rgb_color(color_mid, color_edge, interp_t)
                                
                                strip_color_with_alpha = (*current_rgb, glow_alpha)
                                pygame.draw.line(gradient_rect_surface, strip_color_with_alpha, 
                                                 (x_local, 0), (x_local, glow_bbox_height - 1))

                            
                            
                            polygon_shape_mask = pygame.Surface((glow_bbox_width, glow_bbox_height), pygame.SRCALPHA)
                            polygon_shape_mask.fill((0, 0, 0, 0)) 
                            
                            
                            local_glow_points = [(int(p[0] - min_x_glow), int(p[1] - min_y_glow)) for p in glow_points_screen]
                            pygame.draw.polygon(polygon_shape_mask, (255, 255, 255, 255), local_glow_points) 

                            
                            gradient_rect_surface.blit(polygon_shape_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                            
                            
                            surface.blit(gradient_rect_surface, (int(min_x_glow), int(min_y_glow)), special_flags=pygame.BLEND_RGBA_ADD)
                            
            except (TypeError, ValueError) as e:
                
                pass
            
            
            surface.blit(self.image, draw_rect_sprite.topleft)