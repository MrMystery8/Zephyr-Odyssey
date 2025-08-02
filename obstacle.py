# obstacle.py
import pygame
import math
import random
import os
import sys
import config
from config import PLAYER_SCREEN_X, WIDTH, \
    HEIGHT
import game_state as gs
from debris_effect import DebrisEffect


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, screen_spawn_x, terrain_obj, image_asset_path_name=None, is_tutorial_obstacle=False):
        super().__init__()
        self.image_asset_path_name = image_asset_path_name
        self.is_tutorial_obstacle = is_tutorial_obstacle
        self.obstacle_type = "generic"
        self.damage_value = 10
        self.destructible = True
        self.debris_material = "rock"

        self.terrain = terrain_obj
        self.image = None
        self.rect = None
        self.world_x = float(screen_spawn_x)

     
        if not isinstance(self, (IceFormation, BrokenSatellite, BugObstacle)): 
            self._setup_visuals_and_rect(screen_spawn_x, terrain_obj)

        if self.rect:
            if not isinstance(self, (BrokenSatellite, BugObstacle, CrystalObstacle)):
                current_terrain_y = self.terrain.height_at(self.world_x + self.rect.width / 2)
                if self.is_tutorial_obstacle:
                    tut_x_center = PLAYER_SCREEN_X + WIDTH // 3
                    
                    is_falling_tutorial_satellite = isinstance(self, BrokenSatellite) and \
                                                    hasattr(self, 'is_special_falling_satellite') and \
                                                    self.is_special_falling_satellite
                    if not is_falling_tutorial_satellite:
                        self.world_x = float(tut_x_center - self.rect.width / 2)
                        self.rect.midbottom = (tut_x_center, self.terrain.height_at(tut_x_center))
                else:
                    self.rect.midbottom = (int(self.world_x + self.rect.width / 2), current_terrain_y)
        elif not self.image:
            self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
            self.rect = self.image.get_rect(topleft=(int(self.world_x), terrain_obj.height_at(self.world_x)))

    def _load_image_asset(self, target_width, target_height):
        if self.image_asset_path_name:
            try:
                main_script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                path = os.path.join(main_script_dir, "assets", self.image_asset_path_name)

                if not os.path.exists(path):
                    current_file_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root_dir = os.path.dirname(current_file_dir)
                    path = os.path.join(project_root_dir, "assets", self.image_asset_path_name)
                    if not os.path.exists(path) and project_root_dir != main_script_dir:
                        path = os.path.join(current_file_dir, "assets", self.image_asset_path_name)

                if os.path.exists(path):
                    loaded_image = pygame.image.load(path).convert_alpha()
                    return pygame.transform.smoothscale(loaded_image, (target_width, target_height))
                else:
                    print(f"Obstacle image not found for: {self.image_asset_path_name} at path {path}")
            except Exception as e:
                print(f"Error loading obstacle image '{self.image_asset_path_name}': {e}")
        return None

    def _setup_visuals_and_rect(self, screen_spawn_x, terrain_obj):
        self.world_x = float(screen_spawn_x)
        width_to_use = config.OBSTACLE_SPRITE_WIDTH
        height_to_use = config.OBSTACLE_SPRITE_HEIGHT
        loaded_img = self._load_image_asset(width_to_use, height_to_use)
        if loaded_img:
            self.image = loaded_img
        else:
            self.image = pygame.Surface((width_to_use, height_to_use), pygame.SRCALPHA)
            self.image.fill((128, 128, 128, 128))

        if self.image:
            self.rect = self.image.get_rect()
            initial_y = terrain_obj.height_at(self.world_x + self.rect.width / 2)
            self.rect.midbottom = (int(self.world_x + self.rect.width / 2), initial_y)

    def update(self, dx_world_scroll, game_state_current, time_delta_seconds=0, player_obj=None,
               effects_creation_group=None):
        if self.rect is None: return

        if game_state_current != gs.TUTORIAL:
            self.world_x -= dx_world_scroll
            self.rect.x = int(self.world_x)

        current_center_x_for_terrain = self.rect.centerx
        y_terrain_base = self.terrain.height_at(current_center_x_for_terrain)
        self.rect.bottom = y_terrain_base

        if game_state_current != gs.TUTORIAL and self.rect.right < 0:
            self.kill()

    def on_destroy(self):
        center_x = self.rect.centerx if self.rect else self.world_x
        center_y = self.rect.centery if self.rect else self.terrain.height_at(self.world_x)
        return self.debris_material, center_x, center_y, self.obstacle_type

    def draw(self, surface, camera_y_offset):
        if self.image and self.rect:
            obs_screen_y = self.rect.y - camera_y_offset
            surface.blit(self.image, (self.rect.x, obs_screen_y))


