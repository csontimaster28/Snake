import pygame
import pygame_emojis
import random
import json
import os
import sys
import time
import math

GRID_SIZE = 32
BASE_SPEED = 8.0
SPEED_INCREMENT = 2.0
HIGHSCORE_FILE = "highscore.json"

SKINS = [
    {"name": "Classic", "head": (0, 200, 0), "body": (0, 150, 0)},
    {"name": "Blue", "head": (0, 120, 255), "body": (0, 80, 180)},
    {"name": "Red", "head": (220, 40, 40), "body": (180, 0, 0)},
    {"name": "Yellow", "head": (255, 220, 0), "body": (200, 180, 0)},
    {"name": "White", "head": (255,255,255), "body": (255,255,255)}, # Placeholder
]

FOODS = ["🍏", "🍎"]

def get_rainbow_color(i, t):
    # i: segment index, t: time
    freq = 0.3
    r = int(128 + 127 * math.sin(freq * i + t))
    g = int(128 + 127 * math.sin(freq * i + t + 2))
    b = int(128 + 127 * math.sin(freq * i + t + 4))
    return (r, g, b)

class SnakeGame:
    def __init__(self, screen, skin_idx=0, legendary_unlocked=False):
        pygame.init()
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        self.grid_width = self.screen_width // GRID_SIZE
        self.grid_height = (self.screen_height - 60) // GRID_SIZE
        self.font = pygame.font.SysFont("Consolas", 24)
        self.big_font = pygame.font.SysFont("Consolas", 48, bold=True)
        self.button_font = pygame.font.SysFont("Consolas", 32)
        self.emoji_font = pygame.font.SysFont("Noto Color Emoji", int(GRID_SIZE * 0.8))
        self.clock = pygame.time.Clock()
        self.highscore = self.load_highscore()
        self.state = "menu"
        self.skin_idx = skin_idx
        self.legendary_unlocked = legendary_unlocked

    def start_game(self):
        self.direction = "RIGHT"
        self.snake = [(5, self.grid_height // 2), (4, self.grid_height // 2), (3, self.grid_height // 2)]
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
            self.food = self.create_food()
            self.speed = BASE_SPEED + (self.score // 10) * SPEED_INCREMENT
        else:
            self.snake.pop()

    def draw(self):
        self.screen.fill((40, 40, 40))
        # Draw play area border
        pygame.draw.rect(self.screen, (200, 200, 200), (0, 60, self.screen_width, self.screen_height-60), 2)
        skin = SKINS[self.skin_idx]
        t = time.time()
        for i, (x, y) in enumerate(self.snake):
            if self.skin_idx == 4 and self.legendary_unlocked:  # Legendary
                color = get_rainbow_color(i, t)
                # Glow effect: draw blurred rect behind
                for glow in range(12, 0, -4):
                    glow_color = (min(255, color[0]+80), min(255, color[1]+80), min(255, color[2]+80))
                    glow_rect = pygame.Rect(x*GRID_SIZE-glow//2, y*GRID_SIZE+60-glow//2, GRID_SIZE+glow, GRID_SIZE+glow)
                    pygame.draw.rect(self.screen, glow_color, glow_rect, border_radius=GRID_SIZE//2)
                pygame.draw.rect(self.screen, color, (x*GRID_SIZE, y*GRID_SIZE+60, GRID_SIZE, GRID_SIZE), border_radius=GRID_SIZE//2)
            else:
                color = skin["head"] if i == 0 else skin["body"]
                pygame.draw.rect(self.screen, color, (x*GRID_SIZE, y*GRID_SIZE+60, GRID_SIZE, GRID_SIZE), border_radius=8)
        # Draw food (emoji)
        fx, fy = self.food[0]
        emoji = self.food[1]
        emoji_surf = self.emoji_font.render(emoji, True, (255, 255, 255))
        # Scale emoji to fit exactly in the grid cell
        emoji_surf = pygame.transform.smoothscale(emoji_surf, (GRID_SIZE, GRID_SIZE))
        self.screen.blit(emoji_surf, (fx*GRID_SIZE, fy*GRID_SIZE+60))
        # Draw score bar
        pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, self.screen_width, 60))
        score_text = self.font.render(f"Score: {self.score}    Highscore: {self.highscore}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))

    def draw_menu(self):
        self.screen.fill((40, 40, 40))
        title = self.big_font.render("Snake Game", True, (0, 200, 0))
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 120))

        start_btn = self.button_font.render("Start", True, (255, 255, 255))
        exit_btn = self.button_font.render("Exit", True, (200, 0, 0))

        self.start_btn_rect = start_btn.get_rect(center=(self.screen_width // 2, 300))
        self.exit_btn_rect = exit_btn.get_rect(center=(self.screen_width // 2, 360))

        self.screen.blit(start_btn, self.start_btn_rect)
        self.screen.blit(exit_btn, self.exit_btn_rect)

        # Skin selection
        skin_text = self.font.render("Choose Snake Skin:", True, (255,255,255))
        self.screen.blit(skin_text, (self.screen_width // 2 - skin_text.get_width() // 2, 180))
        self.skin_btn_rects = []
        for idx, skin in enumerate(SKINS):
            if idx == 4 and not self.legendary_unlocked:
                continue  # Skip legendary skin if not unlocked
            btn = self.button_font.render(skin["name"], True, skin["head"])
            rect = btn.get_rect(center=(self.screen_width // 2 - 180 + idx*120, 240))
            self.screen.blit(btn, rect)
            self.skin_btn_rects.append(rect)
            # Draw color preview
            pygame.draw.rect(self.screen, skin["head"], (rect.centerx-30, rect.centery+30, 60, 12), border_radius=6)
            pygame.draw.rect(self.screen, skin["body"], (rect.centerx-30, rect.centery+44, 60, 8), border_radius=4)
        # Highlight selected skin
        sel_rect = self.skin_btn_rects[self.skin_idx]
        pygame.draw.rect(self.screen, (255,255,255), sel_rect, 2)

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

    def save_highscore(self):
        try:
            with open(HIGHSCORE_FILE, "w") as f:
                json.dump({"highscore": self.highscore}, f)
        except:
            pass

    def load_highscore(self):
        if os.path.exists(HIGHSCORE_FILE):
            try:
                with open(HIGHSCORE_FILE, "r") as f:
                    return json.load(f).get("highscore", 0)
            except:
                return 0
        return 0

    def create_food(self):
        while True:
            x = random.randint(0, self.grid_width-1)
            y = random.randint(0, self.grid_height-1)
            if (x, y) not in self.snake:
                emoji = random.choice(FOODS)
                return ((x, y), emoji)

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
                        for idx, rect in enumerate(self.skin_btn_rects):
                            if rect.collidepoint(mx, my):
                                self.skin_idx = idx
                        if self.start_btn_rect.collidepoint(mx, my):
                            self.start_game()
                        elif self.exit_btn_rect.collidepoint(mx, my):
                            self.exit_game()
                    elif self.state == "gameover":
                        if self.restart_btn_rect.collidepoint(mx, my):
                            self.restart_game()
                        elif self.menu_btn_rect.collidepoint(mx, my):
                            return  # <-- Return to caller (menu.py)
                        elif self.exit_btn_rect.collidepoint(mx, my):
                            self.exit_game()
                    elif self.state == "pause":
                        if self.resume_btn_rect.collidepoint(mx, my):
                            self.resume_game()
                        elif self.menu_btn_rect.collidepoint(mx, my):
                            return  # <-- Return to caller (menu.py)
                        elif self.exit_btn_rect.collidepoint(mx, my):
                            self.exit_game()

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

if __name__ == "__main__":
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    SnakeGame(screen).run()
