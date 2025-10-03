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
    "numpy": "numpy"
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



#Theme Nonsense



AZURE_REPO_URL = "https://github.com/rdbende/Azure-ttk-theme.git"
LOCAL_REPO_DIR = "azure-ttk-theme"
THEME_DIRECTORY = "theme"



def ensure_theme_installed():
    
    """Ensure the theme files are present, clone the repo if necessary."""
    # Clone the repo if not already present
    clone_azure_repo()

    #Get the azure theme file
    if not os.path.exists("azure.tcl"):
        try:
            print("Downloading Azure theme...")
            urllib.request.urlretrieve("https://raw.githubusercontent.com/rdbende/Azure-ttk-theme/main/azure.tcl", "azure.tcl")
            print("Azure theme downloaded successfully.")
        except Exception as e:
            print(f"Failed to download Azure theme: {e}")

    # Ensure the 'theme/' directory exists in your project
    theme_folder = os.path.join(LOCAL_REPO_DIR, "theme")
    if os.path.exists(theme_folder):
        destination_theme_folder = THEME_DIRECTORY
        
        # If themes directory doesn't exist, copy the theme folder
        if not os.path.exists(destination_theme_folder):
            print(f"Copying theme files to {destination_theme_folder}...")
            shutil.copytree(theme_folder, destination_theme_folder)
            print("Theme files copied successfully.")
    else:
        print("Theme folder not found in the repository.")
        
def clone_azure_repo():
    """Clone the Azure TTK theme repository if it doesn't exist locally."""
    if not os.path.exists(LOCAL_REPO_DIR):
        print("Cloning the Azure TTK theme repository...")
        try:
            subprocess.check_call(["git", "clone", AZURE_REPO_URL])
            print("Repository cloned successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone repository: {e}")