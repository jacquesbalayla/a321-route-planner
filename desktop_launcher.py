import atexit
import base64
import logging
import mimetypes
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


APP_NAME = "A321 Flight Planner"
WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 960
SERVER_HOST = "127.0.0.1"
SPLASH_MIN_SECONDS = 8.0
THEME_OPTIONS = {
    "theme.base": "light",
    "theme.primaryColor": "#4DA3FF",
    "theme.backgroundColor": "#FFFFFF",
    "theme.secondaryBackgroundColor": "#F3F5F9",
    "theme.textColor": "#262730",
}
SPLASH_IMAGE_PARTS = ("assets", "splash", "loading_logo.png")
SPLASH_AUDIO_PARTS = ("assets", "splash", "AudioIntro.mp3")


def resource_path(*parts: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent
    return base_path.joinpath(*parts)


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((SERVER_HOST, 0))
        return sock.getsockname()[1]


def wait_for_server(url: str, timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):
                return
        except Exception:
            time.sleep(0.25)
    raise TimeoutError(f"Timed out waiting for {url}")


def as_data_uri(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type is None:
        mime_type = "application/octet-stream"

    encoded_bytes = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded_bytes}"


def build_splash_html() -> str:
    logo_uri = as_data_uri(resource_path(*SPLASH_IMAGE_PARTS))
    audio_uri = as_data_uri(resource_path(*SPLASH_AUDIO_PARTS))
    accent = THEME_OPTIONS["theme.primaryColor"]
    background = THEME_OPTIONS["theme.backgroundColor"]
    secondary_background = THEME_OPTIONS["theme.secondaryBackgroundColor"]
    text_color = THEME_OPTIONS["theme.textColor"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{APP_NAME}</title>
  <style>
    :root {{
      color-scheme: light;
      --accent: {accent};
      --accent-strong: #1E62D9;
      --background: {background};
      --secondary: {secondary_background};
      --text: {text_color};
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      min-height: 100vh;
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(77, 163, 255, 0.28), transparent 38%),
        radial-gradient(circle at top right, rgba(30, 98, 217, 0.14), transparent 32%),
        linear-gradient(180deg, #FFFFFF 0%, #F6FAFF 100%);
      color: var(--text);
      overflow: hidden;
    }}

    .shell {{
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 36px;
    }}

    .panel {{
      position: relative;
      width: min(720px, 100%);
      padding: 30px 38px 28px;
      border-radius: 30px;
      background: rgba(255, 255, 255, 0.9);
      border: 1px solid rgba(77, 163, 255, 0.16);
      box-shadow:
        0 30px 90px rgba(43, 91, 165, 0.16),
        0 8px 32px rgba(77, 163, 255, 0.1);
      text-align: center;
      backdrop-filter: blur(16px);
    }}

    .panel::before {{
      content: "";
      position: absolute;
      inset: -25%;
      background: radial-gradient(circle, rgba(77, 163, 255, 0.12), transparent 55%);
      animation: pulse 4s ease-in-out infinite;
      pointer-events: none;
    }}

    .logo-wrap {{
      position: relative;
      width: min(430px, 78vw);
      margin: 0 auto 20px;
      z-index: 1;
    }}

    .logo-wrap::after {{
      content: "";
      position: absolute;
      inset: 24px;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(77, 163, 255, 0.26), transparent 68%);
      filter: blur(22px);
      z-index: -1;
    }}

    .logo {{
      display: block;
      width: 100%;
      height: auto;
      border-radius: 0;
      box-shadow: none;
    }}

    h1 {{
      margin: 0;
      font-size: 2rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      position: relative;
      z-index: 1;
    }}

    .subhead {{
      margin: 10px auto 0;
      max-width: 30ch;
      font-size: 1rem;
      line-height: 1.6;
      color: rgba(38, 39, 48, 0.72);
      position: relative;
      z-index: 1;
    }}

    .progress {{
      margin: 24px auto 14px;
      width: 100%;
      height: 12px;
      padding: 2px;
      border-radius: 999px;
      background: rgba(77, 163, 255, 0.12);
      overflow: hidden;
      position: relative;
      z-index: 1;
    }}

    .progress-bar {{
      width: 42%;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--accent) 0%, var(--accent-strong) 100%);
      animation: glide 1.6s ease-in-out infinite;
      box-shadow: 0 0 24px rgba(77, 163, 255, 0.32);
    }}

    .status {{
      margin: 0;
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--accent-strong);
      position: relative;
      z-index: 1;
    }}

    .hint {{
      margin: 12px auto 0;
      max-width: 34ch;
      font-size: 0.9rem;
      line-height: 1.55;
      color: rgba(38, 39, 48, 0.62);
      position: relative;
      z-index: 1;
    }}

    .caption {{
      margin-top: 22px;
      padding-top: 18px;
      border-top: 1px solid rgba(77, 163, 255, 0.14);
      font-size: 0.86rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: rgba(38, 39, 48, 0.5);
      position: relative;
      z-index: 1;
    }}

    @keyframes pulse {{
      0%, 100% {{ transform: scale(0.96); opacity: 0.62; }}
      50% {{ transform: scale(1.05); opacity: 1; }}
    }}

    @keyframes glide {{
      0% {{ transform: translateX(-14%); }}
      50% {{ transform: translateX(132%); }}
      100% {{ transform: translateX(-14%); }}
    }}

    @media (max-width: 640px) {{
      .shell {{
        padding: 22px;
      }}

      .panel {{
        padding: 28px 22px 24px;
        border-radius: 24px;
      }}

      .logo-wrap {{
        width: min(320px, 78vw);
      }}

      h1 {{
        font-size: 1.7rem;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <main class="panel">
      <div class="logo-wrap">
        <img class="logo" src="{logo_uri}" alt="A321 Flight Planner logo">
      </div>
      <h1>Welcome aboard</h1>
      <p class="subhead">Preparing your A321 Flight Planner with your saved routes, airport data, and briefing tools.</p>
      <div class="progress" aria-hidden="true">
        <div class="progress-bar"></div>
      </div>
      <p class="status">Starting your flight deck...</p>
      <p class="hint" id="audio-status">Playing your greeting while the planner gets ready.</p>
      <p class="caption">A321 Flight Planner</p>
      <audio id="intro-audio" autoplay preload="auto">
        <source src="{audio_uri}" type="audio/mpeg">
      </audio>
    </main>
  </div>
  <script>
    const audio = document.getElementById("intro-audio");
    const audioStatus = document.getElementById("audio-status");

    const playGreeting = () => {{
      const playRequest = audio.play();

      if (playRequest && typeof playRequest.then === "function") {{
        playRequest
          .then(() => {{
            audioStatus.textContent = "Playing your greeting while the planner gets ready.";
          }})
          .catch(() => {{
            audioStatus.textContent = "If the greeting stays silent, click once anywhere in this window.";
          }});
      }}
    }};

    document.addEventListener("DOMContentLoaded", () => {{
      playGreeting();
    }});

    document.body.addEventListener("pointerdown", () => {{
      if (audio.paused) {{
        playGreeting();
      }}
    }});
  </script>
</body>
</html>
"""


def get_log_path() -> Path:
    if sys.platform == "darwin":
        log_dir = Path.home() / "Library" / "Logs" / APP_NAME
    elif sys.platform.startswith("win"):
        log_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / APP_NAME / "Logs"
    else:
        log_dir = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / APP_NAME

    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "launcher.log"


try:
    logging.basicConfig(
        filename=str(get_log_path()),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
except Exception:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def show_error_dialog(message: str) -> None:
    try:
        if sys.platform == "darwin":
            escaped = message.replace("\\", "\\\\").replace('"', '\\"')
            subprocess.run(
                ["osascript", "-e", f'display alert "{APP_NAME}" message "{escaped}" as critical'],
                check=False,
            )
            return

        if sys.platform.startswith("win"):
            import ctypes

            ctypes.windll.user32.MessageBoxW(None, message, APP_NAME, 0x10)
            return
    except Exception:
        logging.exception("Failed to show error dialog")


def launch_command(port: int) -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--run-server", str(port)]
    return [sys.executable, str(resource_path("server_runner.py")), str(port)]


def start_server_process(port: int) -> subprocess.Popen:
    env = os.environ.copy()
    env["STREAMLIT_SERVER_ADDRESS"] = SERVER_HOST
    env["STREAMLIT_SERVER_PORT"] = str(port)
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    log_path = get_log_path()
    log_handle = open(log_path, "a", encoding="utf-8")

    creationflags = 0
    if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW"):
        creationflags = subprocess.CREATE_NO_WINDOW

    process = subprocess.Popen(
        launch_command(port),
        cwd=str(resource_path()),
        env=env,
        stdout=log_handle,
        stderr=log_handle,
        creationflags=creationflags,
    )
    process._codex_log_handle = log_handle
    atexit.register(stop_server_process, process)
    return process


def stop_server_process(process: subprocess.Popen | None) -> None:
    if process is None:
        return

    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    log_handle = getattr(process, "_codex_log_handle", None)
    if log_handle is not None and not log_handle.closed:
        log_handle.close()


def run_streamlit_server(port: int) -> None:
    os.environ["STREAMLIT_SERVER_ADDRESS"] = SERVER_HOST
    os.environ["STREAMLIT_SERVER_PORT"] = str(port)
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    app_path = str(resource_path("app.py"))
    from streamlit import config
    from streamlit.web import bootstrap

    streamlit_options = {
        "global.developmentMode": False,
        "server.headless": True,
        "server.address": SERVER_HOST,
        "server.port": port,
        "browser.serverAddress": SERVER_HOST,
        "browser.serverPort": port,
        "browser.gatherUsageStats": False,
    }
    streamlit_options.update(THEME_OPTIONS)

    for option_name, option_value in streamlit_options.items():
        config.set_option(option_name, option_value)

    bootstrap.run(app_path, False, [], streamlit_options)


def load_app_after_splash(window: object, port: int, state: dict[str, object]) -> None:
    startup_started_at = time.monotonic()
    url = f"http://{SERVER_HOST}:{port}"

    try:
        server_process = start_server_process(port)
        state["process"] = server_process
        wait_for_server(url)

        remaining_splash_seconds = SPLASH_MIN_SECONDS - (time.monotonic() - startup_started_at)
        if remaining_splash_seconds > 0:
            time.sleep(remaining_splash_seconds)

        window.load_url(url)
    except Exception as exc:
        state["error"] = exc
        logging.exception("Launcher failed during splash screen")
        show_error_dialog(
            f"{APP_NAME} could not start.\n\nDetails: {exc}\n\nLog: {get_log_path()}"
        )
        try:
            window.destroy()
        except Exception:
            logging.exception("Unable to close the startup window after a launcher error")


def open_window(port: int) -> bool:
    import webview

    gui = "cocoa" if sys.platform == "darwin" else None
    state: dict[str, object] = {"process": None, "error": None}
    window = webview.create_window(
        APP_NAME,
        html=build_splash_html(),
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(1100, 760),
        background_color=THEME_OPTIONS["theme.secondaryBackgroundColor"],
    )
    try:
        webview.start(
            func=load_app_after_splash,
            args=(window, port, state),
            gui=gui,
            debug=False,
            http_server=False,
        )
    finally:
        stop_server_process(state["process"])

    return state["error"] is None


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "--run-server":
        logging.info("Starting embedded Streamlit server on port %s", sys.argv[2])
        run_streamlit_server(int(sys.argv[2]))
        return 0

    port = find_free_port()
    url = f"http://{SERVER_HOST}:{port}"
    logging.info("Launching desktop app at %s", url)

    try:
        return 0 if open_window(port) else 1
    except Exception as exc:
        logging.exception("Launcher failed")
        show_error_dialog(
            f"{APP_NAME} could not start.\n\nDetails: {exc}\n\nLog: {get_log_path()}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
