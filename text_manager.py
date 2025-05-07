import tkinter as tk
import re

class TextManager:
    def __init__(self, root):
        self.root = root
        self.typing_box = tk.Text(root, height=10, width=50, font=("Arial", 14))
        self.typing_box.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.results_label = tk.Label(root, text="", font=("Arial", 24, "bold"), fg="blue")
        self.results_label.grid(row=0, column=1, pady=10, sticky="s")
        self.results_label.grid_remove()

        self.typing_box.tag_configure("correct", foreground="black")
        self.typing_box.tag_configure("incorrect", foreground="red")

        self.timer_label = tk.Label(self.root, text="Time: 0.0s", font=("Arial", 16, "bold"), fg="black")
        self.timer_label.grid(row=0, column=1, sticky="e", padx=20)
        self.timer_label.grid_remove()  # Hide initially



    def get_text(self):
        return self.typing_box.get("1.0", "end-1c")

    def clear_text(self):
        self.typing_box.delete("1.0", "end")

    def show_results(self, results):
        self.results_label.config(text=results)
        self.results_label.grid()

    def hide_results(self):
        self.results_label.grid_remove()

    def highlight_typing_progress(self, user_text, reference_text, highlight_enabled=True):
        if not highlight_enabled:
            return
        
        def normalize(text):
            return re.sub(r'\s+', '', re.sub(r'[^\w\s]', '', text)).lower()

        norm_user = normalize(user_text)
        norm_ref = normalize(reference_text)

        self.typing_box.tag_remove("correct", "1.0", "end")
        self.typing_box.tag_remove("incorrect", "1.0", "end")

        i = 0  # index in normalized ref
        cursor = 0  # index in raw user_text
        mistake_found = False

        while cursor < len(user_text) and i < len(norm_ref):
            char = user_text[cursor]
            if not char.isalnum():
                cursor += 1
                continue

            tag = "correct" if not mistake_found and char.lower() == norm_ref[i] else "incorrect"
            if char.lower() != norm_ref[i]:
                mistake_found = True

            start = f"1.0 + {cursor} chars"
            end = f"1.0 + {cursor+1} chars"
            self.typing_box.tag_add(tag, start, end)

            cursor += 1
            i += 1

    def highlight_submission_errors(self, reference_text):
        self.typing_box.tag_remove("error", "1.0", "end")

        user_words = self.get_text().split()
        reference_words = reference_text.split()

        # Apply error highlighting word by word
        index = 0  # character index from start of text

        for i, user_word in enumerate(user_words):
            start_idx = f"1.0+{index}c"
            end_idx = f"1.0+{index + len(user_word)}c"

            if i >= len(reference_words) or user_word.lower().strip(".,!?") != reference_words[i].lower().strip(".,!?"):
                self.typing_box.tag_add("error", start_idx, end_idx)

            index += len(user_word) + 1  # move to next word (includes the space)

        self.typing_box.tag_config("error", background="#ffcccc")  # light red

