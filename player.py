# player.py
import pygame
import math
import random
import config as cfg
from config import (PLAYER_SCREEN_X, MAX_BULLETS, GRAVITY,
                    PLAYER_ANIMATION_SPEED, JUMP_VEL, MAX_JUMPS, SLOWDOWN_DURATION)
import game_state as gs

PLAYER_SHOOTING_ANIM_SPEED = 0.07
NUM_FRAMES_FOR_HIT_ANIM_SPEED_CALC = 3
PLAYER_DYING_ANIM_SPEED = (SLOWDOWN_DURATION / 1000.0) / NUM_FRAMES_FOR_HIT_ANIM_SPEED_CALC \
    if SLOWDOWN_DURATION > 0 and NUM_FRAMES_FOR_HIT_ANIM_SPEED_CALC > 0 else 0.2

DEBUG_TILT_AMPLIFIER = 1.0  
GROUND_ROTATION_SMOOTHING_FACTOR = 0.2
GROUND_DETECTION_TOLERANCE = 3 


class Rider(pygame.sprite.Sprite):
    def __init__(self, idle_frames, shooting_frames=None, dying_frames=None):
        super().__init__()
        self.is_active = True
        self.x = PLAYER_SCREEN_X
        self.y_world = 0.0
        self.vy = 0.0
        self.on_ground = True
        self.was_on_ground = True
        self.jump_count = 0
        self.bullets_remaining = MAX_BULLETS
        self.is_hidden = False 

        self.idle_frames = idle_frames
        self.shooting_frames = shooting_frames if shooting_frames else []
        self.dying_frames = dying_frames if dying_frames else []

        self.current_frames_set = self.idle_frames
        self.current_frame_index = 0
        self.animation_timer = 0.0

        self.is_shooting_animating = False
        self.shooting_anim_timer = 0.0
        self.shooting_anim_frame_index = 0

        self.is_dying_animating = False
        self.dying_anim_timer = 0.0
        self.dying_phase_timer = 0.0
        self.dying_anim_frame_index = 0
        self.is_fatal_dying_animation = False
        self.num_dying_frames_to_play = 0
        self.dying_animation_phase = None

        self.is_flipping = False
        self.flip_angle = 0.0
        self.ground_rotation_angle = 0.0
        self.smoothed_ground_rotation_angle = 0.0
        self.flip_rotation_speed = 360
        self.original_image = None

        self.is_landing_assisting = False
        self.landing_assist_threshold_distance = cfg.PLAYER_TARGET_HEIGHT * 1.25
        self.landing_assist_p_gain = 7.0

        if not self.idle_frames or len(self.idle_frames) == 0:
            print("CRITICAL FALLBACK: Rider idle_frames missing. Using RED placeholder.")
            fallback_img = pygame.Surface((cfg.PLAYER_TARGET_WIDTH, cfg.PLAYER_TARGET_HEIGHT), pygame.SRCALPHA)
            fallback_img.fill((255, 0, 0, 180))
            self.idle_frames = [fallback_img]
            self.current_frames_set = self.idle_frames

        if self.current_frames_set and len(self.current_frames_set) > 0:
            self.original_image = self.current_frames_set[self.current_frame_index]
        else:
            fb_img = pygame.Surface((cfg.PLAYER_TARGET_WIDTH, cfg.PLAYER_TARGET_HEIGHT), pygame.SRCALPHA)
            fb_img.fill((255, 0, 0, 120))
            self.original_image = fb_img
            if not self.current_frames_set:
                self.current_frames_set = [self.original_image]
            elif len(self.current_frames_set) == 0:
                self.current_frames_set.append(self.original_image)
            self.current_frame_index = 0

        self.image = self.original_image
        self.rect = self.image.get_rect(centerx=self.x)
        self.y_world = float(cfg.GROUND_Y)
        self.rect.midbottom = (self.x, self.y_world)

        self.trail_points = []
        self.max_trail_points = 90
        self.trail_distance_accumulated = 0.0
        self.trail_spawn_distance_threshold = 3.0
        self.trail_base_alpha = 250
        self.trail_alpha_decay_rate = 0.7
        self.trail_radius = 5

        self.splash_particles = []
        self.max_splash_particles = 250
        self.splash_particle_gravity = 0.15
        self.splash_particle_base_alpha = 200
        self.splash_particle_alpha_decay = 2.8
        self.continuous_splash_size_range = (2, 4)
        self.jump_puff_size_range = (4, 7)
        self.land_puff_size_range = (5, 9)

    def _update_image_and_rect(self):
        if not self.current_frames_set or len(self.current_frames_set) == 0:
            fb_img = pygame.Surface((cfg.PLAYER_TARGET_WIDTH, cfg.PLAYER_TARGET_HEIGHT), pygame.SRCALPHA)
            fb_img.fill((255, 0, 0, 120))
            self.original_image = fb_img
            if not self.current_frames_set:
                self.current_frames_set = [self.original_image]
            elif len(self.current_frames_set) == 0:
                self.current_frames_set.append(self.original_image)
            self.current_frame_index = 0
        else:
            safe_idx = self.current_frame_index % len(self.current_frames_set)
            self.original_image = self.current_frames_set[safe_idx]

        applied_angle = 0.0

        physics_active_for_rotation = True
        if self.is_dying_animating and self.is_fatal_dying_animation and \
                self.dying_frames and len(self.dying_frames) > 0 and \
                self.dying_anim_frame_index >= len(self.dying_frames) - 1:
            physics_active_for_rotation = False

        if self.on_ground and physics_active_for_rotation:
            applied_angle = self.smoothed_ground_rotation_angle * DEBUG_TILT_AMPLIFIER
            self.image = pygame.transform.rotate(self.original_image, applied_angle)
        elif self.is_flipping and not self.on_ground:
            applied_angle = self.flip_angle
            self.image = pygame.transform.rotate(self.original_image, applied_angle)
        else:
            self.image = self.original_image

        new_rect = self.image.get_rect()
        new_rect.centerx = self.x
        new_rect.bottom = int(self.y_world)
        self.rect = new_rect

    def emit_snow_puff(self, num_particles, intensity_factor=1.0, location_offset_x=0, upward_bias=0.0,
                       size_range=(3, 6)):
        if not self.rect: return
        spawn_x_base = self.rect.midbottom[0] + location_offset_x
        spawn_y_world_base = self.y_world
        particle_base_color_snow = cfg.PLAYER_TRAIL_COLOR_SNOW
        for _ in range(num_particles):
            if len(self.splash_particles) >= self.max_splash_particles: break
            current_particle_color = particle_base_color_snow
            angle = random.uniform(math.pi * 0.8, math.pi * 1.7)
            if upward_bias < -0.5: angle = random.uniform(math.pi * 0.9, math.pi * 2.1)
            speed = random.uniform(1.5, 3.0) * intensity_factor
            initial_vx = math.cos(angle) * speed
            initial_vy = math.sin(angle) * speed + upward_bias
            self.splash_particles.append({
                'screen_x': spawn_x_base + random.uniform(-self.rect.width / 3, self.rect.width / 3),
                'world_y': spawn_y_world_base + random.uniform(-7, 7),
                'vx': initial_vx, 'vy': initial_vy,
                'alpha': self.splash_particle_base_alpha * random.uniform(0.8, 1.1),
                'size': random.randint(size_range[0], size_range[1]),
                'color': current_particle_color
            })

    def perform_jump(self):
        if self.jump_count < MAX_JUMPS and not self.is_dying_animating:
            self.vy = JUMP_VEL
            self.on_ground = False
            self.ground_rotation_angle = 0.0
            self.jump_count += 1
            self.is_flipping = True
            self.is_landing_assisting = False
            if self.rect:
                self.emit_snow_puff(num_particles=random.randint(12, 18),
                                    intensity_factor=0.9, upward_bias=-0.7,
                                    size_range=self.jump_puff_size_range)
            return True
        return False

    def start_shooting_animation(self):
        if not self.shooting_frames or self.is_dying_animating:
            return
        self.is_shooting_animating = True
        self.shooting_anim_timer = 0.0
        self.shooting_anim_frame_index = 0

    def start_dying_animation(self, is_fatal_hit):
        if not self.dying_frames or len(self.dying_frames) == 0:
            return
        if self.is_dying_animating and \
                (self.is_fatal_dying_animation == is_fatal_hit or self.is_fatal_dying_animation):
            return
        self.is_dying_animating = True
        self.is_fatal_dying_animation = is_fatal_hit
        self.dying_anim_timer = 0.0
        self.dying_phase_timer = 0.0
        self.dying_anim_frame_index = 0
        if self.is_fatal_dying_animation:
            self.num_dying_frames_to_play = len(self.dying_frames)
            self.dying_animation_phase = 'FATAL_FALL'
        else:
            self.num_dying_frames_to_play = len(self.dying_frames)
            self.dying_animation_phase = 'FALLING_PHASE'
        self.is_shooting_animating = False
        self.is_flipping = False
        self.flip_angle = 0.0
        self.is_hidden = False

    def reset_animation_flags(self):
        self.is_dying_animating = False
        self.dying_anim_frame_index = 0
        self.is_fatal_dying_animation = False
        self.num_dying_frames_to_play = 0
        self.dying_animation_phase = None
        self.dying_anim_timer = 0.0
        self.dying_phase_timer = 0.0
        self.is_shooting_animating = False
        self.shooting_anim_frame_index = 0
        self.shooting_anim_timer = 0.0
        self.is_flipping = False
        self.flip_angle = 0.0
        self.ground_rotation_angle = 0.0
        self.smoothed_ground_rotation_angle = 0.0
        self.current_frame_index = 0
        self.is_hidden = False  
        if self.idle_frames and len(self.idle_frames) > 0:
            self.current_frames_set = self.idle_frames
        else:
            if not hasattr(self, 'original_image') or self.original_image is None or \
                    (not self.current_frames_set or len(self.current_frames_set) == 0):
                fb_img = pygame.Surface((cfg.PLAYER_TARGET_WIDTH, cfg.PLAYER_TARGET_HEIGHT), pygame.SRCALPHA)
                fb_img.fill((255, 0, 0, 120))
                self.current_frames_set = [fb_img]
                self.original_image = fb_img

    def update(self, terrain_obj, current_ramp_obj, game_state_str, time_delta_seconds, world_scroll_dx):
        if not self.is_active:
            return

        if self.is_hidden:  
            
            if terrain_obj: self.y_world = terrain_obj.height_at(self.x)
            if self.rect: self.rect.midbottom = (self.x, int(self.y_world))
            return

        apply_physics_this_frame = True
        if self.is_dying_animating and self.is_fatal_dying_animation and \
                self.dying_frames and len(self.dying_frames) > 0 and \
                self.dying_anim_frame_index >= len(self.dying_frames) - 1:
            apply_physics_this_frame = False

        if apply_physics_this_frame:
            current_gravity = GRAVITY
            self.vy += current_gravity
            self.y_world += self.vy

            if gs.is_level_2_simple_mode and self.rect and terrain_obj:
                ceiling_y_world = terrain_obj.ceiling_height_at(self.x)
                unrotated_height = cfg.PLAYER_TARGET_HEIGHT
                player_top_y = self.y_world - unrotated_height
                if player_top_y < ceiling_y_world:
                    if self.vy < 0:
                        self.y_world = ceiling_y_world + unrotated_height
                        self.vy = 0
                        
        else:
            self.vy = 0
            if terrain_obj: self.y_world = terrain_obj.height_at(self.x)
            self.on_ground = True
            self.smoothed_ground_rotation_angle = 0.0
            self.ground_rotation_angle = 0.0

        ground_y_world = terrain_obj.height_at(self.x) if terrain_obj else self.y_world
        y_on_ramp = None
        if current_ramp_obj: y_on_ramp = current_ramp_obj.on_ramp(self.x)
        effective_ground_y = ground_y_world
        if y_on_ramp is not None and y_on_ramp < ground_y_world + 5.0: effective_ground_y = y_on_ramp

        was_on_ground_before_collision_check = self.on_ground
        if apply_physics_this_frame:
            if self.y_world >= effective_ground_y - GROUND_DETECTION_TOLERANCE:
                if self.vy >= 0:
                    self.y_world = effective_ground_y
                    self.vy = 0
                    self.on_ground = True
                    if not was_on_ground_before_collision_check:
                        self.jump_count = 0
                        if self.rect:
                            self.emit_snow_puff(num_particles=random.randint(20, 30),
                                                intensity_factor=1.3, upward_bias=0.1,
                                                size_range=self.land_puff_size_range)
                    if not self.is_dying_animating:
                        self.is_flipping = False
                        self.flip_angle = 0.0
                    self.is_landing_assisting = False
            else:
                self.on_ground = False

        if not self.is_dying_animating:
            if not self.on_ground:
                distance_to_ground = effective_ground_y - self.y_world
                unrotated_height = cfg.PLAYER_TARGET_HEIGHT
                can_activate_assist = (self.is_flipping and self.vy > 0 and
                                       distance_to_ground < self.landing_assist_threshold_distance and
                                       distance_to_ground > -unrotated_height * 0.5)
                if can_activate_assist:
                    self.is_landing_assisting = True
                elif not self.is_flipping:
                    self.is_landing_assisting = False
                if self.is_landing_assisting and not can_activate_assist:
                    self.is_landing_assisting = False

                if self.is_landing_assisting:
                    current_angle_norm = self.flip_angle % 360.0
                    dynamic_rotation_value = 0.0
                    if abs(current_angle_norm) > 1.0 and abs(current_angle_norm - 360.0) > 1.0:
                        error = current_angle_norm if current_angle_norm <= 180.0 else -(360.0 - current_angle_norm)
                        dynamic_rotation_value = -error * self.landing_assist_p_gain
                    self.flip_angle += dynamic_rotation_value * time_delta_seconds
                elif self.is_flipping:
                    self.flip_angle += self.flip_rotation_speed * time_delta_seconds
            else:
                self.is_flipping = False
                self.is_landing_assisting = False
        else:
            self.is_flipping = False
            self.flip_angle = 0.0
            self.is_landing_assisting = False

        if self.on_ground and apply_physics_this_frame:
            delta_x_slope = cfg.PLAYER_TARGET_WIDTH * 0.5
            if delta_x_slope < 1.0: delta_x_slope = 1.0
            x_left = self.x - delta_x_slope
            x_right = self.x + delta_x_slope

            def get_eff_ground_y_at_x(x_pos, terrain, ramp):
                g_y = terrain.height_at(x_pos)
                r_y = None
                if ramp and ramp.screen_spawn_x <= x_pos <= ramp.end_x_screen: r_y = ramp.on_ramp(x_pos)
                return r_y if r_y is not None and r_y < g_y + 5.0 else g_y

            y_left_ground = get_eff_ground_y_at_x(x_left, terrain_obj, current_ramp_obj)
            y_right_ground = get_eff_ground_y_at_x(x_right, terrain_obj, current_ramp_obj)
            actual_dx_for_slope = x_right - x_left
            self.ground_rotation_angle = -math.degrees(
                math.atan2(y_right_ground - y_left_ground, actual_dx_for_slope)) if abs(
                actual_dx_for_slope) > 0.001 else 0.0
        else:
            self.ground_rotation_angle = 0.0

        target_angle_for_smoothing = 0.0
        if self.on_ground and apply_physics_this_frame:
            target_angle_for_smoothing = self.ground_rotation_angle
        self.smoothed_ground_rotation_angle += (
                                                           target_angle_for_smoothing - self.smoothed_ground_rotation_angle) * GROUND_ROTATION_SMOOTHING_FACTOR

        if self.is_dying_animating:
            if not self.dying_frames or len(self.dying_frames) == 0:
                self.is_dying_animating = False
            else:
                self.current_frames_set = self.dying_frames
                self.dying_anim_timer += time_delta_seconds
                num_total_dying_frames = len(self.dying_frames)

                if self.is_fatal_dying_animation:
                    self.dying_phase_timer += time_delta_seconds
                    if self.dying_phase_timer >= PLAYER_DYING_ANIM_SPEED:
                        self.dying_phase_timer -= PLAYER_DYING_ANIM_SPEED
                        if self.dying_anim_frame_index < num_total_dying_frames - 1:
                            self.dying_anim_frame_index += 1
                        else:
                            self.is_dying_animating = False
                    self.current_frame_index = self.dying_anim_frame_index

                else:
                    self.dying_phase_timer += time_delta_seconds

                    FALLING_ANIM_DURATION_SECONDS = 0.5
                    RISING_ANIM_DURATION_SECONDS = 0.5
                    TOTAL_RECOVERY_DURATION_SECONDS = SLOWDOWN_DURATION / 1000.0

                    if TOTAL_RECOVERY_DURATION_SECONDS <= 0.001:
                        self.is_dying_animating = False
                    else:
                        actual_falling_phase_end_time = FALLING_ANIM_DURATION_SECONDS
                        actual_rising_phase_start_time = max(
                            actual_falling_phase_end_time,
                            TOTAL_RECOVERY_DURATION_SECONDS - RISING_ANIM_DURATION_SECONDS
                        )

                        num_anim_steps_fall_rise = min(num_total_dying_frames, 3)
                        if num_anim_steps_fall_rise == 0:
                            self.is_dying_animating = False
                        else:
                            idx_f0, idx_f1, idx_f2 = 0, 0, 0
                            if num_anim_steps_fall_rise >= 1: idx_f0 = 0
                            if num_anim_steps_fall_rise >= 2: idx_f1 = 1
                            if num_anim_steps_fall_rise == 3: idx_f2 = 2

                            if self.dying_animation_phase == 'FALLING_PHASE':
                                current_phase_duration = actual_falling_phase_end_time
                                time_per_step = current_phase_duration / num_anim_steps_fall_rise if num_anim_steps_fall_rise > 0 else current_phase_duration

                                step = 0
                                if time_per_step > 0.0001:
                                    step = math.floor(self.dying_phase_timer / time_per_step)
                                else:
                                    step = num_anim_steps_fall_rise - 1

                                if num_anim_steps_fall_rise == 1:
                                    self.dying_anim_frame_index = idx_f0
                                elif num_anim_steps_fall_rise == 2:
                                    self.dying_anim_frame_index = idx_f0 if step == 0 else idx_f1
                                elif num_anim_steps_fall_rise == 3:
                                    if step == 0:
                                        self.dying_anim_frame_index = idx_f0
                                    elif step == 1:
                                        self.dying_anim_frame_index = idx_f1
                                    else:
                                        self.dying_anim_frame_index = idx_f2

                                if self.dying_anim_timer >= actual_falling_phase_end_time:
                                    if actual_rising_phase_start_time > actual_falling_phase_end_time + 0.001:
                                        self.dying_animation_phase = 'HOLDING_PHASE'
                                        if num_anim_steps_fall_rise == 1:
                                            self.dying_anim_frame_index = idx_f0
                                        elif num_anim_steps_fall_rise == 2:
                                            self.dying_anim_frame_index = idx_f1
                                        elif num_anim_steps_fall_rise == 3:
                                            self.dying_anim_frame_index = idx_f2
                                    else:
                                        self.dying_animation_phase = 'RISING_PHASE'
                                        if num_anim_steps_fall_rise == 1:
                                            self.dying_anim_frame_index = idx_f0
                                        elif num_anim_steps_fall_rise == 2:
                                            self.dying_anim_frame_index = idx_f1
                                        elif num_anim_steps_fall_rise == 3:
                                            self.dying_anim_frame_index = idx_f2
                                    self.dying_phase_timer = 0.0

                            elif self.dying_animation_phase == 'HOLDING_PHASE':
                                if num_anim_steps_fall_rise == 1:
                                    self.dying_anim_frame_index = idx_f0
                                elif num_anim_steps_fall_rise == 2:
                                    self.dying_anim_frame_index = idx_f1
                                elif num_anim_steps_fall_rise == 3:
                                    self.dying_anim_frame_index = idx_f2

                                if self.dying_anim_timer >= actual_rising_phase_start_time:
                                    self.dying_animation_phase = 'RISING_PHASE'
                                    self.dying_phase_timer = 0.0
                                    if num_anim_steps_fall_rise == 1:
                                        self.dying_anim_frame_index = idx_f0
                                    elif num_anim_steps_fall_rise == 2:
                                        self.dying_anim_frame_index = idx_f1
                                    elif num_anim_steps_fall_rise == 3:
                                        self.dying_anim_frame_index = idx_f2


                            elif self.dying_animation_phase == 'RISING_PHASE':
                                current_phase_duration = TOTAL_RECOVERY_DURATION_SECONDS - actual_rising_phase_start_time
                                if current_phase_duration <= 0.001:
                                    self.is_dying_animating = False
                                    self.dying_anim_frame_index = idx_f0
                                else:
                                    time_per_step = current_phase_duration / num_anim_steps_fall_rise if num_anim_steps_fall_rise > 0 else current_phase_duration

                                    step = 0
                                    if time_per_step > 0.0001:
                                        step = math.floor(self.dying_phase_timer / time_per_step)
                                    else:
                                        step = num_anim_steps_fall_rise - 1

                                    if num_anim_steps_fall_rise == 1:
                                        self.dying_anim_frame_index = idx_f0
                                    elif num_anim_steps_fall_rise == 2:
                                        self.dying_anim_frame_index = idx_f1 if step == 0 else idx_f0
                                    elif num_anim_steps_fall_rise == 3:
                                        if step == 0:
                                            self.dying_anim_frame_index = idx_f2
                                        elif step == 1:
                                            self.dying_anim_frame_index = idx_f1
                                        else:
                                            self.dying_anim_frame_index = idx_f0

                        if self.dying_anim_timer >= TOTAL_RECOVERY_DURATION_SECONDS:
                            self.is_dying_animating = False
                            if num_anim_steps_fall_rise > 0: self.dying_anim_frame_index = idx_f0

                    self.current_frame_index = min(self.dying_anim_frame_index, num_total_dying_frames - 1) \
                        if num_total_dying_frames > 0 else 0

            if not self.is_dying_animating:
                self.reset_animation_flags()


        elif self.is_shooting_animating:
            if not self.shooting_frames or len(self.shooting_frames) == 0:
                self.is_shooting_animating = False
            else:
                self.current_frames_set = self.shooting_frames
                self.shooting_anim_timer += time_delta_seconds
                if self.shooting_anim_timer >= PLAYER_SHOOTING_ANIM_SPEED:
                    self.shooting_anim_timer -= PLAYER_SHOOTING_ANIM_SPEED
                    self.shooting_anim_frame_index = (self.shooting_anim_frame_index + 1)
                    if self.shooting_anim_frame_index >= len(self.shooting_frames):
                        self.is_shooting_animating = False
                        self.shooting_anim_frame_index = 0

            if not self.is_shooting_animating:
                self.shooting_anim_frame_index = 0
                if self.idle_frames and len(self.idle_frames) > 0:
                    self.current_frames_set = self.idle_frames
                    self.current_frame_index = 0

        if not self.is_dying_animating and not self.is_shooting_animating:
            if self.idle_frames and len(self.idle_frames) > 0:
                self.current_frames_set = self.idle_frames
                self.animation_timer += time_delta_seconds
                if self.animation_timer >= PLAYER_ANIMATION_SPEED:
                    self.animation_timer -= PLAYER_ANIMATION_SPEED
                    self.current_frame_index = (self.current_frame_index + 1) % len(self.idle_frames)
            else:
                pass

        if not self.current_frames_set or len(self.current_frames_set) == 0:
            fb_img = pygame.Surface((cfg.PLAYER_TARGET_WIDTH, cfg.PLAYER_TARGET_HEIGHT), pygame.SRCALPHA)
            fb_img.fill((255, 0, 0, 120))
            self.current_frames_set = [fb_img]
            self.current_frame_index = 0
            if hasattr(self, 'original_image'): self.original_image = self.current_frames_set[0]
        else:
            self.current_frame_index = self.current_frame_index % len(self.current_frames_set)

        self._update_image_and_rect()

        active_trail_points = []
        for point in self.trail_points:
            point['screen_x'] -= world_scroll_dx
            point['alpha'] -= self.trail_alpha_decay_rate
            if point['screen_x'] > -self.trail_radius * 2 and point['alpha'] > 0:
                active_trail_points.append(point)
        self.trail_points = active_trail_points

        if not self.is_dying_animating and self.on_ground and world_scroll_dx > 0 and game_state_str == gs.PLAYING:
            self.trail_distance_accumulated += world_scroll_dx
            while self.trail_distance_accumulated >= self.trail_spawn_distance_threshold:
                self.trail_distance_accumulated -= self.trail_spawn_distance_threshold
                if self.rect:
                    trail_spawn_x = self.rect.midbottom[0]
                    trail_spawn_y_world = self.y_world
                    trail_particle_color = cfg.PLAYER_TRAIL_COLOR_SNOW
                    self.trail_points.append({
                        'screen_x': trail_spawn_x, 'world_y': trail_spawn_y_world,
                        'alpha': self.trail_base_alpha, 'color': trail_particle_color
                    })
                    if len(self.trail_points) > self.max_trail_points: self.trail_points.pop(0)
                    num_trail_splashes = random.randint(1, 2)
                    splash_particle_base_color_for_trail_snow = cfg.PLAYER_TRAIL_COLOR_SNOW
                    for _ in range(num_trail_splashes):
                        if len(self.splash_particles) < self.max_splash_particles:
                            current_splash_color = splash_particle_base_color_for_trail_snow
                            self.splash_particles.append({
                                'screen_x': trail_spawn_x + random.uniform(-self.trail_radius / 2,
                                                                           self.trail_radius / 2),
                                'world_y': trail_spawn_y_world + random.uniform(-2, 2),
                                'vx': random.uniform(-1.0, -0.3), 'vy': random.uniform(-1.8, -0.6),
                                'alpha': self.splash_particle_base_alpha * random.uniform(0.6, 0.9),
                                'size': random.randint(self.continuous_splash_size_range[0],
                                                       self.continuous_splash_size_range[1]),
                                'color': current_splash_color
                            })
        active_splash_particles = []
        for p_splash in self.splash_particles:
            p_splash['screen_x'] += p_splash['vx']
            p_splash['screen_x'] -= world_scroll_dx
            p_splash['vy'] += self.splash_particle_gravity
            p_splash['world_y'] += p_splash['vy']
            p_splash['alpha'] -= self.splash_particle_alpha_decay
            if p_splash['alpha'] > 0 and \
                    p_splash['screen_x'] > -p_splash['size'] * 5 and \
                    p_splash['world_y'] < self.y_world + cfg.HEIGHT * 0.3:
                active_splash_particles.append(p_splash)
        self.splash_particles = active_splash_particles

        self.was_on_ground = self.on_ground

    def draw(self, surface, camera_y_offset):
        if not self.is_active or self.is_hidden: return  
        if self.rect and self.image:
            screen_rect = self.rect.copy()
            screen_rect.top -= camera_y_offset
            surface.blit(self.image, screen_rect.topleft)

    def draw_trails(self, surface, camera_y_offset):
        if not self.is_active or not self.rect or self.is_hidden: return
        for point in self.trail_points:
            current_alpha = max(0, min(255, int(point['alpha'])))
            if current_alpha > 0:
                trail_draw_x, trail_draw_y = point['screen_x'], point['world_y'] - camera_y_offset
                point_color = point.get('color', cfg.PLAYER_TRAIL_COLOR_SNOW)
                trail_mark_surface = pygame.Surface((self.trail_radius * 2, self.trail_radius * 2), pygame.SRCALPHA)
                trail_mark_surface.fill((0, 0, 0, 0))
                pygame.draw.circle(trail_mark_surface, (point_color[0], point_color[1], point_color[2], current_alpha),
                                   (self.trail_radius, self.trail_radius), self.trail_radius)
                surface.blit(trail_mark_surface,
                             (int(trail_draw_x - self.trail_radius), int(trail_draw_y - self.trail_radius)))

    def draw_splash_particles(self, surface, camera_y_offset):
        if not self.is_active or not self.rect or self.is_hidden: return
        for p_splash in self.splash_particles:
            current_alpha = max(0, min(255, int(p_splash['alpha'])))
            if current_alpha > 0:
                splash_draw_x, splash_draw_y = p_splash['screen_x'], p_splash['world_y'] - camera_y_offset
                size = p_splash['size']
                particle_color = p_splash.get('color', cfg.PLAYER_TRAIL_COLOR_SNOW)
                splash_mark_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                splash_mark_surface.fill((0, 0, 0, 0))
                pygame.draw.circle(splash_mark_surface,
                                   (particle_color[0], particle_color[1], particle_color[2], current_alpha),
                                   (size, size), size)
                surface.blit(splash_mark_surface, (int(splash_draw_x - size), int(splash_draw_y - size)))