import tkinter as tk
from game import SnakeGame

def show_menu(root):  # <-- root paraméter
    def start_game():
        for widget in root.winfo_children():
            widget.destroy()
        SnakeGame(root, on_exit=lambda: show_menu(root))  # <-- fontos: root továbbadása

    root.title("Snake Game Menü")
    root.attributes("-fullscreen", True)
    for widget in root.winfo_children():
        widget.destroy()

    canvas = tk.Canvas(root, bg="black")
    canvas.pack(fill="both", expand=True)

    title = tk.Label(root, text="🐍 Snake Game", fg="lime", bg="black", font=("Consolas", 48))
    title.place(relx=0.5, rely=0.3, anchor="center")

    start_btn = tk.Button(root, text="Start", command=start_game,
                          font=("Consolas", 24), bg="black", fg="white", relief="ridge")
    exit_btn = tk.Button(root, text="Exit", command=root.destroy,
                         font=("Consolas", 24), bg="black", fg="red", relief="ridge")

    start_btn.place(relx=0.5, rely=0.5, anchor="center")
    exit_btn.place(relx=0.5, rely=0.6, anchor="center")

# csak közvetlen futtatáskor hozza létre a root ablakot
if __name__ == "__main__":
    root = tk.Tk()
    show_menu(root)
    root.mainloop()
