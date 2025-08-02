# avalanche.py
import pygame
from config import WIDTH, HEIGHT, AVALANCHE_SPEED, CHECKPOINT_DISTANCES, PLAYER_SCREEN_X 
import game_state as gs 

AVALANCHE_ENDGAME_CATCHUP_SLOW_FACTOR = 0.4 
MAX_CONTINUOUS_AVALANCHE_SHAKE = 7  


class Avalanche:
    def __init__(self, sound_effect=None):
        self.sound_effect = sound_effect
        self.offset = -WIDTH // 3 
        self.rumble_effect_triggered = False
        self.request_rumble_effect_flag = False  

        self.sound_channel = None
        self.is_sound_looping = False
        self.continuous_shake_magnitude = 0

    def reset(self, initial_offset_val):
        self.offset = initial_offset_val
        self.rumble_effect_triggered = False
        self.request_rumble_effect_flag = False
        self.continuous_shake_magnitude = 0
        if self.sound_channel and self.is_sound_looping:
            print("Avalanche: Stopping looped sound (reset).")
            self.sound_channel.stop()
        self.sound_channel = None
        self.is_sound_looping = False

    def update(self, player_screen_x_pos, _player_is_in_cloud_jump_unused, current_game_state,
               set_game_state_func):  
        
        if current_game_state == 'tutorial':
            if self.is_sound_looping and self.sound_channel:  
                self.sound_channel.stop()
                self.is_sound_looping = False
            self.continuous_shake_magnitude = 0
            return

        current_applied_avalanche_speed = AVALANCHE_SPEED 

      
        all_checkpoints_collected = (len(CHECKPOINT_DISTANCES) > 0 and
                                     gs.collected_checkpoints >= len(CHECKPOINT_DISTANCES))

        if all_checkpoints_collected:
         
            distance_avalanche_to_player = player_screen_x_pos - self.offset
            catch_up_threshold = WIDTH * 0.33
            if 0 < distance_avalanche_to_player < catch_up_threshold:
                current_applied_avalanche_speed = AVALANCHE_SPEED * AVALANCHE_ENDGAME_CATCHUP_SLOW_FACTOR

        self.offset += current_applied_avalanche_speed

     
     
        sound_trigger_offset = -50

        if self.offset > sound_trigger_offset and current_game_state == 'playing':
          
            if not self.is_sound_looping and self.sound_effect and pygame.mixer.get_init():
                self.sound_channel = pygame.mixer.find_channel(True) 
                if self.sound_channel:
                    print("Avalanche: Starting looped sound.")
                    try:
                        self.sound_channel.play(self.sound_effect, loops=-1)
                        self.is_sound_looping = True
                    except pygame.error as e:
                        print(f"Error playing looping avalanche sound: {e}")
                        self.sound_channel = None  
                else:
                    print("Avalanche: Could not find a channel for looping sound.")

       
            if not self.rumble_effect_triggered:
                self.request_rumble_effect_flag = True 
                self.rumble_effect_triggered = True

        
        elif (current_game_state != 'playing' or self.offset <= sound_trigger_offset):
            if self.is_sound_looping and self.sound_channel:
                print("Avalanche: Stopping looped sound (not relevant or game state changed).")
                self.sound_channel.stop()
                self.is_sound_looping = False

      
        if self.offset >= 0 and current_game_state == 'playing':  
            
            
            shake_intensity_start_offset = 0
            shake_intensity_full_offset = player_screen_x_pos * 0.8 

            if self.offset >= shake_intensity_start_offset:
                clamped_offset = max(shake_intensity_start_offset, min(self.offset, shake_intensity_full_offset))
                range_for_intensity_increase = shake_intensity_full_offset - shake_intensity_start_offset

                proximity_factor = 0.0
                if range_for_intensity_increase <= 0: 
                    if self.offset >= shake_intensity_full_offset:
                        proximity_factor = 1.0
                else:
                    proximity_factor = (clamped_offset - shake_intensity_start_offset) / range_for_intensity_increase

                self.continuous_shake_magnitude = proximity_factor * MAX_CONTINUOUS_AVALANCHE_SHAKE

                if self.offset > shake_intensity_full_offset: 
                    self.continuous_shake_magnitude = MAX_CONTINUOUS_AVALANCHE_SHAKE
            else:
                self.continuous_shake_magnitude = 0
        else:
            self.continuous_shake_magnitude = 0


        if self.offset >= player_screen_x_pos and current_game_state == 'playing':
            set_game_state_func('failed')
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            if self.is_sound_looping and self.sound_channel: 
                print("Avalanche: Stopping looped sound (game failed).")
                self.sound_channel.stop()
                self.is_sound_looping = False
            self.continuous_shake_magnitude = 0 

    def draw(self, surface, current_game_state, terrain_obj, camera_y_offset, avalanche_image_surface=None):
        if current_game_state == 'tutorial':
            return

        avalanche_visible_width_on_screen = int(max(0, self.offset))

        if avalanche_visible_width_on_screen <= 0:
            return  

        if avalanche_image_surface:
            img_total_width = avalanche_image_surface.get_width()
            img_height = avalanche_image_surface.get_height()

            draw_width_from_image = min(avalanche_visible_width_on_screen, img_total_width)

            if draw_width_from_image > 0:
                source_rect_x_on_main_image = img_total_width - draw_width_from_image
                source_rect = pygame.Rect(source_rect_x_on_main_image, 0, draw_width_from_image, img_height)
                blit_target_pos = (0, 0)
                per_frame_avalanche_draw_surface = pygame.Surface((draw_width_from_image, img_height), pygame.SRCALPHA)
                per_frame_avalanche_draw_surface.fill((0, 0, 0, 0))
                per_frame_avalanche_draw_surface.blit(avalanche_image_surface, (0, 0), area=source_rect)

                if terrain_obj:
                    mask_polygon_points = []
                    terrain_check_step = 5
                    for x_on_temp_surf in range(0, draw_width_from_image, terrain_check_step):
                        terrain_world_y = terrain_obj.height_at(x_on_temp_surf)
                        terrain_y_on_temp_surf = terrain_world_y - camera_y_offset
                        mask_polygon_points.append((x_on_temp_surf, terrain_y_on_temp_surf))

                    if not mask_polygon_points or mask_polygon_points[-1][0] < draw_width_from_image - 1:
                        x_on_temp_surf = draw_width_from_image - 1
                        terrain_world_y = terrain_obj.height_at(x_on_temp_surf)
                        terrain_y_on_temp_surf = terrain_world_y - camera_y_offset
                        mask_polygon_points.append((x_on_temp_surf, terrain_y_on_temp_surf))

                    if len(mask_polygon_points) >= 2:
                        mask_polygon_points.append((draw_width_from_image - 1, img_height))
                        mask_polygon_points.append((0, img_height))
                        try:
                            pygame.draw.polygon(per_frame_avalanche_draw_surface, (0, 0, 0, 0), mask_polygon_points)
                        except Exception as e:
                            pass
                surface.blit(per_frame_avalanche_draw_surface, blit_target_pos)
        else:
            fallback_surface = pygame.Surface((avalanche_visible_width_on_screen, HEIGHT), pygame.SRCALPHA)
            fallback_surface.fill((220, 220, 230, 100))
            surface.blit(fallback_surface, (0, 0))