class IceFormation(Obstacle):
    def __init__(self, screen_spawn_x, terrain_obj, image_asset_path_name=None,
                 is_tutorial_obstacle=False):
        self.is_erupting = False
        self.has_erupted = False
        self.current_eruption_height = 0.01
        self.eruption_speed = random.uniform(350, 550)
        self.base_image = None
        self.spike_overlay_image_base = None
        self.eruption_proximity_range = WIDTH * 0.45
        self.spawn_debris_on_eruption = True
        self.glint_timer = 0
        self.glint_next_time = 0
        self.glint_duration = random.randint(80, 200)
        self.glint_active = False
        self.glint_alpha = 0
        self.glint_elements = []

        super().__init__(screen_spawn_x, terrain_obj, image_asset_path_name=None,
                         is_tutorial_obstacle=is_tutorial_obstacle)
        self.obstacle_type = "ice_formation"
        self.damage_value = 25
        self.debris_material = "ice"
        self.destructible = True
        self._setup_visuals_and_rect(screen_spawn_x, terrain_obj)
        if self.spike_overlay_image_base:
            self.image = pygame.Surface((config.ICE_SPIKE_OVERLAY_WIDTH, 1), pygame.SRCALPHA)
        elif self.base_image:
            self.image = pygame.Surface((self.base_image.get_width(), 1), pygame.SRCALPHA)
        else:
            self.image = pygame.Surface((10, 1), pygame.SRCALPHA)

        if not self.rect:
            self.rect = self.image.get_rect()
            initial_y = self.terrain.height_at(self.world_x + (self.rect.width / 2 if self.rect else 0))
            self.rect.midbottom = (int(self.world_x + (self.rect.width / 2 if self.rect else 0)), initial_y)
        self._update_erupting_image(initial_setup=True)

    def _setup_visuals_and_rect(self, screen_spawn_x, terrain_obj):
        self.world_x = float(screen_spawn_x)
        self.target_formation_height = config.ICE_SPIKE_OVERLAY_HEIGHT
        formation_visual_width = config.ICE_SPIKE_OVERLAY_WIDTH
        extra_draw_depth = 50
        temp_render_surf_height = self.target_formation_height + extra_draw_depth
        temp_render_surf = pygame.Surface((formation_visual_width, temp_render_surf_height), pygame.SRCALPHA)
        temp_render_surf.fill((0, 0, 0, 0))
        num_main_spikes = random.randint(4, 7)
        for i in range(num_main_spikes):
            spike_tilt_angle_rad = math.radians(random.uniform(-25, 25))
            spike_height = self.target_formation_height * random.uniform(0.5, 1.0)
            spike_height = max(30, spike_height)
            base_y_on_surf = temp_render_surf_height - 1 - random.uniform(0, extra_draw_depth * 0.3)
            spike_base_width = max(4, spike_height * random.uniform(0.08, 0.20))
            base_center_x = (formation_visual_width / 2) + (random.uniform(-0.45, 0.45) * formation_visual_width)
            tip_x = base_center_x - spike_height * math.sin(spike_tilt_angle_rad)
            tip_y = base_y_on_surf - spike_height * math.cos(spike_tilt_angle_rad)
            dx_base = (spike_base_width / 2) * math.cos(spike_tilt_angle_rad)
            dy_base = (spike_base_width / 2) * math.sin(spike_tilt_angle_rad)
            bl_x, bl_y = base_center_x - dy_base, base_y_on_surf + dx_base
            br_x, br_y = base_center_x + dy_base, base_y_on_surf - dx_base
            main_spike_points = [(tip_x, tip_y), (bl_x, bl_y), (br_x, br_y)]
            main_ice_color = (250, 250, 255, random.randint(100, 150))
            highlight_color = (220, 230, 255, random.randint(80, 120))
            try:
                pygame.draw.polygon(temp_render_surf, main_ice_color, main_spike_points)
                pygame.draw.lines(temp_render_surf, highlight_color, False, main_spike_points, 1)
            except (ValueError, TypeError) as e:
                print(f"Error drawing procedural spike for base: {e}")
        self.base_image = temp_render_surf
        try:
            main_script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            overlay_path = os.path.join(main_script_dir, "assets", config.ICE_SPIKE_IMAGE_FILENAME)
            if not os.path.exists(overlay_path):
                current_file_dir = os.path.dirname(os.path.abspath(__file__))
                project_root_dir = os.path.dirname(current_file_dir)
                overlay_path = os.path.join(project_root_dir, "assets", config.ICE_SPIKE_IMAGE_FILENAME)
                if not os.path.exists(overlay_path) and project_root_dir != main_script_dir:
                    overlay_path = os.path.join(current_file_dir, "assets", config.ICE_SPIKE_IMAGE_FILENAME)
            if os.path.exists(overlay_path):
                loaded_overlay = pygame.image.load(overlay_path).convert_alpha()
                self.spike_overlay_image_base = pygame.transform.smoothscale(
                    loaded_overlay, (config.ICE_SPIKE_OVERLAY_WIDTH, config.ICE_SPIKE_OVERLAY_HEIGHT)
                )
            else:
                print(
                    f"ERROR: Spike overlay image '{config.ICE_SPIKE_IMAGE_FILENAME}' not found at {overlay_path}. Using fallback.")
                self.spike_overlay_image_base = pygame.Surface(
                    (config.ICE_SPIKE_OVERLAY_WIDTH, config.ICE_SPIKE_OVERLAY_HEIGHT), pygame.SRCALPHA)
                self.spike_overlay_image_base.fill((200, 220, 255, 200))
        except Exception as e:
            print(f"Error loading spike overlay image '{config.ICE_SPIKE_IMAGE_FILENAME}': {e}")
            self.spike_overlay_image_base = pygame.Surface(
                (config.ICE_SPIKE_OVERLAY_WIDTH, config.ICE_SPIKE_OVERLAY_HEIGHT), pygame.SRCALPHA)
            self.spike_overlay_image_base.fill((200, 220, 255, 180))
        self.rect = pygame.Rect(0, 0, config.ICE_SPIKE_OVERLAY_WIDTH, config.ICE_SPIKE_OVERLAY_HEIGHT)
        initial_y_on_terrain = terrain_obj.height_at(self.world_x + self.rect.width / 2)
        self.rect.midbottom = (int(self.world_x + self.rect.width / 2), initial_y_on_terrain)

    def _update_erupting_image(self, initial_setup=False):
        if not self.spike_overlay_image_base:
            if self.base_image:
                source_image_for_subsurface = self.base_image
                target_h = self.base_image.get_height() - 50
            else:
                self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
                self.image.fill((255, 0, 0, 100))
                if self.rect:
                    original_center_x = self.world_x + self.rect.width / 2
                    original_bottom_y_on_terrain = self.terrain.height_at(original_center_x)
                    self.rect = self.image.get_rect(midbottom=(int(original_center_x), original_bottom_y_on_terrain))
                else:
                    self.rect = self.image.get_rect(center=(0, 0))
                return
        else:
            source_image_for_subsurface = self.spike_overlay_image_base
            target_h = self.target_formation_height
        original_center_x = self.world_x + (
            config.ICE_SPIKE_OVERLAY_WIDTH / 2 if not self.rect else self.rect.width / 2)
        original_bottom_y_on_terrain = self.terrain.height_at(original_center_x)
        erupt_h_visual = int(max(1, self.current_eruption_height))
        sub_y_offset_from_top_of_source = source_image_for_subsurface.get_height() - erupt_h_visual
        sub_y_offset_from_top_of_source = max(0, sub_y_offset_from_top_of_source)
        actual_sub_h = min(erupt_h_visual, source_image_for_subsurface.get_height() - sub_y_offset_from_top_of_source)
        actual_sub_h = max(1, actual_sub_h)
        if source_image_for_subsurface.get_width() > 0 and actual_sub_h > 0:
            try:
                self.image = source_image_for_subsurface.subsurface(pygame.Rect(
                    0, sub_y_offset_from_top_of_source,
                    source_image_for_subsurface.get_width(), actual_sub_h
                ))
                current_image_rect = self.image.get_rect(
                    midbottom=(int(original_center_x), original_bottom_y_on_terrain))
                self.rect.size = current_image_rect.size
                self.rect.midbottom = current_image_rect.midbottom
            except ValueError as e:
                self.image = source_image_for_subsurface.copy()
                self.rect = self.image.get_rect(midbottom=(int(original_center_x), original_bottom_y_on_terrain))
                self.current_eruption_height = target_h
                self.is_erupting = False
                if not initial_setup: self.glint_next_time = pygame.time.get_ticks() + random.randint(500, 1500)
                print(f"Error during subsurface for IceFormation: {e}. Showing full image.")
        else:
            self.image = source_image_for_subsurface.copy()
            self.rect = self.image.get_rect(midbottom=(int(original_center_x), original_bottom_y_on_terrain))
            self.current_eruption_height = target_h
            if not self.is_erupting and not initial_setup: self.glint_next_time = pygame.time.get_ticks() + random.randint(
                500, 1500)
            self.is_erupting = False

    def update(self, dx_world_scroll, game_state_current, time_delta_seconds=0, player_obj=None,
               effects_creation_group=None):
        if not hasattr(self, 'rect') or self.rect is None:
            if hasattr(self, 'world_x'): self._setup_visuals_and_rect(self.world_x, self.terrain)
            if not hasattr(self, 'rect') or self.rect is None: self.kill(); return

        if game_state_current != gs.TUTORIAL:
            self.world_x -= dx_world_scroll

        if player_obj and not self.has_erupted and not self.is_erupting:
            distance_to_player_x = abs((self.world_x + self.rect.width / 2) - player_obj.rect.centerx)
            current_screen_x_center = self.world_x + (self.rect.width / 2)
            if distance_to_player_x < self.eruption_proximity_range and \
                    current_screen_x_center + (self.rect.width / 2) > 0 and \
                    current_screen_x_center - (self.rect.width / 2) < WIDTH:
                self.is_erupting = True
                self.has_erupted = True
                if self.current_eruption_height < 1.0: self.current_eruption_height = 1.0
        target_height_for_eruption = config.ICE_SPIKE_OVERLAY_HEIGHT
        if self.is_erupting:
            if target_height_for_eruption > 0 and self.current_eruption_height < target_height_for_eruption:
                self.current_eruption_height += self.eruption_speed * time_delta_seconds
                self.current_eruption_height = min(self.current_eruption_height, target_height_for_eruption)
                self._update_erupting_image()
            else:
                self.is_erupting = False
                self.glint_next_time = pygame.time.get_ticks() + random.randint(500, 1500)
                if self.current_eruption_height < target_height_for_eruption:
                    self.current_eruption_height = target_height_for_eruption
                    self._update_erupting_image()
        if not self.is_erupting and self.has_erupted:
            current_time = pygame.time.get_ticks()
            if not self.glint_active and current_time >= self.glint_next_time:
                self.glint_active = True
                self.glint_timer = current_time
                self.glint_alpha = 255
                self.glint_elements = []
                if self.rect and self.image and self.image.get_width() > 0 and self.image.get_height() > 0:
                    num_glints = random.randint(1, 3)
                    for _ in range(num_glints):
                        start_x = random.uniform(self.image.get_width() * .05, self.image.get_width() * .95)
                        start_y = random.uniform(self.image.get_height() * .05, self.image.get_height() * .25)
                        length = random.uniform(self.image.get_height() * .05, self.image.get_height() * .25)
                        angle = random.uniform(-math.pi / 2.5, math.pi / 2.5)
                        end_x = start_x + length * math.cos(angle)
                        end_y = start_y + length * math.sin(angle)
                        self.glint_elements.append({'start': (start_x, start_y), 'end': (end_x, end_y),
                                                    'alpha_multi': random.uniform(0.7, 1.0),
                                                    'thickness': random.randint(1, 2)})
            if self.glint_active:
                elapsed = current_time - self.glint_timer
                if elapsed > self.glint_duration:
                    self.glint_active = False
                    self.glint_next_time = current_time + random.randint(800, 2500)
                    if self.current_eruption_height >= target_height_for_eruption:
                        self._update_erupting_image()
                else:
                    progress = elapsed / self.glint_duration
                    self.glint_alpha = 255 * (1 - progress ** 2.0)
                    current_img_for_glint = self.image
                    if not self.is_erupting and self.current_eruption_height >= target_height_for_eruption and self.spike_overlay_image_base:
                        sub_y_offset = self.spike_overlay_image_base.get_height() - int(target_height_for_eruption)
                        sub_h = int(target_height_for_eruption)
                        if sub_y_offset >= 0 and sub_h > 0 and self.spike_overlay_image_base.get_height() >= sub_y_offset + sub_h:
                            try:
                                current_img_for_glint = self.spike_overlay_image_base.subsurface(
                                    pygame.Rect(0, sub_y_offset, self.spike_overlay_image_base.get_width(), sub_h))
                            except ValueError:
                                current_img_for_glint = self.spike_overlay_image_base.copy() if self.spike_overlay_image_base else self.image
                        else:
                            current_img_for_glint = self.spike_overlay_image_base.copy() if self.spike_overlay_image_base else self.image
                    if current_img_for_glint and current_img_for_glint.get_width() > 0 and current_img_for_glint.get_height() > 0:
                        temp_image_for_glint = current_img_for_glint.copy()
                        if self.glint_alpha > 10:
                            for glint_el in self.glint_elements:
                                alpha = int(self.glint_alpha * glint_el['alpha_multi'])
                                if alpha > 10:
                                    try:
                                        pygame.draw.line(temp_image_for_glint, (255, 255, 255, alpha),
                                                         glint_el['start'], glint_el['end'], glint_el['thickness'])
                                    except (TypeError, ValueError):
                                        pass
                        self.image = temp_image_for_glint
        if self.rect:
            current_center_x = self.world_x + self.rect.width / 2
            self.rect.midbottom = (int(current_center_x), self.terrain.height_at(current_center_x))
        if game_state_current != gs.TUTORIAL and self.rect and self.rect.right < 0:
            self.kill()

    def draw(self, surface, camera_y_offset):
        super().draw(surface, camera_y_offset)


