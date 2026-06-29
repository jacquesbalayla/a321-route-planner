# A321 Flight Planner Desktop Build

This project now includes a desktop launcher so the Streamlit planner can be packaged as:

- a macOS app bundle: `dist/A321 Flight Planner.app`
- a Windows executable: `dist/A321 Flight Planner.exe`

## 1. Create a virtual environment

### macOS

```bash
cd "/Users/jacquesbalayla/Documents/Playground/A321 Routes"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-desktop.txt
```

### Windows

```bat
cd "C:\path\to\A321 Routes"
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements-desktop.txt
```

Or, on Windows, just double-click `build_windows.bat` in the project folder.

## 2. Run the desktop app from source

```bash
python desktop_launcher.py
```

## 3. Build for the current operating system

```bash
python build.py
```

## Output

- On macOS, the build creates `dist/A321 Flight Planner.app`
- On Windows, the build creates `dist/A321 Flight Planner.exe`

## Notes

- You must build on the target operating system. Build the Mac app on macOS and the Windows `.exe` on Windows.
- The desktop launcher uses a native webview when `pywebview` is available and falls back to the default browser if it is not.
- Announcement files now save to `C:\Users\Jacques\AppData\Roaming\Microsoft Flight Simulator 2024\Packages\Community\FNX Announcements\announcements\JBU` on Windows by default.
- On macOS, announcement files save to `~/Library/Application Support/A321 Route Planner/Announcements`.
- You can override the announcement export folder on any platform with the `A321_ANNOUNCEMENTS_DIR` environment variable.
- API keys can also be overridden with `OPENWEATHERMAP_API_KEY` and `ELEVENLABS_API_KEY`.
- The included `assets/icons/app_icon.ico` and `assets/icons/app_icon.icns` are already wired into future Windows and macOS builds.
