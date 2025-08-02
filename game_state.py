# game_state.py

MENU = 'menu'
PLAYING = 'playing'
PAUSED = 'paused'
FAILED = 'failed'
CONTROLS = 'controls'
SETTINGS = 'settings'
PROLOGUE = 'prologue'
TUTORIAL = 'tutorial'
MID_CUTSCENE = 'mid_cutscene'
WIN_CUTSCENE = 'win_cutscene' 
CREDITS = 'credits'


current_state = MENU


menu_options = ['Start Level 1', 'Start Level 2', 'Controls', 'Settings', 'Quit']
menu_idx = 0
pause_menu_options = ["Resume", "Restart Level", "Controls", "Settings", "Quit to Main Menu"]
pause_menu_idx = 0
previous_game_state_before_options = None


mid_cutscene_start_time = 0
win_cutscene_start_time = 0 


tutorial_jump_done = False
tutorial_shoot_done = False


world_distance_scrolled = 0.0
checkpoint_idx = 0
collected_checkpoints = 0
spawned_ramp = False
player_health = 100
waiting_for_death_anim_to_finish = False
is_slowed_down = False
slowdown_end_time = 0
last_obstacle_spawn_time = 0
next_obstacle_spawn_delay = 0
last_shot_time = 0
portal_message_pending = False
is_level_2_simple_mode = False
level1_video_playthrough_start_time = 0
level2_video_playthrough_start_time = 0


consecutive_obstacle_hits = 0
boulder_catch_up_active = False
boulder_is_visible = False
boulder_death_sequence_active = False
boulder_death_sequence_end_time = 0



level2_win_sequence_active = False      
level2_win_sequence_timer_end = 0       
level2_win_flash_current_color_idx = 0  
level2_win_last_flash_time = 0          


level2_stairs_visible = False       
level2_stairs_rect_world = None     
level2_player_reached_stairs = False    
level2_player_hidden_after_stairs = False 



portal_spawn_pending = False
portal_object_exists = False
portal_reached = False
portal_reached_time = 0
PORTAL_OUTCOME_DELAY = 1500


colony_saved_message_active = False
colony_saved_message_timer_end = 0
colony_saved_message_text = "GRAVITY NODE ONLINE!"
colony_saved_message_duration = 2500
colony_saved_message_last_trigger_checkpoint_count = -1


ariel_display_active = False
ariel_display_on_screen_end_time = 0
ariel_current_message_lines = []
ariel_anim_state = 'hidden'
ariel_current_x = 0
ariel_target_x_on_screen = 0
ariel_next_message_on_screen_duration_ms = 0


music_volume = 0.5


screen_shake_magnitude = 0
screen_shake_duration = 0.0
screen_shake_timer = 0.0


credits_text = []
credits_scroll_y = 0.0
credits_line_height = 35
credits_scroll_speed = 40.0


level2_bug_warning_trigger_time = 0
level2_bug_warning_triggered_this_level = False


level2_halfway_message_triggered = False
level2_halfway_trigger_time = 0


level2_end_message_triggered = False
level2_end_message_trigger_time = 0


def set_state(new_state):
    global current_state
    current_state = new_state

def get_state():
    global current_state
    return current_state