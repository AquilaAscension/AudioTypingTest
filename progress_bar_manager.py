# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 echoType

from tkinter import ttk


class ProgressBarManager:
    def __init__(
        self,
        root,
        tts_manager,
        update_interval_ms: int = 100,
        use_stream_progress: bool = True,
        bar_container=None,
        style_name: str = "Horizontal.TProgressbar"
    ):
        self.root = root
        self.parent = bar_container or root
        self.tts_manager = tts_manager
        self.update_interval = int(update_interval_ms)
        self.use_stream_progress = bool(use_stream_progress)

        self.progress_value = 0.0
        self.timer_id = None
        self.is_paused = True
        self.on_complete = None

        try:
            self.parent.columnconfigure(0, weight=1)
        except Exception:
            pass

        self.progress_bar = ttk.Progressbar(self.parent, orient="horizontal", mode="determinate", style=style_name)
        self.progress_bar.grid(row=0, column=0, pady=6, sticky="ew")
        self.progress_bar["maximum"] = 100

        self.audio_duration = 0.0   # seconds
        self.increment = 0.0        # % per tick (fallback)
        self.update_audio_duration()

    def update_audio_duration(self, speed=1.0):
        base_duration = float(self.tts_manager.getTTSDuration() or 0.0)

        # If the TTS pipeline uses synth-time speed, the WAV on disk already encodes the final duration; do not divide by speed again.
        if getattr(self.tts_manager, "use_synth_speed", False):
            self.audio_duration = base_duration
        else:
            self.audio_duration = base_duration / speed if speed > 0 else base_duration

        # Increment is only used when not using stream driven progress
        ticks = (self.audio_duration * 1000.0) / max(self.update_interval, 1)
        self.increment = 100.0 / ticks if ticks > 0 else 0.0

    def set_on_complete(self, callback):
        self.on_complete = callback

    def _finish_progress(self):
        self.is_paused = True
        self.timer_id = None
        if self.progress_value < 100.0 and self._is_complete():
            self.progress_value = 100.0
        self.progress_value = min(max(self.progress_value, 0.0), 100.0)
        self.progress_bar["value"] = self.progress_value
        if callable(self.on_complete):
            self.on_complete()

    def _is_complete(self):
        if self.progress_value >= 99.9:
            return True
        return bool(getattr(self.tts_manager, "playback_finished", False))

    def _tick_stream_driven(self):
        if self.is_paused:
            self.timer_id = None
            return
        self.progress_value = float(self.tts_manager.get_progress_percent())
        self.progress_bar["value"] = self.progress_value

        if self._is_complete():
            self._finish_progress()
        else:
            self.timer_id = self.root.after(self.update_interval, self._tick_stream_driven)

    def _tick_time_driven(self):
        if self.is_paused:
            self.timer_id = None
            return

        if self.progress_value < 100.0:
            self.progress_value += self.increment
            self.progress_bar["value"] = self.progress_value

        if self._is_complete():
            self._finish_progress()
        else:
            self.timer_id = self.root.after(self.update_interval, self._tick_time_driven)

    def start_progress_bar(self, speed=1.0):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

        # Reset visuals
        self.progress_value = 0.0
        self.progress_bar["value"] = 0.0
        self.is_paused = False

        # Always refresh duration (used for display or fallback calc)
        self.update_audio_duration(speed)

        # Prefer stream-driven sync if available
        if self.use_stream_progress and hasattr(self.tts_manager, "get_progress_percent"):
            self.timer_id = self.root.after(self.update_interval, self._tick_stream_driven)
        else:
            self.timer_id = self.root.after(self.update_interval, self._tick_time_driven)

    def reset_progress_bar(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        self.progress_value = 0.0
        self.progress_bar["value"] = 0.0
        self.is_paused = True
        self.progress_bar.grid()

    def hide_progress_bar(self):
        self.progress_bar.grid_remove()

    def pause_progress_bar(self):
        self.is_paused = True

    def resume_progress_bar(self):
        if self.is_paused and self.progress_value < 100.0:
            self.is_paused = False
            # resume appropriate ticking mode
            if self.use_stream_progress and hasattr(self.tts_manager, "get_progress_percent"):
                self._tick_stream_driven()
            else:
                self._tick_time_driven()
