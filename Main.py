# Main.py
import pygame
import sys
import os
import random  
import math
import cv2

import config  
import ui
import game_state as gs

from player import Rider
from terrain import Terrain, Ramp
from obstacle import Obstacle, IceFormation, BrokenSatellite, BugObstacle, CrystalObstacle
from laser import Laser
from checkpoint import Beacon
from avalanche import Avalanche
from video_player import VideoPlayer
from explosion import Explosion
from debris_effect import DebrisEffect
from portal import Portal
from ceiling_decoration import CeilingDecoration
from hanging_light import HangingLight
from boulder import Boulder
from hud import HUD

print("--- Main.py: Starting execution ---")

pygame.init()
if pygame.mixer.get_init() is None:
    try:
        pygame.mixer.init()
        print("Pygame mixer initialized successfully.")
    except pygame.error as e:
        print(f"Pygame mixer could NOT be initialized: {e}")
else:
    print("Pygame mixer already initialized.")
screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
pygame.display.set_caption("Zephyr Odyssey")
clock = pygame.time.Clock()
base_dir = os.path.dirname(os.path.abspath(__file__))

try:
    font = pygame.font.SysFont("consolas", 24)
    title_font = pygame.font.SysFont("consolas", 48, bold=True)
    tutorial_font = pygame.font.SysFont("consolas", 30, bold=True)
    message_font = pygame.font.SysFont(" तहसील ", 60, bold=True)
    ariel_font = pygame.font.SysFont("consolas", 18, bold=True)
except Exception:
    font = pygame.font.Font(None, 30)
    title_font = pygame.font.Font(None, 60)
    tutorial_font = pygame.font.Font(None, 36)
    message_font = pygame.font.Font(None, 72)
    ariel_font = pygame.font.Font(None, 24)

hud_font = None
try:
    hud_font = pygame.font.SysFont("consolas", 24, bold=True)
except Exception as e_consolas:
    print(f"Note: Could not load bold 'consolas' (size 24) for HUD: {e_consolas}. Trying system default bold.")
    try:
        hud_font = pygame.font.SysFont(None, 26, bold=True)
    except Exception as e_sysbold:
        print(f"Note: Could not load system default bold font for HUD: {e_sysbold}. Using main game font as fallback.")
        hud_font = font
if hud_font is None:
    print("Critical Error: Main font and HUD font fallbacks failed. Using Pygame default font for HUD.")
    hud_font = pygame.font.Font(None, 26)

hud_manager = HUD(font, hud_font) 

soundtrack_loaded = False
if pygame.mixer.get_init():
    pygame.mixer.music.set_volume(gs.music_volume)
    for name in ("SoundTrack.wav", "SoundTrack.ogg", "SoundTrack.mp3"):
        path = os.path.join(base_dir, "assets", name)
        if os.path.exists(path):
            try:
                pygame.mixer.music.load(path)
                soundtrack_loaded = True
                print(f"Soundtrack: {name} loaded.")
                break
            except pygame.error as e:
                print(f"Could not load soundtrack {name}: {e}")
    if not soundtrack_loaded: print("No suitable soundtrack file found.")
else:
    print("Mixer not initialized for music.")

sound_effects = {}
ariel_node_sounds = []
ariel_node_sound_default_volumes = []
MAX_NODE_SOUNDS = 10

if pygame.mixer.get_init():
    sound_data = [("checkpoint_sound", "Checkpoint Sound Effect.wav", 0.7),
                  ("hit_sound", "HitSound.wav", 0.8),
                  ("laser_sound", "Laser Gun.wav", 0.5),
                  ("explosion_sound", "Explosion Sound Effect.wav", 0.7),
                  ("jump_sound", "Jump Sound.wav", 0.6),
                  ("spike_breaking_sound", "spike breaking.wav", 0.7),
                  ("satellite_crash_sound", "satellite_crash.wav", 0.9),
                  ("portal_sound", "portal.wav", 0.8),
                  ("prologue_audio", "Prologue.WAV", 1.0),
                  ("satellite_impact_sound", "Satellite_crash2.WAV", 0.9),
                  ("avalanche_sound", "Avalanche.WAV", 0.7),
                  ("bug_spawn_sound", "bug1.wav", 0.6),
                  ("bug_die_sound", "bug_die.wav", 0.7),
                  (config.CRYSTAL_GROUND_IMPACT_SOUND_KEY, "crystal_impact.wav", 0.85),
                  ("middle_cutscene_audio", "MiddleCutscene.wav", 1.0),
                  ("final_cutscene_audio", "Finalscene.wav", 1.0),
                  ("bug_warning_sound_effect", "bug_warning.wav", 0.8),
                  ("level2_halfway_sound", "level2_halfway.wav", 0.8),
                  ("level2_end_sound", "level2_end.wav", 0.85),
                  ("boulder_sound", "boulder.wav", 0.8)  
                  ]
    for var_name, filename, default_vol in sound_data:
        path = os.path.join(base_dir, "assets", filename)
        if os.path.exists(path):
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(
                    min(1.0, default_vol * (
                        gs.music_volume / 0.5 if gs.music_volume > 0 else 1.0)))
                sound_effects[var_name] = sound
                print(f"Sound effect: {filename} loaded as {var_name}.")
            except pygame.error as e:
                print(f"Could not load sound {filename}: {e}")
        else:
            print(f"Sound effect file not found: {filename}")

    num_ariel_messages = len(config.ARIEL_MESSAGES) if hasattr(config, 'ARIEL_MESSAGES') else MAX_NODE_SOUNDS
    for i in range(1, num_ariel_messages + 1):
        filename = f"node{i}.wav"
        path = os.path.join(base_dir, "assets", filename)
        sound_to_add = None
        default_vol_for_this_node = 0.9
        if os.path.exists(path):
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(
                    min(1.0, default_vol_for_this_node * (gs.music_volume / 0.5 if gs.music_volume > 0 else 1.0))
                )
                sound_to_add = sound
                print(f"Ariel node sound: {filename} loaded.")
            except pygame.error as e:
                print(f"Could not load Ariel node sound {filename}: {e}")
        else:
            print(f"Ariel node sound file not found: {filename}")
        ariel_node_sounds.append(sound_to_add)
        ariel_node_sound_default_volumes.append(default_vol_for_this_node if sound_to_add else 0)

checkpoint_sound = sound_effects.get("checkpoint_sound")
hit_sound = sound_effects.get("hit_sound")
laser_sound = sound_effects.get("laser_sound")
explosion_sound = sound_effects.get("explosion_sound")
jump_sound = sound_effects.get("jump_sound")
spike_breaking_sound = sound_effects.get("spike_breaking_sound")
satellite_falling_sound_asset = sound_effects.get("satellite_crash_sound")
satellite_impact_sound_asset = sound_effects.get("satellite_impact_sound")
portal_sound_effect = sound_effects.get("portal_sound")
prologue_audio_sound = sound_effects.get("prologue_audio")
avalanche_rumble_sound = sound_effects.get("avalanche_sound")
bug_spawn_sound_effect = sound_effects.get("bug_spawn_sound")
bug_die_sound_effect = sound_effects.get("bug_die_sound")
middle_cutscene_audio_sound = sound_effects.get("middle_cutscene_audio")
final_cutscene_audio_sound = sound_effects.get("final_cutscene_audio")
bug_warning_sound_effect = sound_effects.get("bug_warning_sound_effect")
level2_halfway_sound_effect = sound_effects.get("level2_halfway_sound")
level2_end_sound_effect = sound_effects.get("level2_end_sound")
boulder_sound_effect = sound_effects.get("boulder_sound")  
boulder_sound_effect_channel = None  


def update_sound_effect_volumes():
    if pygame.mixer.get_init():
        pygame.mixer.music.set_volume(gs.music_volume)
        original_sound_data_for_volume_update = [
            ("checkpoint_sound", "Checkpoint Sound Effect.wav", 0.7),
            ("hit_sound", "HitSound.wav", 0.8),
            ("laser_sound", "Laser Gun.wav", 0.5),
            ("explosion_sound", "Explosion Sound Effect.wav", 0.7),
            ("jump_sound", "Jump Sound.wav", 0.6),
            ("spike_breaking_sound", "spike breaking.wav", 0.7),
            ("satellite_crash_sound", "satellite_crash.wav", 0.9),
            ("portal_sound", "portal.wav", 0.8),
            ("prologue_audio", "Prologue.WAV", 1.0),
            ("satellite_impact_sound", "Satellite_crash2.WAV", 0.9),
            ("avalanche_sound", "Avalanche.WAV", 0.7),
            ("bug_spawn_sound", "bug1.wav", 0.6),
            ("bug_die_sound", "bug_die.wav", 0.7),
            (config.CRYSTAL_GROUND_IMPACT_SOUND_KEY, "crystal_impact.wav", 0.85),
            ("middle_cutscene_audio", "MiddleCutscene.wav", 1.0),
            ("final_cutscene_audio", "Finalscene.wav", 1.0),
            ("bug_warning_sound_effect", "bug_warning.wav", 0.8),
            ("level2_halfway_sound", "level2_halfway.wav", 0.8),
            ("level2_end_sound", "level2_end.wav", 0.85),
            ("boulder_sound", "boulder.wav", 0.8) 
        ]
        for var_name, _, default_vol in original_sound_data_for_volume_update:
            if sound_effects.get(var_name):
                sound_effects[var_name].set_volume(
                    min(1.0,
                        default_vol * (gs.music_volume / 0.5 if gs.music_volume > 0 else 1.0)))
        for i, sound in enumerate(ariel_node_sounds):
            if sound:
                default_vol = ariel_node_sound_default_volumes[i]
                sound.set_volume(
                    min(1.0, default_vol * (gs.music_volume / 0.5 if gs.music_volume > 0 else 1.0))
                )


