import os
import sys
import shutil
import subprocess
import numpy as np
import sounddevice as sd
import soundfile as sf

class TTSManager:
    def __init__(self,
                 filename='TypingTTS.wav',
                 voices_dir=None,
                 model_basename='en_US-libritts-high.onnx',
                 piper_length_scale=1.0,
                 use_synth_speed=True,
                 invert_ui_speed=True
                 ):
        self.filename = filename
        self.wav_file = filename
        self.typingText = "This is example text. I just witnessed a robbery at the bank downtown! It's at 123 Main St. The robber had a black ski mask and a red backpack. He ran north on 1st Avenue towards the park."
        self.TTSDuration = 0.0

        self.piper_length_scale = float(piper_length_scale)
        self.use_synth_speed = bool(use_synth_speed)
        self.invert_ui_speed = bool(invert_ui_speed)

        self.audio_data = None
        self.sample_rate = None
        self.stream = None
        self.is_paused = False
        self.position = 0
        self.playback_thread = None
        self.is_armed = False

        # Track last synthesis so we can re-synthesize if speed changes
        self._last_text = None
        self._last_synth_scale = None  # this stores the last *Piper* length_scale used

        base_dir = self._resource_root()
        self.voices_dir = voices_dir or os.path.join(base_dir, "voices")
        if not os.path.isdir(self.voices_dir):
            raise FileNotFoundError(
                f"Voices folder not found: {self.voices_dir}\n"
                f"Create it and place <voice>.onnx + <voice>.onnx.json inside."
            )
        self.model_path = os.path.join(self.voices_dir, model_basename)
        self.config_path = self.model_path + ".json"
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Missing Piper model: {self.model_path}")
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Missing Piper config (.json): {self.config_path}")

        self._piper_cmd = self._find_piper_cmd()

    # helpers 
    def _resource_root(self):
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

    def _find_piper_cmd(self):
        exe = shutil.which("piper")
        if exe:
            return [exe]
        # Fallback if not on PATH:
        return [sys.executable, "-m", "piper"]

    def _to_piper_scale(self, ui_speed: float) -> float:
        s = max(float(ui_speed), 1e-6)  # guard against zero/negatives
        return (1.0 / s) if self.invert_ui_speed else s

    def get_progress_percent(self) -> float:
        if self.audio_data is None:
            return 0.0
        total = len(self.audio_data)
        if total <= 0:
            return 0.0
        # position is advanced in the sounddevice callback; this is safe to read
        pct = 100.0 * (self.position / total)
        if pct < 0.0: pct = 0.0
        if pct > 100.0: pct = 100.0
        return pct

    def getTypingText(self):
        return self.typingText

    def getTTSDuration(self):
        return self.TTSDuration

    def deleteTTSFile(self):
        for f in [self.filename, self.wav_file]:
            if os.path.exists(f):
                os.remove(f)

    def TTSGenerate(self, input_text: str, length_scale: float | None = None):
        self.typingText = input_text  # keep for later re-synthesis if speed changes
        eff_scale = self.piper_length_scale if length_scale is None else float(length_scale)

        cmd = (
            self._piper_cmd
            + ["--model", self.model_path,
               "--config", self.config_path,
               "--output_file", self.wav_file]
        )
        if eff_scale != 1.0:
            cmd += ["--length_scale", str(eff_scale)]

        completed = subprocess.run(
            cmd,
            input=input_text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Piper synthesis failed:\n"
                f"CMD: {' '.join(cmd)}\n"
                f"STDERR:\n{completed.stderr.decode(errors='ignore')}"
            )

        # update last-synth (store the actual Piper scale used)
        self._last_text = input_text
        self._last_synth_scale = eff_scale

        # update duration
        info = sf.info(self.wav_file)
        self.TTSDuration = float(info.frames) / float(info.samplerate)

    def load_audio(self):
        data, sr = sf.read(self.wav_file, dtype="float32")
        if data.ndim > 1:
            data = np.mean(data, axis=1)  # mono
        self.audio_data = data.astype(np.float32)
        self.sample_rate = sr
        self.position = 0

    def play_callback(self, outdata, frames, time_info, status):
        if self.is_paused or self.audio_data is None:
            outdata[:] = np.zeros((frames, 1), dtype=np.float32)
            return
        end = min(self.position + frames, len(self.audio_data))
        chunk = self.audio_data[self.position:end]
        out_frames = np.zeros((frames, 1), dtype=np.float32)
        out_frames[:len(chunk), 0] = chunk
        outdata[:] = out_frames
        self.position += frames
        if self.position >= len(self.audio_data):
            self.is_armed = False
            raise sd.CallbackStop

    def playTTS(self, speed=1.0):
        if not self.is_armed:
            self.prepareTTS(speed)
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=self.play_callback
        )
        self.is_paused = False
        self.stream.start()

    def pauseTTS(self):
        self.is_paused = True

    def resumeTTS(self):
        if self.stream:
            self.is_paused = False

    def prepareTTS(self, speed=1.0):
        if self.use_synth_speed:
            target_scale = self._to_piper_scale(speed)  # map UI scale to Piper scale
            if self._last_synth_scale is None or abs(target_scale - self._last_synth_scale) > 1e-6:
                text = self._last_text or self.typingText
                self.TTSGenerate(text, length_scale=target_scale)

        self.load_audio()
        self.is_armed = True