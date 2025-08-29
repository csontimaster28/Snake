# game.py
import pygame
import random
import json
import os
import sys
import time
import math
import platform

# Optional emoji helper package (used on Windows if available)
try:
    import pygame_emojis as _pe
except Exception:
    _pe = None

# --- Constants (kept compatible with a közeli eredeti verzióddal) ---
GRID_SIZE = 32
BASE_SPEED = 8.0
SPEED_INCREMENT = 2.0
HIGHSCORE_FILE = "highscore.json"

# Support both spellings: legacy typo file and corrected file
ACHIEVEMENT_FILE_PREFERRED = "achievements.csv"
ACHIEVEMENT_FILE_LEGACY = "achievments.csv"
ACHIEVEMENT_THRESHOLDS = [10, 20, 30, 50, 100, 250, 500]

SKINS = [
    {"name": "Classic", "head": (0, 200, 0), "body": (0, 150, 0)},
    {"name": "Blue", "head": (0, 120, 255), "body": (0, 80, 180)},
    {"name": "Red", "head": (220, 40, 40), "body": (180, 0, 0)},
    {"name": "Yellow", "head": (255, 220, 0), "body": (200, 180, 0)},
    {"name": "White", "head": (255,255,255), "body": (255,255,255)}, # Placeholder / legendary
]

FOODS = ["🍇", "🍈", "🍉", "🍊", "🍋", "🍋‍🟩", "🍌", "🍍", "🥭", "🍐", "🍑", "🍒", "🍓", "🫐", "🥝", "🍎", "🍏"]

# --- Helpers -----------------------------------------------------------
def get_rainbow_color(i, t):
    freq = 0.3
    r = int(128 + 127 * math.sin(freq * i + t))
    g = int(128 + 127 * math.sin(freq * i + t + 2))
    b = int(128 + 127 * math.sin(freq * i + t + 4))
    return (r, g, b)

def _read_achievement_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            return set(int(line) for line in lines if line.strip().isdigit())
    except Exception:
        return set()

def load_achievements():
    # Prefer corrected filename if present, otherwise fall back to legacy typo file
    if os.path.exists(ACHIEVEMENT_FILE_PREFERRED):
        return _read_achievement_file(ACHIEVEMENT_FILE_PREFERRED)
    if os.path.exists(ACHIEVEMENT_FILE_LEGACY):
        return _read_achievement_file(ACHIEVEMENT_FILE_LEGACY)
    return set()

def save_achievements(achievements):
    # Write both files for compatibility (so older installs still see the data)
    try:
        with open(ACHIEVEMENT_FILE_PREFERRED, "w", encoding="utf-8") as f:
            for ach in sorted(achievements):
                f.write(f"{ach}\n")
    except Exception:
        pass
    try:
        with open(ACHIEVEMENT_FILE_LEGACY, "w", encoding="utf-8") as f:
            for ach in sorted(achievements):
                f.write(f"{ach}\n")
    except Exception:
        pass

