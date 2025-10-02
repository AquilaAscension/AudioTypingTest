from __future__ import annotations
from pathlib import Path
import io
import os
import numpy as np
import soundfile as sf

# Optional: if we add espeak-ng
_ESPEAK_PORTABLE_ACTIVATED = False
_ESPEAK_DLL_HANDLE = None

def _activate_portable_espeak():
    global _ESPEAK_PORTABLE_ACTIVATED, _ESPEAK_DLL_HANDLE
    if _ESPEAK_PORTABLE_ACTIVATED:
        return

    base = Path(__file__).resolve().parents[1] / "tools" / "espeak-portable" / "x64"
    data = base / "espeak-ng-data"
    if not base.exists():
        return

    if data.exists():
        os.environ.setdefault("ESPEAK_DATA_PATH", str(data))

    if hasattr(os, "add_dll_directory"):
        _ESPEAK_DLL_HANDLE = os.add_dll_directory(str(base))  # keep ref alive
    else:
        os.environ["PATH"] = str(base) + os.pathsep + os.environ.get("PATH", "")

    _ESPEAK_PORTABLE_ACTIVATED = True



# Initialize Kokoro lazily to avoid import cost during app startup
_pipeline = None

def _get_pipeline(lang_code: str):
    global _pipeline
    from kokoro import KPipeline
    if _pipeline is None:
        _pipeline = KPipeline(lang_code=lang_code)
    return _pipeline

class kTTS:

    def __init__(self, text: str, lang: str = "en", voice: str = "af_bella", speed: float = 1.0):
        # optional: enable portable espeak-ng if present
        _activate_portable_espeak()

        self.text = text
        self.lang = lang
        self.voice = voice
        self.speed = float(speed)

        # map ISO-ish 'en' to Kokoro's family code
        self.lang_code = "a" if (lang or "en").lower().startswith("en") else "a"

    def save(self, out_path: str | Path, sample_rate: int = 24000):
        pipe = _get_pipeline(self.lang_code)

        # Split long text by blank lines; tweak split_pattern as needed
        gen = pipe(self.text, voice=self.voice, speed=self.speed, split_pattern=r"\n+")
        chunks = [audio for _, _, audio in gen]
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)

        out_path = Path(out_path)
        ext = out_path.suffix.lower()

        if ext == ".wav":
            sf.write(out_path, audio, sample_rate)
            return out_path

        if ext == ".mp3":
            # Requires pydub + ffmpeg in PATH (only if you need mp3)
            from pydub import AudioSegment
            buf = io.BytesIO()
            sf.write(buf, audio, sample_rate, format="WAV")
            buf.seek(0)
            AudioSegment.from_file(buf, format="wav").export(out_path, format="mp3", bitrate="192k")
            return out_path

        # default to wav if unknown extension
        sf.write(out_path.with_suffix(".wav"), audio, sample_rate)
        return out_path.with_suffix(".wav")
