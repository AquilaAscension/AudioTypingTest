import tkinter as tk

class TextManager:
    def __init__(self, root):
        self.root = root
        self.typing_box = tk.Text(root, height=10, width=50, font=("Arial", 14))
        self.typing_box.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.results_label = tk.Label(root, text="", font=("Arial", 24, "bold"), fg="blue")
        self.results_label.grid(row=0, column=1, pady=10, sticky="s")
        self.results_label.grid_remove()

    def get_text(self):
        return self.typing_box.get("1.0", "end-1c")

    def clear_text(self):
        self.typing_box.delete("1.0", "end")

    def show_results(self, results):
        self.results_label.config(text=results)
        self.results_label.grid()

    def hide_results(self):
        self.results_label.grid_remove()
