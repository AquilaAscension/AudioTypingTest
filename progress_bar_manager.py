from tkinter import ttk

class ProgressBarManager:
    def __init__(self, root, tts_manager):
        self.root = root
        self.tts_manager = tts_manager
        self.update_interval = 100
        self.progress_value = 0
        self.timer_id = None
        self.is_paused = True

        self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.grid(row=0, column=1, pady=10, sticky="s")
        self.progress_bar["maximum"] = 100

        self.update_audio_duration()

    def update_audio_duration(self, speed=1.0):
        base_duration = self.tts_manager.getTTSDuration()
        self.audio_duration = base_duration / speed if speed > 0 else base_duration
        if self.audio_duration > 0:
            self.increment = 100 / (self.audio_duration * 1000 / self.update_interval)
        else:
            self.increment = 0


    def update_progress_bar(self):
        if not self.is_paused and self.progress_value < 100:
            self.progress_value += self.increment
            self.progress_bar["value"] = self.progress_value
            self.timer_id = self.root.after(self.update_interval, self.update_progress_bar)

    def start_progress_bar(self, speed=1.0):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.progress_value = 0
        self.progress_bar["value"] = 0
        self.is_paused = False
        self.update_audio_duration(speed)
        self.update_progress_bar()

    def reset_progress_bar(self):
        self.progress_bar.grid()
        self.start_progress_bar()

    def hide_progress_bar(self):
        self.progress_bar.grid_remove()

    def pause_progress_bar(self):
        self.is_paused = True

    def resume_progress_bar(self):
        self.is_paused = False
        self.update_progress_bar()
