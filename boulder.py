# boulder.py
import pygame
import os
import sys
import math
import config as cfg
import game_state as gs


class Boulder(pygame.sprite.Sprite):
    def __init__(self, image_asset, terrain_obj):
        super().__init__()
        self.terrain = terrain_obj
        self.original_image = image_asset
        
        if not self.original_image:
            print("BOULDER ERROR: Original image asset is None. Using fallback.")
            self.original_image = pygame.Surface((cfg.BOULDER_TARGET_WIDTH, cfg.BOULDER_TARGET_HEIGHT), pygame.SRCALPHA)
            self.original_image.fill((100,100,100,150))
        
        self.image = self.original_image 
        self.rect = self.image.get_rect()

        
        self.offset = cfg.BOULDER_INITIAL_OFFSET
        
        self.rotation_angle = 0.0
        

        self._update_rect_and_y_from_offset() 

    def reset(self):
        self.offset = cfg.BOULDER_INITIAL_OFFSET
        self.rotation_angle = 0.0
        if self.original_image: 
            self.image = self.original_image
        self._update_rect_and_y_from_offset()

    def _update_rect_and_y_from_offset(self):
        """
        Updates the Pygame rect's position based on self.offset (right edge screen X)
        and sets its Y position based on terrain.
        """
        if not self.terrain or not self.image or not self.rect: return

      
        self.rect.right = int(self.offset) 
        
     
        terrain_y_world_at_boulder_center = self.terrain.height_at(self.rect.centerx)
    
        self.rect.midbottom = (self.rect.centerx, int(terrain_y_world_at_boulder_center))


    def update(self, is_catch_up_mode, player_screen_x_pos): 
        """
        Updates the boulder's position and rotation.
        is_catch_up_mode: Boolean, true if boulder should speed up.
        player_screen_x_pos: The player's fixed screen X coordinate (e.g., cfg.PLAYER_SCREEN_X).
        """
        if not self.rect or not self.original_image:
            return

       
        current_speed_this_frame = cfg.BOULDER_SPEED_PER_FRAME
        if is_catch_up_mode:
            current_speed_this_frame += cfg.BOULDER_CATCHUP_SPEED_BONUS_PER_FRAME
        
        self.offset += current_speed_this_frame

    
        self.rotation_angle = (self.rotation_angle - current_speed_this_frame * cfg.BOULDER_ROTATION_SPEED_DEG_PER_PIXEL) % 360
        
      
        old_center_x = self.rect.centerx 
        
      
        self.image = pygame.transform.rotate(self.original_image, self.rotation_angle)
        
     
        self.rect = self.image.get_rect(centerx=old_center_x)

     
        self._update_rect_and_y_from_offset()

      


    def draw(self, surface, camera_y_offset):
        if not gs.boulder_is_visible: 
             if self.rect.right >= cfg.BOULDER_APPEAR_OFFSET:
                 gs.boulder_is_visible = True
             else:
                 return

        if self.image and self.rect:
          
            draw_rect_y_on_screen = self.rect.top - camera_y_offset
            
       
            if self.rect.right > 0 and self.rect.left < cfg.WIDTH:
                surface.blit(self.image, (self.rect.left, draw_rect_y_on_screen))