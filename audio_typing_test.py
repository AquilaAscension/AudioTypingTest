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
import csv
import json
import hashlib
import shutil

ROAD_VARIATIONS = {
    "street": ["street", "st", "st."],
    "avenue": ["avenue", "ave", "ave."],
    "road": ["road", "rd", "rd."],
    "boulevard": ["boulevard", "blvd", "blvd."],
    "drive": ["drive", "dr", "dr."],
    "lane": ["lane", "ln", "ln."],
    "court": ["court", "ct", "ct."],
    "terrace": ["terrace", "ter", "ter.", "terr"],
    "place": ["place", "pl", "pl."],
    "square": ["square", "sq", "sq."],
    "highway": ["highway", "hwy", "hwy."],
    "parkway": ["parkway", "pkwy", "pkwy."],
    "circle": ["circle", "cir", "cir."],
    "trail": ["trail", "trl", "trl."],
    "way": ["way", "wy", "wy."]
}

from tts_manager import TTSManager
from text_manager import TextManager
from progress_bar_manager import ProgressBarManager

class AudioTypingTest:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Typing Test")

        root.tk.call("source", "azure.tcl")
        root.tk.call("set_theme", "dark")

        self.details_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Details")
        os.makedirs(self.details_dir, exist_ok=True)
        self.generations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Generations")
        os.makedirs(self.generations_dir, exist_ok=True)
        self.current_detail_key = None
        self.current_file_key = None
        self.current_details = []
        self.details_dialog_open = False
        self.pending_file_loaded_message = False

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}")

        self.setup_ui()
        self.tts_manager = TTSManager()
        self.tts_from_file = False
        self.progress_bar_manager = ProgressBarManager(self.root, self.tts_manager)
        self.text_manager = TextManager(self.root)
        self.text_manager.typing_box.bind("<KeyRelease>", self.on_typing)
        self.text_manager.typing_box.bind("<KeyPress>", self.start_timer_if_needed)
        self.start_time = None
        self.timer_id = None  # For scheduling timer updates
        self.road_variant_map = self.build_road_variant_map()
        self.update_distortion_setting()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

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
        self.distortion_on = ttk.Radiobutton(
            self.sidebar,
            text="On",
            variable=self.distortion_status,
            value="on_distortion",
            command=self.update_distortion_setting
        )
        self.distortion_on.grid(row=2, column=0, padx=10, pady=0, sticky="ew")
        self.distortion_off = ttk.Radiobutton(
            self.sidebar,
            text="Off",
            variable=self.distortion_status,
            value="off_distortion",
            command=self.update_distortion_setting
        )
        self.distortion_off.grid(row=3, column=0, padx=10, pady=0, sticky="ew")
        self.distortion_status.set("off_distortion")

        self.show_text_box_label = tk.Label(self.sidebar, text="Show Text Box:", font=("Times New Roman", 12))
        self.show_text_box_label.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

        self.text_box_status = tk.StringVar()
        self.text_box_on = ttk.Radiobutton(self.sidebar, text="Yes", variable=self.text_box_status, value="on_text_box")
        self.text_box_on.grid(row=5, column=0, padx=10, pady=0, sticky="ew")
        self.text_box_off = ttk.Radiobutton(self.sidebar, text="No", variable=self.text_box_status, value="off_text_box")
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

        self.highlight_on = ttk.Radiobutton(self.sidebar, text="Yes", variable=self.highlight_var, value="on_highlight")
        self.highlight_on.grid(row=16, column=0, padx=10, sticky="w")

        self.highlight_off = ttk.Radiobutton(self.sidebar, text="No", variable=self.highlight_var, value="off_highlight")
        self.highlight_off.grid(row=17, column=0, padx=10, sticky="w")

    def on_close(self):
        # Stop timers/UI loops
        self.stop_timer_display()
        self.progress_bar_manager.reset_progress_bar()

        # Stop audio stream cleanly
        try:
            self.tts_manager.pauseTTS()
            if self.tts_manager.stream:
                try:
                    self.tts_manager.stream.stop()
                except Exception:
                    pass
                try:
                    self.tts_manager.stream.close()
                except Exception:
                    pass
        except Exception:
            pass

        # Delete synthesized files
        try:
            self.tts_manager.deleteTTSFile()
        except Exception:
            pass

        # Close the window
        self.root.destroy()

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
            if self.text_box_status.get() == "on_text_box":
                self.text_manager.clear_text()  # Do not insert the answer

            self.start_time = None

            file_key = self.get_file_key(file_path)
            self.current_file_key = file_key
            generation_path = self.get_generation_path(file_key)

            if os.path.isfile(generation_path):
                reuse_audio = messagebox.askyesno(
                    "Existing Audio Found",
                    "Audio for this document already exists.\n"
                    "Select Yes to reuse it or No to regenerate."
                )
                if reuse_audio and self.load_existing_generation(generation_path, text_content):
                    self.handle_details_for_file(file_key, text_content)
                    return

            self.generate_tts_in_background(text_content, save_key=file_key)
            self.handle_details_for_file(file_key, text_content)

        except Exception as e:
            messagebox.showerror("Error", f"Could not load file:\n{str(e)}")

    def get_file_key(self, file_path):
        abs_path = os.path.abspath(file_path)
        return hashlib.sha256(abs_path.encode("utf-8")).hexdigest()

    def get_generation_path(self, file_key):
        return os.path.join(self.generations_dir, f"{file_key}.wav")

    def load_existing_generation(self, generation_path, text_content):
        try:
            shutil.copy2(generation_path, self.tts_manager.wav_file)
            self.tts_manager.typingText = text_content
            self.tts_manager._last_text = text_content
            target_scale = self.tts_manager._to_piper_scale(self.speed_var.get())
            self.tts_manager._last_synth_scale = target_scale
            self.tts_manager.load_audio()
            self.tts_manager.is_armed = True
            self.tts_manager.is_paused = False
            self.progress_bar_manager.update_audio_duration(speed=self.speed_var.get())
            messagebox.showinfo("Audio Loaded", "Existing audio has been loaded for this document.")
            return True
        except Exception as exc:
            messagebox.showerror("Audio Error", f"Failed to load saved audio:\n{exc}\nA new version will be generated.")
            return False

    def handle_details_for_file(self, file_key, text_content):
        self.current_detail_key = file_key
        details_path = os.path.join(self.details_dir, f"{file_key}.json")
        saved_details = self.load_saved_details(details_path)

        if saved_details:
            reuse_saved = messagebox.askyesno(
                "Saved Details Detected",
                "Previously saved details were found for this file.\n"
                "Select Yes to reuse them or No to choose new details."
            )
            if reuse_saved:
                self.current_details = saved_details
                return

        selection = self.show_details_selection_dialog(text_content, saved_details or [])
        if selection is None:
            self.current_details = saved_details or []
            return

        self.current_details = selection
        self.save_details(details_path, selection)

    def update_distortion_setting(self):
        enabled = self.distortion_status.get() == "on_distortion"
        if hasattr(self, "tts_manager"):
            self.tts_manager.set_distortion_enabled(enabled)

    def try_show_file_loaded_message(self):
        if self.pending_file_loaded_message and not self.details_dialog_open and getattr(self, "tts_from_file", False):
            self.pending_file_loaded_message = False
            messagebox.showinfo("File Loaded", "The file has been successfully loaded for the typing test.")

    def load_saved_details(self, details_path):
        if os.path.isfile(details_path):
            try:
                with open(details_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                return data.get("details", [])
            except Exception:
                return []
        return []

    def save_details(self, details_path, details):
        payload = {
            "details": details,
            "saved_at": time.time()
        }
        with open(details_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)

    def show_details_selection_dialog(self, text_content, initial_details):
        self.details_dialog_open = True
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Important Details")
        dialog.geometry("800x600")
        dialog.grab_set()
        dialog.transient(self.root)

        instructions = tk.Label(
            dialog,
            text="Highlight text below and click 'Add Detail' to track it during grading.",
            font=("Arial", 12)
        )
        instructions.pack(pady=(10, 5))

        text_frame = tk.Frame(dialog)
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)

        text_widget = tk.Text(text_frame, wrap="word", height=15)
        text_widget.insert("1.0", text_content)
        text_widget.pack(side="left", fill="both", expand=True)
        text_widget.bind("<Key>", lambda event: "break")

        text_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_scroll.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=text_scroll.set)

        list_label = tk.Label(dialog, text="Selected Details:", font=("Arial", 11))
        list_label.pack(pady=(10, 0))

        listbox = tk.Listbox(dialog, height=6)
        listbox.pack(fill="x", padx=10)

        details = [detail for detail in initial_details if detail.strip()]
        for detail in details:
            listbox.insert("end", detail)

        button_frame = tk.Frame(dialog)
        button_frame.pack(fill="x", pady=10)

        def add_detail():
            try:
                selection = text_widget.get("sel.first", "sel.last").strip()
            except tk.TclError:
                selection = ""
            cleaned = " ".join(selection.split())
            if cleaned and cleaned not in details:
                details.append(cleaned)
                listbox.insert("end", cleaned)

        def remove_detail():
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                detail = listbox.get(index)
                details.remove(detail)
                listbox.delete(index)

        def clear_all_details():
            if details:
                details.clear()
                listbox.delete(0, "end")

        result = {"value": None}

        def confirm():
            result["value"] = details.copy()
            dialog.destroy()

        def cancel():
            result["value"] = None
            dialog.destroy()

        add_button = tk.Button(button_frame, text="Add Detail", command=add_detail)
        add_button.pack(side="left", padx=5)

        remove_button = tk.Button(button_frame, text="Remove Detail", command=remove_detail)
        remove_button.pack(side="left", padx=5)

        clear_button = tk.Button(button_frame, text="Clear All", command=clear_all_details)
        clear_button.pack(side="left", padx=5)

        spacer = tk.Frame(button_frame)
        spacer.pack(side="left", expand=True)

        save_button = tk.Button(button_frame, text="Save Details", command=confirm)
        save_button.pack(side="right", padx=5)

        cancel_button = tk.Button(button_frame, text="Cancel", command=cancel)
        cancel_button.pack(side="right", padx=5)

        dialog.protocol("WM_DELETE_WINDOW", cancel)
        try:
            dialog.wait_window()
        finally:
            self.details_dialog_open = False
        self.try_show_file_loaded_message()
        return result["value"]

    def build_road_variant_map(self):
        mapping = {}
        for canonical, variants in ROAD_VARIATIONS.items():
            for variant in variants:
                mapping[variant.lower()] = canonical
        return mapping

    def normalize_words(self, text):
        cleaned = re.sub(r'[^\w\s]', ' ', text).lower().split()
        return [self.road_variant_map.get(word, word) for word in cleaned]

    def normalize_text_for_matching(self, text):
        return " ".join(self.normalize_words(text))

    def submit_text(self):
        self.stop_timer_display()
        user_text = self.text_manager.get_text()
        reference = self.tts_manager.getTypingText()
        word_count = len(user_text.split())
        elapsed_time = time.time() - self.start_time if self.start_time else 1
        wpm = word_count / (elapsed_time / 60) if elapsed_time > 0 else 0

        accuracy = self.calculate_word_accuracy(user_text, reference)
        details_score = self.calculate_details_score(user_text)
        details_text = f"{details_score:.2f}" if details_score is not None else "N/A"

        results = (
            f"You typed {word_count} words.\n"
            f"Words per Minute: {wpm:.2f}\n"
            f"Accuracy: {accuracy:.2f}\n"
            f"Details: {details_text}"
        )
        self.progress_bar_manager.hide_progress_bar()
        self.text_manager.show_results(results)
        self.text_manager.highlight_submission_errors(self.tts_manager.getTypingText())
        username = self.username_value.get().strip() or "Guest"
        self.save_score_to_csv(username, wpm, accuracy, details_score)
        messagebox.showinfo("Score Saved", f"Results saved for {username}.")
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
        if not self.tts_manager.getTypingText().strip():
            messagebox.showwarning("No Document Loaded", "Please load a document before starting the audio.")
            return

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
            self.pending_file_loaded_message = True
            self.try_show_file_loaded_message()

    def generate_tts_in_background(self, text, save_key=None):
        def task():
            self.tts_manager.TTSGenerate(text)
            self.tts_manager.prepareTTS(speed=self.speed_var.get())
            if save_key:
                self.save_generation_copy(save_key)
            self.root.after(0, self.on_tts_ready)

        self.show_loading_window("Generating TTS...")
        threading.Thread(target=task, daemon=True).start()

    def save_generation_copy(self, file_key):
        try:
            target = self.get_generation_path(file_key)
            shutil.copy2(self.tts_manager.wav_file, target)
        except Exception:
            pass

    def on_typing(self, event):
        user_input = self.text_manager.get_text()
        reference = self.tts_manager.getTypingText()
        highlight_enabled = self.highlight_var.get() == "on_highlight"
        self.text_manager.highlight_typing_progress(user_input, reference, highlight_enabled)

    def calculate_word_accuracy(self, user_text, reference_text):
        user_words = self.normalize_words(user_text)
        reference_words = self.normalize_words(reference_text)

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

    def calculate_details_score(self, user_text):
        details = [detail for detail in self.current_details if detail.strip()]
        if not details:
            return None

        user_normalized = self.normalize_text_for_matching(user_text)
        matches = 0
        for detail in details:
            normalized_detail = self.normalize_text_for_matching(detail)
            if normalized_detail and normalized_detail in user_normalized:
                matches += 1
        return (matches / len(details)) * 100
    
    def save_score_to_csv(self, username, wpm, accuracy, details_score):
        filename = "typing_test_scores.csv"
        header = ["Username", "WPM", "Accuracy (%)", "Details (%)", "Timestamp"]
        file_exists = os.path.isfile(filename)

        if file_exists:
            self.ensure_details_column(filename, header)

        with open(filename, mode="a", newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(header)

            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            details_value = f"{details_score:.2f}" if details_score is not None else "N/A"
            writer.writerow([username, f"{wpm:.2f}", f"{accuracy:.2f}", details_value, timestamp])

    def ensure_details_column(self, filename, header):
        try:
            with open(filename, mode="r", newline='', encoding='utf-8') as file:
                rows = list(csv.reader(file))
        except Exception:
            return

        if not rows:
            with open(filename, mode="w", newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(header)
            return

        if "Details (%)" in rows[0]:
            return

        try:
            timestamp_index = rows[0].index("Timestamp")
        except ValueError:
            timestamp_index = len(rows[0])

        updated_rows = [header]
        for row in rows[1:]:
            existing = row[:]
            while len(existing) < len(rows[0]):
                existing.append("")
            existing.insert(timestamp_index, "N/A")
            updated_rows.append(existing)

        with open(filename, mode="w", newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(updated_rows)


    
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