class BrokenSatellite(Obstacle):
    def __init__(self, screen_spawn_x, terrain_obj, image_asset_path_name="satellite.png", is_tutorial_obstacle=False,
                 crash_sound_obj=None, impact_sound_obj=None):
        self.smoke_particles = []
        self.max_smoke_particles = 50
        self.smoke_spawn_interval = 80
        self.last_smoke_spawn_time = 0
        self.y_sink_offset = 80

        self.is_special_falling_satellite = False
        self.current_visual_y_offset = 0.0
        self.fall_velocity = 0.0
        self.fall_acceleration = 0.0

        self.satellite_sprite_height = 220
        self.initial_fall_offset_val = - (self.satellite_sprite_height * 3.0)
        self.fall_duration_secs = 1.4
        self.has_impacted = False

        self.flame_particles = []
        self.max_flame_particles = 200
        self.flame_spawn_interval = 10
        self.last_flame_spawn_time = 0
        self.flame_colors = [(255, 100, 0), (255, 150, 0), (255, 50, 0), (255, 200, 50), (255, 180, 30), (255, 220, 80)]

        self.falling_sound_asset = crash_sound_obj
        self.impact_sound_asset = impact_sound_obj
        self.falling_sound_channel = None
        self.is_falling_sound_playing = False
        self.was_falling_sound_playing_before_pause = False

        self.is_special_falling_satellite = True
        self.current_visual_y_offset = self.initial_fall_offset_val
        distance_to_cover = abs(self.initial_fall_offset_val)
        if self.fall_duration_secs > 0:
            self.fall_acceleration = (2 * distance_to_cover) / (self.fall_duration_secs ** 2)
        else:
            self.fall_acceleration = 4000

        super().__init__(screen_spawn_x, terrain_obj, image_asset_path_name, is_tutorial_obstacle)

        if not self.image or (self.image and self.image.get_width() <= config.OBSTACLE_SPRITE_WIDTH):
            self._setup_visuals_and_rect(screen_spawn_x, terrain_obj)

        self.horizontal_entry_speed = 50.0
        self.obstacle_type = "satellite_debris"
        self.damage_value = 35
        self.debris_material = "machinery"
        self.destructible = True

        if self.falling_sound_asset and self.is_special_falling_satellite and not self.has_impacted:
            self._start_falling_sound()

    def _start_falling_sound(self):
        if self.falling_sound_asset and pygame.mixer.get_init() and not self.is_falling_sound_playing:
            try:
                self.falling_sound_channel = pygame.mixer.find_channel(True)
                if self.falling_sound_channel:
                    channel_repr = str(self.falling_sound_channel)
                 
                    self.falling_sound_channel.play(self.falling_sound_asset, loops=-1)
                    self.is_falling_sound_playing = True
                 
                else:
                 
                    self.is_falling_sound_playing = False
            except Exception as e:
                print(f"Satellite Obj {id(self)}: Error playing satellite falling sound: {e}")
                self.falling_sound_channel = None
                self.is_falling_sound_playing = False
            finally:
                if self.falling_sound_channel and self.falling_sound_channel.get_sound() == self.falling_sound_asset and self.falling_sound_channel.get_busy():
                    self.is_falling_sound_playing = True
                else:
                    self.is_falling_sound_playing = False

    def _stop_falling_sound(self):
        channel_repr_to_stop = 'N/A'
        channel_was_busy_with_our_sound = False

        if self.falling_sound_channel:
            channel_repr_to_stop = str(self.falling_sound_channel)
            if self.falling_sound_channel.get_sound() == self.falling_sound_asset and self.falling_sound_channel.get_busy():
                channel_was_busy_with_our_sound = True

        if channel_was_busy_with_our_sound:
       
            self.falling_sound_channel.stop()
        elif self.falling_sound_channel and self.falling_sound_channel.get_sound() == self.falling_sound_asset:
       
            self.falling_sound_channel.stop()
       

        self.falling_sound_channel = None
        self.is_falling_sound_playing = False
        self.was_falling_sound_playing_before_pause = False

    def pause_falling_sound(self):
        if self.is_falling_sound_playing and self.falling_sound_channel:
            if self.falling_sound_channel.get_sound() == self.falling_sound_asset and self.falling_sound_channel.get_busy():
                self.falling_sound_channel.pause()
                self.was_falling_sound_playing_before_pause = True
                self.is_falling_sound_playing = False
             
            else:
             
                self.was_falling_sound_playing_before_pause = False
                self.is_falling_sound_playing = False

    def resume_falling_sound(self):
        if self.was_falling_sound_playing_before_pause and self.falling_sound_channel:
            if self.falling_sound_channel.get_sound() == self.falling_sound_asset:
                self.falling_sound_channel.unpause()
                self.is_falling_sound_playing = True
              
            else:
              
                self.falling_sound_channel = None
                self._start_falling_sound()
            self.was_falling_sound_playing_before_pause = False
        elif not self.is_falling_sound_playing and self.falling_sound_asset and self.is_special_falling_satellite and not self.has_impacted:
           
            self._start_falling_sound()

    def _setup_visuals_and_rect(self, screen_spawn_x, terrain_obj):
        self.world_x = float(screen_spawn_x)
        satellite_width = 200
        loaded_img = self._load_image_asset(satellite_width, self.satellite_sprite_height)
        if loaded_img:
            self.image = loaded_img
        else:
            self.image = pygame.Surface((satellite_width, self.satellite_sprite_height), pygame.SRCALPHA)
            self.image.fill((100, 100, 110, 128))

        if self.image:
            self.rect = self.image.get_rect()
            terrain_y_for_anchor = terrain_obj.height_at(self.world_x + self.rect.width / 2)
            self.rect.midbottom = (int(self.world_x + self.rect.width / 2),
                                   terrain_y_for_anchor + int(self.current_visual_y_offset))

    def _generate_flame_polygon_points(self, center_x, center_y, size):
        num_points = random.randint(4, 7)
        points = []
        angle_step = 360 / num_points
        for i in range(num_points):
            angle_rad = math.radians(i * angle_step + random.uniform(-angle_step * 0.3, angle_step * 0.3))
            radius_factor = random.uniform(0.5, 1.2)
            if i % 2 == 0:
                radius_factor *= random.uniform(0.4, 0.8)
            else:
                radius_factor *= random.uniform(1.0, 1.5)
            flame_point_x = center_x + size * radius_factor * math.cos(angle_rad) 
            flame_point_y = center_y + size * radius_factor * math.sin(angle_rad) 
            points.append((flame_point_x, flame_point_y))
        return points

    def _update_flame_particles(self, time_delta_seconds, dx_world_scroll):
        current_time = pygame.time.get_ticks()
        if self.is_special_falling_satellite and self.rect:
            if current_time - self.last_flame_spawn_time > self.flame_spawn_interval:
                self.last_flame_spawn_time = current_time
                if len(self.flame_particles) < self.max_flame_particles:
                    num_new_flames = random.randint(7, 15)
                    for _ in range(num_new_flames):
                        angle_offset_from_fall = random.uniform(math.pi * 0.4, math.pi * 0.6)
                        spawn_angle = math.atan2(-self.fall_velocity if self.fall_velocity != 0 else -1,
                                                 0) + angle_offset_from_fall + random.uniform(-0.5, 0.5)
                        spawn_dist_from_center = random.uniform(self.rect.width * 0.2, self.rect.height * 0.6)
                        spawn_x_abs = self.rect.centerx + spawn_dist_from_center * math.cos(spawn_angle)
                        spawn_y_abs = self.rect.centery + spawn_dist_from_center * math.sin(spawn_angle)
                        
                        particle_diameter = random.randint(12, 28) 
                        
                        self.flame_particles.append({
                            'x': spawn_x_abs, 'y': spawn_y_abs,
                            'vx': random.uniform(-1.5, 1.5) + math.cos(spawn_angle) * 2.0,
                            'vy': random.uniform(-1.5, -0.5) + math.sin(spawn_angle) * 2.0 - (
                                    self.fall_velocity * 0.02),
                            'size': particle_diameter,
                            'start_size': particle_diameter, 
                            'alpha': random.randint(220, 255), 'max_alpha': 255,
                            'life': random.uniform(0.4, 0.8), 'max_life': 0.8,
                            'color': random.choice(self.flame_colors),
                            'rotation_speed': random.uniform(-120, 120), 'current_rotation': random.uniform(0, 360),
                            'poly_points_base': self._generate_flame_polygon_points(0, 0, particle_diameter / 2.0)
                        })
        active_flames = []
        for p in self.flame_particles:
            p['x'] += p['vx'] * (60 * time_delta_seconds)
            p['y'] += p['vy'] * (60 * time_delta_seconds)
            p['vy'] += 0.05 * (60 * time_delta_seconds)
            p['x'] -= dx_world_scroll
            p['life'] -= time_delta_seconds
            p['current_rotation'] = (p['current_rotation'] + p['rotation_speed'] * time_delta_seconds) % 360
            if p['max_life'] > 0 and p['life'] > 0:
                p['alpha'] = p['max_alpha'] * (p['life'] / p['max_life']) ** 0.5
            else:
                p['alpha'] = 0
            p['size'] *= (1 - 0.25 * time_delta_seconds) 
            if p['alpha'] > 15 and p['size'] > 4:
                active_flames.append(p)
        self.flame_particles = active_flames

    def update(self, dx_world_scroll, game_state_current, time_delta_seconds=0, player_obj=None,
               effects_creation_group=None):
        if self.rect is None: return

        if game_state_current != gs.TUTORIAL:
            self.world_x -= dx_world_scroll
            if self.is_special_falling_satellite and not self.has_impacted and not self.is_tutorial_obstacle:
                self.world_x -= self.horizontal_entry_speed * time_delta_seconds

        self.rect.x = int(self.world_x)

        if self.is_special_falling_satellite:
            if not self.has_impacted:
                self.fall_velocity += self.fall_acceleration * time_delta_seconds
                self.current_visual_y_offset += self.fall_velocity * time_delta_seconds

            self._update_flame_particles(time_delta_seconds,
                                         dx_world_scroll if game_state_current != gs.TUTORIAL else 0.0)

            if self.current_visual_y_offset >= 0.0 and not self.has_impacted:
                self.current_visual_y_offset = 0.0
                self.fall_velocity = 0.0
                self.has_impacted = True
                self._stop_falling_sound()

                if self.impact_sound_asset and pygame.mixer.get_init():
                    try:
                        self.impact_sound_asset.play()
                    except Exception as e:
                        print(f"Error playing satellite impact sound: {e}")

                gs.screen_shake_magnitude = 20
                gs.screen_shake_duration = 0.45
                if effects_creation_group and self.rect:
                    effects_creation_group.add(
                        DebrisEffect(self.rect.centerx, self.rect.bottom - self.y_sink_offset, "machinery",
                                     intensity=2.8))
                    effects_creation_group.add(
                        DebrisEffect(self.rect.centerx, self.rect.bottom - self.y_sink_offset, "snow_puff",
                                     intensity=5.5))
                self.flame_particles = []

        current_center_x_for_terrain = self.rect.centerx
        y_terrain_base = self.terrain.height_at(current_center_x_for_terrain)
        final_y_sink_to_apply = 0
        if self.has_impacted:
            final_y_sink_to_apply = self.y_sink_offset
        self.rect.bottom = y_terrain_base + int(self.current_visual_y_offset) + final_y_sink_to_apply

        if game_state_current != gs.TUTORIAL and self.rect.right < 0:
            self.kill()
            return

        current_time = pygame.time.get_ticks()
        if self.has_impacted:
            if current_time - self.last_smoke_spawn_time > self.smoke_spawn_interval:
                self.last_smoke_spawn_time = current_time
                if self.rect and len(self.smoke_particles) < self.max_smoke_particles:
                    num_puffs_this_frame = random.randint(1, 2)
                    for _ in range(num_puffs_this_frame):
                        rel_x = random.uniform(0.1, 0.9) * self.rect.width
                        rel_y = random.uniform(0.3, 0.7) * self.rect.height
                        spawn_x_world = self.rect.x + rel_x
                        spawn_y_world = self.rect.y + rel_y
                        self.smoke_particles.append({
                            'x': spawn_x_world, 'y': spawn_y_world,
                            'vx': random.uniform(-0.7, 0.7), 'vy': random.uniform(-2.0, -0.8),
                            'size': random.randint(8, 18), 'alpha': random.uniform(120, 200),
                            'max_alpha': 200, 'life': random.uniform(1.5, 3.0), 'max_life': 3.0,
                            'color': random.choice([(40, 40, 40), (60, 60, 60), (30, 30, 30), (80, 70, 60)]),
                            'rotation': random.uniform(0, 360), 'angular_velocity': random.uniform(-25, 25)
                        })
        active_smoke_particles = []
        for p in self.smoke_particles:
            p['x'] += p['vx'] * (60 * time_delta_seconds)
            p['y'] += p['vy'] * (60 * time_delta_seconds)
            p['vy'] += 0.02 * (60 * time_delta_seconds)
            p['x'] -= (
                dx_world_scroll if game_state_current != gs.TUTORIAL else 0.0)
            p['rotation'] = (p['rotation'] + p['angular_velocity'] * time_delta_seconds) % 360
            p['life'] -= time_delta_seconds
            if p['max_life'] > 0 and p['life'] > 0:
                p['alpha'] = p['max_alpha'] * (p['life'] / p['max_life']) ** 0.7
            else:
                p['alpha'] = 0
            p['size'] *= (1 - 0.05 * time_delta_seconds)
            if p['alpha'] > 5 and p['size'] > 2:
                active_smoke_particles.append(p)
        self.smoke_particles = active_smoke_particles

    def on_destroy(self):
        self._stop_falling_sound()
        center_x = self.rect.centerx if self.rect else self.world_x
        center_y = self.rect.centery if self.rect else self.terrain.height_at(self.world_x)
        return self.debris_material, center_x, center_y, self.obstacle_type

    def kill(self):
        self._stop_falling_sound()
        super().kill()

    def _rotate_points(self, points, angle_degrees, center_x, center_y): 
        angle_rad = math.radians(angle_degrees)
        s, c = math.sin(angle_rad), math.cos(angle_rad)
        rotated_points = []
        for px, py in points:
            translated_x, translated_y = px - center_x, py - center_y
            new_x = translated_x * c - translated_y * s
            new_y = translated_x * s + translated_y * c
            rotated_points.append((new_x + center_x, new_y + center_y))
        return rotated_points

    def _draw_flame_particles(self, surface, camera_y_offset): 
        for p in self.flame_particles:
            if p['alpha'] <= 10: continue
            size = int(p['size']) 
            if size <= 2: continue 

            draw_x_center = p['x'] 
            draw_y_center = p['y'] - camera_y_offset

            flame_color_with_alpha = (*p['color'], int(p['alpha']))

            
            flame_width = int(size * random.uniform(0.6, 1.1)) 
            flame_height = int(size * random.uniform(1.0, 1.8))
            
            if flame_width > 1 and flame_height > 1:
                try:
                    temp_flame_surf = pygame.Surface((flame_width, flame_height), pygame.SRCALPHA)
                    pygame.draw.ellipse(temp_flame_surf, flame_color_with_alpha, (0,0, flame_width, flame_height))
                    rotated_flame = pygame.transform.rotate(temp_flame_surf, p['current_rotation'])
                    flame_rect = rotated_flame.get_rect(center=(int(draw_x_center), int(draw_y_center)))
                    surface.blit(rotated_flame, flame_rect)

                    
                    if size > 6: 
                        core_size_radius = int(size * 0.3) 
                        pygame.draw.circle(surface, (255,255,180, int(p['alpha'] * 0.7)),
                                           (int(draw_x_center), int(draw_y_center)), core_size_radius)
                except (TypeError, ValueError) as e:
                    
                    pass

    def draw_smoke(self, surface, camera_y_offset):
        if not self.rect: return 
        for p in self.smoke_particles:
            if p['alpha'] <= 10: continue
            size_radius = int(p['size']) 
            if size_radius <= 1: continue

            draw_x = p['x'] 
            draw_y = p['y'] - camera_y_offset 
            
            smoke_color_with_alpha = (*p['color'], int(p['alpha']))

            ellipse_w = int(size_radius * 2 * random.uniform(0.8, 1.2))
            ellipse_h = int(size_radius * 2 * random.uniform(0.7, 1.1)) 
            max_dim = max(ellipse_w, ellipse_h, 1)

            if max_dim <= 0: continue
            
            try:
                temp_surf_smoke = pygame.Surface((max_dim, max_dim), pygame.SRCALPHA)
                temp_surf_smoke.fill((0,0,0,0)) 
                ellipse_rect_on_temp = pygame.Rect(0,0, ellipse_w, ellipse_h)
                ellipse_rect_on_temp.center = (max_dim // 2, max_dim // 2)
                pygame.draw.ellipse(temp_surf_smoke, smoke_color_with_alpha, ellipse_rect_on_temp)
                
                rotated_surf = pygame.transform.rotate(temp_surf_smoke, p['rotation'])
                rotated_rect = rotated_surf.get_rect(center=(int(draw_x), int(draw_y)))
                surface.blit(rotated_surf, rotated_rect)
            except (TypeError, ValueError) as e:
                
                pass

    def draw(self, surface, camera_y_offset): 
        if not self.image or not self.rect:
            return

       
        self._draw_flame_particles(surface, camera_y_offset)

       
        temp_satellite_image_surf = self.image.copy()
        TERRAIN_MASK_STEP = 5
        Y_BUFFER = 5
        terrain_points_local_to_sprite = []
        world_x_start_of_sprite = self.rect.left 
        world_y_top_of_sprite = self.rect.top 

        for local_x_on_sprite in range(0, temp_satellite_image_surf.get_width(), TERRAIN_MASK_STEP):
            world_x_current = world_x_start_of_sprite + local_x_on_sprite
            terrain_world_y = self.terrain.height_at(world_x_current)
            local_y_on_sprite = terrain_world_y - world_y_top_of_sprite
            terrain_points_local_to_sprite.append((local_x_on_sprite, local_y_on_sprite))

        if not terrain_points_local_to_sprite or terrain_points_local_to_sprite[-1][0] < temp_satellite_image_surf.get_width() - 1:
            local_x_on_sprite_last = temp_satellite_image_surf.get_width() - 1
            if local_x_on_sprite_last >= 0 :
                world_x_current = world_x_start_of_sprite + local_x_on_sprite_last
                terrain_world_y = self.terrain.height_at(world_x_current)
                local_y_on_sprite = terrain_world_y - world_y_top_of_sprite
                if not terrain_points_local_to_sprite or terrain_points_local_to_sprite[-1][0] < local_x_on_sprite_last:
                    terrain_points_local_to_sprite.append((local_x_on_sprite_last, local_y_on_sprite))
        
      
        draw_pos_x_sprite = self.rect.x 
        draw_pos_y_sprite = self.rect.y - camera_y_offset 

        if len(terrain_points_local_to_sprite) < 2:
            surface.blit(self.image, (draw_pos_x_sprite, draw_pos_y_sprite)) 
        else:
            erase_polygon_points_on_sprite = list(terrain_points_local_to_sprite)
            erase_polygon_points_on_sprite.append(
                (temp_satellite_image_surf.get_width() - 1, temp_satellite_image_surf.get_height() + Y_BUFFER))
            erase_polygon_points_on_sprite.append((0, temp_satellite_image_surf.get_height() + Y_BUFFER))
            try:
                pygame.draw.polygon(temp_satellite_image_surf, (0, 0, 0, 0), erase_polygon_points_on_sprite)
            except ValueError:
                 pass 
            surface.blit(temp_satellite_image_surf, (draw_pos_x_sprite, draw_pos_y_sprite))
        
      
        self.draw_smoke(surface, camera_y_offset)


class BugObstacle(Obstacle):
    def __init__(self, screen_spawn_x, terrain_obj, is_tutorial_obstacle=False,
                 spawn_sound=None, die_sound=None):
        self.frames = []
        self.anim_frame_index = 0
        self.anim_timer = 0.0
        self.move_speed = config.BUG_MOVE_SPEED
        self.facing_left = True

        self.spawn_sound = spawn_sound
        self.die_sound = die_sound
        self.spawn_sound_channel = None

        base_dir_bug = os.path.dirname(os.path.abspath(sys.argv[0] if hasattr(sys, 'argv') and sys.argv else __file__))
        assets_dir_bug = os.path.join(base_dir_bug, "assets")
        if not os.path.isdir(assets_dir_bug):
            parent_dir_bug = os.path.dirname(base_dir_bug)
            assets_dir_bug = os.path.join(parent_dir_bug, "assets")

        for i in range(1, 3):
            filename = f"bug{i}.png"
            path = os.path.join(assets_dir_bug, filename)
            try:
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    img_scaled = pygame.transform.smoothscale(img, (config.BUG_SPRITE_WIDTH, config.BUG_SPRITE_HEIGHT))
                    self.frames.append(img_scaled)
                else:
                    print(f"BugObstacle: Image {filename} not found at {path}")
            except Exception as e:
                print(f"BugObstacle: Error loading image {filename}: {e}")

        if not self.frames:
            print("BugObstacle: No animation frames loaded. Using red square fallback.")
            fallback_img = pygame.Surface((config.BUG_SPRITE_WIDTH, config.BUG_SPRITE_HEIGHT))
            fallback_img.fill((255, 0, 0))
            self.frames.append(fallback_img)

        super().__init__(screen_spawn_x, terrain_obj, image_asset_path_name=None,
                         is_tutorial_obstacle=is_tutorial_obstacle)

        self.obstacle_type = "bug"
        self.damage_value = config.BUG_DAMAGE_VALUE
        self.debris_material = config.BUG_DEBRIS_MATERIAL
        self.destructible = True

        self.image = self.frames[self.anim_frame_index]
        self.rect = self.image.get_rect()
        initial_y = self.terrain.height_at(self.world_x + self.rect.width / 2)
        self.rect.midbottom = (int(self.world_x + self.rect.width / 2), initial_y)

        if self.spawn_sound and pygame.mixer.get_init():
            try:
                self.spawn_sound_channel = self.spawn_sound.play()
            except pygame.error as e:
                print(f"BugObstacle: Error playing spawn sound: {e}")
                self.spawn_sound_channel = None

    def update(self, dx_world_scroll, game_state_current, time_delta_seconds=0, player_obj=None,
               effects_creation_group=None):
        if self.rect is None: return

        original_world_x = self.world_x
        if game_state_current != gs.TUTORIAL:
            self.world_x -= dx_world_scroll

        if player_obj and self.rect.right > 0 and self.rect.left < WIDTH:
            direction_to_player_x = 0
            if player_obj.rect.centerx < self.rect.centerx:
                direction_to_player_x = -1
                if not self.facing_left:
                    self.facing_left = True
            elif player_obj.rect.centerx > self.rect.centerx:
                direction_to_player_x = 1
                if self.facing_left:
                    self.facing_left = False
            self.world_x += direction_to_player_x * self.move_speed * (60 * time_delta_seconds)

        self.rect.x = int(self.world_x)

        self.anim_timer += time_delta_seconds
        if self.anim_timer >= config.BUG_ANIMATION_SPEED:
            self.anim_timer = 0.0
            self.anim_frame_index = (self.anim_frame_index + 1) % len(self.frames)
            current_image_base = self.frames[self.anim_frame_index]
            if not self.facing_left:
                self.image = pygame.transform.flip(current_image_base, True, False)
            else:
                self.image = current_image_base

        current_center_x_for_terrain = self.rect.centerx
        y_terrain_base = self.terrain.height_at(current_center_x_for_terrain)
        self.rect.bottom = y_terrain_base

        if game_state_current != gs.TUTORIAL and self.rect.right < 0:
            self.kill()

    def on_destroy(self):
        if self.spawn_sound_channel and self.spawn_sound_channel.get_busy():
            self.spawn_sound_channel.stop()
        self.spawn_sound_channel = None

        if self.die_sound and pygame.mixer.get_init():
            try:
                self.die_sound.play()
            except pygame.error as e:
                print(f"BugObstacle: Error playing die sound: {e}")

        center_x = self.rect.centerx if self.rect else self.world_x
        center_y = self.rect.centery if self.rect else self.terrain.height_at(self.world_x)
        return self.debris_material, center_x, center_y, self.obstacle_type

    def kill(self):
        if self.spawn_sound_channel and self.spawn_sound_channel.get_busy():
            self.spawn_sound_channel.stop()
        self.spawn_sound_channel = None
        super().kill()
    


class CrystalObstacle(Obstacle):
    def __init__(self, screen_spawn_x, terrain_obj, impact_sound_obj=None, destruction_sound_obj=None):
        
        self.is_falling = True
        self.fall_velocity_y = config.CRYSTAL_INITIAL_FALL_VELOCITY
        self.fall_acceleration_y = config.CRYSTAL_FALL_ACCELERATION
        self.has_impacted = False
        self.impact_sound_asset = impact_sound_obj          
        self.destruction_sound_asset = destruction_sound_obj
        self.target_ground_y = float('inf') 

        super().__init__(screen_spawn_x, terrain_obj)

       
        self.obstacle_type = "crystal"
        self.damage_value = config.CRYSTAL_DAMAGE_VALUE
        self.debris_material = config.CRYSTAL_DEBRIS_MATERIAL
        self.destructible = True 
        self.image_asset_path_name = config.CRYSTAL_SPRITE_FILENAME

        loaded_img = self._load_image_asset(config.CRYSTAL_SPRITE_WIDTH, config.CRYSTAL_SPRITE_HEIGHT)
        if loaded_img:
            self.image = loaded_img
        else: 
            self.image = pygame.Surface((config.CRYSTAL_SPRITE_WIDTH, config.CRYSTAL_SPRITE_HEIGHT), pygame.SRCALPHA)
            self.image.fill((180, 180, 255, 150)) 

        self.rect = self.image.get_rect()

       
        effective_spawn_x_for_ceiling_query = self.world_x + self.rect.width / 2.0
        ceiling_y_at_spawn = self.terrain.ceiling_height_at(effective_spawn_x_for_ceiling_query)

     
        self.world_y_pos = ceiling_y_at_spawn - config.CRYSTAL_SPAWN_Y_OFFSET_ABOVE_CEILING - self.rect.height
        
     
        self.rect.topleft = (int(self.world_x), int(self.world_y_pos))

    def update(self, dx_world_scroll, game_state_current, time_delta_seconds=0, player_obj=None, effects_creation_group=None):
        if self.rect is None: return 

        
        self.world_x -= dx_world_scroll
        self.rect.x = int(self.world_x) 

        time_factor = ( (60 * time_delta_seconds) if time_delta_seconds > 0 else 1.0)

        if self.is_falling and not self.has_impacted:
            self.fall_velocity_y += self.fall_acceleration_y * time_factor
            self.world_y_pos += self.fall_velocity_y * time_factor

          
            self.target_ground_y = self.terrain.height_at(self.rect.centerx)

          
            if (self.world_y_pos + self.rect.height) >= self.target_ground_y:
                self.world_y_pos = self.target_ground_y - self.rect.height
                self.has_impacted = True
                self.is_falling = False 

                if self.impact_sound_asset and pygame.mixer.get_init():
                    try:
                        self.impact_sound_asset.play()
                    except pygame.error as e:
                        print(f"Error playing crystal impact sound: {e}")

                
                if config.CRYSTAL_IMPACT_SHAKE_MAGNITUDE > 0:
                    gs.screen_shake_magnitude = config.CRYSTAL_IMPACT_SHAKE_MAGNITUDE
                    gs.screen_shake_duration = config.CRYSTAL_IMPACT_SHAKE_DURATION
                    gs.screen_shake_timer = 0.0 

                
                if effects_creation_group and self.rect:
                    effects_creation_group.add(
                        DebrisEffect(self.rect.centerx, self.rect.bottom, self.debris_material, intensity=1.8) 
                    )
        
        
        self.rect.y = int(self.world_y_pos)

        
        if self.rect.right < -50: 
            self.kill()

    def on_destroy(self):
        
        if self.destruction_sound_asset and pygame.mixer.get_init():
            try:
                self.destruction_sound_asset.play()
            except pygame.error as e: 
                print(f"CrystalObstacle: Error playing destruction sound: {e}")

      
        center_x = self.rect.centerx if self.rect else self.world_x
        center_y = self.rect.centery if self.rect else self.terrain.height_at(self.world_x)
        return self.debris_material, center_x, center_y, self.obstacle_type
 