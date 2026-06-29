import os
import platform
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path


APP_NAME = "A321 Flight Planner"
PROJECT_DIR = Path(__file__).resolve().parent
ENTRYPOINT = PROJECT_DIR / "desktop_launcher.py"
MACOS_ICON = PROJECT_DIR / "assets" / "icons" / "app_icon.icns"
WINDOWS_ICON = PROJECT_DIR / "assets" / "icons" / "app_icon.ico"
DATA_FILES = [
    ".streamlit/config.toml",
    "app.py",
    "server_runner.py",
    "Route List.csv",
    "airports.json",
    "countries.csv",
    "assets/splash/loading_logo.png",
    "assets/splash/AudioIntro.mp3",
    "assets/branding/jetblue_logo.png",
    "assets/branding/american.png",
    "assets/branding/united.png",
    "assets/branding/aircanada.png",
    "assets/branding/lufthansa.png",
    "assets/branding/delta.png",
    "assets/branding/britishairways.png",
]
COLLECT_DATA_PACKAGES = [
    "streamlit",
    "pydeck",
]
COLLECT_SUBMODULE_PACKAGES = [
    "streamlit",
    "pydeck",
    "pydub",
    "imageio_ffmpeg",
]
HIDDEN_IMPORTS = [
    "pandas",
    "pydeck",
    "pytz",
]
COPY_METADATA_PACKAGES = [
    "streamlit",
    "pydeck",
]
EXCLUDED_MODULES = [
    "IPython",
    "jupyter",
    "matplotlib",
    "notebook",
    "onnxruntime",
    "scipy",
    "sklearn",
    "sympy",
    "tensorboard",
    "tensorflow",
    "torch",
    "torchaudio",
    "torchvision",
]
MACOS_INFO_PLIST_UPDATES = {
    "NSAppTransportSecurity": {
        "NSAllowsArbitraryLoadsInWebContent": True,
        "NSAllowsLocalNetworking": True,
    }
}


def add_data_argument(relative_path: str) -> str:
    source_path = PROJECT_DIR / relative_path
    destination = str(Path(relative_path).parent)
    if destination == "":
        destination = "."
    return f"{source_path}{os.pathsep}{destination}"


def build_command() -> list[str]:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        APP_NAME,
    ]

    current_system = platform.system()
    if current_system == "Windows":
        command.append("--onefile")
    if current_system == "Darwin":
        command.extend(["--osx-bundle-identifier", "com.jacquesbalayla.a321routeplanner"])
        if MACOS_ICON.exists():
            command.extend(["--icon", str(MACOS_ICON)])
    elif WINDOWS_ICON.exists():
        command.extend(["--icon", str(WINDOWS_ICON)])

    for package_name in COLLECT_DATA_PACKAGES:
        command.extend(["--collect-data", package_name])

    for package_name in COLLECT_SUBMODULE_PACKAGES:
        command.extend(["--collect-submodules", package_name])

    for module_name in HIDDEN_IMPORTS:
        command.extend(["--hidden-import", module_name])

    for package_name in COPY_METADATA_PACKAGES:
        command.extend(["--copy-metadata", package_name])

    for module_name in EXCLUDED_MODULES:
        command.extend(["--exclude-module", module_name])

    for relative_path in DATA_FILES:
        command.extend(["--add-data", add_data_argument(relative_path)])

    command.append(str(ENTRYPOINT))
    return command


def update_macos_bundle_metadata(app_path: Path) -> None:
    plist_path = app_path / "Contents" / "Info.plist"
    with open(plist_path, "rb") as fh:
        info = plistlib.load(fh)

    info.update(MACOS_INFO_PLIST_UPDATES)

    with open(plist_path, "wb") as fh:
        plistlib.dump(info, fh)

    runtime_icon_path = app_path / "Contents" / "Resources" / "icon-windowed.icns"
    if MACOS_ICON.exists():
        shutil.copyfile(MACOS_ICON, runtime_icon_path)

    subprocess.run(
        ["codesign", "--force", "--deep", "--sign", "-", str(app_path)],
        check=True,
        cwd=PROJECT_DIR,
    )


def main() -> int:
    command = build_command()
    print("Running:", " ".join(str(part) for part in command))
    env = os.environ.copy()
    env["PYINSTALLER_CONFIG_DIR"] = str(PROJECT_DIR / ".pyinstaller")

    try:
        subprocess.run(command, check=True, cwd=PROJECT_DIR, env=env)
    except subprocess.CalledProcessError as exc:
        return exc.returncode

    current_system = platform.system()
    if current_system == "Darwin":
        output_path = PROJECT_DIR / "dist" / f"{APP_NAME}.app"
        update_macos_bundle_metadata(output_path)
    elif current_system == "Windows":
        output_path = PROJECT_DIR / "dist" / f"{APP_NAME}.exe"
    else:
        output_path = PROJECT_DIR / "dist"

    print(f"Build complete: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
