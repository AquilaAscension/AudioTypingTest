# Building echoType (PyInstaller)

echoType can be packaged as a single-file executable on each OS using PyInstaller `--onefile`.

## Prerequisites

- A Python environment with echoType dependencies installed (including `pyinstaller`).
- Piper voice model files available in a local `voices/` folder (e.g. `*.onnx` + `*.onnx.json`).

## Build (Linux)

```bash
python -m PyInstaller --noconfirm --clean echoType.spec
```

Output: `dist/echoType`

## Build (Windows)

```powershell
py -m PyInstaller --noconfirm --clean echoType.spec
```

Output: `dist\\echoType.exe`

## Notes

- User-writable files are stored outside the executable:
  - Config: `$XDG_CONFIG_HOME/echoType/config.json` (Linux), `%APPDATA%\\echoType\\config.json` (Windows).
  - App data (scores, generated audio): `$XDG_DATA_HOME/echoType/` (Linux), `%LOCALAPPDATA%\\echoType\\` (Windows).
- Linux audio output uses PortAudio via `sounddevice`; if you see “PortAudio library not found”, install your distro’s PortAudio package (e.g. `portaudio` / `libportaudio2`).

