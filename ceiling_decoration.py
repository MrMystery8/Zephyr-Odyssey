# ceiling_decoration.py
import pygame
import random
import math


class CeilingDecoration(pygame.sprite.Sprite):
    def __init__(self, image_surface, world_x_spawn_pos, world_y_ceiling_bottom_edge_at_spawn,
                 y_offset_of_deco_top_from_ceiling_bottom_edge,  
                 terrain_obj,
                 horizontal_flip=False):
        super().__init__()

        self.unrotated_image_asset_original_size = image_surface 
        self.terrain = terrain_obj
        self.y_offset_of_deco_top_from_ceiling_bottom_edge = y_offset_of_deco_top_from_ceiling_bottom_edge

        
        image_to_process = self.unrotated_image_asset_original_size.copy()
        if horizontal_flip:
            image_to_process = pygame.transform.flip(image_to_process, True, False)

   
        self.world_x_logical_spawn = float(world_x_spawn_pos)

        
        
        unrotated_asset_width = self.unrotated_image_asset_original_size.get_width()
        slope_calc_center_x_world = self.world_x_logical_spawn + unrotated_asset_width / 2.0
        slope_delta_x = 10.0

        x1_slope = slope_calc_center_x_world - slope_delta_x
        x2_slope = slope_calc_center_x_world + slope_delta_x

        y1_ceiling_val = self.terrain.ceiling_height_at(x1_slope)
        y2_ceiling_val = self.terrain.ceiling_height_at(x2_slope)

        if (x2_slope - x1_slope) == 0: 
            rotation_angle_rad = -math.pi / 2 if (y2_ceiling_val - y1_ceiling_val) > 0 else math.pi / 2
        else:
            rotation_angle_rad = math.atan2(y2_ceiling_val - y1_ceiling_val, x2_slope - x1_slope)

        rotation_angle_deg = math.degrees(rotation_angle_rad)

        
        self.image = pygame.transform.rotate(image_to_process, rotation_angle_deg)

        
        self.rect = self.image.get_rect()

        
        
        self.rect.centerx = int(self.world_x_logical_spawn + unrotated_asset_width / 2.0)

     
        self.rect.top = int(world_y_ceiling_bottom_edge_at_spawn + self.y_offset_of_deco_top_from_ceiling_bottom_edge)

    def update(self, dx_world_scroll):
     
        self.world_x_logical_spawn -= dx_world_scroll

       
        unrotated_asset_width = self.unrotated_image_asset_original_size.get_width()
        self.rect.centerx = int(self.world_x_logical_spawn + unrotated_asset_width / 2.0)

       
        current_world_y_ceiling_bottom_edge = self.terrain.ceiling_height_at(self.rect.centerx)
        self.rect.top = int(current_world_y_ceiling_bottom_edge + self.y_offset_of_deco_top_from_ceiling_bottom_edge)

        if self.rect.right < -50:
            self.kill()

    def draw(self, surface, camera_y_offset):
        if self.image and self.rect:
            draw_rect = self.rect.copy()
            draw_rect.y -= camera_y_offset 
            surface.blit(self.image, draw_rect)