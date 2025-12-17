# Building echoType (PyInstaller)

echoType can be packaged as a single-file executable on each OS using PyInstaller `--onefile`.

## Prerequisites

- A Python environment with echoType dependencies installed (including `pyinstaller`).
- Piper voice model files available in a local `voices/` folder (e.g. `*.onnx` + `*.onnx.json`).
- Optional app icons:
  - Windows EXE icon: `icons/echoType.ico` (include sizes like 16/32/48/256)
  - Tk window icon: `icons/echoType.png`

### Generating a proper Windows `.ico`

Windows icons should contain multiple sizes (at least 16/32/48/256). If your `.ico` isn’t showing up, regenerate it from the PNG:

```bash
python -c "from PIL import Image; img=Image.open('icons/echoType.png').convert('RGBA').resize((256,256), Image.LANCZOS); img.save('icons/echoType.ico', format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
```

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

- If Windows Explorer still shows the old icon after rebuilding, try renaming the `.exe` or restarting Explorer (icon cache).
- User-writable files are stored outside the executable:
  - Config: `$XDG_CONFIG_HOME/echoType/config.json` (Linux), `%APPDATA%\\echoType\\config.json` (Windows).
  - App data (scores, generated audio): `$XDG_DATA_HOME/echoType/` (Linux), `%LOCALAPPDATA%\\echoType\\` (Windows).
- Linux audio output uses PortAudio via `sounddevice`; if you see “PortAudio library not found”, install your distro’s PortAudio package (e.g. `portaudio` / `libportaudio2`).
