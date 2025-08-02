# hud.py
import pygame
import math
import os


class HUD:
    def __init__(self, font, hud_font):
        self.font = font
        self.hud_font = hud_font

        self.primary_color = (230, 230, 245)
        self.secondary_color = (180, 180, 200)
        self.warning_color = (255, 100, 100)
        self.critical_color = (255, 50, 50)
        self.bar_bg_color = (40, 40, 60, 200) 
        self.bar_border_color = (120, 120, 150, 220)
        self.health_bar_green = (80, 220, 80)
        self.health_bar_yellow = (230, 230, 90)
        self.health_bar_red = (220, 80, 80)
        self.flash_color = (255, 255, 255)

        self.health_icon = None
        self.bullet_icon = None
        self.checkpoint_icon = None
        self.load_assets()

        self.displayed_health = 100
        self.previous_actual_health = 100
        self.health_change_flash_timer = 0
        self.health_change_flash_duration = 350  

        self.low_ammo_pulse_timer = 0
        self.critical_health_pulse_timer = 0
        self._last_pulse_update_time = pygame.time.get_ticks() 

    def load_assets(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(script_dir, "assets")

        if not os.path.isdir(assets_dir):
            project_root_alt = os.path.dirname(script_dir)
            assets_dir_alt = os.path.join(project_root_alt, "assets")
            if os.path.isdir(assets_dir_alt):
                assets_dir = assets_dir_alt
            else:
                print(
                    f"HUD Warning: Could not locate 'assets' directory from {script_dir} or its parent. Placeholder icons will be used.")
                self._create_placeholder_icon("health")
                self._create_placeholder_icon("bullet")
                self._create_placeholder_icon("checkpoint")
                return

        icon_size = (34, 34) 

        try:
            path = os.path.join(assets_dir, "icon_health.png")
            if os.path.exists(path):
                self.health_icon = pygame.image.load(path).convert_alpha()
                self.health_icon = pygame.transform.smoothscale(self.health_icon, icon_size)
            else:
                self._create_placeholder_icon("health")
        except Exception as e:
            print(f"HUD: Error loading health icon: {e}"); self._create_placeholder_icon("health")

        try:
            path = os.path.join(assets_dir, "icon_bullet.png")
            if os.path.exists(path):
                self.bullet_icon = pygame.image.load(path).convert_alpha()
                self.bullet_icon = pygame.transform.smoothscale(self.bullet_icon, icon_size)
            else:
                self._create_placeholder_icon("bullet")
        except Exception as e:
            print(f"HUD: Error loading bullet icon: {e}"); self._create_placeholder_icon("bullet")

        try:
            path_specific = os.path.join(assets_dir, "icon_checkpoint.png")
            path_fallback = os.path.join(assets_dir, "BeconGreen.png")  

            loaded_checkpoint_img = None
            if os.path.exists(path_specific):
                loaded_checkpoint_img = pygame.image.load(path_specific).convert_alpha()
            elif os.path.exists(path_fallback):
                loaded_checkpoint_img = pygame.image.load(path_fallback).convert_alpha()

            if loaded_checkpoint_img:
              
                img_w, img_h = loaded_checkpoint_img.get_size()
                if img_h > img_w * 1.3: 
                    scaled_h = icon_size[1]
                    aspect_ratio = img_w / img_h if img_h > 0 else 1
                    scaled_w = max(1, int(scaled_h * aspect_ratio))
                    self.checkpoint_icon = pygame.transform.smoothscale(loaded_checkpoint_img, (scaled_w, scaled_h))
                else:
                    self.checkpoint_icon = pygame.transform.smoothscale(loaded_checkpoint_img, icon_size)
            else:
                self._create_placeholder_icon("checkpoint")
        except Exception as e:
            print(f"HUD: Error loading checkpoint icon: {e}"); self._create_placeholder_icon("checkpoint")

    def _create_placeholder_icon(self, icon_type):
        icon_size = (28, 28)
        surf = pygame.Surface(icon_size, pygame.SRCALPHA)
        if icon_type == "health":
            pygame.draw.circle(surf, (220, 50, 50), (icon_size[0] // 2, icon_size[1] // 2), icon_size[0] // 2 - 3)
            pygame.draw.line(surf, (255, 150, 150), (icon_size[0] // 2, 5), (icon_size[0] // 2, icon_size[1] - 5), 4)
            pygame.draw.line(surf, (255, 150, 150), (5, icon_size[1] // 2), (icon_size[0] - 5, icon_size[1] // 2), 4)
            self.health_icon = surf
        elif icon_type == "bullet":
            pygame.draw.rect(surf, (220, 220, 80),
                             (icon_size[0] // 3, icon_size[1] // 6, icon_size[0] // 3, icon_size[1] * 0.7),
                             border_radius=3)
            pygame.draw.polygon(surf, (180, 180, 60), [(icon_size[0] // 3, icon_size[1] // 6),
                                                       (icon_size[0] // 3 + icon_size[0] // 3, icon_size[1] // 6),
                                                       (icon_size[0] // 2, 3)])
            self.bullet_icon = surf
        elif icon_type == "checkpoint":
            pygame.draw.polygon(surf, (80, 220, 220), [(3, icon_size[1] // 2), (icon_size[0] // 2, 3),
                                                       (icon_size[0] - 3, icon_size[1] // 2),
                                                       (icon_size[0] // 2, icon_size[1] - 3)])
            pygame.draw.circle(surf, (255, 255, 255), (icon_size[0] // 2, icon_size[1] // 2), 3)
            self.checkpoint_icon = surf
        print(f"HUD: Created placeholder for {icon_type} icon.")

    def draw_health_bar(self, surface, current_health, max_health, x, y, width, height, delta_time_ms):
        
        if current_health < self.previous_actual_health and self.health_change_flash_timer <= 0:
            self.health_change_flash_timer = self.health_change_flash_duration
        self.previous_actual_health = current_health

        
        
        transition_speed_factor = delta_time_ms / 150.0
        if abs(self.displayed_health - current_health) > 0.01: 
            self.displayed_health += (current_health - self.displayed_health) * transition_speed_factor
            self.displayed_health = max(0, min(max_health, self.displayed_health)) 
        else:
            self.displayed_health = current_health

        health_percent_display = self.displayed_health / max_health if max_health > 0 else 0
        health_percent_actual = current_health / max_health if max_health > 0 else 0

        
        icon_spacing = 10
        text_spacing = 10
        bar_corner_radius = 7

        
        current_x_offset = x
        if self.health_icon:
            icon_y = y + (height - self.health_icon.get_height()) // 2
            surface.blit(self.health_icon, (current_x_offset, icon_y))
            current_x_offset += self.health_icon.get_width() + icon_spacing

        bar_x = current_x_offset
        bar_rect_on_surface = pygame.Rect(bar_x, y, width, height)

        
        bar_area_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        bar_local_rect = bar_area_surface.get_rect()

        
        pygame.draw.rect(bar_area_surface, self.bar_bg_color, bar_local_rect, border_radius=bar_corner_radius)

        
        fill_width = int(width * health_percent_display)
        fill_rect_local = pygame.Rect(0, 0, fill_width, height)

        health_color_fill = self.health_bar_green
        if health_percent_actual <= 0.6: health_color_fill = self.health_bar_yellow
        if health_percent_actual <= 0.3: health_color_fill = self.health_bar_red
        pygame.draw.rect(bar_area_surface, health_color_fill, fill_rect_local, border_radius=bar_corner_radius)

        
        if self.health_change_flash_timer > 0:
            progress = (
                                   self.health_change_flash_duration - self.health_change_flash_timer) / self.health_change_flash_duration
            flash_alpha = int(255 * math.sin(progress * math.pi))  

            if flash_alpha > 0: 
                flash_color_with_alpha = (self.flash_color[0], self.flash_color[1], self.flash_color[2], flash_alpha)

             
                flash_surface = pygame.Surface(bar_local_rect.size, pygame.SRCALPHA)
             
                pygame.draw.rect(flash_surface, flash_color_with_alpha, flash_surface.get_rect(),
                                 border_radius=bar_corner_radius)

                
                bar_area_surface.blit(flash_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

            self.health_change_flash_timer -= delta_time_ms
            if self.health_change_flash_timer < 0: self.health_change_flash_timer = 0

        surface.blit(bar_area_surface, (bar_x, y))  
        pygame.draw.rect(surface, self.bar_border_color, bar_rect_on_surface, 2, border_radius=bar_corner_radius)

        
        health_text_str = f"{int(current_health)} / {max_health}"
        health_text_surf = self.hud_font.render(health_text_str, True, self.primary_color)
        text_x = bar_x + width + text_spacing
        text_y = y + (height - health_text_surf.get_height()) // 2
        surface.blit(health_text_surf, (text_x, text_y))

        
        if health_percent_actual <= 0.25: 
            self.critical_health_pulse_timer += delta_time_ms * 0.008
            pulse_alpha = int(abs(math.sin(self.critical_health_pulse_timer) * 70)) + 30  
            pulse_color = (self.critical_color[0], self.critical_color[1], self.critical_color[2], pulse_alpha)

            glow_rect = bar_rect_on_surface.inflate(10, 10) 
            glow_surface = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, pulse_color, glow_surface.get_rect(), border_radius=bar_corner_radius + 5)
            surface.blit(glow_surface, glow_rect.topleft)

    def draw_bullet_counter(self, surface, bullets_remaining, max_bullets, x, y, delta_time_ms):
        icon_spacing = 10
        text_spacing = 10

        height_ref = self.bullet_icon.get_height() if self.bullet_icon else 30
        current_x_offset = x

        if self.bullet_icon:
            icon_y = y + (height_ref - self.bullet_icon.get_height()) // 2
            surface.blit(self.bullet_icon, (current_x_offset, icon_y))
            current_x_offset += self.bullet_icon.get_width() + icon_spacing

        bullet_text_str = f"{bullets_remaining} / {max_bullets}"

        text_color = self.primary_color
        
        is_low_ammo = (bullets_remaining <= max_bullets * 0.25 and max_bullets > 0) or bullets_remaining == 0

        if bullets_remaining == 0:
            text_color = self.critical_color
        elif is_low_ammo:
            self.low_ammo_pulse_timer += delta_time_ms * 0.01  
            pulse_factor = (math.sin(self.low_ammo_pulse_timer) + 1) / 2  
            
            text_color = (
                int(self.primary_color[0] * (1 - pulse_factor) + self.warning_color[0] * pulse_factor),
                int(self.primary_color[1] * (1 - pulse_factor) + self.warning_color[1] * pulse_factor),
                int(self.primary_color[2] * (1 - pulse_factor) + self.warning_color[2] * pulse_factor)
            )

        bullet_text_surf = self.hud_font.render(bullet_text_str, True, text_color)
        text_y = y + (height_ref - bullet_text_surf.get_height()) // 2
        surface.blit(bullet_text_surf, (current_x_offset, text_y))

    def draw_checkpoint_counter(self, surface, collected, total, x, y):
        icon_spacing = 10
        text_spacing = 10
        height_ref = self.checkpoint_icon.get_height() if self.checkpoint_icon else 30
        current_x_offset = x

        if self.checkpoint_icon:
            icon_y = y + (height_ref - self.checkpoint_icon.get_height()) // 2
            surface.blit(self.checkpoint_icon, (current_x_offset, icon_y))
            current_x_offset += self.checkpoint_icon.get_width() + icon_spacing

        checkpoint_text_str = f"NODE: {collected} / {total}"
        checkpoint_text_surf = self.hud_font.render(checkpoint_text_str, True, self.primary_color)
        text_y = y + (height_ref - checkpoint_text_surf.get_height()) // 2
        surface.blit(checkpoint_text_surf, (current_x_offset, text_y))

    def draw(self, surface, gs_obj, player_obj, config_obj, time_delta_seconds):
        delta_time_ms = int(time_delta_seconds * 1000)

        margin = 25
        hud_element_spacing = 18  

        
        health_bar_width = 240
        health_bar_height = 26 
        health_x = margin
        health_y = margin
        self.draw_health_bar(surface, gs_obj.player_health, config_obj.MAX_PLAYER_HEALTH,
                             health_x, health_y, health_bar_width, health_bar_height, delta_time_ms)

        
        ref_h_health = health_bar_height
        if self.health_icon: ref_h_health = max(health_bar_height, self.health_icon.get_height())
        bullet_y = health_y + ref_h_health + hud_element_spacing

        if player_obj: 
            self.draw_bullet_counter(surface, player_obj.bullets_remaining, config_obj.MAX_BULLETS,
                                     margin, bullet_y, delta_time_ms)

        
        if not gs_obj.is_level_2_simple_mode and len(config_obj.CHECKPOINT_DISTANCES) > 0:
            ref_h_bullet = 30
            if self.bullet_icon: ref_h_bullet = self.bullet_icon.get_height()

            checkpoint_y = bullet_y + ref_h_bullet + hud_element_spacing
            checkpoint_x = margin
            self.draw_checkpoint_counter(surface, gs_obj.collected_checkpoints, len(config_obj.CHECKPOINT_DISTANCES),
                                         checkpoint_x, checkpoint_y)