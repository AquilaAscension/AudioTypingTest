import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import docx
import PyPDF2
import time
import os
import threading
import re

from tts_manager import TTSManager
from text_manager import TextManager
from progress_bar_manager import ProgressBarManager

class AudioTypingTest:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Typing Test")

        root.tk.call("source", "azure.tcl")
        root.tk.call("set_theme", "dark")

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}")

        self.setup_ui()
        self.tts_manager = TTSManager()
        self.tts_from_file = False
        self.generate_tts_in_background(self.tts_manager.getTypingText())
        self.progress_bar_manager = ProgressBarManager(self.root, self.tts_manager)
        self.text_manager = TextManager(self.root)
        self.text_manager.typing_box.bind("<KeyRelease>", self.on_typing)
        self.text_manager.typing_box.bind("<KeyPress>", self.start_timer_if_needed)
        self.start_time = None
        self.timer_id = None  # For scheduling timer updates

    def setup_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=3)
        self.root.columnconfigure(2, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=4)
        self.root.rowconfigure(2, weight=1)

        tk.Label(self.root, text="Audio Typing Test", font=("Times New Roman", 16, "bold")).grid(row=0, column=1, pady=10, sticky="n")

        self.sidebar = tk.Frame(self.root, width=500, bd=1 , relief="raised")
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsw")

        self.settings_label = tk.Label(self.sidebar, text='Settings', font=("Times New Roman", 14))
        self.settings_label.grid(row=0, column=0, padx=10, pady=10, sticky="new")

        self.distortion_label = tk.Label(self.sidebar, text='Distortion:', font=("Times New Roman", 12))
        self.distortion_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.distortion_status = tk.StringVar()
        self.distortion_on = tk.Radiobutton(self.sidebar, text="On", variable=self.distortion_status, value="on_distortion")
        self.distortion_on.grid(row=2, column=0, padx=10, pady=0, sticky="ew")
        self.distortion_off = tk.Radiobutton(self.sidebar, text="Off", variable=self.distortion_status, value="off_distortion")
        self.distortion_off.grid(row=3, column=0, padx=10, pady=0, sticky="ew")
        self.distortion_status.set("off_distortion")

        self.show_text_box_label = tk.Label(self.sidebar, text="Show Text Box:", font=("Times New Roman", 12))
        self.show_text_box_label.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

        self.text_box_status = tk.StringVar()
        self.text_box_on = tk.Radiobutton(self.sidebar, text="Yes", variable=self.text_box_status, value="on_text_box")
        self.text_box_on.grid(row=5, column=0, padx=10, pady=0, sticky="ew")
        self.text_box_off = tk.Radiobutton(self.sidebar, text="No", variable=self.text_box_status, value="off_text_box")
        self.text_box_off.grid(row=6, column=0, padx=10, pady=0, sticky="ew")
        self.text_box_status.set("on_text_box")

        self.username_label = tk.Label(self.sidebar, text="Username:")
        self.username_label.grid(row=7, column=0, padx=10, pady=10, sticky="esw")
        self.username_value = tk.StringVar()
        self.username_entry = tk.Entry(self.sidebar, textvariable=self.username_value)
        self.username_entry.grid(row=8, column=0, padx=10, pady=0, sticky="esw")

        self.password_label = tk.Label(self.sidebar, text="Password:")
        self.password_label.grid(row=9, column=0, padx=10, pady=10, sticky="esw")
        self.password_value = tk.StringVar()
        self.password_entry = tk.Entry(self.sidebar, textvariable=self.password_value, show="*")
        self.password_entry.grid(row=10, column=0, padx=10, pady=0, sticky="esw")

        self.sign_in_button = tk.Button(self.sidebar, text="Sign In", command=self.sign_in)
        self.sign_in_button.grid(row=11, column=0, padx=10, pady=0, sticky="esw")

        self.load_file_button = tk.Button(self.sidebar, text="Load File for TTS", command=self.load_file_for_tts)
        self.load_file_button.grid(row=12, column=0, padx=10, pady=10, sticky="ew")

        self.submit_button = tk.Button(self.root, text="Submit", command=self.submit_text)
        self.submit_button.grid(row=2, column=2, padx=10, pady=10, sticky="w")

        self.discard_button = tk.Button(self.root, text="Discard", command=self.discard_text)
        self.discard_button.grid(row=2, column=2, padx=10, pady=10, sticky="e")

        self.pause_button = tk.Button(self.root, text="⏸", font=("Arial", 14), command=self.pause_progress_bar)
        self.pause_button.grid(row=0, column=2, padx=10, pady=10, sticky="e")

        self.play_button = tk.Button(self.root, text="▶", font=("Arial", 14), command=self.resume_progress_bar)
        self.play_button.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        self.speed_label = tk.Label(self.sidebar, text='TTS Speed:', font=("Times New Roman", 12))
        self.speed_label.grid(row=13, column=0, padx=10, pady=(20, 0), sticky="w")

        self.speed_var = tk.DoubleVar(value=1.0)  # Default speed = 1.0
        self.speed_slider = tk.Scale(self.sidebar, from_=0.5, to=2.0, resolution=0.1,
                                    orient="horizontal", variable=self.speed_var,
                                    length=200)
        self.speed_slider.grid(row=14, column=0, padx=10, pady=5, sticky="ew")

        self.highlight_label = tk.Label(self.sidebar, text="Show Spelling Errors:", font=("Times New Roman", 12))
        self.highlight_label.grid(row=15, column=0, padx=10, pady=(20, 0), sticky="w")

        self.highlight_var = tk.StringVar(value="off_highlight")  # Default = OFF

        self.highlight_on = tk.Radiobutton(self.sidebar, text="Yes", variable=self.highlight_var, value="on_highlight")
        self.highlight_on.grid(row=16, column=0, padx=10, sticky="w")

        self.highlight_off = tk.Radiobutton(self.sidebar, text="No", variable=self.highlight_var, value="off_highlight")
        self.highlight_off.grid(row=17, column=0, padx=10, sticky="w")


    def sign_in(self):
        return "0"

    def load_file_for_tts(self):
        file_path = filedialog.askopenfilename(
            title="Select a Text Document",
            filetypes=[
                ("All Supported", "*.txt *.docx *.pdf"),
                ("Text Files", "*.txt"),
                ("Word Documents", "*.docx"),
                ("PDF Files", "*.pdf")
            ]
        )

        if not file_path:
            return

        text_content = ""

        try:
            if file_path.endswith(".txt"):
                with open(file_path, 'r', encoding='utf-8') as file:
                    text_content = file.read()
            elif file_path.endswith(".docx"):
                doc = docx.Document(file_path)
                text_content = "\n".join(p.text for p in doc.paragraphs)
            elif file_path.endswith(".pdf"):
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text_content = "\n".join(p.extract_text() for p in reader.pages if p.extract_text())

            self.tts_manager.typingText = text_content
            self.tts_from_file = True
            self.generate_tts_in_background(text_content)
            self.progress_bar_manager.update_audio_duration()

            if self.text_box_status.get() == "on_text_box":
                self.text_manager.clear_text()  # Do not insert the answer

            self.start_time = None

        except Exception as e:
            messagebox.showerror("Error", f"Could not load file:\n{str(e)}")

    def submit_text(self):
        self.stop_timer_display()
        user_text = self.text_manager.get_text()
        reference = self.tts_manager.getTypingText()
        word_count = len(user_text.split())
        elapsed_time = time.time() - self.start_time if self.start_time else 1
        wpm = word_count / (elapsed_time / 60) if elapsed_time > 0 else 0

        accuracy = self.calculate_word_accuracy(user_text, reference)

        results = f"You typed {word_count} words.\nWords per Minute: {wpm:.2f}\nAccuracy: {accuracy:.2f}"
        self.progress_bar_manager.hide_progress_bar()
        self.text_manager.show_results(results)
        self.text_manager.highlight_submission_errors(self.tts_manager.getTypingText())
        self.root.after(5000, self.reset_ui)

    def reset_ui(self):
        self.text_manager.typing_box.tag_remove("error", "1.0", "end")
        self.text_manager.hide_results()
        self.text_manager.clear_text()
        self.progress_bar_manager.reset_progress_bar()
        self.start_time = None

    def discard_text(self):
        self.stop_timer_display()
        self.text_manager.clear_text()
        self.start_time = None

    def pause_progress_bar(self):
        self.tts_manager.pauseTTS()
        self.progress_bar_manager.pause_progress_bar()

    def resume_progress_bar(self):
        speed = self.speed_var.get()

        if self.tts_manager.is_paused:
            self.tts_manager.resumeTTS()
            self.progress_bar_manager.resume_progress_bar()
        else:
            if not self.tts_manager.is_armed:
                self.tts_manager.prepareTTS(speed=speed)

            self.tts_manager.playTTS(speed=speed)
            self.progress_bar_manager.start_progress_bar(speed=speed)

    def show_loading_window(self, message="Generating TTS..."):
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("Please Wait")
        self.loading_window.geometry("300x100")
        self.loading_window.resizable(False, False)
        self.loading_window.grab_set()
        self.loading_window.transient(self.root)

        label = tk.Label(self.loading_window, text=message, font=("Arial", 12))
        label.pack(pady=10)

        progress = ttk.Progressbar(self.loading_window, mode='indeterminate', length=200)
        progress.pack(pady=10)
        progress.start()
        
        self.loading_window.update()

    def hide_loading_window(self):
        if hasattr(self, "loading_window") and self.loading_window.winfo_exists():
            self.loading_window.destroy()

    def on_tts_ready(self):
        self.hide_loading_window()
        self.progress_bar_manager.update_audio_duration(speed=self.speed_var.get())

        if getattr(self, "tts_from_file", False):
            messagebox.showinfo("File Loaded", "The file has been successfully loaded for the typing test.")

    def generate_tts_in_background(self, text):
        def task():
            self.tts_manager.TTSGenerate(text)
            self.tts_manager.prepareTTS(speed=self.speed_var.get())
            self.root.after(0, self.on_tts_ready)

        self.show_loading_window("Generating TTS...")
        threading.Thread(target=task, daemon=True).start()

    def on_typing(self, event):
        user_input = self.text_manager.get_text()
        reference = self.tts_manager.getTypingText()
        highlight_enabled = self.highlight_var.get() == "on_highlight"
        self.text_manager.highlight_typing_progress(user_input, reference, highlight_enabled)

    def calculate_word_accuracy(self, user_text, reference_text):
        def normalize(text):
            return re.sub(r'[^\w\s]', '', text).lower().split()

        user_words = normalize(user_text)
        reference_words = normalize(reference_text)

        # Word-level Levenshtein distance
        def levenshtein(seq1, seq2):
            m, n = len(seq1), len(seq2)
            dp = [[0] * (n+1) for _ in range(m+1)]

            for i in range(m+1):
                dp[i][0] = i
            for j in range(n+1):
                dp[0][j] = j

            for i in range(1, m+1):
                for j in range(1, n+1):
                    cost = 0 if seq1[i-1] == seq2[j-1] else 1
                    dp[i][j] = min(
                        dp[i-1][j] + 1,     # deletion
                        dp[i][j-1] + 1,     # insertion
                        dp[i-1][j-1] + cost # substitution
                    )
            return dp[m][n]

        distance = levenshtein(user_words, reference_words)
        total = max(len(reference_words), len(user_words), 1)  # avoid div by zero
        accuracy = (1 - distance / total) * 100
        return accuracy

    
    def start_timer_display(self):
        if self.timer_id is None:
            self.text_manager.timer_label.grid()
            self.update_timer_display()

    def update_timer_display(self):
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.text_manager.timer_label.config(text=f"Time: {elapsed:.1f}s")
            self.timer_id = self.root.after(500, self.update_timer_display)

    def stop_timer_display(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        self.text_manager.timer_label.grid_remove()


    def start_timer_if_needed(self, event=None):
        if self.start_time is None:
            self.start_time = time.time()
            self.start_timer_display()
