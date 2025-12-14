import tkinter as tk
import re


class TextManager:
    def __init__(self, root, palette, fonts):
        self.root = root
        self.palette = palette
        self.fonts = fonts
        self.root.configure(bg=self.palette["bg"])

        header = tk.Frame(self.root, bg=self.palette["bg"])
        header.pack(fill="x", pady=(0, 8))

        self.results_label = tk.Label(header, text="", font=self.fonts["display"], fg=self.palette["accent"], bg=self.palette["bg"])
        self.results_label.pack(side="left")
        self.results_label.pack_forget()

        self.timer_label = tk.Label(header, text="Time: 0.0s", font=self.fonts["caption"], fg=self.palette["muted"], bg=self.palette["bg"])
        self.timer_label.pack(side="right")
        self.timer_label.pack_forget()

        text_shell = tk.Frame(self.root, bg=self.palette["bg"])
        text_shell.pack(fill="both", expand=True)

        text_container = tk.Frame(text_shell, bg=self.palette["bg"])
        text_container.pack(fill="both", expand=True, padx=2, pady=2)
        shadow_dark = tk.Frame(text_container, bg=self.palette["shadow_dark"], bd=0, highlightthickness=0)
        shadow_dark.place(relx=0, rely=0, relwidth=1, relheight=1, x=8, y=8)
        shadow_light = tk.Frame(text_container, bg=self.palette["shadow_light"], bd=0, highlightthickness=0)
        shadow_light.place(relx=0, rely=0, relwidth=1, relheight=1, x=-4, y=-4)

        self.text_frame = tk.Frame(
            text_container,
            bg=self.palette["sunken"],
            bd=0,
            relief="flat",
            highlightthickness=0
        )
        self.text_frame.pack(fill="both", expand=True, padx=6, pady=6)

        self.typing_box = tk.Text(
            self.text_frame,
            height=12,
            width=50,
            font=self.fonts["mono"],
            bg=self.palette["sunken"],
            fg=self.palette["text"],
            insertbackground=self.palette["accent"],
            selectbackground=self.palette["accent_soft"],
            selectforeground=self.palette["bg"],
            relief="flat",
            bd=0,
            padx=4,
            pady=4,
            highlightthickness=0
        )
        self.typing_box.pack(fill="both", expand=True, padx=8, pady=8)

        self.typing_box.tag_configure("correct", foreground=self.palette["text"])
        self.typing_box.tag_configure("incorrect", foreground=self.palette["danger"])

    def get_text(self):
        return self.typing_box.get("1.0", "end-1c")

    def clear_text(self):
        self.typing_box.delete("1.0", "end")

    def show_results(self, results):
        self.results_label.config(text=results)
        self.results_label.pack(side="left")

    def hide_results(self):
        self.results_label.pack_forget()

    def show_timer(self):
        self.timer_label.pack(side="right")

    def hide_timer(self):
        self.timer_label.pack_forget()

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

        self.typing_box.tag_config("error", background=self.palette["accent_soft"])
