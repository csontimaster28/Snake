import tkinter as tk
import random
import json
import os
import time

SIZE = 20
DELAY = 8
MOVE_INTERVAL = 6
HIGHSCORE_FILE = "highscore.json"

class SnakeGame:
    def __init__(self, root, on_exit=None):
        self.root = root
        self.on_exit = on_exit

        self.root.attributes("-fullscreen", True)
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()

        self.canvas = tk.Canvas(root, width=self.screen_width, height=self.screen_height, bg="black", highlightthickness=0)
        self.canvas.pack()

        self.score = 0
        self.highscore = self.load_highscore()

        self.score_text = self.canvas.create_text(10, 10, anchor="nw", fill="white", font=("Consolas", 20),
                                                  text=f"Score: 0    Highscore: {self.highscore}")

        self.restart_button = tk.Button(root, text="Restart", command=self.restart_game,
                                        bg="black", fg="lime", font=("Consolas", 18))
        self.exit_button = tk.Button(root, text="Exit", command=self.exit_game,
                                     bg="black", fg="red", font=("Consolas", 18))
        self.menu_button_gameover = tk.Button(root, text="Menu", command=self.return_to_menu,
                                              bg="black", fg="cyan", font=("Consolas", 18))

        self.pause_frame = tk.Frame(root, bg="black")
        self.resume_button = tk.Button(self.pause_frame, text="Resume", command=self.resume_game,
                                       bg="black", fg="lime", font=("Consolas", 18))
        self.menu_button_pause = tk.Button(self.pause_frame, text="Menu", command=self.return_to_menu,
                                           bg="black", fg="cyan", font=("Consolas", 18))
        self.exit_button2 = tk.Button(self.pause_frame, text="Exit", command=self.exit_game,
                                      bg="black", fg="red", font=("Consolas", 18))

        self.root.bind("<KeyPress>", self.change_direction)

        self.active_powerup = None
        self.powerup_effect_until = 0
        self.powerups = []
        self.paused = False

        self.start_game()

    def start_game(self):
        self.direction = "Right"
        self.snake = [(100, 100), (80, 100), (60, 100)]
        self.food = self.create_food()
        self.score = 0
        self.running = True
        self.frame_count = 0
        self.update_score()
        self.powerups.clear()
        self.active_powerup = None
        self.powerup_effect_until = 0

        self.restart_button.place_forget()
        self.exit_button.place_forget()
        self.menu_button_gameover.place_forget()
        self.pause_frame.place_forget()

        self.update()

    def restart_game(self):
        self.canvas.delete("all")
        self.score_text = self.canvas.create_text(10, 10, anchor="nw", fill="white", font=("Consolas", 20),
                                                  text=f"Score: 0    Highscore: {self.highscore}")
        self.start_game()

    def exit_game(self):
        self.root.destroy()

    def return_to_menu(self):
        self.running = False
        self.paused = False
        self.canvas.destroy()
        self.pause_frame.place_forget()
        if self.on_exit:
            self.on_exit()

    def pause_game(self):
        self.paused = True
        self.pause_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.resume_button.pack(pady=5)
        self.menu_button_pause.pack(pady=5)
        self.exit_button2.pack(pady=5)

    def resume_game(self):
        self.paused = False
        self.pause_frame.place_forget()
        self.resume_button.pack_forget()
        self.menu_button_pause.pack_forget()
        self.exit_button2.pack_forget()
        self.update()

    def change_direction(self, event):
        key = event.keysym
        opposites = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
        if key in opposites and key != opposites[self.direction]:
            self.direction = key
        elif key == "Escape":
            if self.paused:
                self.resume_game()
            else:
                self.pause_game()

    def move(self):
        head_x, head_y = self.snake[0]
        dx, dy = {"Up": (0, -SIZE), "Down": (0, SIZE), "Left": (-SIZE, 0), "Right": (SIZE, 0)}[self.direction]
        new_head = (head_x + dx, head_y + dy)

        if (new_head in self.snake or
            new_head[0] < 0 or new_head[0] >= self.screen_width or
            new_head[1] < 0 or new_head[1] >= self.screen_height):
            self.running = False
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.score += 2 if self.active_powerup == "double" else 1
            if self.score > self.highscore:
                self.highscore = self.score
                self.save_highscore()
            self.food = self.create_food()
            self.update_score()
        else:
            self.snake.pop()

        # Powerup felszedés
        for p in self.powerups:
            if new_head == p["pos"]:
                self.active_powerup = p["type"]
                self.powerup_effect_until = time.time() + 5
                self.powerups.remove(p)
                break

        # Powerup spawn (ha nincs kint és pont osztható 10-zel)
        if self.score % 10 == 0 and not self.powerups:
            self.spawn_powerup()

    def draw(self):
        self.canvas.delete("snake", "food", "powerup")
        for (x, y) in self.snake:
            self.canvas.create_rectangle(x, y, x + SIZE, y + SIZE, fill="green", outline="", tags="snake")
        fx, fy = self.food
        self.canvas.create_oval(fx, fy, fx + SIZE, fy + SIZE, fill="red", outline="", tags="food")

        for p in self.powerups:
            x, y = p["pos"]
            color = "cyan" if p["type"] == "slow" else "lime"
            symbol = "🐢" if p["type"] == "slow" else "🍀"
            self.canvas.create_text(x + SIZE // 2, y + SIZE // 2, text=symbol, fill=color,
                                    font=("Consolas", SIZE), tags="powerup")

    def update(self):
        if self.paused:
            return

        if time.time() > self.powerup_effect_until:
            self.active_powerup = None

        interval = MOVE_INTERVAL + 4 if self.active_powerup == "slow" else MOVE_INTERVAL

        if self.running:
            self.frame_count += 1
            if self.frame_count % interval == 0:
                self.move()
            self.draw()
            self.root.after(DELAY, self.update)
        else:
            self.canvas.create_text(self.screen_width // 2, self.screen_height // 2 - 40,
                                    text="GAME OVER", fill="white", font=("Consolas", 48))
            self.restart_button.place(relx=0.5, rely=0.6, anchor="center")
            self.menu_button_gameover.place(relx=0.5, rely=0.7, anchor="center")
            self.exit_button.place(relx=0.5, rely=0.8, anchor="center")

    def update_score(self):
        self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}    Highscore: {self.highscore}")

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
            x = random.randint(0, (self.screen_width - SIZE) // SIZE) * SIZE
            y = random.randint(0, (self.screen_height - SIZE) // SIZE) * SIZE
            if (x, y) not in self.snake:
                return (x, y)

    def spawn_powerup(self):
        types = ["slow", "double"]
        ptype = random.choice(types)
        while True:
            x = random.randint(0, (self.screen_width - SIZE) // SIZE) * SIZE
            y = random.randint(0, (self.screen_height - SIZE) // SIZE) * SIZE
            if (x, y) not in self.snake and (x, y) != self.food:
                self.powerups.append({"type": ptype, "pos": (x, y)})
                break
