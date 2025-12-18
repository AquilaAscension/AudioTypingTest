# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys
from typing import Optional

from PyInstaller.utils.hooks import collect_all, collect_data_files

# PyInstaller injects SPECPATH (directory containing this spec file).
project_root = Path(globals().get("SPECPATH", ".")).resolve()

block_cipher = None


def _require_dir(path: Path, help_text: str) -> Path:
    if path.is_dir():
        return path
    raise SystemExit(help_text)

def _optional_file(path: Path) -> Optional[str]:
    return str(path) if path.is_file() else None

def _collect_dir_files(src_dir: Path, dest_root: str) -> list[tuple[str, str]]:
    collected: list[tuple[str, str]] = []
    for file_path in src_dir.rglob("*"):
        if not file_path.is_file():
            continue
        rel_parent = file_path.relative_to(src_dir).parent
        dest = dest_root if str(rel_parent) == "." else str(Path(dest_root) / rel_parent)
        collected.append((str(file_path), dest))
    return collected


# --- App resources ---
datas: list = []
binaries: list = []
hiddenimports: list = []

datas += _collect_dir_files(_require_dir(project_root / "icons", "Missing `icons/` directory."), "icons")
datas += _collect_dir_files(
    _require_dir(
        project_root / "voices",
        "Missing `voices/` directory.\n"
        "Download Piper voice model files into `voices/` before building (e.g. *.onnx + *.onnx.json).",
    ),
    "voices",
)


# --- Third-party packaged data/binaries ---
# Piper needs its packaged espeak-ng data and the espeak bridge extension.
piper_datas, piper_binaries, piper_hiddenimports = collect_all("piper")
datas += piper_datas
binaries += piper_binaries
hiddenimports += piper_hiddenimports

# onnxruntime bundles shared libraries that must be collected.
ort_datas, ort_binaries, ort_hiddenimports = collect_all("onnxruntime")
datas += ort_datas
binaries += ort_binaries
hiddenimports += ort_hiddenimports

# soundfile bundles libsndfile in _soundfile_data on many platforms.
try:
    datas += collect_data_files("_soundfile_data")
except Exception:
    pass

# sounddevice may bundle PortAudio in _sounddevice_data (optional).
try:
    datas += collect_data_files("_sounddevice_data")
except Exception:
    pass


app_icon = None
if sys.platform.startswith("win"):
    _win_icon_path = project_root / "icons" / "echoType.ico"
    app_icon = _optional_file(_win_icon_path)
    if app_icon is None:
        raise SystemExit(f"Missing Windows icon file: {_win_icon_path}")
elif sys.platform == "darwin":
    app_icon = _optional_file(project_root / "icons" / "echoType.icns")


a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="echoType",
    debug=False,
    bootloader_ignore_signals=False,
    icon=app_icon,
    strip=False,
    upx=True,
    console=False,
)
