# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 echoType

import sys
#fix for blurry text
if sys.platform == "win32":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass
    
#from dependency_checker import ensure_dependencies_installed
#ensure_dependencies_installed()


import atexit
import signal
from pathlib import Path
import tkinter as tk
import tkinter.ttk as ttk
from audio_typing_test import AudioTypingTest

def _set_app_icon(root: tk.Tk) -> None:
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    icon_dir = base_dir / "icons"

    ico_path = icon_dir / "echoType.ico"
    png_path = icon_dir / "echoType.png"

    # Windows titlebar/taskbar icon (when available)
    if sys.platform.startswith("win") and ico_path.is_file():
        try:
            root.iconbitmap(str(ico_path))
        except Exception:
            pass
        try:
            # Also set as default for any Toplevel windows.
            root.iconbitmap(default=str(ico_path))
        except Exception:
            pass

    # Cross-platform icon (requires a PNG)
    if png_path.is_file():
        try:
            img = tk.PhotoImage(file=str(png_path))
            root.iconphoto(True, img)
            # Keep a reference to prevent garbage collection.
            root._echotype_icon = img  # type: ignore[attr-defined]
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    _set_app_icon(root)
    try:
        root.state("zoomed")
    except tk.TclError:
        # Some Tk builds don't support "zoomed"; fallback to platform attribute
        root.attributes("-zoomed", True)

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
