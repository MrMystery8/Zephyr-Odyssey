# portal.py
import pygame
import os
import sys
from config import WIDTH  

PORTAL_TARGET_WIDTH = 100
PORTAL_TARGET_HEIGHT = 150
PORTAL_ANIMATION_SPEED = 0.12


class Portal(pygame.sprite.Sprite):
    def __init__(self, screen_spawn_x, terrain_obj,
                 portal_image_asset_ignored):  
        super().__init__()
        self.terrain = terrain_obj

        self.frames = []
        self.current_frame_index = 0
        self.animation_timer = 0.0

        
        try:
        
            main_script_dir = os.path.dirname(
                os.path.abspath(sys.argv[0] if hasattr(sys, 'argv') and sys.argv else __file__))
            assets_dir = os.path.join(main_script_dir, "assets")
            if not os.path.isdir(assets_dir):
                parent_dir = os.path.dirname(main_script_dir)
                assets_dir = os.path.join(parent_dir, "assets")

            for i in range(1, 6): 
                filename = f"portal{i}.png"
                image_path = os.path.join(assets_dir, filename)
                if os.path.exists(image_path):
                    loaded_image = pygame.image.load(image_path).convert_alpha()
                    scaled_image = pygame.transform.smoothscale(loaded_image,
                                                                (PORTAL_TARGET_WIDTH, PORTAL_TARGET_HEIGHT))
                    self.frames.append(scaled_image)
                else:
                    print(f"Warning: Portal image {filename} not found at {image_path}")
        except Exception as e:
            print(f"Error loading portal animation frames: {e}")

        if not self.frames:  
            print("Error: No portal animation frames loaded. Using fallback.")
            fallback_surface = pygame.Surface((PORTAL_TARGET_WIDTH, PORTAL_TARGET_HEIGHT), pygame.SRCALPHA)
            fallback_surface.fill((150, 50, 200, 180))  
            pygame.draw.ellipse(fallback_surface, (200, 100, 255, 220), fallback_surface.get_rect().inflate(-20, -20))
            self.frames.append(fallback_surface)

        self.image = self.frames[self.current_frame_index]
        self.rect = self.image.get_rect()
        self.world_x = float(screen_spawn_x)

        
        initial_terrain_y = self.terrain.height_at(screen_spawn_x + self.rect.width / 2)
        self.rect.bottom = initial_terrain_y + 5
        self.world_y = float(self.rect.centery)

    def update(self, dx_world_scroll, terrain_obj, time_delta_seconds):  
        self.world_x -= dx_world_scroll
        self.rect.x = int(self.world_x)

     
        if self.rect and terrain_obj:
            current_center_x_for_terrain = self.rect.centerx
            y_terrain_base = terrain_obj.height_at(current_center_x_for_terrain)
            self.rect.bottom = y_terrain_base + 5
            self.world_y = float(self.rect.centery)

        
        if self.frames and len(self.frames) > 1:  
            self.animation_timer += time_delta_seconds
            if self.animation_timer >= PORTAL_ANIMATION_SPEED:
                self.animation_timer = 0.0 
                self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)

              
                old_center = self.rect.center
                self.image = self.frames[self.current_frame_index]
                self.rect = self.image.get_rect(center=old_center)

        if self.rect.right < 0:
            self.kill()

    def draw(self, surface, camera_y_offset):
        if self.image and self.rect:
            portal_screen_y = self.rect.y - camera_y_offset
            surface.blit(self.image, (self.rect.x, portal_screen_y))
