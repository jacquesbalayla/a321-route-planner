import os
import sys
from pathlib import Path


SERVER_HOST = "127.0.0.1"
THEME_OPTIONS = {
    "theme.base": "light",
    "theme.primaryColor": "#4DA3FF",
    "theme.backgroundColor": "#FFFFFF",
    "theme.secondaryBackgroundColor": "#F3F5F9",
    "theme.textColor": "#262730",
}


def run_streamlit_server(port: int) -> None:
    os.environ["STREAMLIT_SERVER_ADDRESS"] = SERVER_HOST
    os.environ["STREAMLIT_SERVER_PORT"] = str(port)
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    app_path = str(Path(__file__).resolve().parent / "app.py")
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


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: server_runner.py <port>")

    run_streamlit_server(int(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
