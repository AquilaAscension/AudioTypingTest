import importlib
import os
import subprocess
import sys
import shutil
import urllib.request
from tkinter import messagebox, Tk

REQUIRED_LIBRARIES = {
    "piper": "piper-tts",
    "docx": "python-docx",
    "PyPDF2": "PyPDF2",
    "sounddevice": "sounddevice",
    "soundfile": "soundfile",
    "numpy": "numpy",
    "scipy": "scipy"
}


def ensure_dependencies_installed():
    for module_name, pip_name in REQUIRED_LIBRARIES.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
                print(f"Installed: {pip_name}")
            except Exception as e:
                print(f"Failed to install {pip_name}: {e}")
