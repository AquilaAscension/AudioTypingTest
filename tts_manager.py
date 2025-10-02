import os
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
import librosa
import subprocess
import time
from tts_kokoro import kTTS
#from gtts import gTTS
#from mutagen.mp3 import MP3

class TTSManager:
    def __init__(self, filename='TypingTTS.wav'):
        self.filename = filename
        self.wav_file = 'TypingTTS.wav'
        self.typingText = "This is example text."
        self.TTSDuration = 0

        self.audio_data = None
        self.sample_rate = None
        self.stream = None
        self.is_paused = False
        self.position = 0  # playback index
        self.playback_thread = None
        self.is_armed = False

    def getTypingText(self):
        return self.typingText

    def getTTSDuration(self):
        return self.TTSDuration

    def deleteTTSFile(self):
        for f in [self.filename, self.wav_file]:
            if os.path.exists(f):
                os.remove(f)

    def TTSGenerate(self, input_text):
        kTTS(input_text, lang = 'en').save(self.wav_file)
        info = sf.info(self.wav_file)
        self.TTSDuration = info.frames / info.samplerate
        """
        tts_file = gTTS(input_text, lang='en')
        tts_file.save(self.filename)
        file_generated = MP3(self.filename)
        self.TTSDuration = file_generated.info.length 
        base_dir = os.path.dirname(os.path.abspath(__file__)) #Get the current directory of the file we are running
        ffmpeg_path = os.path.join(base_dir, "ffmpeg", "ffmpeg.exe") #from our current directory go into the folder ffmpeg and find ffmpeg.exe
        subprocess.run([ffmpeg_path, "-y", "-i", self.filename, self.wav_file],
                       check=True)
        """

    def load_and_stretch_audio(self, speed=1.0):
        data, sr = sf.read(self.wav_file, dtype='float32')
        if data.ndim > 1:
            data = np.mean(data, axis=1)  # convert to mono if stereo
        if speed != 1.0:
            data = librosa.effects.time_stretch(data, rate=speed)
        self.audio_data = data
        self.sample_rate = sr
        self.position = 0

    def play_callback(self, outdata, frames, time_info, status):
        if self.is_paused or self.audio_data is None:
            outdata[:] = 0.0
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
        self.load_and_stretch_audio(speed)
        self.is_armed = True