# --- Emoji renderer factory (robust across multiple pygame_emojis variants) -
def _make_emoji_renderer(cell_size):
    """
    Returns a function render_emoji(char, size) -> pygame.Surface.
    Tries multiple APIs of pygame_emojis if present; otherwise uses a font render fallback.
    """
    os_name = platform.system()

    # If pygame_emojis is available, attempt to adapt to its available API
    if _pe is not None:
        # Try several possible APIs. We'll return a function that tries them in order.
        def render_with_pe(char, size):
            # 1) try load_emoji(char, size) or load_emoji(char, (w,h))
            try:
                if hasattr(_pe, "load_emoji"):
                    # many forks take either a tuple or integer
                    try:
                        surf = _pe.load_emoji(char, (size, size))
                        if isinstance(surf, pygame.Surface):
                            return surf
                    except Exception:
                        pass
                    try:
                        surf = _pe.load_emoji(char, size)
                        if isinstance(surf, pygame.Surface):
                            return surf
                    except Exception:
                        pass
                # 2) try render / render_emoji functions
                if hasattr(_pe, "render"):
                    try:
                        surf = _pe.render(char, size)
                        if isinstance(surf, pygame.Surface):
                            return surf
                    except Exception:
                        pass
                if hasattr(_pe, "render_emoji"):
                    try:
                        surf = _pe.render_emoji(char, size)
                        if isinstance(surf, pygame.Surface):
                            return surf
                    except Exception:
                        pass
                # 3) try draw(surface, char, rect) - if only draw() exists, draw to a temp surface
                if hasattr(_pe, "draw"):
                    try:
                        tmp = pygame.Surface((size, size), pygame.SRCALPHA)
                        # Some implementations expect (surface, emoji, rect)
                        try:
                            _pe.draw(tmp, char, pygame.Rect(0,0,size,size))
                        except TypeError:
                            # maybe parameters order is different; try (char, surface, rect)
                            try:
                                _pe.draw(char, tmp, pygame.Rect(0,0,size,size))
                            except Exception:
                                pass
                        return tmp
                    except Exception:
                        pass
                # 4) 'emojis' factory with render_text_and_emojis
                if hasattr(_pe, "emojis"):
                    try:
                        # create helper instance and call render_text_and_emojis on a temp surface
                        tmp = pygame.Surface((size, size), pygame.SRCALPHA)
                        helper = _pe.emojis(tmp)
                        # some versions: helper.render_text_and_emojis(text, color, pos, size)
                        try:
                            helper.render_text_and_emojis(char, (255,255,255), (0,0), size)
                        except TypeError:
                            # maybe different signature
                            try:
                                helper.render_text_and_emojis(char, (255,255,255), (0,0), font_size=size)
                            except Exception:
                                pass
                        return tmp
                    except Exception:
                        pass
            except Exception:
                pass
            # If all attempts fail, raise to let caller fallback
            raise RuntimeError("pygame_emojis available but all tried APIs failed")
        # Use the sprite-based renderer on Windows (more reliable there), otherwise still attempt PE.
        return render_with_pe

    # Fallback: use system fonts (Noto Color Emoji on Linux, Segoe UI Emoji on Windows)
    # If neither supports color emojis the characters may still render monochrome.
    try:
        # prefer Noto Color Emoji (common on Linux)
        emoji_font = pygame.font.SysFont("Noto Color Emoji", int(cell_size * 0.9))
    except Exception:
        try:
            emoji_font = pygame.font.SysFont("Segoe UI Emoji", int(cell_size * 0.9))
        except Exception:
            emoji_font = pygame.font.SysFont(None, int(cell_size * 0.9))

    def render_with_font(char, size):
        try:
            surf = emoji_font.render(char, True, (255, 255, 255))
            if surf.get_width() != size or surf.get_height() != size:
                surf = pygame.transform.smoothscale(surf, (size, size))
            return surf
        except Exception:
            # final fallback: small colored circle surface
            tmp = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(tmp, (255, 120, 120), (size//2, size//2), size//2 - 2)
            return tmp

    return render_with_font

# --- Main game class ----------------------------------------------------
class SnakeGame:
    def __init__(self, screen, skin_idx=0, legendary_unlocked=False):
        pygame.init()
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        self.grid_width = max(4, self.screen_width // GRID_SIZE)
        self.grid_height = max(4, (self.screen_height - 60) // GRID_SIZE)

        self.font = pygame.font.SysFont("Consolas", 24)
        self.big_font = pygame.font.SysFont("Consolas", 48, bold=True)
        self.button_font = pygame.font.SysFont("Consolas", 32)

        # emoji renderer (robust)
        self.render_emoji = _make_emoji_renderer(GRID_SIZE)

        self.clock = pygame.time.Clock()
        self.highscore = self.load_highscore()
        self.state = "menu"
        self.skin_idx = max(0, min(skin_idx, len(SKINS)-1))
        self.legendary_unlocked = legendary_unlocked
        self.achievements = load_achievements()

        # UI rects (populated by draw_menu / draw_gameover / draw_pause)
        self.start_btn_rect = None
        self.exit_btn_rect = None
        self.skin_btn_rects = []
        self.restart_btn_rect = None
        self.menu_btn_rect = None
        self.exit_btn_rect = None
        self.resume_btn_rect = None

        # Ensure music tries to run (menu usually sets it, but handle direct run too)
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            if not pygame.mixer.music.get_busy():
                if os.path.exists("music1.mp3"):
                    pygame.mixer.music.load("music1.mp3")
                    pygame.mixer.music.set_volume(0.4)
                    pygame.mixer.music.play(-1)
        except Exception:
            pass

    # --- Game control methods ---
    def start_game(self):
        self.direction = "RIGHT"
        mid_y = max(2, self.grid_height // 2)
        self.snake = [(5, mid_y), (4, mid_y), (3, mid_y)]
        self.food = self.create_food()
        self.score = 0
        self.state = "game"
        self.last_move_time = time.time()
        self.speed = BASE_SPEED

    def restart_game(self):
        self.start_game()

    def exit_game(self):
        pygame.quit()
        sys.exit()

    def return_to_menu(self):
        self.state = "menu"

    def pause_game(self):
        self.state = "pause"

    def resume_game(self):
        self.state = "game"

    def change_direction(self, key):
        opposites = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
        if key in opposites and key != opposites[self.direction]:
            self.direction = key

    def move(self):
        head_x, head_y = self.snake[0]
        dx, dy = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}[self.direction]
        new_head = (head_x + dx, head_y + dy)

        if (new_head in self.snake or
            new_head[0] < 0 or new_head[0] >= self.grid_width or
            new_head[1] < 0 or new_head[1] >= self.grid_height):
            self.state = "gameover"
            return

        self.snake.insert(0, new_head)

        if new_head == self.food[0]:
            self.score += 1
            if self.score > self.highscore:
                self.highscore = self.score
                self.save_highscore()
                self.check_achievements(self.highscore)
            self.food = self.create_food()
            self.speed = BASE_SPEED + (self.score // 10) * SPEED_INCREMENT
        else:
            self.snake.pop()

    # --- Drawing methods ---
    def draw(self):
        self.screen.fill((40, 40, 40))
        # Draw play area border
        pygame.draw.rect(self.screen, (200, 200, 200), (0, 60, self.screen_width, self.screen_height-60), 2)

        skin = SKINS[self.skin_idx]
        t = time.time()
        for i, (x, y) in enumerate(self.snake):
            if self.skin_idx == 4 and self.legendary_unlocked:  # Legendary rainbow effect
                color = get_rainbow_color(i, t)
                for glow in range(12, 0, -4):
                    glow_color = (min(255, color[0]+80), min(255, color[1]+80), min(255, color[2]+80))
                    glow_rect = pygame.Rect(x*GRID_SIZE-glow//2, y*GRID_SIZE+60-glow//2, GRID_SIZE+glow, GRID_SIZE+glow)
                    pygame.draw.rect(self.screen, glow_color, glow_rect, border_radius=GRID_SIZE//2)
                pygame.draw.rect(self.screen, color, (x*GRID_SIZE, y*GRID_SIZE+60, GRID_SIZE, GRID_SIZE), border_radius=GRID_SIZE//2)
            else:
                color = skin["head"] if i == 0 else skin["body"]
                pygame.draw.rect(self.screen, color, (x*GRID_SIZE, y*GRID_SIZE+60, GRID_SIZE, GRID_SIZE), border_radius=8)

        # Draw food (emoji) with robust renderer
        fx, fy = self.food[0]
        emoji = self.food[1]
        try:
            emoji_surf = self.render_emoji(emoji, GRID_SIZE)
            # ensure correct size
            if emoji_surf.get_size() != (GRID_SIZE, GRID_SIZE):
                emoji_surf = pygame.transform.smoothscale(emoji_surf, (GRID_SIZE, GRID_SIZE))
            self.screen.blit(emoji_surf, (fx*GRID_SIZE, fy*GRID_SIZE+60))
        except Exception:
            # fallback: plain circle
            pygame.draw.circle(self.screen, (255, 120, 120),
                               (fx*GRID_SIZE + GRID_SIZE//2, fy*GRID_SIZE + 60 + GRID_SIZE//2),
                               GRID_SIZE//2 - 2)

        # Draw score bar
        pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, self.screen_width, 60))
        score_text = self.font.render(f"Score: {getattr(self,'score',0)}    Highscore: {self.highscore}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))

    def draw_menu(self):
        self.screen.fill((40, 40, 40))
        title = self.big_font.render("Snake Game", True, (0, 200, 0))
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 120))

        # Buttons
        start_btn = self.button_font.render("Start", True, (255, 255, 255))
        exit_btn = self.button_font.render("Exit", True, (200, 0, 0))

        self.start_btn_rect = start_btn.get_rect(center=(self.screen_width // 2, 300))
        self.exit_btn_rect = exit_btn.get_rect(center=(self.screen_width // 2, 360))

        self.screen.blit(start_btn, self.start_btn_rect)
        self.screen.blit(exit_btn, self.exit_btn_rect)

        # Skin selection
        skin_text = self.font.render("Choose Snake Skin:", True, (255,255,255))
        self.screen.blit(skin_text, (self.screen_width // 2 - skin_text.get_width() // 2, 180))

        # Build visible skins (skip legendary if locked)
        visible_indices = []
        self.skin_btn_rects = []
        x_start = self.screen_width // 2 - 180
        spacing = 120
        idx_offset = 0
        for idx, skin in enumerate(SKINS):
            if idx == 4 and not self.legendary_unlocked:
                continue
            visible_indices.append(idx)
            btn = self.button_font.render(skin["name"], True, (0,0,0))
            rect = btn.get_rect(center=(self.screen_width // 2 - 180 + idx_offset*spacing, 240))
            # selected highlight: invert background
            btn_bg = (200,200,200) if idx == self.skin_idx else skin["head"]
            pygame.draw.rect(self.screen, btn_bg, pygame.Rect(rect.left-20, rect.top-10, rect.width+40, rect.height+20), border_radius=12)
            self.screen.blit(btn, rect)
            # color preview
            pygame.draw.rect(self.screen, skin["head"], (rect.centerx-30, rect.centery+30, 60, 12), border_radius=6)
            pygame.draw.rect(self.screen, skin["body"], (rect.centerx-30, rect.centery+44, 60, 8), border_radius=4)
            self.skin_btn_rects.append((rect, idx))  # store tuple (rect, actual_skin_index)
            idx_offset += 1

    def draw_gameover(self):
        self.draw()
        over_text = self.big_font.render("GAME OVER", True, (255, 255, 255))
        self.screen.blit(over_text, (self.screen_width // 2 - over_text.get_width() // 2, 120))

        restart_btn = self.button_font.render("Restart", True, (0, 200, 0))
        menu_btn = self.button_font.render("Menu", True, (0, 150, 200))
        exit_btn = self.button_font.render("Exit", True, (200, 0, 0))

        self.restart_btn_rect = restart_btn.get_rect(center=(self.screen_width // 2, 300))
        self.menu_btn_rect = menu_btn.get_rect(center=(self.screen_width // 2, 360))
        self.exit_btn_rect = exit_btn.get_rect(center=(self.screen_width // 2, 420))

        self.screen.blit(restart_btn, self.restart_btn_rect)
        self.screen.blit(menu_btn, self.menu_btn_rect)
        self.screen.blit(exit_btn, self.exit_btn_rect)

    def draw_pause(self):
        self.draw()
        pause_text = self.big_font.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(pause_text, (self.screen_width // 2 - pause_text.get_width() // 2, 120))

        resume_btn = self.button_font.render("Resume", True, (0, 200, 0))
        menu_btn = self.button_font.render("Menu", True, (0, 150, 200))
        exit_btn = self.button_font.render("Exit", True, (200, 0, 0))

        self.resume_btn_rect = resume_btn.get_rect(center=(self.screen_width // 2, 300))
        self.menu_btn_rect = menu_btn.get_rect(center=(self.screen_width // 2, 360))
        self.exit_btn_rect = exit_btn.get_rect(center=(self.screen_width // 2, 420))

        self.screen.blit(resume_btn, self.resume_btn_rect)
        self.screen.blit(menu_btn, self.menu_btn_rect)
        self.screen.blit(exit_btn, self.exit_btn_rect)

    # --- Persistence ------------------------------------------------------
    def save_highscore(self):
        try:
            with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
                json.dump({"highscore": self.highscore}, f)
        except Exception:
            pass

    def load_highscore(self):
        if os.path.exists(HIGHSCORE_FILE):
            try:
                with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f).get("highscore", 0)
            except Exception:
                return 0
        return 0

    def check_achievements(self, score):
        unlocked = set(self.achievements)
        for threshold in ACHIEVEMENT_THRESHOLDS:
            if score >= threshold and threshold not in unlocked:
                unlocked.add(threshold)
        if unlocked != self.achievements:
            self.achievements = unlocked
            save_achievements(self.achievements)

    # --- Gameplay helpers -----------------------------------------------
    def create_food(self):
        while True:
            x = random.randint(0, self.grid_width-1)
            y = random.randint(0, self.grid_height-1)
            if not hasattr(self, "snake") or (x, y) not in self.snake:
                emoji = random.choice(FOODS)
                return ((x, y), emoji)

    # --- Main loop -------------------------------------------------------
    def run(self):
        self.start_game()
        while True:
            self.clock.tick(100)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit_game()
                elif event.type == pygame.KEYDOWN:
                    if self.state == "game":
                        if event.key == pygame.K_UP:
                            self.change_direction("UP")
                        elif event.key == pygame.K_DOWN:
                            self.change_direction("DOWN")
                        elif event.key == pygame.K_LEFT:
                            self.change_direction("LEFT")
                        elif event.key == pygame.K_RIGHT:
                            self.change_direction("RIGHT")
                        elif event.key == pygame.K_ESCAPE:
                            self.pause_game()
                    elif self.state == "pause":
                        if event.key == pygame.K_ESCAPE:
                            self.resume_game()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if self.state == "menu":
                        # skin buttons: stored as (rect, actual_skin_index)
                        for rect, actual_idx in self.skin_btn_rects:
                            if rect.collidepoint(mx, my):
                                self.skin_idx = actual_idx
                        if self.start_btn_rect and self.start_btn_rect.collidepoint(mx, my):
                            self.start_game()
                        elif self.exit_btn_rect and self.exit_btn_rect.collidepoint(mx, my):
                            self.exit_game()
                    elif self.state == "gameover":
                        if self.restart_btn_rect and self.restart_btn_rect.collidepoint(mx, my):
                            self.restart_game()
                        elif self.menu_btn_rect and self.menu_btn_rect.collidepoint(mx, my):
                            return  # <-- Return to caller (menu.py)
                        elif self.exit_btn_rect and self.exit_btn_rect.collidepoint(mx, my):
                            self.exit_game()
                    elif self.state == "pause":
                        if self.resume_btn_rect and self.resume_btn_rect.collidepoint(mx, my):
                            self.resume_game()
                        elif self.menu_btn_rect and self.menu_btn_rect.collidepoint(mx, my):
                            return
                        elif self.exit_btn_rect and self.exit_btn_rect.collidepoint(mx, my):
                            self.exit_game()

            # State updates + drawing
            if self.state == "menu":
                self.draw_menu()
            elif self.state == "game":
                now = time.time()
                move_interval = 1.0 / self.speed
                if now - getattr(self, "last_move_time", 0) >= move_interval:
                    self.move()
                    self.last_move_time = now
                self.draw()
            elif self.state == "gameover":
                self.draw_gameover()
            elif self.state == "pause":
                self.draw_pause()

            pygame.display.flip()


# If run directly, allow testing the game by itself (fullscreen)
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    try:
        pygame.mixer.init()
        if os.path.exists("music1.mp3"):
            pygame.mixer.music.load("music1.mp3")
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(-1)
    except Exception:
        pass
    SnakeGame(screen).run()
