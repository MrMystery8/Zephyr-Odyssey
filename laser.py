# laser.py
import pygame
import math
import os
import sys
from config import LASER_SPEED_X, LASER_GRAVITY, WIDTH, HEIGHT


class Laser(pygame.sprite.Sprite):
    def __init__(self, start_screen_x, start_world_y, target_rock=None):
        super().__init__()

        
        base_width = 15
        base_height = 4

        
        overlay_loaded_image = None
        try:
        
            script_dir = os.path.dirname(
                os.path.abspath(sys.argv[0] if hasattr(sys, 'argv') and sys.argv else __file__))
            assets_dir = os.path.join(script_dir, "assets")
            if not os.path.isdir(assets_dir):  
                parent_dir = os.path.dirname(script_dir)
                assets_dir = os.path.join(parent_dir, "assets")

            image_path = os.path.join(assets_dir, "laser.png")

            if os.path.exists(image_path):
                overlay_loaded_image = pygame.image.load(image_path).convert_alpha()
           
           
        except Exception as e:
            print(f"Error loading laser.png for overlay: {e}. Overlay will not be applied.")

      
        if overlay_loaded_image:
            self.image = pygame.Surface((base_width, base_height), pygame.SRCALPHA)
       
            self.image.fill((255, 0, 0, 255))

       
            overlay_rect = overlay_loaded_image.get_rect(center=self.image.get_rect().center)
            self.image.blit(overlay_loaded_image, overlay_rect)
        else:
           
            self.image = pygame.Surface((base_width, base_height))
            self.image.fill((255, 0, 0))
        

        self.rect = self.image.get_rect(left=int(start_screen_x), centery=int(start_world_y))

        self.world_x = float(start_screen_x) 
        self.world_y = float(start_world_y)  

        self.target_rock = target_rock 
        self.is_homing = target_rock is not None

        if self.is_homing and self.target_rock:
            dx = self.target_rock.rect.centerx - self.world_x
            dy = self.target_rock.rect.centery - self.world_y
            distance = math.hypot(dx, dy)
            if distance == 0: distance = 1  
            self.vx = (dx / distance) * LASER_SPEED_X
            self.vy = (dy / distance) * LASER_SPEED_X
        else: 
            self.is_homing = False 
            self.vx = LASER_SPEED_X
            self.vy = 0  

    def update(self, camera_y_offset): 
        if self.is_homing:
            if self.target_rock and self.target_rock.alive():
              
                dx = self.target_rock.rect.centerx - self.world_x
                dy = self.target_rock.rect.centery - self.world_y
                distance = math.hypot(dx, dy)

             
                if distance < LASER_SPEED_X * 1.5: 
                    self.world_x = self.target_rock.rect.centerx
                    self.world_y = self.target_rock.rect.centery
                elif distance > 0: 
                    self.vx = (dx / distance) * LASER_SPEED_X
                    self.vy = (dy / distance) * LASER_SPEED_X

                self.world_x += self.vx
                self.world_y += self.vy
            else: 
                self.is_homing = False
               
                self.vy += LASER_GRAVITY
                self.world_x += self.vx
                self.world_y += self.vy
        else:  
            self.vy += LASER_GRAVITY
            self.world_x += self.vx
            self.world_y += self.vy

      
        self.rect.x = int(self.world_x)
        self.rect.y = int(self.world_y)

      
        screen_y_pos = self.world_y - camera_y_offset 
        if self.rect.left > WIDTH or self.rect.right < 0 or \
                screen_y_pos > HEIGHT + 50 or screen_y_pos < -self.rect.height - 50:
            self.kill()