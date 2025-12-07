import os
import sys
import shutil
import subprocess
import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import butter, lfilter

try:
    from piper import PiperVoice
except ImportError:
    PiperVoice = None

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
        self.typingText = ""
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
        self.distortion_enabled = False
        self._clean_audio = None

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
        self.model_path, self.config_path = self._resolve_voice_paths(model_basename)

        self._piper_cmd = self._find_piper_cmd()
        self._embedded_voice = None
        self._use_embedded_voice = False
        self._init_embedded_voice()

    # helpers 
    def _resource_root(self):
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

    def _find_piper_cmd(self):
        exe = shutil.which("piper")
        if exe:
            return [exe]
        # Fallback if not on PATH:
        return [sys.executable, "-m", "piper"]

    def _resolve_voice_paths(self, model_basename):
        model_path = os.path.join(self.voices_dir, model_basename)
        config_path = model_path + ".json"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Missing Piper model: {model_path}")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Missing Piper config (.json): {config_path}")
        return model_path, config_path

    def _init_embedded_voice(self):
        if PiperVoice is None:
            return
        try:
            with open(self.model_path, "rb") as model_file, open(self.config_path, "r", encoding="utf-8") as config_file:
                self._embedded_voice = PiperVoice.load(model_file, config_file)
            self._use_embedded_voice = True
        except Exception:
            self._embedded_voice = None
            self._use_embedded_voice = False

    def _synthesize_with_cli(self, input_text, eff_scale):
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

    def _synthesize_with_embedded(self, input_text, eff_scale):
        if self._embedded_voice is None:
            raise RuntimeError("Embedded Piper voice unavailable.")
        with open(self.wav_file, "wb") as wav_file:
            self._embedded_voice.synthesize(
                input_text,
                wav_file,
                length_scale=eff_scale
            )

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

    def set_voice_model(self, model_basename: str):
        model_path, config_path = self._resolve_voice_paths(model_basename)
        if model_path == self.model_path:
            return

        # Stop any active playback before swapping voices
        self.pauseTTS()
        if self.stream:
            try:
                self.stream.stop()
            except Exception:
                pass
            try:
                self.stream.close()
            except Exception:
                pass
            self.stream = None

        self.model_path = model_path
        self.config_path = config_path
        self._embedded_voice = None
        self._use_embedded_voice = False
        self._init_embedded_voice()

        # Force re-synthesis on next play
        self.audio_data = None
        self.sample_rate = None
        self.position = 0
        self.is_armed = False
        self._clean_audio = None
        self._last_synth_scale = None
        self.TTSDuration = 0.0

    def TTSGenerate(self, input_text: str, length_scale: float | None = None):
        self.typingText = input_text  # keep for later re-synthesis if speed changes
        eff_scale = self.piper_length_scale if length_scale is None else float(length_scale)

        if self._use_embedded_voice:
            self._synthesize_with_embedded(input_text, eff_scale)
        else:
            self._synthesize_with_cli(input_text, eff_scale)

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
        data = self._soften_audio(data)
        self._clean_audio = data.copy()
        data = self._apply_distortion(data, sr)
        self.audio_data = data.astype(np.float32)
        self.sample_rate = sr
        self.position = 0
        if self.sample_rate and len(self.audio_data):
            self.TTSDuration = len(self.audio_data) / float(self.sample_rate)

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

    def _soften_audio(self, data):
        if data.size == 0:
            return data
        peak = np.max(np.abs(data))
        if peak > 0:
            data = data / max(peak / 0.9, 1.0)
        softened = np.tanh(data * 0.85)
        kernel = np.array([0.2, 0.6, 0.2], dtype=np.float32)
        return np.convolve(softened, kernel, mode="same")

    def _apply_distortion(self, data, sample_rate):
        if not self.distortion_enabled or sample_rate is None or sample_rate <= 0:
            return data
        try:
            nyquist = sample_rate * 0.5
            low = max(300.0 / nyquist, 0.0001)
            high = min(3400.0 / nyquist, 0.99)
            if low >= high:
                return data
            b, a = butter(4, [low, high], btype="band")
            filtered = lfilter(b, a, data)
        except Exception:
            filtered = data
        crushed = np.tanh(filtered * 1.3)
        combined = crushed
        return np.clip(combined, -1.0, 1.0)

    def set_distortion_enabled(self, enabled):
        self.distortion_enabled = bool(enabled)
        if self._clean_audio is not None and self.sample_rate:
            processed = self._apply_distortion(self._clean_audio.copy(), self.sample_rate)
            self.audio_data = processed.astype(np.float32)
            if self.stream is None:
                self.position = 0
