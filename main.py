import sys
#fix for blurry text
if sys.platform == "win32":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass
    
from dependency_checker import ensure_dependencies_installed
ensure_dependencies_installed()


import atexit
import signal
import tkinter as tk
import ttkbootstrap as ttk
from audio_typing_test import AudioTypingTest

if __name__ == "__main__":
    root = ttk.Tk()
    style = ttk.Style("darkly")
    
    app = AudioTypingTest(root)

    # Delete audio file on normal interpreter shutdown
    atexit.register(lambda: getattr(app, "tts_manager", None) and app.tts_manager.deleteTTSFile())

    def _cleanup_and_quit(*_):
        try:
            app.on_close()
        except Exception:
            try:
                app.tts_manager.deleteTTSFile()
            except Exception:
                pass

    signal.signal(getattr(signal, "SIGTERM", signal.SIGINT), _cleanup_and_quit)
    signal.signal(signal.SIGINT, _cleanup_and_quit)

    root.mainloop()