# ramp.py

import pygame
from config import FINAL_RAMP_HEIGHT_RISE, WIDTH

class Ramp:
    def __init__(self, screen_spawn_x, terrain_obj, is_final_ramp=False):
        self.screen_spawn_x = screen_spawn_x
        self.length = 350
        self.height_rise = FINAL_RAMP_HEIGHT_RISE if is_final_ramp else 250
        self.terrain = terrain_obj
        self.base_y_at_start = self.terrain.height_at(self.screen_spawn_x)
        self.end_x_screen = self.screen_spawn_x + self.length
        self.is_final = is_final_ramp

    def update(self, dx_scroll):
        self.screen_spawn_x -= dx_scroll
        self.end_x_screen -= dx_scroll
        if 0 <= self.screen_spawn_x < WIDTH:
            self.base_y_at_start = self.terrain.height_at(self.screen_spawn_x)

    def draw(self, surface, cam_y):
        p1y = self.base_y_at_start - cam_y
        p2y = (self.base_y_at_start - self.height_rise) - cam_y
        p1 = (self.screen_spawn_x, p1y)
        p2 = (self.end_x_screen, p2y)

        if self.end_x_screen > 0 and self.screen_spawn_x < WIDTH:
            p_bottom_right = (self.end_x_screen, p1y + 5)
            p_bottom_left = (self.screen_spawn_x, p1y + 5)
            pygame.draw.polygon(surface, (180, 180, 190), [p1, p2, p_bottom_right, p_bottom_left])

    def on_ramp(self, player_obj):
        if self.screen_spawn_x <= player_obj.x <= self.end_x_screen:
            if self.length == 0:
                return self.base_y_at_start
            return self.base_y_at_start - ((player_obj.x - self.screen_spawn_x) / self.length) * self.height_rise
        return None
