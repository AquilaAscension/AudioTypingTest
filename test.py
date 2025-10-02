from tts_kokoro import kTTS
kTTS("Testing Kokoro direct WAV").save("TypingTTS.wav")
import soundfile as sf
info = sf.info("TypingTTS.wav")
print(round(info.frames / info.samplerate, 3), "seconds")