cloud_image_1, cloud_image_2 = None, None
try:
    cloud1_path = os.path.join(base_dir, "assets", "clouds1.png")
    _exists = os.path.exists(cloud1_path)
    if _exists: cloud_image_1 = pygame.image.load(cloud1_path).convert_alpha()
    if cloud_image_1: cloud_image_1 = pygame.transform.scale(cloud_image_1, (config.WIDTH, config.HEIGHT // 2))
    cloud2_path = os.path.join(base_dir, "assets", "clouds2.png")
    _exists = os.path.exists(cloud2_path)
    if _exists: cloud_image_2 = pygame.image.load(cloud2_path).convert_alpha()
    if cloud_image_2: cloud_image_2 = pygame.transform.scale(cloud_image_2, (config.WIDTH, config.HEIGHT // 2))
except Exception as e:
    print(f"Error loading cloud images: {e}")

menu_bg_frames = []
menu_frame_idx = 0
menu_frame_timer = pygame.time.get_ticks()
menu_gif_path = os.path.join(base_dir, "assets", "MenuBackground.gif")
gif_frame_duration = 100

if os.path.exists(menu_gif_path):
    try:
        from PIL import Image

        gif = Image.open(menu_gif_path)
        default_gif_duration = 100
        if 'duration' in gif.info: default_gif_duration = gif.info['duration']
        gif_frame_duration = default_gif_duration
        for frame_num in range(gif.n_frames):
            gif.seek(frame_num)
            frame_rgba = gif.convert("RGBA")
            pygame_image = pygame.image.frombuffer(frame_rgba.tobytes(), frame_rgba.size, "RGBA")
            scaled_image = pygame.transform.scale(pygame_image, (config.WIDTH, config.HEIGHT))
            menu_bg_frames.append(scaled_image)
    except ImportError:
        print("Pillow library not found, GIF menu background will not be animated.")
        menu_bg_frames = []
    except Exception as e:
        print(f"Error loading menu GIF: {e}")
        menu_bg_frames = []

if not menu_bg_frames:
    fallback_bg = pygame.Surface((config.WIDTH, config.HEIGHT))
    fallback_bg.fill((20, 20, 50))
    menu_bg_frames.append(fallback_bg)

prologue_video_player = None
prologue_audio_channel = None
middle_cutscene_video_player = None
middle_cutscene_audio_channel = None
final_cutscene_video_player = None
final_cutscene_audio_channel = None

player_idle_frames = []
player_sprite_dir = os.path.join(base_dir, "assets")
target_player_w, target_player_h = config.PLAYER_TARGET_WIDTH, config.PLAYER_TARGET_HEIGHT
for i in range(1, 9):
    frame_filename = f"Shepherd_idle_{i}.png"
    frame_path = os.path.join(player_sprite_dir, frame_filename)
    if os.path.exists(frame_path):
        try:
            frame_img = pygame.image.load(frame_path).convert_alpha()
            frame_img = pygame.transform.smoothscale(
                frame_img, (target_player_w, target_player_h))
            player_idle_frames.append(frame_img)
        except pygame.error as e:
            print(f"Could not load player idle frame {frame_path}: {e}")
if not player_idle_frames: print("ERROR: No player idle frames loaded.")

player_shooting_frames = []
for i in range(1, 4):
    frame_filename = f"Shepherd_gun_{i}_standardized.png"
    frame_path = os.path.join(player_sprite_dir, frame_filename)
    if os.path.exists(frame_path):
        try:
            frame_img = pygame.image.load(frame_path).convert_alpha()
            frame_img = pygame.transform.smoothscale(
                frame_img, (target_player_w, target_player_h))
            player_shooting_frames.append(frame_img)
        except pygame.error as e:
            print(f"Could not load player shooting frame {frame_path}: {e}")
if not player_shooting_frames:
    print("WARNING: No player shooting frames loaded. Shooting animation will not use specific frames.")

player_dying_frames = []
for i in range(1, 5):
    frame_filename = f"Shepherd_die_{i}.png"
    frame_path = os.path.join(player_sprite_dir, frame_filename)
    if os.path.exists(frame_path):
        try:
            frame_img = pygame.image.load(frame_path).convert_alpha()
            frame_img = pygame.transform.smoothscale(
                frame_img, (target_player_w, target_player_h))
            player_dying_frames.append(frame_img)
        except pygame.error as e:
            print(f"Could not load player dying frame {frame_path}: {e}")
if not player_dying_frames:
    print("WARNING: No player dying frames loaded. Dying animation will not use specific frames.")

level1_video_player = None
video_path_level1 = os.path.join(base_dir, "assets", "background.mp4")
if os.path.exists(video_path_level1):
    print(f"Level 1 video path found: {video_path_level1}")
else:
    print(f"Level 1 video path NOT found: {video_path_level1}")

level2_video_player = None
video_path_level2 = os.path.join(base_dir, "assets", "Background2.mp4")
if os.path.exists(video_path_level2):
    print(f"Level 2 video path found: {video_path_level2}")
else:
    print(f"Level 2 video path NOT found: {video_path_level2}")

ariel_image = None
ariel_image_scaled = None
ariel_target_height = int(config.HEIGHT * 0.22)

try:
    ariel_path = os.path.join(base_dir, "assets", config.ARIEL_IMAGE_FILENAME)
    if os.path.exists(ariel_path):
        ariel_image = pygame.image.load(ariel_path).convert_alpha()
        original_width, original_height = ariel_image.get_size()
        if original_height > 0:
            scale_ratio = ariel_target_height / original_height
            ariel_scaled_width = int(original_width * scale_ratio)
            ariel_image_scaled = pygame.transform.smoothscale(ariel_image, (ariel_scaled_width, ariel_target_height))
            padding_from_right_edge_percentage = 0.10
            gs.ariel_target_x_on_screen = config.WIDTH - ariel_scaled_width - int(
                config.WIDTH * padding_from_right_edge_percentage)
        else:
            ariel_image_scaled = pygame.transform.smoothscale(ariel_image, (100, ariel_target_height))
            padding_from_right_edge_percentage = 0.25
            gs.ariel_target_x_on_screen = config.WIDTH - 100 - int(config.WIDTH * padding_from_right_edge_percentage)
            print(f"Warning: Original ariel.png height is 0. Using default scaled width.")
    else:
        print(f"ERROR: Ariel image '{config.ARIEL_IMAGE_FILENAME}' not found at {ariel_path}")
except Exception as e:
    print(f"Error loading or scaling Ariel image: {e}")

if ariel_image_scaled is None:
    ariel_image_scaled = pygame.Surface((int(ariel_target_height * 0.75), ariel_target_height), pygame.SRCALPHA)
    ariel_image_scaled.fill((100, 100, 255, 150))
    padding_from_right_edge_percentage = 0.25
    gs.ariel_target_x_on_screen = config.WIDTH - ariel_image_scaled.get_width() - int(
        config.WIDTH * padding_from_right_edge_percentage)

planet_image = None
planet_x = config.WIDTH
planet_y = 5
planet_speed = 0.70
planet2_image = None
planet2_x = config.WIDTH + 300
planet2_y = 15
planet2_speed = 0.45

planet_image_path = os.path.join(base_dir, "assets", "planet.png")
if os.path.exists(planet_image_path):
    try:
        planet_image_loaded_temp = pygame.image.load(planet_image_path).convert_alpha()
        desired_planet_width = 55
        if planet_image_loaded_temp.get_width() > 0:
            scale_factor = desired_planet_width / planet_image_loaded_temp.get_width()
            desired_planet_height = int(planet_image_loaded_temp.get_height() * scale_factor)
            planet_image = pygame.transform.smoothscale(planet_image_loaded_temp,
                                                        (desired_planet_width, desired_planet_height))
        else:
            planet_image = planet_image_loaded_temp
        print(f"Planet image loaded and scaled: {planet_image_path}")
    except Exception as e:
        print(f"Error loading or scaling planet.png: {e}")
        planet_image = None
else:
    print(f"Planet image not found at {planet_image_path}, will not be displayed.")

planet2_image_path = os.path.join(base_dir, "assets", "planet2.png")
if os.path.exists(planet2_image_path):
    try:
        planet2_image_loaded_temp = pygame.image.load(planet2_image_path).convert_alpha()
        desired_planet2_width = 45
        if planet2_image_loaded_temp.get_width() > 0:
            scale_factor2 = desired_planet2_width / planet2_image_loaded_temp.get_width()
            desired_planet2_height = int(planet2_image_loaded_temp.get_height() * scale_factor2)
            planet2_image = pygame.transform.smoothscale(planet2_image_loaded_temp,
                                                         (desired_planet2_width, desired_planet2_height))
        else:
            planet2_image = planet2_image_loaded_temp
        print(f"Planet2 image loaded and scaled: {planet2_image_path}")
    except Exception as e:
        print(f"Error loading or scaling planet2.png: {e}")
        planet2_image = None
else:
    print(f"Planet2 image not found at {planet2_image_path}, will not be displayed.")

avalanche_image = None
avalanche_image_path = os.path.join(base_dir, "assets", "avalanche.png")
if os.path.exists(avalanche_image_path):
    try:
        loaded_avalanche_img = pygame.image.load(avalanche_image_path).convert_alpha()
        original_width, original_height = loaded_avalanche_img.get_size()
        if original_height > 0:
            scale_ratio = config.HEIGHT / original_height
            scaled_width = int(original_width * scale_ratio)
            avalanche_image = pygame.transform.smoothscale(loaded_avalanche_img, (scaled_width, config.HEIGHT))
        else:
            print(f"Warning: avalanche.png original height is {original_height}. Using fallback scaling.")
            avalanche_image = pygame.transform.smoothscale(loaded_avalanche_img, (config.WIDTH // 2, config.HEIGHT))
        print(
            f"Avalanche image loaded and scaled: {avalanche_image_path}. Dimensions: {avalanche_image.get_size() if avalanche_image else 'None'}")
    except Exception as e:
        print(f"Error loading or scaling avalanche.png: {e}")
        avalanche_image = None
else:
    print(f"Avalanche image not found at {avalanche_image_path}. Avalanche will use fallback rendering.")

portal_image_asset_placeholder = None
try:
    portal_placeholder_path = os.path.join(base_dir, "assets", "portal1.png")
    if os.path.exists(portal_placeholder_path):
        loaded_portal_img = pygame.image.load(portal_placeholder_path).convert_alpha()
        portal_image_asset_placeholder = pygame.transform.smoothscale(loaded_portal_img, (100, 150))
        print(f"Portal placeholder image loaded (for reference): {portal_placeholder_path}")
    else:
        print(
            f"Portal placeholder image 'portal1.png' not found. Portal will use internal fallback if its own loading fails.")
except Exception as e:
    print(f"Error loading or scaling portal placeholder: {e}")

print("--- Loading Level 2 Ceiling Decoration Assets ---")
all_loaded_ceiling_decor_images = []
filename_to_decor_surface_map = {}

if config.L2_CEILING_DECORATION_ENABLED:
    for img_name, target_w, target_h in config.L2_MINERAL_ASSETS_CONFIG:
        path = os.path.join(base_dir, "assets", img_name)
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                img_scaled = pygame.transform.smoothscale(img, (target_w, target_h))
                all_loaded_ceiling_decor_images.append(img_scaled)
                filename_to_decor_surface_map[img_name] = img_scaled
                print(f"Loaded ceiling mineral: {img_name} scaled to ({target_w}x{target_h})")
            except Exception as e:
                print(f"Error loading/scaling mineral {img_name}: {e}")
        else:
            print(f"Mineral asset not found: {img_name}")

    for img_name, target_w, target_h in config.L2_FOSSIL_ASSETS_CONFIG:
        path = os.path.join(base_dir, "assets", img_name)
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                img_scaled = pygame.transform.smoothscale(img, (target_w, target_h))
                all_loaded_ceiling_decor_images.append(img_scaled)
                filename_to_decor_surface_map[img_name] = img_scaled
                print(f"Loaded ceiling fossil: {img_name} scaled to ({target_w}x{target_h})")
            except Exception as e:
                print(f"Error loading/scaling fossil {img_name}: {e}")
        else:
            print(f"Fossil asset not found: {img_name}")

if config.L2_CEILING_DECORATION_ENABLED and not all_loaded_ceiling_decor_images:
    print("WARNING: No ceiling decoration images loaded, L2 ceiling decoration effect will be disabled.")
    config.L2_CEILING_DECORATION_ENABLED = False

hanging_light_image_surface = None
if config.L2_HANGING_LIGHTS_ENABLED:
    path = os.path.join(base_dir, "assets", config.L2_HANGING_LIGHT_IMAGE_FILENAME)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            hanging_light_image_surface = pygame.transform.smoothscale(
                img, (config.L2_HANGING_LIGHT_TARGET_WIDTH, config.L2_HANGING_LIGHT_TARGET_HEIGHT)
            )
            print(
                f"Loaded hanging light: {config.L2_HANGING_LIGHT_IMAGE_FILENAME} scaled to ({config.L2_HANGING_LIGHT_TARGET_WIDTH}x{config.L2_HANGING_LIGHT_TARGET_HEIGHT})")
        except Exception as e:
            print(f"Error loading/scaling hanging light {config.L2_HANGING_LIGHT_IMAGE_FILENAME}: {e}")
            hanging_light_image_surface = None
    else:
        print(f"Hanging light asset not found: {config.L2_HANGING_LIGHT_IMAGE_FILENAME}")

if config.L2_HANGING_LIGHTS_ENABLED and not hanging_light_image_surface:
    print("WARNING: Hanging light image not loaded, L2 hanging light effect will be disabled.")
    config.L2_HANGING_LIGHTS_ENABLED = False

boulder_image_asset = None
if config.BOULDER_ENABLED_L2:
    boulder_path = os.path.join(base_dir, "assets", "boulder.png")
    if os.path.exists(boulder_path):
        try:
            img = pygame.image.load(boulder_path).convert_alpha()
            boulder_image_asset = pygame.transform.smoothscale(
                img, (config.BOULDER_TARGET_WIDTH, config.BOULDER_TARGET_HEIGHT)
            )
            print(
                f"Loaded boulder: boulder.png scaled to ({config.BOULDER_TARGET_WIDTH}x{config.BOULDER_TARGET_HEIGHT})")
        except Exception as e:
            print(f"Error loading/scaling boulder.png: {e}")
            boulder_image_asset = None
    else:
        print(f"Boulder asset not found: boulder.png. Boulder will not appear.")
        config.BOULDER_ENABLED_L2 = False

if config.BOULDER_ENABLED_L2 and not boulder_image_asset:
    print("WARNING: Boulder image not loaded but enabled. Boulder will be disabled.")
    config.BOULDER_ENABLED_L2 = False

stairs_image_asset = None
stairs_image_path = os.path.join(base_dir, "assets", "stairs.png")
STAIRS_TARGET_HEIGHT = config.HEIGHT // 2.5
if os.path.exists(stairs_image_path):
    try:
        loaded_stairs_img = pygame.image.load(stairs_image_path).convert_alpha()
        original_width, original_height = loaded_stairs_img.get_size()
        if original_height > 0:
            scale_ratio = STAIRS_TARGET_HEIGHT / original_height
            scaled_width = int(original_width * scale_ratio)
            stairs_image_asset = pygame.transform.smoothscale(loaded_stairs_img,
                                                              (scaled_width, int(STAIRS_TARGET_HEIGHT)))
            print(
                f"Stairs image loaded and scaled: {stairs_image_path} to ({scaled_width}x{int(STAIRS_TARGET_HEIGHT)})")
        else:
            print(f"Warning: stairs.png original height is 0. Using fallback scaling.")
            stairs_image_asset = pygame.transform.smoothscale(loaded_stairs_img, (100, int(STAIRS_TARGET_HEIGHT)))
    except Exception as e:
        print(f"Error loading or scaling stairs.png: {e}")
        stairs_image_asset = None
else:
    print(f"Stairs image not found: {stairs_image_path}. Level 2 win sequence might not work as intended.")

avalanche_obj = Avalanche(sound_effect=avalanche_rumble_sound)

fog_layers = []
if config.ENABLE_FOG_EFFECT:
    print("Creating procedural fog layers...")
    for layer_conf in config.PROCEDURAL_FOG_LAYERS_CONFIG:
        try:
            fog_surface_width = int(config.WIDTH * 1.5)
            fog_surface_height = layer_conf["height_on_screen"]
            if fog_surface_width <= 0 or fog_surface_height <= 0: continue
            layer_surface = pygame.Surface((fog_surface_width, fog_surface_height), pygame.SRCALPHA)
            layer_surface.fill((0, 0, 0, 0))

            for _ in range(layer_conf["num_main_puffs"]):
                main_puff_center_x = random.randint(0, fog_surface_width)
                main_puff_center_y = random.randint(int(fog_surface_height * 0.2), int(fog_surface_height * 0.8))
                main_puff_base_radius = random.randint(layer_conf["puff_base_radius_min"],
                                                       layer_conf["puff_base_radius_max"])

                for _ in range(layer_conf["puff_sub_puffs"]):
                    offset_x = random.randint(-main_puff_base_radius // 2, main_puff_base_radius // 2)
                    offset_y = random.randint(-main_puff_base_radius // 3, main_puff_base_radius // 3)
                    sub_puff_x = main_puff_center_x + offset_x
                    sub_puff_y = main_puff_center_y + offset_y
                    sub_puff_radius = int(
                        main_puff_base_radius * layer_conf["puff_sub_radius_factor"] * random.uniform(0.6, 1.4))
                    if sub_puff_radius <= 0: continue
                    sub_puff_alpha = random.randint(layer_conf["puff_alpha_min"], layer_conf["puff_alpha_max"])
                    puff_color_rgb = layer_conf["color"]

                    ellipse_width = int(sub_puff_radius * random.uniform(1.2, 2.8))
                    ellipse_height = int(sub_puff_radius * random.uniform(0.7, 1.7))
                    ellipse_width = max(3, ellipse_width)
                    ellipse_height = max(3, ellipse_height)

                    temp_ellipse_surf = pygame.Surface((ellipse_width, ellipse_height), pygame.SRCALPHA)
                    temp_ellipse_surf.fill((0, 0, 0, 0))
                    pygame.draw.ellipse(temp_ellipse_surf, (*puff_color_rgb, sub_puff_alpha),
                                        (0, 0, ellipse_width, ellipse_height))
                    layer_surface.blit(temp_ellipse_surf,
                                       (sub_puff_x - ellipse_width // 2, sub_puff_y - ellipse_height // 2))

            alpha_gradient_surf = pygame.Surface((1, fog_surface_height), pygame.SRCALPHA)
            for y_grad in range(fog_surface_height):
                middle_band_ratio = 0.7
                fade_pixels = (fog_surface_height * (1.0 - middle_band_ratio)) / 2.0
                alpha_val = 255
                if fade_pixels > 0:
                    if y_grad < fade_pixels:
                        alpha_val = int(255 * (y_grad / fade_pixels))
                    elif y_grad > fog_surface_height - fade_pixels:
                        alpha_val = int(255 * ((fog_surface_height - y_grad) / fade_pixels))
                alpha_gradient_surf.set_at((0, y_grad), (255, 255, 255, max(0, min(255, alpha_val))))

            alpha_gradient_surf = pygame.transform.scale(alpha_gradient_surf, (fog_surface_width, fog_surface_height))
            layer_surface.blit(alpha_gradient_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            fog_layers.append({
                "surface": layer_surface,
                "y_offset_from_bottom": layer_conf["y_offset_from_bottom"],
                "scroll_factor": layer_conf["scroll_factor"],
                "x_pos": 0.0
            })
        except Exception as e:
            print(f"Error creating procedural organic fog layer: {e}")

player_obj = None
terrain_obj = None
current_ramp_obj = None
boulder_obj = None
obstacles_group = pygame.sprite.Group()
lasers_group = pygame.sprite.Group()
beacons_group = pygame.sprite.Group()
explosions_group = pygame.sprite.Group()
debris_effects_group = pygame.sprite.Group()
portal_group = pygame.sprite.Group()
ceiling_decorations_group = pygame.sprite.Group()
hanging_lights_group = pygame.sprite.Group()
snowflakes_by_layer = []
paused_game_surface_local = None
cam_y_offset = 0
tutorial_obstacle_was_present = False
is_gusting = False
gust_end_time = 0
next_gust_time = 0
current_gust_x_strength = 0
current_gust_y_factor = 0
meteors_list = []
next_meteor_spawn_time = 0
last_ceiling_decoration_spawn_world_x = -float('inf')
next_ceiling_decoration_spawn_target_x = 0
last_hanging_light_spawn_world_x = -float('inf')
next_hanging_light_spawn_target_x = 0

cloud_y_1_draw = config.HEIGHT
cloud_y_2_draw = config.HEIGHT + config.HEIGHT // 2

credits_content_definition = [
    "Zephyr Odyssey",
    "",
    "A Project By Group 32:",
    "AYAAN MINHAS",
    "MUHAMMAD NOORULLAH BAIG",
    "AJNEYA LAL",
    "AMAL DJASREEL BIN AMRIL",
    "",
    "~ Core Gameplay ~",
    "Player Mechanics",
    "Terrain Generation",
    "Obstacle Systems",
    "Level Progression",
    "",
    "~ Visuals & Effects ~",
    "Procedural Backgrounds",
    "Particle Systems (Snow, Smoke, Explosions)",
    "Character Animation",
    "Lighting Effects (L2)",
    "",
    "~ Audio ~",
    "Sound Effects Integration",
    "Dynamic Music Volume",
    "",
    "~ Special Features ~",
    "Level 1: Avalanche & Checkpoints",
    "Level 2: Boulder Chase & Cavern Theme",
    "Cutscenes & Story Elements",
    "UI & Menus",
    "",
    "~ Tools & Libraries ~",
    "Python",
    "Pygame",
    "Pillow (PIL for Gifs)",
    "OpenCV (for MP4 playback)",
    "",
    "~ Assets ~",
    "Many assets generated or placeholders.",
    "Specific asset credits would go here if sourced externally.",
    "",
    "Thank you for playing!",
    "",
    "And thank you to A.R.I.E.L for helping to build this."
]
gs.credits_text = credits_content_definition


def set_current_game_state(new_state): gs.set_state(new_state)


def setup_tutorial_state():
    global player_obj, terrain_obj, current_ramp_obj, obstacles_group, lasers_group, beacons_group, explosions_group, debris_effects_group, portal_group, snowflakes_by_layer, cam_y_offset, tutorial_obstacle_was_present, player_idle_frames, player_shooting_frames, player_dying_frames, planet_x, planet_y, planet2_x, planet2_y
    global prologue_video_player, prologue_audio_sound, prologue_audio_channel
    global avalanche_obj, level1_video_player, level2_video_player
    global ceiling_decorations_group, last_ceiling_decoration_spawn_world_x, next_ceiling_decoration_spawn_target_x
    global hanging_lights_group, last_hanging_light_spawn_world_x, next_hanging_light_spawn_target_x
    global boulder_obj
    global middle_cutscene_video_player, middle_cutscene_audio_channel
    global final_cutscene_video_player, final_cutscene_audio_channel
    global boulder_sound_effect_channel 

    print("DEBUG: Setting up tutorial state.")
    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
        print("DEBUG: Music playing, stopping it for tutorial setup.")
        pygame.mixer.music.stop()
    if prologue_audio_channel and prologue_audio_channel.get_busy():
        print("DEBUG: Prologue audio channel busy, stopping it for tutorial setup.")
        prologue_audio_channel.stop()
    prologue_audio_channel = None

    if prologue_video_player:
        prologue_video_player.release()
        prologue_video_player = None

    if middle_cutscene_video_player:
        middle_cutscene_video_player.release()
        middle_cutscene_video_player = None
    if middle_cutscene_audio_channel and middle_cutscene_audio_channel.get_busy():
        middle_cutscene_audio_channel.stop()
    middle_cutscene_audio_channel = None

    if final_cutscene_video_player:
        final_cutscene_video_player.release()
        final_cutscene_video_player = None
    if final_cutscene_audio_channel and final_cutscene_audio_channel.get_busy():
        final_cutscene_audio_channel.stop()
    final_cutscene_audio_channel = None

    if level1_video_player: level1_video_player.release(); level1_video_player = None
    if level2_video_player: level2_video_player.release(); level2_video_player = None

    
    if boulder_sound_effect_channel and boulder_sound_effect_channel.get_busy():
        print("Boulder sound: Stopping due to tutorial setup.")
        boulder_sound_effect_channel.stop()
    boulder_sound_effect_channel = None

    set_current_game_state(gs.TUTORIAL)
    gs.tutorial_jump_done = False
    gs.tutorial_shoot_done = False
    gs.pause_menu_idx = 0
    terrain_obj = Terrain(is_tutorial=True)
    player_obj = Rider(player_idle_frames, player_shooting_frames, player_dying_frames)
    if player_obj:
        player_obj.is_active = True
        player_obj.reset_animation_flags()
        if player_obj.rect:
            player_obj.y_world = terrain_obj.height_at(player_obj.x)
            player_obj.rect.midbottom = (player_obj.x,
                                         player_obj.y_world)
        else:
            player_obj.y_world = terrain_obj.height_at(player_obj.x)
        player_obj.bullets_remaining = config.MAX_BULLETS
        player_obj.jump_count = 0
        player_obj.is_hidden = False

    gs.player_health = config.MAX_PLAYER_HEALTH

    if hud_manager and player_obj:
        hud_manager.previous_actual_health = gs.player_health
        hud_manager.displayed_health = gs.player_health
        hud_manager.health_change_flash_timer = 0

    gs.waiting_for_death_anim_to_finish = False
    obstacles_group.empty()
    lasers_group.empty()
    beacons_group.empty()
    explosions_group.empty()
    debris_effects_group.empty()
    portal_group.empty()
    ceiling_decorations_group.empty()
    hanging_lights_group.empty()
    boulder_obj = None
    tutorial_obstacle_was_present = False
    tut_obstacle_type = IceFormation
    tut_obstacle_spawn_x = config.PLAYER_SCREEN_X + config.WIDTH // 2.5
    if tut_obstacle_type == BrokenSatellite:
        tut_obstacle = tut_obstacle_type(tut_obstacle_spawn_x, terrain_obj, is_tutorial_obstacle=True,
                                         crash_sound_obj=satellite_falling_sound_asset,
                                         impact_sound_obj=satellite_impact_sound_asset)
    else:
        tut_obstacle = tut_obstacle_type(tut_obstacle_spawn_x, terrain_obj, is_tutorial_obstacle=True)

    obstacles_group.add(tut_obstacle)
    tutorial_obstacle_was_present = len(obstacles_group) > 0
    if not tutorial_obstacle_was_present: gs.tutorial_shoot_done = True

    if avalanche_obj:
        avalanche_obj.reset(initial_offset_val=-config.WIDTH * 5)

    current_ramp_obj = None
    if player_obj and player_obj.rect:
        cam_y_offset = (player_obj.y_world - player_obj.rect.height / 2.0) - config.PLAYER_TARGET_SCREEN_Y
    else:
        cam_y_offset = 0
    gs.checkpoint_idx = 0
    gs.collected_checkpoints = 0
    gs.world_distance_scrolled = 0.0
    gs.spawned_ramp = False
    gs.is_slowed_down = False
    gs.last_shot_time = 0
    snowflakes_by_layer = []
    is_gusting = False
    next_gust_time = 0
    gust_end_time = 0
    for fog_layer in fog_layers: fog_layer["x_pos"] = 0.0
    meteors_list = []
    next_meteor_spawn_time = 0
    last_ceiling_decoration_spawn_world_x = -float('inf')
    next_ceiling_decoration_spawn_target_x = 0
    last_hanging_light_spawn_world_x = -float('inf')
    next_hanging_light_spawn_target_x = 0
    gs.colony_saved_message_active = False
    gs.ariel_display_active = False
    gs.ariel_anim_state = 'hidden'
    gs.screen_shake_magnitude = 0
    gs.screen_shake_duration = 0.0
    gs.screen_shake_timer = 0.0
    gs.portal_message_pending = False
    gs.portal_spawn_pending = False
    gs.portal_object_exists = False
    gs.portal_reached = False
    gs.portal_reached_time = 0
    gs.win_cutscene_start_time = 0
    gs.is_level_2_simple_mode = False
    gs.consecutive_obstacle_hits = 0
    gs.boulder_catch_up_active = False
    gs.boulder_is_visible = False
    gs.boulder_death_sequence_active = False
    gs.boulder_death_sequence_end_time = 0
    if planet_image:
        planet_x = config.WIDTH + random.randint(50, 200)
    if planet2_image:
        planet2_x = config.WIDTH + random.randint(250, 450)
    gs.level2_win_sequence_active = False
    gs.level2_win_sequence_timer_end = 0
    gs.level2_stairs_visible = False
    gs.level2_stairs_rect_world = None
    gs.level2_player_reached_stairs = False
    gs.level2_player_hidden_after_stairs = False
    gs.ariel_next_message_on_screen_duration_ms = 0
    gs.level2_halfway_message_triggered = True
    gs.level2_halfway_trigger_time = 0
    gs.level2_end_message_triggered = True
    gs.level2_end_message_trigger_time = 0


def reset_game_state_vars(start_playing=True, is_simple_level_setup=False):
    global player_obj, terrain_obj, current_ramp_obj, obstacles_group, lasers_group, beacons_group, explosions_group, debris_effects_group, portal_group, snowflakes_by_layer, cam_y_offset, cloud_y_1_draw, cloud_y_2_draw, level1_video_player, level2_video_player, is_gusting, gust_end_time, next_gust_time, current_gust_x_strength, current_gust_y_factor, fog_layers, meteors_list, next_meteor_spawn_time, player_idle_frames, player_shooting_frames, player_dying_frames, planet_x, planet_y, planet2_x, planet2_y
    global prologue_video_player, prologue_audio_sound, prologue_audio_channel
    global avalanche_obj
    global ceiling_decorations_group, last_ceiling_decoration_spawn_world_x, next_ceiling_decoration_spawn_target_x
    global hanging_lights_group, last_hanging_light_spawn_world_x, next_hanging_light_spawn_target_x
    global boulder_obj, boulder_image_asset
    global middle_cutscene_video_player, middle_cutscene_audio_channel
    global final_cutscene_video_player, final_cutscene_audio_channel
    global boulder_sound_effect_channel 

    current_ticks_for_reset = pygame.time.get_ticks()

 
    if boulder_sound_effect_channel and boulder_sound_effect_channel.get_busy():
        print("Boulder sound: Stopping due to game state reset.")
        boulder_sound_effect_channel.stop()
    boulder_sound_effect_channel = None

    gs.is_level_2_simple_mode = is_simple_level_setup
    print(f"DEBUG: Resetting game state. start_playing={start_playing}, is_simple_level_setup={is_simple_level_setup}")

    if prologue_video_player:
        prologue_video_player.release()
        prologue_video_player = None
    if prologue_audio_channel and prologue_audio_channel.get_busy():
        prologue_audio_channel.stop()
    prologue_audio_channel = None

    if middle_cutscene_video_player:
        middle_cutscene_video_player.release()
        middle_cutscene_video_player = None
    if middle_cutscene_audio_channel and middle_cutscene_audio_channel.get_busy():
        middle_cutscene_audio_channel.stop()
    middle_cutscene_audio_channel = None

    if final_cutscene_video_player:
        final_cutscene_video_player.release()
        final_cutscene_video_player = None
    if final_cutscene_audio_channel and final_cutscene_audio_channel.get_busy():
        final_cutscene_audio_channel.stop()
    final_cutscene_audio_channel = None

    if start_playing:
        set_current_game_state(gs.PLAYING)
        if pygame.mixer.get_init() and soundtrack_loaded and not pygame.mixer.music.get_busy():
            print("DEBUG: Starting main soundtrack in reset_game_state_vars (start_playing=True).")
            pygame.mixer.music.play(-1)

        if gs.is_level_2_simple_mode:
            if level1_video_player: level1_video_player.release(); level1_video_player = None
            if level2_video_player is None and os.path.exists(video_path_level2):
                level2_video_player = VideoPlayer(video_path_level2, (config.WIDTH, config.HEIGHT))

            if level2_video_player and not level2_video_player.is_valid():
                level2_video_player = None
            elif level2_video_player and level2_video_player.is_valid():
                level2_video_player.reset_playthrough_counter()
                gs.level2_video_playthrough_start_time = current_ticks_for_reset
        else:
            if level2_video_player: level2_video_player.release(); level2_video_player = None
            if level1_video_player is None and os.path.exists(video_path_level1):
                level1_video_player = VideoPlayer(video_path_level1, (config.WIDTH, config.HEIGHT))

            if level1_video_player and not level1_video_player.is_valid():
                level1_video_player = None
            elif level1_video_player and level1_video_player.is_valid():
                level1_video_player.reset_playthrough_counter()
                gs.level1_video_playthrough_start_time = current_ticks_for_reset

    terrain_obj = Terrain(
        is_tutorial=not start_playing)

    if avalanche_obj:
        initial_av_offset = -config.WIDTH * 10 if gs.is_level_2_simple_mode else -config.WIDTH // 3
        avalanche_obj.reset(initial_offset_val=initial_av_offset)

    player_obj = Rider(player_idle_frames, player_shooting_frames, player_dying_frames)
    if player_obj:
        player_obj.is_active = True
        player_obj.reset_animation_flags()
        if player_obj.rect:
            player_obj.y_world = terrain_obj.height_at(player_obj.x)
            player_obj.rect.midbottom = (player_obj.x,
                                         player_obj.y_world)
        else:
            player_obj.y_world = terrain_obj.height_at(player_obj.x)
        player_obj.bullets_remaining = config.MAX_BULLETS
        player_obj.jump_count = 0
        player_obj.is_hidden = False

    gs.player_health = config.MAX_PLAYER_HEALTH

    if hud_manager and player_obj:
        hud_manager.previous_actual_health = gs.player_health
        hud_manager.displayed_health = gs.player_health
        hud_manager.health_change_flash_timer = 0

    gs.waiting_for_death_anim_to_finish = False
    obstacles_group.empty()
    lasers_group.empty()
    beacons_group.empty()
    explosions_group.empty()
    debris_effects_group.empty()
    portal_group.empty()
    ceiling_decorations_group.empty()
    hanging_lights_group.empty()

    if gs.is_level_2_simple_mode and config.BOULDER_ENABLED_L2 and boulder_image_asset and terrain_obj:
        if boulder_obj is None:
            boulder_obj = Boulder(boulder_image_asset, terrain_obj)
        else:
            boulder_obj.terrain = terrain_obj
        boulder_obj.reset()
        gs.consecutive_obstacle_hits = 0
        gs.boulder_catch_up_active = False
        gs.boulder_is_visible = False
        gs.boulder_death_sequence_active = False
        gs.boulder_death_sequence_end_time = 0
    else:
        boulder_obj = None
        gs.consecutive_obstacle_hits = 0
        gs.boulder_catch_up_active = False
        gs.boulder_is_visible = False
        gs.boulder_death_sequence_active = False
        gs.boulder_death_sequence_end_time = 0

    if gs.is_level_2_simple_mode:
        gs.level2_bug_warning_trigger_time = current_ticks_for_reset + 3000
        gs.level2_bug_warning_triggered_this_level = False
        gs.level2_halfway_message_triggered = False
        gs.level2_halfway_trigger_time = current_ticks_for_reset + config.L2_HALFWAY_DURATION_MS
        gs.level2_end_message_triggered = False
        gs.level2_end_message_trigger_time = current_ticks_for_reset + config.L2_END_MESSAGE_TRIGGER_TIME_MS

    current_ramp_obj = None
    gs.spawned_ramp = False
    if player_obj and player_obj.rect:
        cam_y_offset = (player_obj.y_world - player_obj.rect.height / 2.0) - config.PLAYER_TARGET_SCREEN_Y
    else:
        cam_y_offset = 0

    gs.checkpoint_idx = 0
    gs.collected_checkpoints = 0
    if gs.is_level_2_simple_mode:
        gs.checkpoint_idx = len(config.CHECKPOINT_DISTANCES) + 10
        gs.portal_message_pending = False
        gs.portal_spawn_pending = False
        gs.portal_object_exists = False

    gs.world_distance_scrolled = 0.0
    gs.is_slowed_down = False
    gs.slowdown_end_time = 0
    gs.last_shot_time = 0
    gs.pause_menu_idx = 0
    gs.last_obstacle_spawn_time = current_ticks_for_reset

    if gs.is_level_2_simple_mode:
        gs.next_obstacle_spawn_delay = random.randint(config.BUG_SPAWN_INTERVAL_MIN_L2,
                                                      config.BUG_SPAWN_INTERVAL_MAX_L2)
    else:
        gs.next_obstacle_spawn_delay = random.randint(config.OBSTACLE_SPAWN_INTERVAL_MIN,
                                                      config.OBSTACLE_SPAWN_INTERVAL_MAX)

    snowflakes_by_layer = []
    meteors_list = []
    next_meteor_spawn_time = 0
    last_ceiling_decoration_spawn_world_x = -float('inf')
    last_hanging_light_spawn_world_x = -float('inf')

    if gs.is_level_2_simple_mode and terrain_obj:
        world_x_screen_right_start = (
                                             terrain_obj.world_start_chunk_index + terrain_obj.scroll_fractional_offset) * config.CHUNK + config.WIDTH
        next_ceiling_decoration_spawn_target_x = world_x_screen_right_start + random.randint(
            -config.L2_CEILING_DECORATION_SPAWN_X_VARIATION,
            config.L2_CEILING_DECORATION_SPAWN_X_VARIATION
        )
        next_hanging_light_spawn_target_x = world_x_screen_right_start + random.randint(
            int(-config.L2_HANGING_LIGHT_SPAWN_X_VARIATION * 0.5),
            int(config.L2_HANGING_LIGHT_SPAWN_X_VARIATION * 0.5)
        ) + config.L2_HANGING_LIGHT_SPACING * 0.3
    else:
        next_ceiling_decoration_spawn_target_x = 0
        next_hanging_light_spawn_target_x = 0

    if start_playing and not gs.is_level_2_simple_mode:
        for layer_config in config.SNOW_LAYERS:
            layer_flakes = []
            for _ in range(layer_config["count"]): layer_flakes.append(
                [random.randint(0, config.WIDTH), random.randint(-config.HEIGHT, 0),
                 random.uniform(layer_config["base_speed_x_min"], layer_config["base_speed_x_max"]),
                 random.uniform(layer_config["speed_y_min"], layer_config["speed_y_max"]),
                 random.randint(layer_config["size_min"], layer_config["size_max"]),
                 random.randint(layer_config["alpha_min"], layer_config["alpha_max"]),
                 layer_config["parallax_x_factor"]])
            snowflakes_by_layer.append(layer_flakes)
        is_gusting = False
        gust_end_time = 0
        next_gust_time = current_ticks_for_reset + random.randint(config.WIND_GUST_INTERVAL_MIN,
                                                                  config.WIND_GUST_INTERVAL_MAX)
        current_gust_x_strength = 0
        current_gust_y_factor = 0
        next_meteor_spawn_time = current_ticks_for_reset + random.randint(config.METEOR_SPAWN_INTERVAL_MIN,
                                                                          config.METEOR_SPAWN_INTERVAL_MAX)
    else:
        is_gusting = False
        gust_end_time = 0
        next_gust_time = 0
        next_meteor_spawn_time = 0

    for fog_layer in fog_layers: fog_layer["x_pos"] = 0.0
    gs.colony_saved_message_active = False
    gs.ariel_display_active = False
    gs.ariel_anim_state = 'hidden'
    gs.screen_shake_magnitude = 0
    gs.screen_shake_duration = 0.0
    gs.screen_shake_timer = 0.0

    gs.portal_reached = False
    gs.portal_reached_time = 0
    gs.win_cutscene_start_time = 0
    if planet_image:
        planet_x = config.WIDTH + random.randint(50, 200)
    if planet2_image:
        planet2_x = config.WIDTH + random.randint(250, 450)

    gs.level2_win_sequence_active = False
    gs.level2_win_sequence_timer_end = 0
    gs.level2_stairs_visible = False
    gs.level2_stairs_rect_world = None
    gs.level2_player_reached_stairs = False
    gs.level2_player_hidden_after_stairs = False

    gs.credits_scroll_y = 0.0
    gs.ariel_next_message_on_screen_duration_ms = 0


def wrap_text(text, font_obj, max_width):
    words = text.split(' ')
    lines = []
    current_line = ""
    if not words or words == ['']: return [""]

    for word in words:
        potential_line = current_line + (" " if current_line else "") + word
        if font_obj.size(potential_line)[0] <= max_width:
            current_line = potential_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
            if font_obj.size(current_line)[0] > max_width:
                temp_word = ""
                for char_idx in range(len(current_line)):
                    if font_obj.size(temp_word + current_line[char_idx] + "..")[0] <= max_width:
                        temp_word += current_line[char_idx]
                    else:
                        break
                lines.append(temp_word + ".." if temp_word else current_line[:1] + "..")
                current_line = ""

    if current_line:
        lines.append(current_line)

    return lines if lines else [""]


print("--- Initializing game objects and setting initial state to MENU ---")
reset_game_state_vars(start_playing=False)
set_current_game_state(gs.MENU)
print(f"--- Initial game state: {gs.get_state()} ---")

running = True
print("--- Entering Main Game Loop ---")
last_video_frame_time_level1 = 0
last_video_frame_time_level2 = 0

world_render_surface = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)

while running:
    current_time_ticks = pygame.time.get_ticks()
    dt_raw_ms = clock.tick(config.FPS)
    time_delta_seconds = dt_raw_ms / 1000.0
    keys_pressed = pygame.key.get_pressed()
    if time_delta_seconds <= 0: time_delta_seconds = 1 / config.FPS

    current_gs_logic = gs.get_state()

    current_screen_offset_x, current_screen_offset_y = 0, 0
    if gs.screen_shake_magnitude > 0 and gs.screen_shake_duration > 0:
        gs.screen_shake_timer += time_delta_seconds
        if gs.screen_shake_timer < gs.screen_shake_duration:
            current_screen_offset_x = random.randint(-gs.screen_shake_magnitude, gs.screen_shake_magnitude)
            current_screen_offset_y = random.randint(-gs.screen_shake_magnitude, gs.screen_shake_magnitude)
        else:
            gs.screen_shake_magnitude = 0
            gs.screen_shake_duration = 0.0
            gs.screen_shake_timer = 0.0

    if current_gs_logic == gs.PLAYING and avalanche_obj and avalanche_obj.continuous_shake_magnitude > 0:
        magnitude = int(avalanche_obj.continuous_shake_magnitude)
        current_screen_offset_x += random.randint(-magnitude, magnitude)
        current_screen_offset_y += random.randint(-magnitude, magnitude)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        current_gs_event = gs.get_state()

        if current_gs_event == gs.MENU:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP: gs.menu_idx = (gs.menu_idx - 1 + len(gs.menu_options)) % len(
                    gs.menu_options)
                if event.key == pygame.K_DOWN: gs.menu_idx = (gs.menu_idx + 1) % len(gs.menu_options)
                if event.key == pygame.K_RETURN:
                    selected_option = gs.menu_options[gs.menu_idx]
                    if selected_option == 'Start Level 1':
                        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                            pygame.mixer.music.stop()

                        prologue_video_file_path = os.path.join(base_dir, "assets", "Prologue.mp4")
                        if os.path.exists(prologue_video_file_path):
                            actual_prologue_fps = 30.0
                            prologue_video_player = VideoPlayer(prologue_video_file_path,
                                                                (config.WIDTH, config.HEIGHT),
                                                                forced_fps=actual_prologue_fps)
                            if prologue_video_player and prologue_video_player.is_valid():
                                if prologue_audio_sound:
                                    try:
                                        prologue_audio_channel = prologue_audio_sound.play()
                                    except pygame.error as e:
                                        print(f"Could not play prologue audio: {e}")
                                        prologue_audio_channel = None
                                set_current_game_state(gs.PROLOGUE)
                            else:
                                if prologue_video_player: prologue_video_player.release()
                                prologue_video_player = None
                                print(f"Error loading Prologue.mp4. Skipping to tutorial.")
                                setup_tutorial_state()
                        else:
                            print(f"Prologue.mp4 not found. Skipping to tutorial.")
                            setup_tutorial_state()

                    elif selected_option == 'Start Level 2':
                        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                            pygame.mixer.music.stop()
                        reset_game_state_vars(start_playing=True, is_simple_level_setup=True)
                        print("Starting Level 2 (Simple Mode) directly.")
                    elif selected_option == 'Controls':
                        gs.previous_game_state_before_options = gs.MENU
                        set_current_game_state(gs.CONTROLS)
                    elif selected_option == 'Settings':
                        gs.previous_game_state_before_options = gs.MENU
                        set_current_game_state(gs.SETTINGS)
                    elif selected_option == 'Quit':
                        running = False
        elif current_gs_event == gs.PROLOGUE:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    if hasattr(gs, 'prologue_start_time_ticks'): del gs.prologue_start_time_ticks
                    if prologue_video_player:
                        prologue_video_player.release()
                        prologue_video_player = None
                    if prologue_audio_channel and prologue_audio_channel.get_busy():
                        prologue_audio_channel.stop()
                    prologue_audio_channel = None
                    setup_tutorial_state()

        elif current_gs_event == gs.MID_CUTSCENE:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    if middle_cutscene_video_player:
                        middle_cutscene_video_player.release()
                        middle_cutscene_video_player = None
                    if middle_cutscene_audio_channel and middle_cutscene_audio_channel.get_busy():
                        middle_cutscene_audio_channel.stop()
                    middle_cutscene_audio_channel = None
                    reset_game_state_vars(start_playing=True, is_simple_level_setup=True)
        elif current_gs_event == gs.WIN_CUTSCENE:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    if final_cutscene_video_player:
                        final_cutscene_video_player.release()
                        final_cutscene_video_player = None
                    if final_cutscene_audio_channel and final_cutscene_audio_channel.get_busy():
                        final_cutscene_audio_channel.stop()
                    final_cutscene_audio_channel = None

                    set_current_game_state(gs.CREDITS)
                    gs.credits_scroll_y = 0.0
                    if pygame.mixer.get_init() and soundtrack_loaded:
                        if not pygame.mixer.music.get_busy():
                            pygame.mixer.music.play(-1)
                        elif pygame.mixer.music.get_volume() < gs.music_volume:
                            pygame.mixer.music.set_volume(gs.music_volume)
        elif current_gs_event == gs.CREDITS:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    reset_game_state_vars(start_playing=False)
                    set_current_game_state(gs.MENU)
                    if pygame.mixer.get_init() and soundtrack_loaded and not pygame.mixer.music.get_busy():
                        pygame.mixer.music.play(-1)
        elif current_gs_event == gs.TUTORIAL:
            if player_obj and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if player_obj.perform_jump():
                        if jump_sound: jump_sound.play()
                    gs.tutorial_jump_done = True
                if event.key == pygame.K_f:
                    if player_obj.bullets_remaining > 0 and current_time_ticks - gs.last_shot_time > 200 and not player_obj.is_dying_animating:
                        to = next(iter(obstacles_group), None)
                        if player_obj.rect:
                            lasers_group.add(Laser(player_obj.rect.centerx, player_obj.rect.centery, to))
                            player_obj.bullets_remaining -= 1
                            gs.last_shot_time = current_time_ticks
                            player_obj.start_shooting_animation()
                        if laser_sound: laser_sound.play()
        elif current_gs_event == gs.PLAYING:
            if player_obj and player_obj.is_active and not gs.portal_reached and \
                    not gs.waiting_for_death_anim_to_finish and not gs.boulder_death_sequence_active and \
                    not gs.level2_win_sequence_active and not gs.level2_stairs_visible:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        paused_game_surface_local = screen.copy()
                        set_current_game_state(gs.PAUSED)
                        for obs in obstacles_group:
                            if isinstance(obs, BrokenSatellite):
                                obs.pause_falling_sound()
                     
                        if gs.is_level_2_simple_mode and boulder_sound_effect_channel and boulder_sound_effect_channel.get_busy():
                            print("Boulder sound: Pausing due to game pause.")
                            boulder_sound_effect_channel.pause()

                    if event.key == pygame.K_SPACE:
                        if player_obj.perform_jump():
                            if jump_sound: jump_sound.play()
                    if event.key == pygame.K_f:
                        if player_obj.bullets_remaining > 0 and current_time_ticks - gs.last_shot_time > 200 and not player_obj.is_dying_animating:
                            to = None
                            mds = float('inf')
                            if player_obj.rect:
                                if not gs.is_level_2_simple_mode or \
                                        (gs.is_level_2_simple_mode and any(
                                            isinstance(o, BugObstacle) for o in obstacles_group)):
                                    eo = [o for o in obstacles_group if
                                          o.rect.centerx > player_obj.rect.centerx + 5 and abs(
                                              o.rect.centery - player_obj.rect.centery) < config.HEIGHT / 2]
                                    for ospr in eo:
                                        ds = (ospr.rect.centerx - player_obj.rect.centerx) ** 2 + (
                                                ospr.rect.centery - player_obj.rect.centery) ** 2
                                        if ds < mds: mds = ds; to = ospr
                                lasers_group.add(Laser(player_obj.rect.centerx, player_obj.rect.centery, to))
                                player_obj.bullets_remaining -= 1
                                gs.last_shot_time = current_time_ticks
                                player_obj.start_shooting_animation()
                            if laser_sound: laser_sound.play()
        elif current_gs_event == gs.PAUSED:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    set_current_game_state(gs.PLAYING)
                    for obs in obstacles_group:
                        if isinstance(obs, BrokenSatellite):
                            obs.resume_falling_sound()
                
                    if gs.is_level_2_simple_mode and boulder_sound_effect_channel and not boulder_sound_effect_channel.get_busy():
                
                        should_boulder_sound_be_playing_on_resume = (
                                gs.boulder_is_visible and
                                not gs.level2_win_sequence_active and
                                not gs.boulder_death_sequence_active and
                                (player_obj and player_obj.is_active and gs.player_health > 0)
                        )
                        if should_boulder_sound_be_playing_on_resume:
                            print("Boulder sound: Resuming due to game unpause.")
                            boulder_sound_effect_channel.unpause()

                elif event.key == pygame.K_UP:
                    gs.pause_menu_idx = (gs.pause_menu_idx - 1 + len(gs.pause_menu_options)) % len(
                        gs.pause_menu_options)
                elif event.key == pygame.K_DOWN:
                    gs.pause_menu_idx = (gs.pause_menu_idx + 1) % len(gs.pause_menu_options)
                elif event.key == pygame.K_RETURN:
                    so = gs.pause_menu_options[gs.pause_menu_idx]
                    if so == 'Resume':
                        set_current_game_state(gs.PLAYING)
                        for obs in obstacles_group:
                            if isinstance(obs, BrokenSatellite):
                                obs.resume_falling_sound()
                     
                        if gs.is_level_2_simple_mode and boulder_sound_effect_channel and not boulder_sound_effect_channel.get_busy():
                            should_boulder_sound_be_playing_on_resume = (
                                    gs.boulder_is_visible and
                                    not gs.level2_win_sequence_active and
                                    not gs.boulder_death_sequence_active and
                                    (player_obj and player_obj.is_active and gs.player_health > 0)
                            )
                            if should_boulder_sound_be_playing_on_resume:
                                print("Boulder sound: Resuming due to game unpause (select).")
                                boulder_sound_effect_channel.unpause()
                    elif so == 'Restart Level':
                        reset_game_state_vars(start_playing=True, is_simple_level_setup=gs.is_level_2_simple_mode)
                    elif so == 'Controls':
                        gs.previous_game_state_before_options = gs.PAUSED
                        set_current_game_state(gs.CONTROLS)
                    elif so == 'Settings':
                        gs.previous_game_state_before_options = gs.PAUSED
                        set_current_game_state(gs.SETTINGS)
                    elif so == 'Quit to Main Menu':
                        reset_game_state_vars(start_playing=False)
                        set_current_game_state(gs.MENU)
                        if pygame.mixer.get_init() and soundtrack_loaded and not pygame.mixer.music.get_busy():
                            pygame.mixer.music.play(-1)
        elif current_gs_event == gs.FAILED:
            if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_q):
                if event.key == pygame.K_RETURN:
                    reset_game_state_vars(start_playing=True, is_simple_level_setup=gs.is_level_2_simple_mode)
                if event.key == pygame.K_q:
                    reset_game_state_vars(start_playing=False)
                    set_current_game_state(gs.MENU)
                    if pygame.mixer.get_init() and soundtrack_loaded and not pygame.mixer.music.get_busy():
                        pygame.mixer.music.play(-1)
        elif current_gs_event == gs.CONTROLS or current_gs_event == gs.SETTINGS:
            if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE):
                prev_state_local = gs.previous_game_state_before_options if gs.previous_game_state_before_options else gs.MENU
                set_current_game_state(prev_state_local)
                gs.previous_game_state_before_options = None
                if prev_state_local == gs.MENU and pygame.mixer.get_init() and soundtrack_loaded and not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play(-1)

        if current_gs_event == gs.SETTINGS:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    if pygame.mixer.get_init():
                        if event.key == pygame.K_LEFT: gs.music_volume = max(0, gs.music_volume - .1)
                        if event.key == pygame.K_RIGHT: gs.music_volume = min(1, gs.music_volume + .1)
                        update_sound_effect_volumes()

    world_scroll_this_frame = 0.0

    if gs.colony_saved_message_active and current_time_ticks >= gs.colony_saved_message_timer_end: gs.colony_saved_message_active = False

    if gs.ariel_display_active:
        if gs.ariel_anim_state == 'floating_in':
            gs.ariel_current_x -= config.ARIEL_ANIM_SPEED * time_delta_seconds
            if gs.ariel_current_x <= gs.ariel_target_x_on_screen:
                gs.ariel_current_x = gs.ariel_target_x_on_screen
                gs.ariel_anim_state = 'shown'
                duration_for_shown_state_ms = config.ARIEL_DISPLAY_DURATION_ON_SCREEN
                if hasattr(gs,
                           'ariel_next_message_on_screen_duration_ms') and gs.ariel_next_message_on_screen_duration_ms > 0:
                    duration_for_shown_state_ms = gs.ariel_next_message_on_screen_duration_ms
                    gs.ariel_next_message_on_screen_duration_ms = 0
                gs.ariel_display_on_screen_end_time = current_time_ticks + duration_for_shown_state_ms

        elif gs.ariel_anim_state == 'shown':
            if gs.ariel_display_on_screen_end_time == 0:
                duration_for_shown_state_ms = config.ARIEL_DISPLAY_DURATION_ON_SCREEN
                if hasattr(gs,
                           'ariel_next_message_on_screen_duration_ms') and gs.ariel_next_message_on_screen_duration_ms > 0:
                    duration_for_shown_state_ms = gs.ariel_next_message_on_screen_duration_ms
                    gs.ariel_next_message_on_screen_duration_ms = 0
                gs.ariel_display_on_screen_end_time = current_time_ticks + duration_for_shown_state_ms

            if current_time_ticks >= gs.ariel_display_on_screen_end_time:
                gs.ariel_anim_state = 'floating_out'

        elif gs.ariel_anim_state == 'floating_out':
            gs.ariel_current_x += config.ARIEL_ANIM_SPEED * time_delta_seconds
            if ariel_image_scaled and gs.ariel_current_x > config.WIDTH:
                gs.ariel_anim_state = 'hidden'
                gs.ariel_display_active = False

    if not gs.is_level_2_simple_mode:
        if gs.portal_message_pending and not gs.ariel_display_active and \
                (current_gs_logic == gs.PLAYING or current_gs_logic == gs.PAUSED):
            gs.ariel_display_active = True
            gs.ariel_anim_state = 'floating_in'
            gs.ariel_next_message_on_screen_duration_ms = config.ARIEL_DISPLAY_DURATION_ON_SCREEN
            if ariel_image_scaled:
                gs.ariel_current_x = config.WIDTH
            else:
                gs.ariel_current_x = gs.ariel_target_x_on_screen
                gs.ariel_anim_state = 'shown'
                gs.ariel_display_on_screen_end_time = current_time_ticks + gs.ariel_next_message_on_screen_duration_ms
                gs.ariel_next_message_on_screen_duration_ms = 0

            portal_message_text = "The avalanche is catching up, Hurry to the portal!"
            temp_text_box_width_portal = ariel_image_scaled.get_width() * 1.8 if ariel_image_scaled else config.WIDTH * 0.35
            max_text_render_width_portal = max(150, temp_text_box_width_portal - 20)
            gs.ariel_current_message_lines = wrap_text(portal_message_text, ariel_font, max_text_render_width_portal)
            gs.colony_saved_message_active = False
            gs.portal_message_pending = False
            if portal_sound_effect:
                portal_sound_effect.play()

        if gs.ariel_anim_state == 'hidden' and gs.portal_spawn_pending and not gs.portal_object_exists and current_gs_logic == gs.PLAYING:
            if terrain_obj and player_obj and player_obj.is_active:
                new_portal = Portal(config.WIDTH + 100, terrain_obj, portal_image_asset_placeholder)
                portal_group.add(new_portal)
                gs.portal_object_exists = True
                gs.portal_spawn_pending = False
                print("Portal Spawned!")

    if current_gs_logic == gs.MENU:
        if pygame.mixer.get_init() and soundtrack_loaded and not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1)

        if menu_bg_frames and len(menu_bg_frames) > 0:
            current_frame_data_or_surface = menu_bg_frames[menu_frame_idx % len(menu_bg_frames)]
            if len(menu_bg_frames) > 1 and current_time_ticks - menu_frame_timer > gif_frame_duration:
                menu_frame_idx = (menu_frame_idx + 1) % len(menu_bg_frames)
                menu_frame_timer = current_time_ticks
        elif menu_bg_frames:
            menu_frame_idx = 0


    elif current_gs_logic == gs.PROLOGUE:
        if not hasattr(gs, 'prologue_start_time_ticks'):
            gs.prologue_start_time_ticks = current_time_ticks
            if prologue_video_player:
                prologue_video_player.reset_playthrough_counter()

        proceed_to_tutorial = False
        time_into_prologue_ms = current_time_ticks - gs.prologue_start_time_ticks

        if prologue_video_player and prologue_video_player.is_valid():
            prologue_video_player.get_frame_at_time(time_into_prologue_ms)

        AUDIO_DURATION_MS = 44200
        VIDEO_NEAR_END_GRACE_MS = 500

        if time_into_prologue_ms >= AUDIO_DURATION_MS:
            proceed_to_tutorial = True
        elif prologue_audio_channel and prologue_audio_sound and \
                prologue_audio_channel.get_sound() == prologue_audio_sound and \
                not prologue_audio_channel.get_busy() and time_into_prologue_ms > 1000:
            video_conceptually_done = False
            if prologue_video_player and prologue_video_player.is_valid():
                video_natural_duration_ms = (
                        prologue_video_player.total_frames / prologue_video_player.fps * 1000) if prologue_video_player.fps > 0 else AUDIO_DURATION_MS
                if time_into_prologue_ms >= (video_natural_duration_ms - VIDEO_NEAR_END_GRACE_MS):
                    video_conceptually_done = True
            if video_conceptually_done:
                proceed_to_tutorial = True
        elif not (prologue_video_player and prologue_video_player.is_valid()):
            if not (prologue_audio_channel and prologue_audio_channel.get_busy()):
                proceed_to_tutorial = True

        if proceed_to_tutorial:
            if hasattr(gs, 'prologue_start_time_ticks'):
                del gs.prologue_start_time_ticks
            if prologue_video_player:
                prologue_video_player.release()
                prologue_video_player = None
            if prologue_audio_channel and prologue_audio_channel.get_busy():
                prologue_audio_channel.stop()
            prologue_audio_channel = None
            setup_tutorial_state()

    elif current_gs_logic == gs.MID_CUTSCENE:
        proceed_to_level2 = False
        if not middle_cutscene_video_player or not middle_cutscene_video_player.is_valid():
            print("Mid-cutscene: Video player not valid. Skipping to Level 2.")
            proceed_to_level2 = True
        else:
            time_into_cutscene_ms = current_time_ticks - gs.mid_cutscene_start_time
            middle_cutscene_video_player.get_frame_at_time(time_into_cutscene_ms)

            video_ended = middle_cutscene_video_player.is_one_playthrough_done()
            audio_ended = True
            if middle_cutscene_audio_channel:
                audio_ended = not middle_cutscene_audio_channel.get_busy()

            if video_ended:
                print("Mid-cutscene: Video ended.")
                proceed_to_level2 = True
            elif audio_ended and middle_cutscene_audio_sound and time_into_cutscene_ms > 1000:
                print("Mid-cutscene: Audio ended. Proceeding.")
                proceed_to_level2 = True

        if proceed_to_level2:
            if middle_cutscene_video_player:
                middle_cutscene_video_player.release()
                middle_cutscene_video_player = None
            if middle_cutscene_audio_channel and middle_cutscene_audio_channel.get_busy():
                middle_cutscene_audio_channel.stop()
            middle_cutscene_audio_channel = None
            reset_game_state_vars(start_playing=True, is_simple_level_setup=True)


    elif current_gs_logic == gs.WIN_CUTSCENE:
        proceed_to_credits = False
        if not final_cutscene_video_player or not final_cutscene_video_player.is_valid():
            print("Win Cutscene: Final video player not valid. Skipping to Credits.")
            proceed_to_credits = True
        else:
            time_into_cutscene_ms = current_time_ticks - gs.win_cutscene_start_time
            final_cutscene_video_player.get_frame_at_time(time_into_cutscene_ms)

            video_ended = final_cutscene_video_player.is_one_playthrough_done()
            audio_ended = True
            if final_cutscene_audio_channel:
                audio_ended = not final_cutscene_audio_channel.get_busy()

            if video_ended:
                print("Win Cutscene: Final video ended.")
                proceed_to_credits = True
            elif audio_ended and final_cutscene_audio_sound and time_into_cutscene_ms > 1000:
                print("Win Cutscene: Final audio ended. Proceeding.")
                proceed_to_credits = True

        if proceed_to_credits:
            if final_cutscene_video_player:
                final_cutscene_video_player.release()
                final_cutscene_video_player = None
            if final_cutscene_audio_channel and final_cutscene_audio_channel.get_busy():
                final_cutscene_audio_channel.stop()
            final_cutscene_audio_channel = None

            set_current_game_state(gs.CREDITS)
            gs.credits_scroll_y = 0.0
            if pygame.mixer.get_init() and soundtrack_loaded:
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play(-1)
                elif pygame.mixer.music.get_volume() < gs.music_volume:
                    pygame.mixer.music.set_volume(gs.music_volume)
    elif current_gs_logic == gs.CREDITS:
        gs.credits_scroll_y += gs.credits_scroll_speed * time_delta_seconds
        last_line_initial_y = (config.HEIGHT + gs.credits_line_height) + \
                              ((len(gs.credits_text) - 1) * gs.credits_line_height if gs.credits_text else 0)
        if (last_line_initial_y - gs.credits_scroll_y) < -gs.credits_line_height:
            gs.credits_scroll_y = 0.0

    elif current_gs_logic == gs.TUTORIAL:
        if player_obj: player_obj.update(terrain_obj, None, current_gs_logic, time_delta_seconds, 0.0)
        if player_obj and player_obj.rect:
            cam_y_offset = (player_obj.y_world - player_obj.rect.height / 2.0) - config.PLAYER_TARGET_SCREEN_Y
        else:
            cam_y_offset = 0
        if terrain_obj:
            lasers_group.update(cam_y_offset)
        else:
            lasers_group.update(cam_y_offset)

        for obs in obstacles_group:
            obs.update(0.0, current_gs_logic, time_delta_seconds, player_obj, debris_effects_group)
            if isinstance(obs, IceFormation) and obs.is_erupting and obs.spawn_debris_on_eruption:
                debris_effects_group.add(DebrisEffect(obs.rect.centerx, obs.rect.bottom, "snow_puff", intensity=0.8))
                obs.spawn_debris_on_eruption = False
        hit_obstacle_dict_tutorial = pygame.sprite.groupcollide(lasers_group, obstacles_group, True, True)
        if hit_obstacle_dict_tutorial:
            for obs_hit_list in hit_obstacle_dict_tutorial.values():
                for obs_hit in obs_hit_list:
                    mat, cx, cy, obs_type = obs_hit.on_destroy()
                    debris_effects_group.add(DebrisEffect(cx, cy, mat))
                    if obs_type == "satellite_debris":
                        if explosion_sound: explosion_sound.play()
                        explosions_group.add(Explosion(cx, cy))
                    elif obs_type == "ice_formation":
                        if spike_breaking_sound: spike_breaking_sound.play()
                    elif obs_hit.destructible:
                        if explosion_sound: explosion_sound.play()
            if tutorial_obstacle_was_present and len(obstacles_group) == 0 and not gs.tutorial_shoot_done:
                gs.tutorial_shoot_done = True
        if not tutorial_obstacle_was_present and not gs.tutorial_shoot_done: gs.tutorial_shoot_done = True

        if player_obj and avalanche_obj and player_obj.is_active and player_obj.rect:
            avalanche_obj.update(player_obj.rect.centerx, False, current_gs_logic, set_current_game_state)
            if avalanche_obj.request_rumble_effect_flag:
                gs.screen_shake_magnitude = config.AVALANCHE_SHAKE_MAGNITUDE
                gs.screen_shake_duration = config.AVALANCHE_SHAKE_DURATION
                avalanche_obj.request_rumble_effect_flag = False

        if gs.tutorial_jump_done and gs.tutorial_shoot_done:
            if not hasattr(gs, 'tutorial_complete_timer'): gs.tutorial_complete_timer = current_time_ticks + 1500
            if hasattr(gs, 'tutorial_complete_timer') and current_time_ticks >= gs.tutorial_complete_timer:
                reset_game_state_vars(start_playing=True, is_simple_level_setup=False)
                if hasattr(gs, 'tutorial_complete_timer'): del gs.tutorial_complete_timer
        explosions_group.update(time_delta_seconds, 0.0)
        debris_effects_group.update(time_delta_seconds, 0.0)

    elif current_gs_logic == gs.PLAYING:
        if gs.is_level_2_simple_mode and \
                player_obj and player_obj.is_active and \
                not gs.waiting_for_death_anim_to_finish and \
                not gs.boulder_death_sequence_active and \
                not gs.level2_win_sequence_active and not gs.level2_stairs_visible and \
                not gs.ariel_display_active:

            if not gs.level2_halfway_message_triggered and \
                    current_time_ticks >= gs.level2_halfway_trigger_time:
                gs.ariel_display_active = True
                gs.ariel_anim_state = 'floating_in'
                if ariel_image_scaled:
                    gs.ariel_current_x = config.WIDTH
                else:
                    gs.ariel_current_x = gs.ariel_target_x_on_screen
                    gs.ariel_anim_state = 'shown'

                if level2_halfway_sound_effect: level2_halfway_sound_effect.play()
                specific_duration = config.ARIEL_DISPLAY_DURATION_ON_SCREEN
                if level2_halfway_sound_effect:
                    try:
                        specific_duration = max(specific_duration,
                                                int(level2_halfway_sound_effect.get_length() * 1000) + 200)
                    except:
                        pass
                gs.ariel_next_message_on_screen_duration_ms = specific_duration
                ariel_text_box_width = ariel_image_scaled.get_width() * 1.8 if ariel_image_scaled else config.WIDTH * 0.35
                max_text_render_width = max(150, ariel_text_box_width - 20)
                gs.ariel_current_message_lines = wrap_text("Halfway to the tower", ariel_font, max_text_render_width)
                gs.level2_halfway_message_triggered = True
                gs.colony_saved_message_active = False
                gs.portal_message_pending = False
                print("Ariel L2 Halfway Message Triggered.")

            elif not gs.level2_end_message_triggered and \
                    current_time_ticks >= gs.level2_end_message_trigger_time and \
                    gs.level2_bug_warning_triggered_this_level:
                gs.ariel_display_active = True
                gs.ariel_anim_state = 'floating_in'
                if ariel_image_scaled:
                    gs.ariel_current_x = config.WIDTH
                else:
                    gs.ariel_current_x = gs.ariel_target_x_on_screen
                    gs.ariel_anim_state = 'shown'

                if level2_end_sound_effect: level2_end_sound_effect.play()
                specific_duration = config.ARIEL_DISPLAY_DURATION_ON_SCREEN
                if level2_end_sound_effect:
                    try:
                        specific_duration = max(specific_duration,
                                                int(level2_end_sound_effect.get_length() * 1000) + 200)
                    except:
                        pass
                gs.ariel_next_message_on_screen_duration_ms = specific_duration
                ariel_text_box_width = ariel_image_scaled.get_width() * 1.8 if ariel_image_scaled else config.WIDTH * 0.35
                max_text_render_width = max(150, ariel_text_box_width - 20)
                gs.ariel_current_message_lines = wrap_text("The stairs to the tower are just ahead!", ariel_font,
                                                           max_text_render_width)
                gs.level2_end_message_triggered = True
                gs.colony_saved_message_active = False
                gs.portal_message_pending = False
                print("Ariel L2 End Message Triggered.")

            elif not gs.level2_bug_warning_triggered_this_level and \
                    current_time_ticks >= gs.level2_bug_warning_trigger_time:
                gs.ariel_display_active = True
                gs.ariel_anim_state = 'floating_in'
                if ariel_image_scaled:
                    gs.ariel_current_x = config.WIDTH
                else:
                    gs.ariel_current_x = gs.ariel_target_x_on_screen
                    gs.ariel_anim_state = 'shown'

                if bug_warning_sound_effect: bug_warning_sound_effect.play()
                specific_duration = config.ARIEL_DISPLAY_DURATION_ON_SCREEN
                if bug_warning_sound_effect:
                    try:
                        specific_duration = max(specific_duration,
                                                int(bug_warning_sound_effect.get_length() * 1000) + 200)
                    except:
                        pass
                gs.ariel_next_message_on_screen_duration_ms = specific_duration
                bug_warning_text = "Be careful! The tunnel is filled with radioactive bugs!!"
                ariel_text_box_width = ariel_image_scaled.get_width() * 1.8 if ariel_image_scaled else config.WIDTH * 0.35
                max_text_render_width = max(150, ariel_text_box_width - 20)
                gs.ariel_current_message_lines = wrap_text(bug_warning_text, ariel_font, max_text_render_width)
                gs.level2_bug_warning_triggered_this_level = True
                gs.colony_saved_message_active = False
                gs.portal_message_pending = False
                print("Ariel L2 Bug Warning Triggered.")

        if gs.is_level_2_simple_mode and boulder_obj and player_obj and player_obj.rect and \
                not gs.level2_stairs_visible and not gs.level2_player_reached_stairs and \
                not gs.level2_win_sequence_active and not gs.boulder_death_sequence_active and \
                player_obj.is_active:

            distance_boulder_to_player_x = config.PLAYER_SCREEN_X - boulder_obj.rect.right
            if boulder_obj.rect.right < config.PLAYER_SCREEN_X and \
                    distance_boulder_to_player_x <= config.BOULDER_WIN_PROXIMITY_THRESHOLD and \
                    distance_boulder_to_player_x > 0 and \
                    gs.boulder_is_visible:

                print("L2 Stairs Sequence Triggered by Boulder Proximity!")
                gs.level2_stairs_visible = True
                if stairs_image_asset and terrain_obj and player_obj:
                    player_true_world_x = player_obj.x + (gs.world_distance_scrolled * config.CHUNK)
                    stairs_spawn_world_x = player_true_world_x + config.WIDTH * 1
                    stairs_width = stairs_image_asset.get_width()

                    stairs_base_center_x_world = stairs_spawn_world_x + stairs_width / 2
                    stairs_terrain_y = terrain_obj.height_at(stairs_base_center_x_world)

                    gs.level2_stairs_rect_world = stairs_image_asset.get_rect(
                        bottomleft=(int(stairs_spawn_world_x), int(stairs_terrain_y + config.L2_STAIRS_MANUAL_Y_OFFSET))
                    )
                    print(
                        f"Stairs spawned at world_x (left): {gs.level2_stairs_rect_world.x}, world_y_bottom: {gs.level2_stairs_rect_world.bottom}")
                else:
                    gs.level2_stairs_visible = False
                    print("Stairs image, terrain, or player missing. Falling back to original win sequence trigger.")
                    gs.level2_win_sequence_active = True
                    gs.level2_win_sequence_timer_end = current_time_ticks + config.L2_WIN_WHITE_FLASH_DURATION_MS
                    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                        pygame.mixer.music.fadeout(config.L2_WIN_WHITE_FLASH_DURATION_MS // 2)

        if gs.level2_stairs_visible and not gs.level2_player_reached_stairs and \
                player_obj and player_obj.is_active and gs.level2_stairs_rect_world and terrain_obj:

            total_world_scroll_pixels = gs.world_distance_scrolled * config.CHUNK

            stairs_screen_left = gs.level2_stairs_rect_world.left - total_world_scroll_pixels
            current_stairs_terrain_y_world = terrain_obj.height_at(gs.level2_stairs_rect_world.centerx)
            stairs_screen_top = (current_stairs_terrain_y_world - gs.level2_stairs_rect_world.height) - cam_y_offset

            collision_stairs_rect_screen = pygame.Rect(
                stairs_screen_left,
                stairs_screen_top,
                gs.level2_stairs_rect_world.width,
                gs.level2_stairs_rect_world.height
            )

            player_effective_enter_x = player_obj.rect.centerx
            stairs_entrance_threshold_screen_x = stairs_screen_left + gs.level2_stairs_rect_world.width * 0.15
            player_collision_rect_screen = player_obj.rect.copy()
            player_collision_rect_screen.y = player_obj.rect.y - cam_y_offset

            if player_effective_enter_x >= stairs_entrance_threshold_screen_x and \
                    player_obj.rect.right > stairs_screen_left and \
                    player_collision_rect_screen.colliderect(collision_stairs_rect_screen):
                print("Player reached stairs entrance! COLLISION SUCCESSFUL.")
                gs.level2_player_reached_stairs = True
                gs.level2_player_hidden_after_stairs = True
                if player_obj: player_obj.is_hidden = True

                gs.level2_win_sequence_active = True
                gs.level2_win_sequence_timer_end = current_time_ticks + config.L2_WIN_WHITE_FLASH_DURATION_MS
                if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                    pygame.mixer.music.fadeout(config.L2_WIN_WHITE_FLASH_DURATION_MS)
        if gs.boulder_death_sequence_active:
            world_scroll_this_frame = 0.0
            if player_obj and terrain_obj:
                player_obj.update(terrain_obj, current_ramp_obj, current_gs_logic, time_delta_seconds,
                                  world_scroll_this_frame)
            if boulder_obj:
                boulder_obj.update(False, config.PLAYER_SCREEN_X)
            if player_obj and player_obj.rect:
                cam_y_offset = (player_obj.y_world - player_obj.rect.height / 2.0) - config.PLAYER_TARGET_SCREEN_Y
            else:
                cam_y_offset = 0
            if gs.is_level_2_simple_mode:
                if level2_video_player and level2_video_player.is_valid():
                    if level2_video_player.fps > 0 and \
                            (current_time_ticks - last_video_frame_time_level2) >= (1000 / level2_video_player.fps):
                        time_into_video_ms = current_time_ticks - gs.level2_video_playthrough_start_time
                        level2_video_player.get_frame_at_time(time_into_video_ms)
                        last_video_frame_time_level2 = current_time_ticks
                        if level2_video_player.is_one_playthrough_done():
                            level2_video_player.reset_playthrough_counter()
                            video_duration_ms = (level2_video_player.total_frames / level2_video_player.fps) * 1000.0
                            overshoot_ms = time_into_video_ms - video_duration_ms
                            if overshoot_ms < 0: overshoot_ms = 0
                            gs.level2_video_playthrough_start_time = current_time_ticks - overshoot_ms
                            level2_video_player.get_frame_at_time(overshoot_ms)
            explosions_group.update(time_delta_seconds, world_scroll_this_frame)
            debris_effects_group.update(time_delta_seconds, world_scroll_this_frame)
            if current_time_ticks >= gs.boulder_death_sequence_end_time:
                set_current_game_state(gs.FAILED)
                gs.boulder_death_sequence_active = False
                gs.waiting_for_death_anim_to_finish = False

        elif gs.portal_reached:
            if current_time_ticks - gs.portal_reached_time >= gs.PORTAL_OUTCOME_DELAY:
                if gs.collected_checkpoints >= len(config.CHECKPOINT_DISTANCES) and len(
                        config.CHECKPOINT_DISTANCES) > 0:
                    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                        pygame.mixer.music.fadeout(500)
                    middle_video_path = os.path.join(base_dir, "assets", "MiddleCutscene.mp4")
                    if os.path.exists(middle_video_path):
                        middle_cutscene_video_player = VideoPlayer(middle_video_path, (config.WIDTH, config.HEIGHT))
                        if middle_cutscene_video_player and middle_cutscene_video_player.is_valid():
                            if middle_cutscene_audio_sound:
                                try:
                                    middle_cutscene_audio_channel = middle_cutscene_audio_sound.play()
                                except pygame.error as e:
                                    print(f"Could not play middle cutscene audio: {e}")
                                    middle_cutscene_audio_channel = None
                            gs.mid_cutscene_start_time = current_time_ticks
                            set_current_game_state(gs.MID_CUTSCENE)
                        else:
                            if middle_cutscene_video_player: middle_cutscene_video_player.release()
                            middle_cutscene_video_player = None
                            print("Error loading MiddleCutscene.mp4. Skipping to Level 2.")
                            reset_game_state_vars(start_playing=True, is_simple_level_setup=True)
                    else:
                        print("MiddleCutscene.mp4 not found. Skipping to Level 2.")
                        reset_game_state_vars(start_playing=True, is_simple_level_setup=True)
                else:
                    set_current_game_state(gs.FAILED)
                gs.portal_reached = False
            else:
                world_scroll_this_frame = 0.0
                if player_obj and player_obj.rect:
                    cam_y_offset = (player_obj.y_world - player_obj.rect.height / 2.0) - config.PLAYER_TARGET_SCREEN_Y
                else:
                    cam_y_offset = 0
                if gs.is_level_2_simple_mode:
                    if level2_video_player and level2_video_player.is_valid():
                        time_into_video_ms = current_time_ticks - gs.level2_video_playthrough_start_time
                        level2_video_player.get_frame_at_time(time_into_video_ms)
                else:
                    if level1_video_player and level1_video_player.is_valid():
                        time_into_video_ms = current_time_ticks - gs.level1_video_playthrough_start_time
                        level1_video_player.get_frame_at_time(time_into_video_ms)
                    if planet_image: planet_x -= planet_speed * 0.1
                    if planet2_image: planet2_x -= planet2_speed * 0.1
                explosions_group.update(time_delta_seconds, world_scroll_this_frame)
                debris_effects_group.update(time_delta_seconds, world_scroll_this_frame)
        elif gs.level2_win_sequence_active and gs.level2_player_reached_stairs:
            world_scroll_this_frame = 0.0
            if player_obj and terrain_obj:
                player_obj.update(terrain_obj, current_ramp_obj, current_gs_logic, time_delta_seconds,
                                  world_scroll_this_frame)
            if boulder_obj:
                boulder_obj.update(False, config.PLAYER_SCREEN_X)

            if player_obj and player_obj.rect:
                cam_y_offset = (player_obj.y_world - player_obj.rect.height / 2.0) - config.PLAYER_TARGET_SCREEN_Y
            else:
                cam_y_offset = 0

            if gs.is_level_2_simple_mode:
                if level2_video_player and level2_video_player.is_valid():
                    if level2_video_player.fps > 0 and \
                            (current_time_ticks - last_video_frame_time_level2) >= (1000 / level2_video_player.fps):
                        time_into_video_ms = current_time_ticks - gs.level2_video_playthrough_start_time
                        level2_video_player.get_frame_at_time(time_into_video_ms)
                        last_video_frame_time_level2 = current_time_ticks
                        if level2_video_player.is_one_playthrough_done():
                            level2_video_player.reset_playthrough_counter()
                            video_duration_ms = (level2_video_player.total_frames / level2_video_player.fps) * 1000.0
                            overshoot_ms = time_into_video_ms - video_duration_ms
                            if overshoot_ms < 0: overshoot_ms = 0
                            gs.level2_video_playthrough_start_time = current_time_ticks - overshoot_ms
                            level2_video_player.get_frame_at_time(overshoot_ms)

            explosions_group.update(time_delta_seconds, world_scroll_this_frame)
            debris_effects_group.update(time_delta_seconds, world_scroll_this_frame)

            if current_time_ticks >= gs.level2_win_sequence_timer_end:
                print("L2 White Flash Win Sequence Complete. Transitioning to Final Video Win Cutscene.")

             
                if gs.is_level_2_simple_mode and boulder_sound_effect_channel and boulder_sound_effect_channel.get_busy():
                    print("Boulder sound: Stopping explicitly on transition to WIN_CUTSCENE for L2.")
                    boulder_sound_effect_channel.stop()
             

                final_video_path = os.path.join(base_dir, "assets", "FinalScene.mp4")
                if os.path.exists(final_video_path):
                    final_cutscene_video_player = VideoPlayer(final_video_path, (config.WIDTH, config.HEIGHT))
                    if final_cutscene_video_player and final_cutscene_video_player.is_valid():
                        if final_cutscene_audio_sound:
                            try:
                                final_cutscene_audio_channel = final_cutscene_audio_sound.play()
                            except pygame.error as e:
                                print(f"Could not play final cutscene audio: {e}")
                                final_cutscene_audio_channel = None
                        gs.win_cutscene_start_time = current_time_ticks
                        set_current_game_state(gs.WIN_CUTSCENE)
                    else:
                        if final_cutscene_video_player: final_cutscene_video_player.release()
                        final_cutscene_video_player = None
                        print("Error loading FinalScene.mp4. Skipping to Credits.")
                   
                        if gs.is_level_2_simple_mode and boulder_sound_effect_channel and boulder_sound_effect_channel.get_busy():
                            print("Boulder sound: Stopping explicitly on skipping FinalScene.mp4 to Credits for L2.")
                            boulder_sound_effect_channel.stop()
                        set_current_game_state(gs.CREDITS)
                        gs.credits_scroll_y = 0.0
                        if pygame.mixer.get_init() and soundtrack_loaded and not pygame.mixer.music.get_busy():
                            pygame.mixer.music.play(-1)
                else:
                    print("FinalScene.mp4 not found. Skipping to Credits.")
               
                    if gs.is_level_2_simple_mode and boulder_sound_effect_channel and boulder_sound_effect_channel.get_busy():
                        print("Boulder sound: Stopping explicitly on FinalScene.mp4 not found (to Credits) for L2.")
                        boulder_sound_effect_channel.stop()
                    set_current_game_state(gs.CREDITS)
                    gs.credits_scroll_y = 0.0
                    if pygame.mixer.get_init() and soundtrack_loaded and not pygame.mixer.music.get_busy():
                        pygame.mixer.music.play(-1)

                gs.level2_win_sequence_active = False
                gs.level2_stairs_visible = False
                gs.level2_player_reached_stairs = False
        else:
            scroll_for_player_and_world = 0.0
            if not gs.waiting_for_death_anim_to_finish and not gs.level2_stairs_visible:
                effective_player_speed = config.PLAYER_DOWNHILL_SPEED
                if gs.is_slowed_down:
                    if current_time_ticks < gs.slowdown_end_time:
                        effective_player_speed *= config.SLOWDOWN_FACTOR
                    else:
                        gs.is_slowed_down = False
                scroll_for_player_and_world = effective_player_speed
            elif gs.level2_stairs_visible and not gs.level2_player_reached_stairs:
                scroll_for_player_and_world = config.PLAYER_DOWNHILL_SPEED

            world_scroll_this_frame = scroll_for_player_and_world

            if player_obj and terrain_obj:
                player_obj.update(terrain_obj, current_ramp_obj, current_gs_logic, time_delta_seconds,
                                  scroll_for_player_and_world)

            if player_obj and player_obj.rect:
                cam_y_offset = (player_obj.y_world - player_obj.rect.height / 2.0) - config.PLAYER_TARGET_SCREEN_Y
            else:
                cam_y_offset = 0

            if gs.waiting_for_death_anim_to_finish and player_obj and not player_obj.is_dying_animating:
                gs.waiting_for_death_anim_to_finish = False
                if gs.player_health <= 0 and not gs.boulder_death_sequence_active:
                    set_current_game_state(gs.FAILED)

            if gs.is_level_2_simple_mode:
                if level2_video_player and level2_video_player.is_valid():
                    if level2_video_player.fps > 0 and \
                            (current_time_ticks - last_video_frame_time_level2) >= (1000 / level2_video_player.fps):
                        time_into_video_ms = current_time_ticks - gs.level2_video_playthrough_start_time
                        level2_video_player.get_frame_at_time(time_into_video_ms)
                        last_video_frame_time_level2 = current_time_ticks
                        if level2_video_player.is_one_playthrough_done():
                            level2_video_player.reset_playthrough_counter()
                            video_duration_ms = (level2_video_player.total_frames / level2_video_player.fps) * 1000.0
                            overshoot_ms = time_into_video_ms - video_duration_ms
                            if overshoot_ms < 0: overshoot_ms = 0
                            gs.level2_video_playthrough_start_time = current_time_ticks - overshoot_ms
                            level2_video_player.get_frame_at_time(overshoot_ms)
            else:
                if level1_video_player and level1_video_player.is_valid():
                    if level1_video_player.fps > 0 and \
                            (current_time_ticks - last_video_frame_time_level1) >= (1000 / level1_video_player.fps):
                        time_into_video_ms = current_time_ticks - gs.level1_video_playthrough_start_time
                        level1_video_player.get_frame_at_time(time_into_video_ms)
                        last_video_frame_time_level1 = current_time_ticks
                        if level1_video_player.is_one_playthrough_done():
                            level1_video_player.reset_playthrough_counter()
                            video_duration_ms = (level1_video_player.total_frames / level1_video_player.fps) * 1000.0
                            overshoot_ms = time_into_video_ms - video_duration_ms
                            if overshoot_ms < 0: overshoot_ms = 0
                            gs.level1_video_playthrough_start_time = current_time_ticks - overshoot_ms
                            level1_video_player.get_frame_at_time(overshoot_ms)
                if planet_image:
                    planet_x -= planet_speed
                    if planet_image.get_width() > 0 and planet_x + planet_image.get_width() < 0: planet_x = config.WIDTH + random.randint(
                        50, 200)
                if planet2_image:
                    planet2_x -= planet_speed
                    if planet2_image.get_width() > 0 and planet2_x + planet2_image.get_width() < 0: planet2_x = config.WIDTH + random.randint(
                        250, 450)

            if not gs.is_level_2_simple_mode:
                if is_gusting:
                    if current_time_ticks >= gust_end_time: is_gusting = False
                elif current_time_ticks >= next_gust_time and not gs.waiting_for_death_anim_to_finish:
                    is_gusting = True
                    gust_duration = random.randint(config.WIND_GUST_DURATION_MIN, config.WIND_GUST_DURATION_MAX)
                    gust_end_time = current_time_ticks + gust_duration
                    next_gust_time = gust_end_time + random.randint(config.WIND_GUST_INTERVAL_MIN,
                                                                    config.WIND_GUST_INTERVAL_MAX)
                    current_gust_x_strength = random.uniform(config.WIND_GUST_STRENGTH_X_MIN,
                                                             config.WIND_GUST_STRENGTH_X_MAX)
                    current_gust_y_factor = random.uniform(-config.WIND_GUST_STRENGTH_Y_FACTOR,
                                                           config.WIND_GUST_STRENGTH_Y_FACTOR)

                if config.ENABLE_METEOR_EFFECT:
                    if current_time_ticks >= next_meteor_spawn_time and len(meteors_list) < config.METEOR_MAX_COUNT:
                        angle_deg = random.uniform(config.METEOR_ANGLE_MIN_DEG, config.METEOR_ANGLE_MAX_DEG)
                        angle_rad = math.radians(angle_deg)
                        start_x = random.uniform(-.1 * config.WIDTH, 1.1 * config.WIDTH)
                        start_y = -random.uniform(config.METEOR_TOTAL_LENGTH_MIN, config.METEOR_TOTAL_LENGTH_MAX * 1.5)
                        if math.cos(angle_rad) > .5 and start_x < 0:
                            start_x = random.uniform(0, .1 * config.WIDTH)
                        elif math.cos(angle_rad) < -.5 and start_x > config.WIDTH:
                            start_x = random.uniform(.9 * config.WIDTH, config.WIDTH)
                        meteors_list.append({"x": start_x, "y": start_y,
                                             "speed": random.uniform(config.METEOR_SPEED_MIN, config.METEOR_SPEED_MAX),
                                             "angle": angle_rad,
                                             "total_length": random.uniform(config.METEOR_TOTAL_LENGTH_MIN,
                                                                            config.METEOR_TOTAL_LENGTH_MAX),
                                             "core_width": random.randint(config.METEOR_CORE_WIDTH_MIN,
                                                                          config.METEOR_CORE_WIDTH_MAX)})
                        next_meteor_spawn_time = current_time_ticks + random.randint(config.METEOR_SPAWN_INTERVAL_MIN,
                                                                                     config.METEOR_SPAWN_INTERVAL_MAX)
                    for i in range(len(meteors_list) - 1, -1, -1):
                        m = meteors_list[i]
                        m["x"] += m["speed"] * math.cos(m["angle"]) * time_delta_seconds
                        m["y"] += m["speed"] * math.sin(m["angle"]) * time_delta_seconds
                        tail_tip_y = m["y"] - m["total_length"] * math.sin(m["angle"])
                        mtl = m["total_length"]
                        scw = config.WIDTH * 0.2
                        if tail_tip_y > config.HEIGHT + mtl or m["x"] < -mtl - scw or m[
                            "x"] > config.WIDTH + scw + mtl: meteors_list.pop(i)

                for l_idx, l_flakes in enumerate(snowflakes_by_layer):
                    l_conf = config.SNOW_LAYERS[l_idx]
                    for i_flake in range(len(l_flakes) - 1, -1, -1):
                        f = l_flakes[i_flake]
                        effective_vx = f[2]
                        if is_gusting: effective_vx += current_gust_x_strength * f[6]
                        f[0] += effective_vx * (60 * time_delta_seconds)
                        f[0] -= world_scroll_this_frame * f[6]
                        effective_vy = f[3]
                        if is_gusting: effective_vy += current_gust_x_strength * current_gust_y_factor * f[6]
                        f[1] += effective_vy * (60 * time_delta_seconds)
                        flake_size_radius = f[4]
                        buffer = 50
                        if f[1] > config.HEIGHT + flake_size_radius:
                            f[1] = random.randint(-config.HEIGHT // 2, -flake_size_radius)
                            f[0] = random.randint(0, config.WIDTH)
                        if f[0] < -flake_size_radius - buffer:
                            f[0] = config.WIDTH + flake_size_radius + random.randint(0, 20)
                            f[1] = random.randint(-config.HEIGHT // 2, config.HEIGHT // 2)
                        elif f[0] > config.WIDTH + flake_size_radius + buffer:
                            f[0] = -flake_size_radius - random.randint(0, 20)
                            f[1] = random.randint(-config.HEIGHT // 2, config.HEIGHT // 2)

            if not gs.waiting_for_death_anim_to_finish and not gs.boulder_death_sequence_active:
                gs.world_distance_scrolled += world_scroll_this_frame / config.CHUNK
                if terrain_obj: terrain_obj.update(world_scroll_this_frame)

                if not gs.is_level_2_simple_mode:
                    all_checkpoints_done_for_level = gs.checkpoint_idx >= len(config.CHECKPOINT_DISTANCES)
                    can_spawn_obstacle_l1 = (
                            len(obstacles_group) < config.MAX_OBSTACLES_ON_SCREEN and
                            current_time_ticks - gs.last_obstacle_spawn_time > gs.next_obstacle_spawn_delay and
                            player_obj and player_obj.is_active and
                            not all_checkpoints_done_for_level and not gs.portal_object_exists
                    )
                    if can_spawn_obstacle_l1:
                        spawn_x_generic = config.WIDTH + random.randint(80, 300)
                        choice = random.choices(["ice_formation", "broken_satellite"], weights=[0.6, 0.4], k=1)[0]
                        new_obs_l1 = None
                        if choice == "ice_formation":
                            new_obs_l1 = IceFormation(spawn_x_generic, terrain_obj)
                        elif choice == "broken_satellite":
                            new_obs_l1 = BrokenSatellite(config.WIDTH + random.randint(400, 600), terrain_obj,
                                                         image_asset_path_name="satellite.png",
                                                         crash_sound_obj=satellite_falling_sound_asset,
                                                         impact_sound_obj=satellite_impact_sound_asset)
                        if new_obs_l1: obstacles_group.add(new_obs_l1)
                        gs.last_obstacle_spawn_time = current_time_ticks
                        gs.next_obstacle_spawn_delay = random.randint(config.OBSTACLE_SPAWN_INTERVAL_MIN,
                                                                      config.OBSTACLE_SPAWN_INTERVAL_MAX)
                elif not gs.level2_stairs_visible:
                    if player_obj and player_obj.is_active and \
                            len(obstacles_group) < config.MAX_OBSTACLES_ON_SCREEN and \
                            current_time_ticks - gs.last_obstacle_spawn_time > gs.next_obstacle_spawn_delay:

                        spawn_options_l2 = []
                        if config.BUG_OBSTACLE_ENABLED:
                            spawn_options_l2.append("bug")
                        if config.CRYSTAL_OBSTACLE_ENABLED_L2:
                            spawn_options_l2.append("crystal")

                        if spawn_options_l2:
                            chosen_obstacle_type_l2 = random.choice(spawn_options_l2)
                            new_obstacle_l2 = None
                            spawn_delay_min, spawn_delay_max = 0, 1

                            if chosen_obstacle_type_l2 == "bug":
                                spawn_x_bug = config.WIDTH + random.randint(70, 200)
                                new_obstacle_l2 = BugObstacle(spawn_x_bug, terrain_obj,
                                                              spawn_sound=bug_spawn_sound_effect,
                                                              die_sound=bug_die_sound_effect)
                                spawn_delay_min = config.BUG_SPAWN_INTERVAL_MIN_L2
                                spawn_delay_max = config.BUG_SPAWN_INTERVAL_MAX_L2
                            elif chosen_obstacle_type_l2 == "crystal":
                                spawn_x_crystal = config.WIDTH + random.randint(150, 450)
                                crystal_ground_impact_sound = sound_effects.get(config.CRYSTAL_GROUND_IMPACT_SOUND_KEY)
                                crystal_destruction_sound = sound_effects.get(config.CRYSTAL_DESTRUCTION_SOUND_KEY)

                                new_obstacle_l2 = CrystalObstacle(spawn_x_crystal, terrain_obj,
                                                                  impact_sound_obj=crystal_ground_impact_sound,
                                                                  destruction_sound_obj=crystal_destruction_sound)
                                spawn_delay_min = config.CRYSTAL_SPAWN_INTERVAL_MIN_L2
                                spawn_delay_max = config.CRYSTAL_SPAWN_INTERVAL_MAX_L2

                            if new_obstacle_l2:
                                obstacles_group.add(new_obstacle_l2)
                                gs.last_obstacle_spawn_time = current_time_ticks
                                if spawn_delay_max > spawn_delay_min:
                                    gs.next_obstacle_spawn_delay = random.randint(spawn_delay_min, spawn_delay_max)
                                else:
                                    gs.next_obstacle_spawn_delay = spawn_delay_min

                obstacles_group.update(world_scroll_this_frame, current_gs_logic, time_delta_seconds, player_obj,
                                       debris_effects_group)
                ceiling_decorations_group.update(world_scroll_this_frame)
                hanging_lights_group.update(world_scroll_this_frame)

                if not gs.is_level_2_simple_mode:
                    beacons_group.update(world_scroll_this_frame, time_delta_seconds)
                    portal_group.update(world_scroll_this_frame, terrain_obj, time_delta_seconds)
                    if config.ENABLE_FOG_EFFECT:
                        for fl in fog_layers:
                            if fl["surface"]: fl["x_pos"] -= world_scroll_this_frame * fl["scroll_factor"]
                            if fl["x_pos"] <= -fl["surface"].get_width():
                                fl["x_pos"] += fl["surface"].get_width()
                            elif fl["x_pos"] > 0:
                                fl["x_pos"] -= fl["surface"].get_width()
                    if player_obj and avalanche_obj and player_obj.is_active and player_obj.rect:
                        avalanche_obj.update(player_obj.rect.centerx, False, current_gs_logic, set_current_game_state)
                        if gs.get_state() == gs.FAILED:
                            if pygame.mixer.get_init() and pygame.mixer.music.get_busy(): pygame.mixer.music.stop()
                        if avalanche_obj.request_rumble_effect_flag:
                            if not gs.is_level_2_simple_mode:
                                gs.screen_shake_magnitude = config.AVALANCHE_SHAKE_MAGNITUDE
                                gs.screen_shake_duration = config.AVALANCHE_SHAKE_DURATION
                                gs.screen_shake_timer = 0.0
                            avalanche_obj.request_rumble_effect_flag = False
                else:
                    if not gs.level2_stairs_visible:
                        if config.L2_CEILING_DECORATION_ENABLED and \
                                all_loaded_ceiling_decor_images and terrain_obj:
                            current_world_x_at_right_edge = (
                                                                    terrain_obj.world_start_chunk_index + terrain_obj.scroll_fractional_offset) * config.CHUNK + config.WIDTH
                            if not math.isfinite(next_ceiling_decoration_spawn_target_x):
                                next_ceiling_decoration_spawn_target_x = current_world_x_at_right_edge + \
                                                                         config.L2_CEILING_DECORATION_TARGET_AVG_SPACING * 0.5
                            if current_world_x_at_right_edge > next_ceiling_decoration_spawn_target_x and \
                                    len(ceiling_decorations_group) < config.L2_MAX_CEILING_DECORATIONS_ON_SCREEN:
                                current_attempt_spawn_base_x = next_ceiling_decoration_spawn_target_x
                                spawned_this_cycle = False
                                if random.random() < config.L2_CEILING_DECORATION_SPAWN_PROBABILITY:
                                    spawn_x_world_abs = current_attempt_spawn_base_x + random.uniform(
                                        -config.L2_CEILING_DECORATION_SPAWN_X_VARIATION * 0.3,
                                        config.L2_CEILING_DECORATION_SPAWN_X_VARIATION * 0.3
                                    )
                                    if math.isfinite(last_ceiling_decoration_spawn_world_x):
                                        spawn_x_world_abs = max(spawn_x_world_abs,
                                                                last_ceiling_decoration_spawn_world_x + config.L2_CEILING_DECORATION_MIN_X_SPACING)
                                    if math.isfinite(spawn_x_world_abs):
                                        chosen_asset_surface = random.choice(all_loaded_ceiling_decor_images)
                                        effective_y_offset = random.randint(
                                            config.L2_CEILING_DECO_RANDOM_TOP_Y_OFFSET_MIN,
                                            config.L2_CEILING_DECO_RANDOM_TOP_Y_OFFSET_MAX
                                        )
                                        ceiling_y_world_edge = terrain_obj.ceiling_height_at(spawn_x_world_abs)
                                        should_flip = random.random() < config.L2_CEILING_DECORATION_HORIZONTAL_FLIP_CHANCE
                                        new_deco = CeilingDecoration(chosen_asset_surface,
                                                                     spawn_x_world_abs,
                                                                     ceiling_y_world_edge,
                                                                     effective_y_offset,
                                                                     terrain_obj,
                                                                     horizontal_flip=should_flip)
                                        ceiling_decorations_group.add(new_deco)
                                        last_ceiling_decoration_spawn_world_x = spawn_x_world_abs
                                        spawned_this_cycle = True
                                base_for_next_target_calc = last_ceiling_decoration_spawn_world_x if spawned_this_cycle else current_attempt_spawn_base_x
                                next_ceiling_decoration_spawn_target_x = base_for_next_target_calc + \
                                                                         config.L2_CEILING_DECORATION_TARGET_AVG_SPACING + \
                                                                         random.randint(
                                                                             -config.L2_CEILING_DECORATION_SPAWN_X_VARIATION,
                                                                             config.L2_CEILING_DECORATION_SPAWN_X_VARIATION)
                        if config.L2_HANGING_LIGHTS_ENABLED and hanging_light_image_surface and terrain_obj:
                            current_world_x_at_right_edge = (
                                                                    terrain_obj.world_start_chunk_index + terrain_obj.scroll_fractional_offset
                                                            ) * config.CHUNK + config.WIDTH
                            if not math.isfinite(next_hanging_light_spawn_target_x):
                                next_hanging_light_spawn_target_x = current_world_x_at_right_edge + \
                                                                    config.L2_HANGING_LIGHT_SPACING * 0.5
                            if current_world_x_at_right_edge > next_hanging_light_spawn_target_x and \
                                    len(hanging_lights_group) < config.L2_MAX_HANGING_LIGHTS_ON_SCREEN:
                                current_attempt_spawn_base_x_light = next_hanging_light_spawn_target_x
                                spawned_light_this_cycle = False
                                if random.random() < config.L2_HANGING_LIGHT_SPAWN_PROBABILITY:
                                    spawn_x_world_abs_light = current_attempt_spawn_base_x_light + random.uniform(
                                        -config.L2_HANGING_LIGHT_SPAWN_X_VARIATION * 0.3,
                                        config.L2_HANGING_LIGHT_SPAWN_X_VARIATION * 0.3
                                    )
                                    if math.isfinite(spawn_x_world_abs_light):
                                        initial_ceiling_y = terrain_obj.ceiling_height_at(spawn_x_world_abs_light)
                                        if math.isfinite(initial_ceiling_y):
                                            new_light = HangingLight(
                                                hanging_light_image_surface,
                                                spawn_x_world_abs_light,
                                                initial_ceiling_y,
                                                config.L2_HANGING_LIGHT_Y_OFFSET_FROM_CEILING,
                                                terrain_obj
                                            )
                                            hanging_lights_group.add(new_light)
                                            last_hanging_light_spawn_world_x = spawn_x_world_abs_light
                                            spawned_light_this_cycle = True
                                base_for_next_light_target_calc = last_hanging_light_spawn_world_x if spawned_light_this_cycle else current_attempt_spawn_base_x_light
                                next_hanging_light_spawn_target_x = base_for_next_light_target_calc + \
                                                                    config.L2_HANGING_LIGHT_SPACING + \
                                                                    random.randint(
                                                                        -config.L2_HANGING_LIGHT_SPAWN_X_VARIATION,
                                                                        config.L2_HANGING_LIGHT_SPAWN_X_VARIATION
                                                                    )
                    if gs.is_level_2_simple_mode and boulder_obj and player_obj and player_obj.rect and \
                            not gs.level2_win_sequence_active:
                        boulder_obj.update(gs.boulder_catch_up_active, config.PLAYER_SCREEN_X)

                        if gs.boulder_is_visible and player_obj.is_active:
                            effective_boulder_collision_rect = boulder_obj.rect.inflate(
                                -2 * config.BOULDER_COLLISION_HORIZONTAL_INSET,
                                -2 * config.BOULDER_COLLISION_VERTICAL_INSET
                            )
                            if effective_boulder_collision_rect.colliderect(player_obj.rect):
                                print("Boulder collided with player (Main.py rect collision)!")
                                if gs.player_health > 0:
                                    gs.player_health = 0
                                    player_obj.start_dying_animation(is_fatal_hit=True)
                                    gs.waiting_for_death_anim_to_finish = True
                                    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                                        pygame.mixer.music.stop()

                                    gs.boulder_death_sequence_active = True
                                    gs.boulder_death_sequence_end_time = current_time_ticks + config.BOULDER_DEATH_SCREEN_DELAY_MS

                if terrain_obj:
                    lasers_group.update(cam_y_offset)
                else:
                    lasers_group.update(cam_y_offset)
                if current_ramp_obj: current_ramp_obj.update(world_scroll_this_frame)

                hit_obstacle_dict = pygame.sprite.groupcollide(lasers_group, obstacles_group, True, True)
                if hit_obstacle_dict:
                    if gs.is_level_2_simple_mode:
                        gs.consecutive_obstacle_hits = 0
                        print("Player shot obstacle, L2 consecutive hits reset.")

                    for obs_hit_list in hit_obstacle_dict.values():
                        for obs_hit in obs_hit_list:
                            mat, cx, cy, obs_type = obs_hit.on_destroy()
                            debris_effects_group.add(DebrisEffect(cx, cy, mat, intensity=1.5))
                            if obs_type == "satellite_debris":
                                if explosion_sound: explosion_sound.play(); explosions_group.add(Explosion(cx, cy))
                            elif obs_type == "ice_formation":
                                if spike_breaking_sound: spike_breaking_sound.play()
                            elif obs_type == "bug":
                                pass
                            elif obs_hit.destructible:
                                if explosion_sound: explosion_sound.play()

                if player_obj and player_obj.is_active:
                    collided_obs_player = pygame.sprite.spritecollide(player_obj, obstacles_group, True)
                    if collided_obs_player:
                        for obs_hit in collided_obs_player:
                            gs.player_health -= obs_hit.damage_value
                            is_fatal = gs.player_health <= 0
                            player_obj.start_dying_animation(is_fatal_hit=is_fatal)
                            if hit_sound: hit_sound.play()
                            mat, cx, cy, obs_type = obs_hit.on_destroy()
                            debris_effects_group.add(DebrisEffect(cx, cy, mat, intensity=1.8))

                            if gs.is_level_2_simple_mode:
                                gs.consecutive_obstacle_hits += 1
                                print(f"Player hit obstacle. Consecutive L2 hits: {gs.consecutive_obstacle_hits}")
                                if gs.consecutive_obstacle_hits == 2 and not gs.boulder_is_visible:
                                    gs.boulder_is_visible = True
                                    print(f"Boulder now VISIBLE (threat active). Hits: {gs.consecutive_obstacle_hits}")
                                elif gs.consecutive_obstacle_hits >= 3:
                                    gs.boulder_catch_up_active = True
                                    if not gs.boulder_is_visible: gs.boulder_is_visible = True
                                    print(f"Boulder catch-up mode ACTIVATED. Hits: {gs.consecutive_obstacle_hits}")

                            if obs_type == "satellite_debris":
                                if explosion_sound: explosion_sound.play(); explosions_group.add(Explosion(cx, cy))
                            elif obs_type == "ice_formation":
                                if spike_breaking_sound: spike_breaking_sound.play()
                            elif obs_type == "bug":
                                pass
                            elif obs_hit.destructible:
                                if explosion_sound: explosion_sound.play()
                        gs.is_slowed_down = True
                        gs.slowdown_end_time = current_time_ticks + config.SLOWDOWN_DURATION
                        if gs.player_health <= 0:
                            gs.player_health = 0
                            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                                pygame.mixer.music.stop()
                            gs.waiting_for_death_anim_to_finish = True

                if not gs.is_level_2_simple_mode:
                    if player_obj and player_obj.is_active:
                        coll_beacons = pygame.sprite.spritecollide(player_obj, beacons_group, False)
                        for bhit in coll_beacons:
                            if not bhit.is_collected:
                                if bhit.collect():
                                    gs.collected_checkpoints += 1
                                    if checkpoint_sound: checkpoint_sound.play()
                                    current_checkpoint_num = gs.collected_checkpoints
                                    sound_index = current_checkpoint_num - 1
                                    if 0 <= sound_index < len(ariel_node_sounds):
                                        node_sound_to_play = ariel_node_sounds[sound_index]
                                        if node_sound_to_play: node_sound_to_play.play()
                                    gs.ariel_display_active = True
                                    gs.ariel_anim_state = 'floating_in'
                                    gs.ariel_next_message_on_screen_duration_ms = config.ARIEL_DISPLAY_DURATION_ON_SCREEN
                                    if ariel_image_scaled:
                                        gs.ariel_current_x = config.WIDTH
                                    else:
                                        gs.ariel_current_x = gs.ariel_target_x_on_screen
                                        gs.ariel_anim_state = 'shown'
                                        gs.ariel_display_on_screen_end_time = current_time_ticks + gs.ariel_next_message_on_screen_duration_ms
                                        gs.ariel_next_message_on_screen_duration_ms = 0

                                    msg_idx = gs.collected_checkpoints - 1
                                    if 0 <= msg_idx < len(config.ARIEL_MESSAGES):
                                        full_message = config.ARIEL_MESSAGES[msg_idx]
                                    else:
                                        full_message = f"Node {gs.collected_checkpoints} Online. System Anomaly."
                                    temp_text_box_width = ariel_image_scaled.get_width() * 1.8 if ariel_image_scaled else config.WIDTH * 0.35
                                    max_text_render_width = max(150, temp_text_box_width - 20)
                                    gs.ariel_current_message_lines = wrap_text(full_message, ariel_font,
                                                                               max_text_render_width)
                                    gs.colony_saved_message_active = False
                                    if gs.collected_checkpoints == len(config.CHECKPOINT_DISTANCES) and len(
                                            config.CHECKPOINT_DISTANCES) > 0:
                                        gs.portal_message_pending = True
                                        gs.portal_spawn_pending = True
                                        print("Portal Spawn Pending set to True")
                    if player_obj and player_obj.is_active:
                        collided_portal = pygame.sprite.spritecollideany(player_obj, portal_group)
                        if collided_portal:
                            print("Player reached Portal!")
                            player_obj.is_active = False
                            collided_portal.kill()
                            gs.portal_reached = True
                            gs.portal_reached_time = current_time_ticks
                            if pygame.mixer.get_init() and pygame.mixer.music.get_busy(): pygame.mixer.music.fadeout(
                                1000)
                    if player_obj and player_obj.is_active and gs.checkpoint_idx < len(
                            config.CHECKPOINT_DISTANCES) and gs.world_distance_scrolled >= config.CHECKPOINT_DISTANCES[
                        gs.checkpoint_idx]:
                        beacons_group.add(Beacon(config.WIDTH + 50, terrain_obj))
                        gs.checkpoint_idx += 1

            explosions_group.update(time_delta_seconds, world_scroll_this_frame)
            debris_effects_group.update(time_delta_seconds, world_scroll_this_frame)

       
            if gs.is_level_2_simple_mode and boulder_obj and boulder_sound_effect and pygame.mixer.get_init():
                should_boulder_sound_be_playing = (
                        gs.boulder_is_visible and
                        not gs.level2_win_sequence_active and
                        not gs.boulder_death_sequence_active and
                        (player_obj and player_obj.is_active and gs.player_health > 0) and
                        not gs.waiting_for_death_anim_to_finish 
                )

                is_currently_playing_our_sound = False
                if boulder_sound_effect_channel and \
                        boulder_sound_effect_channel.get_sound() == boulder_sound_effect and \
                        boulder_sound_effect_channel.get_busy():
                    is_currently_playing_our_sound = True

                if should_boulder_sound_be_playing and not is_currently_playing_our_sound:
                    if boulder_sound_effect_channel and not boulder_sound_effect_channel.get_busy():
                        try:
                            boulder_sound_effect_channel.play(boulder_sound_effect, loops=-1)
                        except pygame.error as e:
                            print(f"Boulder sound: Error re-playing: {e}")
                            boulder_sound_effect_channel = None
                    if not boulder_sound_effect_channel: 
                        try:
                            boulder_sound_effect_channel = pygame.mixer.find_channel(True)
                            if boulder_sound_effect_channel:
                                boulder_sound_effect_channel.play(boulder_sound_effect, loops=-1)
                        except pygame.error as e:
                            print(f"Boulder sound: Error finding/playing on new channel: {e}")
                            boulder_sound_effect_channel = None
                elif not should_boulder_sound_be_playing and is_currently_playing_our_sound:
                    print("Boulder sound: Stopping due to condition change (should_boulder_sound_be_playing is False).")
                    boulder_sound_effect_channel.stop()



    current_gs_draw = gs.get_state()

    if current_gs_draw == gs.MENU:
        frame_to_draw = None
        if menu_bg_frames: frame_to_draw = menu_bg_frames[menu_frame_idx % len(menu_bg_frames)]
        ui.draw_menu(screen, title_font, font, [frame_to_draw] if frame_to_draw else [], menu_frame_idx,
                     gs.menu_options, gs.menu_idx, config.WIDTH, config.HEIGHT)
        pygame.display.flip()

    elif current_gs_draw == gs.PROLOGUE:
        if prologue_video_player and prologue_video_player.is_valid():
            frame_surface = prologue_video_player.get_current_surface()
            if frame_surface:
                screen.blit(frame_surface, (0, 0))
            else:
                screen.fill((0, 0, 0))
        else:
            screen.fill((0, 0, 0))
        pygame.display.flip()

    elif current_gs_draw == gs.MID_CUTSCENE:
        screen.fill((0, 0, 0))
        if middle_cutscene_video_player and middle_cutscene_video_player.is_valid():
            frame_surface = middle_cutscene_video_player.get_current_surface()
            if frame_surface:
                screen.blit(frame_surface, (0, 0))
        skip_text_mid = font.render("Press Enter or Esc to Skip", True, (200, 200, 200))
        screen.blit(skip_text_mid, (config.WIDTH - skip_text_mid.get_width() - 20,
                                    config.HEIGHT - skip_text_mid.get_height() - 35))
        pygame.display.flip()
        continue

    elif current_gs_draw == gs.WIN_CUTSCENE:
        screen.fill((0, 0, 0))
        if final_cutscene_video_player and final_cutscene_video_player.is_valid():
            frame_surface = final_cutscene_video_player.get_current_surface()
            if frame_surface:
                screen.blit(frame_surface, (0, 0))
        skip_text_win = font.render("Press Enter or Esc to Skip", True, (200, 200, 200))
        screen.blit(skip_text_win, (config.WIDTH - skip_text_win.get_width() - 20,
                                    config.HEIGHT - skip_text_win.get_height() - 35))
        pygame.display.flip()
        continue

    elif current_gs_draw == gs.CREDITS:
        ui.draw_credits_screen(screen, font, title_font, gs.credits_text, gs.credits_scroll_y, gs.credits_line_height,
                               config.WIDTH, config.HEIGHT)
        pygame.display.flip()

    elif current_gs_draw in [gs.PLAYING, gs.TUTORIAL]:
        world_render_surface.fill((0, 0, 0, 0))

        if current_gs_draw == gs.TUTORIAL:
            world_render_surface.fill((50, 50, 80))
            if terrain_obj:
                terrain_obj.draw_background_elements(world_render_surface, cam_y_offset)
                terrain_obj.draw_tutorial_snow_platform(world_render_surface, cam_y_offset)
            if player_obj and not player_obj.is_hidden:
                player_obj.draw_splash_particles(world_render_surface, cam_y_offset)
                player_obj.draw(world_render_surface, cam_y_offset)
            for obs_sprite in obstacles_group: obs_sprite.draw(world_render_surface, cam_y_offset)
            for lsr_sprite in lasers_group: world_render_surface.blit(lsr_sprite.image, (lsr_sprite.rect.x,
                                                                                         lsr_sprite.rect.y - cam_y_offset))
            for exp in explosions_group: exp.draw(world_render_surface, cam_y_offset)
            for deb_fx in debris_effects_group: deb_fx.draw(world_render_surface, cam_y_offset)

        elif current_gs_draw == gs.PLAYING:
            video_frame = None
            if gs.is_level_2_simple_mode:
                if level2_video_player and level2_video_player.is_valid(): video_frame = level2_video_player.get_current_surface()
            else:
                if level1_video_player and level1_video_player.is_valid(): video_frame = level1_video_player.get_current_surface()
            if video_frame:
                world_render_surface.blit(video_frame, (0, 0))
            else:
                fill_color = (30, 30, 50) if not gs.is_level_2_simple_mode else (20, 15, 10)
                world_render_surface.fill(fill_color)

            if not gs.is_level_2_simple_mode:
                if planet_image: world_render_surface.blit(planet_image, (int(planet_x), planet_y))
                if planet2_image: world_render_surface.blit(planet2_image, (int(planet2_x), planet_y))
                if config.ENABLE_METEOR_EFFECT:
                    for m in meteors_list:
                        head_x, head_y = m["x"], m["y"]
                        for i in range(config.METEOR_TRAIL_SEGMENTS):
                            t = (i + 1) / (config.METEOR_TRAIL_SEGMENTS + 1)
                            tc = (int(
                                config.METEOR_TRAIL_COLOR_START[0] * (1 - t) + config.METEOR_TRAIL_COLOR_END[0] * t),
                                  int(config.METEOR_TRAIL_COLOR_START[1] * (1 - t) + config.METEOR_TRAIL_COLOR_END[
                                      1] * t),
                                  int(config.METEOR_TRAIL_COLOR_START[2] * (1 - t) + config.METEOR_TRAIL_COLOR_END[
                                      2] * t))
                            tw = max(1, int(m["core_width"] * (1 - t * .8)))
                            tsp = i / config.METEOR_TRAIL_SEGMENTS * .8 + .2
                            tep = (i + 1) / config.METEOR_TRAIL_SEGMENTS * .8 + .2
                            ssx = head_x - (m["total_length"] * tsp * math.cos(m["angle"]))
                            ssy = head_y - (m["total_length"] * tsp * math.sin(m["angle"]))
                            sex = head_x - (m["total_length"] * tep * math.cos(m["angle"]))
                            sey = head_y - (m["total_length"] * tep * math.sin(m["angle"]))
                            try:
                                pygame.draw.line(world_render_surface, tc, (ssx, ssy), (sex, sey), tw)
                            except:
                                pass
                        cep = .25
                        ctx = head_x - (m["total_length"] * cep * math.cos(m["angle"]))
                        cty = head_y - (m["total_length"] * cep * math.sin(m["angle"]))
                        try:
                            pygame.draw.line(world_render_surface, config.METEOR_CORE_COLOR, (ctx, cty),
                                             (head_x, head_y), m["core_width"])
                        except:
                            pass

            if terrain_obj: terrain_obj.draw_background_elements(world_render_surface, cam_y_offset)
            if player_obj and player_obj.rect and (
                    player_obj.y_world - player_obj.rect.height / 2.0) < config.GROUND_Y - 100:
                if not gs.is_level_2_simple_mode:
                    if cloud_image_2: world_render_surface.blit(cloud_image_2, (0, cloud_y_2_draw - cam_y_offset))
                    if cloud_image_1: world_render_surface.blit(cloud_image_1, (0, cloud_y_1_draw - cam_y_offset))

            if not gs.is_level_2_simple_mode and avalanche_obj and not (
                    gs.waiting_for_death_anim_to_finish or gs.boulder_death_sequence_active or gs.level2_win_sequence_active):
                avalanche_obj.draw(world_render_surface, current_gs_draw, terrain_obj, cam_y_offset, avalanche_image)

            if gs.is_level_2_simple_mode and boulder_obj and not (
                    gs.waiting_for_death_anim_to_finish or gs.level2_win_sequence_active):
                boulder_obj.draw(world_render_surface, cam_y_offset)

            if not gs.is_level_2_simple_mode and config.ENABLE_FOG_EFFECT:
                for fog_layer in fog_layers:
                    if fog_layer["surface"]:
                        fog_y = config.HEIGHT - fog_layer["surface"].get_height() - fog_layer["y_offset_from_bottom"]
                        world_render_surface.blit(fog_layer["surface"], (fog_layer["x_pos"], fog_y))
                        world_render_surface.blit(fog_layer["surface"],
                                                  (fog_layer["x_pos"] + fog_layer["surface"].get_width(), fog_y))

            if terrain_obj: terrain_obj.draw_snow_platform_and_clumps(world_render_surface, cam_y_offset)

            if gs.is_level_2_simple_mode:
                if config.L2_CEILING_DECORATION_ENABLED:
                    for deco in ceiling_decorations_group: deco.draw(world_render_surface, cam_y_offset)
                if config.L2_HANGING_LIGHTS_ENABLED:
                    for light in hanging_lights_group: light.draw(world_render_surface, cam_y_offset)

                if gs.level2_stairs_visible and not gs.level2_player_reached_stairs and \
                        stairs_image_asset and gs.level2_stairs_rect_world and terrain_obj and player_obj:
                    total_world_scroll_pixels = gs.world_distance_scrolled * config.CHUNK
                    stairs_draw_x_on_world_surface = gs.level2_stairs_rect_world.left - total_world_scroll_pixels
                    stairs_bottom_world_y = gs.level2_stairs_rect_world.bottom
                    stairs_draw_y_on_world_surface = (
                                                             stairs_bottom_world_y - gs.level2_stairs_rect_world.height) - cam_y_offset
                    world_render_surface.blit(stairs_image_asset,
                                              (stairs_draw_x_on_world_surface, stairs_draw_y_on_world_surface))

            if player_obj and not player_obj.is_hidden:
                player_obj.draw_trails(world_render_surface, cam_y_offset)
                player_obj.draw_splash_particles(world_render_surface, cam_y_offset)

            if not gs.is_level_2_simple_mode:
                for layer_flakes_list in snowflakes_by_layer:
                    for flk in layer_flakes_list:
                        diameter = flk[4] * 2
                        if diameter > 0:
                            flake_surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
                            pygame.draw.circle(flake_surf, (255, 255, 255, flk[5]), (flk[4], flk[4]), flk[4])
                            world_render_surface.blit(flake_surf, (int(flk[0] - flk[4]), int(flk[1] - flk[4])))
                for bcn in beacons_group: bcn.draw(world_render_surface, cam_y_offset)
                for portal_sprite in portal_group: portal_sprite.draw(world_render_surface, cam_y_offset)

            for obs in obstacles_group: obs.draw(world_render_surface, cam_y_offset)
            for exp in explosions_group: exp.draw(world_render_surface, cam_y_offset)
            for deb_fx in debris_effects_group: deb_fx.draw(world_render_surface, cam_y_offset)
            if current_ramp_obj: current_ramp_obj.draw(world_render_surface, cam_y_offset)

            if player_obj and not player_obj.is_hidden:
                player_obj.draw(world_render_surface, cam_y_offset)

            for lsr in lasers_group: world_render_surface.blit(lsr.image, (lsr.rect.x, lsr.rect.y - cam_y_offset))

            if current_gs_draw == gs.PLAYING and gs.is_level_2_simple_mode and \
                    gs.level2_win_sequence_active and gs.level2_player_reached_stairs:

                flash_start_time = gs.level2_win_sequence_timer_end - config.L2_WIN_WHITE_FLASH_DURATION_MS
                elapsed_flash_time = current_time_ticks - flash_start_time
                flash_progress = 0.0
                if config.L2_WIN_WHITE_FLASH_DURATION_MS > 0:
                    flash_progress = min(1.0, max(0.0, elapsed_flash_time / config.L2_WIN_WHITE_FLASH_DURATION_MS))

                alpha = int(255 * flash_progress)

                flash_surface_overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
                flash_surface_overlay.fill((255, 255, 255, alpha))
                world_render_surface.blit(flash_surface_overlay, (0, 0))

        screen.blit(world_render_surface, (current_screen_offset_x, current_screen_offset_y))

        if current_gs_draw == gs.TUTORIAL:
            ui.draw_tutorial_ui_elements(screen, tutorial_font, font, player_obj, gs.tutorial_jump_done,
                                         gs.tutorial_shoot_done, config.WIDTH, config.HEIGHT, config.MAX_BULLETS)
        elif current_gs_draw == gs.PLAYING:
            if player_obj and (
                    player_obj.is_active or not gs.portal_reached) and not gs.level2_player_hidden_after_stairs:
                hud_manager.draw(screen, gs, player_obj, config, time_delta_seconds)

            if gs.ariel_display_active and ariel_image_scaled and ariel_font:
                ariel_draw_x_base = gs.ariel_current_x
                ariel_draw_y_base = int(config.HEIGHT * 0.15)
                screen.blit(ariel_image_scaled,
                            (ariel_draw_x_base + current_screen_offset_x, ariel_draw_y_base + current_screen_offset_y))
                text_box_width = ariel_image_scaled.get_width() * 1.8
                num_lines = len(gs.ariel_current_message_lines)
                num_lines = 1 if num_lines == 0 else num_lines
                current_text_box_height = (config.ARIEL_TEXT_BOX_HEIGHT_PER_LINE * num_lines) + 10
                text_box_x_base = ariel_draw_x_base - text_box_width - 10
                text_box_x_base = max(10, text_box_x_base)
                text_box_y_base = ariel_draw_y_base + (ariel_image_scaled.get_height() // 2) - (
                        current_text_box_height // 2)
                text_box_draw_x, text_box_draw_y = text_box_x_base + current_screen_offset_x, text_box_y_base + current_screen_offset_y
                text_bg_surface = pygame.Surface((text_box_width, current_text_box_height), pygame.SRCALPHA)
                text_bg_surface.fill((50, 50, 80, 180))
                screen.blit(text_bg_surface, (text_box_draw_x, text_box_draw_y))
                pygame.draw.rect(screen, (100, 100, 150, 200),
                                 (text_box_draw_x, text_box_draw_y, text_box_width, current_text_box_height), 2)
                total_text_block_height = (
                                                  num_lines - 1) * ariel_font.get_linesize() + ariel_font.get_height() if num_lines > 0 else 0
                line_y_start = text_box_draw_y + (current_text_box_height - total_text_block_height) / 2
                for i, line_text in enumerate(gs.ariel_current_message_lines):
                    text_surface = ariel_font.render(line_text, True, config.ARIEL_TEXT_COLOR)
                    text_rect = text_surface.get_rect(centerx=text_box_draw_x + text_box_width / 2,
                                                      top=line_y_start + i * ariel_font.get_linesize())
                    screen.blit(text_surface, text_rect)

            if not gs.is_level_2_simple_mode and gs.colony_saved_message_active:
                time_left = gs.colony_saved_message_timer_end - current_time_ticks
                fade_duration_ms = 500
                alpha = 255
                if fade_duration_ms > 0:
                    if time_left < fade_duration_ms:
                        alpha = int(255 * (time_left / fade_duration_ms))
                    elif (gs.colony_saved_message_duration - time_left) < fade_duration_ms:
                        alpha = int(255 * ((gs.colony_saved_message_duration - time_left) / fade_duration_ms))
                alpha = max(0, min(255, alpha))
                shadow_offset = 3
                shadow_color = (30, 100, 30)
                text_color = (100, 255, 100)
                msg_center_x, msg_center_y = config.WIDTH // 2 + current_screen_offset_x, config.HEIGHT // 3 + current_screen_offset_y
                msg_surf_shadow = message_font.render(gs.colony_saved_message_text, True, shadow_color)
                msg_surf_shadow.set_alpha(int(alpha * 0.7))
                msg_rect_shadow = msg_surf_shadow.get_rect(
                    center=(msg_center_x + shadow_offset, msg_center_y + shadow_offset))
                screen.blit(msg_surf_shadow, msg_rect_shadow)
                msg_surf_main = message_font.render(gs.colony_saved_message_text, True, text_color)
                msg_surf_main.set_alpha(alpha)
                msg_rect_main = msg_surf_main.get_rect(center=(msg_center_x, msg_center_y))
                screen.blit(msg_surf_main, msg_rect_main)
        pygame.display.flip()

    elif current_gs_draw == gs.PAUSED:
        ui.draw_pause_menu(screen, title_font, font, gs.pause_menu_options, gs.pause_menu_idx,
                           paused_game_surface_local, config.WIDTH, config.HEIGHT)
        pygame.display.flip()

    elif current_gs_draw == gs.FAILED:
        
        if gs.is_level_2_simple_mode and boulder_sound_effect_channel and boulder_sound_effect_channel.get_busy():
            print("Boulder sound: Stopping due to FAILED game state.")
            boulder_sound_effect_channel.stop()
        ui.draw_failed_screen(screen, title_font, font, config.WIDTH, config.HEIGHT)
        pygame.display.flip()

    elif current_gs_draw == gs.CONTROLS:
        ui.draw_controls(screen, font, config.WIDTH, config.HEIGHT)
        pygame.display.flip()

    elif current_gs_draw == gs.SETTINGS:
        vol_str = "N/A" if not pygame.mixer.get_init() else f"{int(gs.music_volume * 100)}%"
        ui.draw_settings(screen, font, vol_str, config.WIDTH, config.HEIGHT)
        pygame.display.flip()

pygame.quit()
if level1_video_player: level1_video_player.release()
if level2_video_player: level2_video_player.release()
if prologue_video_player: prologue_video_player.release()
if middle_cutscene_video_player: middle_cutscene_video_player.release()
if final_cutscene_video_player: final_cutscene_video_player.release()
if prologue_audio_channel and prologue_audio_channel.get_busy():
    prologue_audio_channel.stop()
if middle_cutscene_audio_channel and middle_cutscene_audio_channel.get_busy():
    middle_cutscene_audio_channel.stop()
if final_cutscene_audio_channel and final_cutscene_audio_channel.get_busy():
    final_cutscene_audio_channel.stop()
if avalanche_obj and avalanche_obj.sound_channel and hasattr(avalanche_obj,
                                                             'is_sound_looping') and avalanche_obj.is_sound_looping:
    avalanche_obj.sound_channel.stop()
for obs in obstacles_group:
    if isinstance(obs, BrokenSatellite):
        if hasattr(obs, '_stop_falling_sound'):
            obs._stop_falling_sound()
    if isinstance(obs, BugObstacle):
        if hasattr(obs, 'spawn_sound_channel') and obs.spawn_sound_channel and obs.spawn_sound_channel.get_busy():
            obs.spawn_sound_channel.stop()
if boulder_sound_effect_channel and boulder_sound_effect_channel.get_busy():
    print("Boulder sound: Stopping due to game exit.")
    boulder_sound_effect_channel.stop()
sys.exit()
