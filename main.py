from dependency_checker import ensure_dependencies_installed, ensure_theme_installed
ensure_dependencies_installed()
ensure_theme_installed()


import tkinter as tk
from audio_typing_test import AudioTypingTest

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioTypingTest(root)
    root.mainloop()
