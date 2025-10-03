from dependency_checker import ensure_dependencies_installed, ensure_theme_installed
ensure_dependencies_installed()
ensure_theme_installed()

import atexit
import signal
import tkinter as tk
from audio_typing_test import AudioTypingTest

if __name__ == "__main__":
    root = tk.Tk()
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