import importlib
import os
import subprocess
import sys
import shutil
import time
import urllib.request
from tkinter import messagebox, Tk
from pathlib import Path
from typing import Dict
CONSTRAINTS = Path(__file__).with_name("pip-constraints.txt")
PREFERRED_PYTHON = "3.11"

REQUIRED_LIBRARIES: Dict[str, str] = {
    "kokoro": "kokoro",
#    "mutagen": "mutagen",
    "docx": "python-docx",
    "PyPDF2": "PyPDF2",
    "librosa": "librosa",
    "sounddevice": "sounddevice",
    "soundfile": "soundfile",
    "numpy": "numpy"
}

UPGRADE_PIP = True

_ENV_REENTER_FLAG = "DEPENDENCY_CHECKER_REENTERED"


def _find_preferred_python_exe():
    import shutil, subprocess, os
    if os.name == "nt":
        try:
            out = subprocess.check_output(["py", f"-{PREFERRED_PYTHON}", "-c", "import sys;print(sys.executable)"], text=True)
            exe = out.strip()
            return exe if os.path.exists(exe) else None
        except Exception:
            pass
    for cand in (f"python{PREFERRED_PYTHON}", f"python{PREFERRED_PYTHON.replace('.', '')}"):
        p = shutil.which(cand)
        if p: return p
    return None

def _venv_dir() -> Path:
    return Path(__file__).resolve().parent / ".venv"

def _in_venv() -> bool:
    return getattr(sys, "base_prefix", sys.prefix) != sys.prefix or bool(os.environ.get("VIRTUAL_ENV"))

def _venv_python() -> Path:
    v = _venv_dir()
    if os.name == "nt":
        return v / "Scripts" / "python.exe"
    else:
        return v / "bin" / "python"

def ensure_venv():
    if _in_venv():
        return

    vdir = _venv_dir()
    creator = _find_preferred_python_exe() or sys.executable

    if not vdir.exists():
        print(f"[checker] Creating venv at {vdir} with {creator} ...")
        try:
            subprocess.check_call([creator, "-m", "venv", str(vdir)])
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"[checker] venv creation failed with {creator}: {e}") from e

    vpy = _venv_python()
    for _ in range(50):
        if vpy.exists():
            break
        time.sleep(0.1)
    
    if not vpy.exists():
        # extra diagnostics to help on Windows installs
        print(f"[checker] Expected venv python missing: {vpy}")
        try:
            print("[checker] Listing .venv\\Scripts:")
            for p in (vdir / "Scripts").glob("*"):
                print(" -", p.name)
        except Exception:
            pass
        raise FileNotFoundError(f"[checker] .venv appears incomplete; delete {vdir} and retry.")

    # Re-enter this same script under the venv interpreter
    if not os.environ.get(_ENV_REENTER_FLAG):
        env = os.environ.copy()
        env[_ENV_REENTER_FLAG] = "1"

        # Use absolute script path to avoid odd launchers/wrappers
        script_path = Path(sys.argv[0]).resolve()
        args = [str(vpy), str(script_path), *sys.argv[1:]]

        # Prefer execl (replace process) with inherited env; fall back if needed
        try:
            os.execl(str(vpy), str(vpy), str(script_path), *sys.argv[1:])
        except Exception as e:
            print(f"[checker] execl failed ({e}); falling back to subprocess...")
            subprocess.check_call(args, env=env)
            sys.exit(0)


def _pip(*args: str):
    args = list(args)
    cmd = [str(_venv_python() if _in_venv() and _venv_python().exists() else Path(sys.executable)), "-m", "pip"]

    # Insert constraints right after the subcommand (e.g., "install")
    if CONSTRAINTS.exists() and args:
        subcmd = args[0]
        if subcmd in {"install", "wheel", "download"}:
            args[1:1] = ["-c", str(CONSTRAINTS)]

    subprocess.check_check_call = subprocess.check_call  # optional: keep your style
    subprocess.check_call(cmd + args)

def preinstall_wheel_only():
    try:
        # Install wheel-only to prevent source builds on Windows
        _pip("install", "--only-binary=:all:", "spacy<4")
        _pip("install", "--only-binary=:all:", "spacy-curated-transformers<0.3")
    except subprocess.CalledProcessError as e:
        print(f"[checker] wheel-only preinstall skipped/failed: {e}")

def ensure_dependencies_installed():
    if UPGRADE_PIP:
        try:
            _pip("install", "--upgrade", "pip", "setuptools", "wheel")
        except Exception as e:
            print(f"[dependency_checker] pip upgrade failed (continuing): {e}")
    preinstall_wheel_only()
    for module_name, pip_name in REQUIRED_LIBRARIES.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            try:
                print(f"[dependency_checker] Installing: {pip_name}")
                _pip("install", pip_name)
                importlib.import_module(module_name)
            except Exception as e:
                print(f"[dependency_checker] Failed to install {pip_name}: {e}")


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

def ensure_env_and_deps():
    ensure_venv()
    ensure_dependencies_installed()

if __name__ == "__main__":
    # Running the checker directly: create venv, install, and optionally freeze
    ensure_env_and_deps()
    ensure_theme_installed()
    print("[dependency_checker] Environment ready.")