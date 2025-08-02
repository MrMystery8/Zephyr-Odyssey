# ui.py
import pygame


def draw_menu(screen, title_font, font, menu_bg_frames, menu_frame_idx, menu_options, current_menu_idx, WIDTH, HEIGHT):
    if not menu_bg_frames:
        screen.fill((30, 30, 70))
    else:
        safe_menu_frame_idx = menu_frame_idx % len(menu_bg_frames)
        current_frame_surface = menu_bg_frames[safe_menu_frame_idx]
        screen.blit(current_frame_surface, (0, 0))

    if title_font:
        title_text_surf = title_font.render("Zephyr Odyssey", True, (255, 255, 255))
        screen.blit(title_text_surf, ((WIDTH - title_text_surf.get_width()) // 2, HEIGHT // 4))

    if font:
        for i, option_text in enumerate(menu_options):
            color = (255, 255, 255) if i == current_menu_idx else (180, 180, 180)
            text_surf = font.render(option_text, True, color)
            screen.blit(text_surf, ((WIDTH - text_surf.get_width()) // 2, HEIGHT // 2 + i * 40))

        hint_text_surf = font.render("Up/Down: Navigate   Enter: Select", True, (180, 180, 180))
        screen.blit(hint_text_surf, ((WIDTH - hint_text_surf.get_width()) // 2, HEIGHT - 60))

    pygame.display.flip()


def draw_controls(screen, font, WIDTH, HEIGHT):
    screen.fill((0, 0, 0))
    lines = ["Controls:",
             "Spacebar: Jump (Can Double Jump)",
             "F: Shoot Rocks (Aimbot, Limited Ammo)",
             "Activate all checkpoints to win!"]
    for i, line_text in enumerate(lines):
        text_surf = font.render(line_text, True, (220, 220, 220))
        screen.blit(text_surf, (WIDTH // 4, HEIGHT // 4 + i * 30))
    back_text_surf = font.render("Enter/Esc: Back", True, (180, 180, 180))
    screen.blit(back_text_surf, ((WIDTH - back_text_surf.get_width()) // 2, HEIGHT - 60))
    pygame.display.flip()


def draw_settings(screen, font, music_volume_percent_str, WIDTH, HEIGHT):
    screen.fill((0, 0, 0))
    lines = ["Settings:",
             f"Volume: {music_volume_percent_str}",
             "←/→ Adjust Volume"]
    for i, line_text in enumerate(lines):
        text_surf = font.render(line_text, True, (220, 220, 220))
        screen.blit(text_surf, (WIDTH // 4, HEIGHT // 4 + i * 30))
    back_text_surf = font.render("Enter/Esc: Back", True, (180, 180, 180))
    screen.blit(back_text_surf, ((WIDTH - back_text_surf.get_width()) // 2, HEIGHT - 60))
    pygame.display.flip()


def draw_failed_screen(screen, title_font, font, WIDTH, HEIGHT):
    screen.fill((0, 0, 0))
    fail_msg1_surf = title_font.render("Level Failed!", True, (255, 0, 0))
    fail_msg2_surf = font.render("Press Enter to Retry or Q to Quit to Menu", True, (255, 255, 255))
    screen.blit(fail_msg1_surf, ((WIDTH - fail_msg1_surf.get_width()) // 2, HEIGHT // 2 - 30))
    screen.blit(fail_msg2_surf, ((WIDTH - fail_msg2_surf.get_width()) // 2, HEIGHT // 2 + 30))
    pygame.display.flip()


def draw_pause_menu(screen, title_font, font, pause_menu_options_list, current_pause_idx, paused_surf, WIDTH, HEIGHT):
    if paused_surf:
        screen.blit(paused_surf, (0, 0))
    else:
        screen.fill((30, 30, 30))
    overlay_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay_surf.fill((0, 0, 0, 150))
    screen.blit(overlay_surf, (0, 0))
    paused_title_surf = title_font.render("Paused", True, (255, 255, 255))
    screen.blit(paused_title_surf, ((WIDTH - paused_title_surf.get_width()) // 2, HEIGHT // 4))
    for i, option_text in enumerate(pause_menu_options_list):
        color = (255, 255, 255) if i == current_pause_idx else (180, 180, 180)
        text_surf = font.render(option_text, True, color)
        screen.blit(text_surf, ((WIDTH - text_surf.get_width()) // 2, HEIGHT // 2 - 40 + i * 40))
    hint_text_surf = font.render("Up/Down: Navigate   Enter: Select", True, (180, 180, 180))
    screen.blit(hint_text_surf, ((WIDTH - hint_text_surf.get_width()) // 2, HEIGHT - 60))
    pygame.display.flip()


def draw_tutorial_ui_elements(screen, tutorial_font, font, player_obj, tutorial_jump_flag, tutorial_shoot_flag, WIDTH,
                              HEIGHT, MAX_BULLETS_CONST):
    instruction_text = ""
    if not tutorial_jump_flag:
        instruction_text = "Press SPACE to Jump"
    elif not tutorial_shoot_flag:
        instruction_text = "Press F to Shoot the Rock"
    else:
        instruction_text = "Tutorial Complete! Starting game..."
    if instruction_text:
        text_surf = tutorial_font.render(instruction_text, True, (220, 220, 255))
        text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        screen.blit(text_surf, text_rect)
    if player_obj:
        bullet_hud_text = font.render(f"Bullets: {player_obj.bullets_remaining}/{MAX_BULLETS_CONST}", True,
                                      (220, 220, 220))
        screen.blit(bullet_hud_text, (20, 20))


def draw_credits_screen(screen, font, title_font_main_menu, credits_text_list, scroll_y, line_height, WIDTH, HEIGHT):
    screen.fill((10, 10, 20))  

    
    credits_title_text = "CREDITS"
    
    title_surf = title_font_main_menu.render(credits_title_text, True, (220, 220, 255))
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 70)) 
    screen.blit(title_surf, title_rect)

   
    initial_text_y_start_position = HEIGHT + line_height

    for i, line_text in enumerate(credits_text_list):
        text_surf = font.render(line_text, True, (200, 200, 220))
        text_rect = text_surf.get_rect(centerx=WIDTH // 2)
       
        text_rect.centery = int(initial_text_y_start_position + (i * line_height) - scroll_y)

       
        if text_rect.bottom > 0 and text_rect.top < HEIGHT:
            screen.blit(text_surf, text_rect)

    hint_text_surf = font.render("Press Enter/Esc to Return to Menu", True, (180, 180, 180))
    screen.blit(hint_text_surf, ((WIDTH - hint_text_surf.get_width()) // 2, HEIGHT - 40))
