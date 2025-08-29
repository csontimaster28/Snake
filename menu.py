import pygame
import sys
from game import SnakeGame, SKINS, ACHIEVEMENT_THRESHOLDS, load_achievements
import pygame_emojis

pygame.init()
pygame.mixer.init()

# Colors
BG_COLOR = (30, 30, 30)
BUTTON_COLOR = (60, 180, 75)
BUTTON_HOVER = (80, 220, 100)
TEXT_COLOR = (255, 255, 255)
EXIT_COLOR = (220, 50, 50)
EXIT_HOVER = (255, 80, 80)

# Fonts
TITLE_FONT = pygame.font.SysFont("Segoe UI Emoji", 72)
BUTTON_FONT = pygame.font.SysFont("Segoe UI Emoji", 48)

# Music control
music_on = True
try:
    pygame.mixer.music.load("music1.mp3")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
except Exception as e:
    print("Zene betöltése sikertelen:", e)
    music_on = False


def draw_text(surface, text, font, color, center):
    text_surf = font.render(text, True, color)
    rect = text_surf.get_rect(center=center)
    surface.blit(text_surf, rect)
    return rect


def draw_button(surface, text, font, color, hover_color, center, mouse_pos):
    text_surf = font.render(text, True, TEXT_COLOR)
    rect = text_surf.get_rect(center=center)
    button_rect = pygame.Rect(rect.left - 30, rect.top - 20, rect.width + 60, rect.height + 40)
    is_hover = button_rect.collidepoint(mouse_pos)
    pygame.draw.rect(surface, hover_color if is_hover else color, button_rect, border_radius=20)
    surface.blit(text_surf, rect)
    return button_rect


def show_achievements(screen):
    achievements = load_achievements()
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(BG_COLOR)
        draw_text(screen, "Achievements", TITLE_FONT, BUTTON_COLOR,
                  (screen.get_width() // 2, 120))
        y = 220
        for threshold in ACHIEVEMENT_THRESHOLDS:
            unlocked = threshold in achievements
            color = (255, 215, 0) if unlocked else (120, 120, 120)
            status = "Unlocked ✅" if unlocked else "Locked ❌"
            text = f"{threshold} Points: {status}"
            draw_text(screen, text, BUTTON_FONT, color, (screen.get_width() // 2, y))
            y += 60

        back_rect = draw_button(
            screen, "Back", BUTTON_FONT, BUTTON_COLOR, BUTTON_HOVER,
            (screen.get_width() // 2, y + 40), mouse_pos
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    running = False
        pygame.display.flip()


def show_menu(screen):
    global music_on
    running = True
    selected_skin = 0
    skin_btn_rects = []
    button_spacing = 100

    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(BG_COLOR)
        draw_text(screen, "Snake Game", TITLE_FONT, BUTTON_COLOR,
                  (screen.get_width() // 2, screen.get_height() // 3))

        # --- Skins ---
        skin_btn_rects.clear()
        total_width = sum([BUTTON_FONT.size(skin["name"])[0] + 40 for skin in SKINS]) + (len(SKINS) - 1) * 20
        start_x = screen.get_width() // 2 - total_width // 2
        x = start_x
        for idx, skin in enumerate(SKINS):
            name_surf = BUTTON_FONT.render(skin["name"], True, (0, 0, 0) if idx != selected_skin else skin["head"])
            btn_width = name_surf.get_width() + 40
            btn_height = name_surf.get_height() + 20
            btn_rect = pygame.Rect(x, screen.get_height() // 2 - 60, btn_width, btn_height)
            btn_color = skin["head"] if idx != selected_skin else (255, 255, 255)
            pygame.draw.rect(screen, btn_color, btn_rect, border_radius=16)
            screen.blit(name_surf, name_surf.get_rect(center=btn_rect.center))
            skin_btn_rects.append(btn_rect)
            x += btn_width + 20

        # --- Buttons ---
        start_y = screen.get_height() // 2 + 60
        start_rect = draw_button(screen, "Start", BUTTON_FONT, BUTTON_COLOR, BUTTON_HOVER,
                                 (screen.get_width() // 2, start_y), mouse_pos)
        achievements_rect = draw_button(screen, "Achievements", BUTTON_FONT, BUTTON_COLOR, BUTTON_HOVER,
                                        (screen.get_width() // 2, start_y + button_spacing), mouse_pos)
        exit_rect = draw_button(screen, "Exit", BUTTON_FONT, EXIT_COLOR, EXIT_HOVER,
                                (screen.get_width() // 2, start_y + 2 * button_spacing), mouse_pos)

        # --- Music toggle (jobb felső sarok) ---
        music_rect = draw_button(screen, f"Music: {'On' if music_on else 'Off'}",
                                 BUTTON_FONT, BUTTON_COLOR, BUTTON_HOVER,
                                 (screen.get_width() - 150, 50), mouse_pos)

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for idx, rect in enumerate(skin_btn_rects):
                    if rect.collidepoint(event.pos):
                        selected_skin = idx
                if start_rect.collidepoint(event.pos):
                    SnakeGame(screen, skin_idx=selected_skin).run()
                    running = True
                elif achievements_rect.collidepoint(event.pos):
                    show_achievements(screen)
                elif exit_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
                elif music_rect.collidepoint(event.pos):
                    music_on = not music_on
                    if music_on:
                        pygame.mixer.music.play(-1)
                    else:
                        pygame.mixer.music.stop()

        pygame.display.flip()


if __name__ == "__main__":
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Snake Game Menu")
    show_menu(screen)
