import os
import io
import re
import base64
import json
import math
import platform
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime
from html import escape
from pathlib import Path
from textwrap import dedent

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
import pytz
import numpy as np
from pydub import AudioSegment


APP_NAME = "A321 Route Planner"
APP_DIR = Path(__file__).resolve().parent
ROUTES_CSV = APP_DIR / "Route List.csv"
AIRPORTS_JSON = APP_DIR / "airports.json"
SETTINGS_FILE_NAME = "settings.json"
MENU_OPTIONS = [
    "Dashboard",
    "Route Database",
    "Manual Planner",
    "Saved Flights",
    "Aircraft Setup",
    "Performance",
    "Weather",
    "SimBrief",
    "Logs",
    "Settings",
]
AIRLINE_THEME_OPTIONS = [
    "American",
    "United",
    "JetBlue",
    "Air Canada",
    "Lufthansa",
    "Delta",
    "British Airways",
]
AIRLINE_THEME_CODES = {
    "american": "AAL",
    "united": "UAL",
    "jetblue": "JBU",
    "aircanada": "ACA",
    "lufthansa": "DLH",
    "delta": "DAL",
    "britishairways": "BAW",
}
AIRLINE_THEME_LOGOS = {
    "american": "american.png",
    "united": "united.png",
    "jetblue": "jetblue_logo.png",
    "aircanada": "aircanada.png",
    "lufthansa": "lufthansa.png",
    "delta": "delta.png",
    "britishairways": "britishairways.png",
}
MAP_STYLES = {
    "Voyager": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
    "Voyager No Labels": "https://basemaps.cartocdn.com/gl/voyager-nolabels-gl-style/style.json",
    "Light": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    "Light No Labels": "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json",
    "Dark": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    "Dark No Labels": "https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json",
}
AIRLINE_THEME_CONFIG = {
    "jetblue": {
        "name": "JetBlue",
        "shell": "#011735",
        "sidebar": "#011735",
        "sidebarActive": "#082681",
        "primary": "#021C48",
        "primaryHover": "#062A65",
        "accent": "#0B5CAD",
        "card": "#F6F8FA",
        "border": "#D7DFEA",
        "text": "#07162D",
        "muted": "#5D6B7C",
        "success": "#35D87A",
        "swatches": ["#011735", "#082681", "#0B5CAD"],
    },
    "american": {
        "name": "American",
        "shell": "#0A2240",
        "sidebar": "#0A2240",
        "sidebarActive": "#0078D2",
        "primary": "#0A2240",
        "primaryHover": "#123865",
        "accent": "#B31942",
        "card": "#F7F8FA",
        "border": "#D7DFEA",
        "text": "#07162D",
        "muted": "#5D6B7C",
        "success": "#35D87A",
        "swatches": ["#0A2240", "#0078D2", "#B31942"],
    },
    "united": {
        "name": "United",
        "shell": "#002244",
        "sidebar": "#002244",
        "sidebarActive": "#005DAA",
        "primary": "#002244",
        "primaryHover": "#003E7E",
        "accent": "#009CDE",
        "card": "#F7FAFC",
        "border": "#D7DFEA",
        "text": "#07162D",
        "muted": "#5D6B7C",
        "success": "#35D87A",
        "swatches": ["#002244", "#005DAA", "#009CDE"],
    },
    "aircanada": {
        "name": "Air Canada",
        "shell": "#111111",
        "sidebar": "#111111",
        "sidebarActive": "#E31B23",
        "primary": "#111111",
        "primaryHover": "#2A2A2A",
        "accent": "#E31B23",
        "card": "#F8F8F8",
        "border": "#D7DFEA",
        "text": "#111111",
        "muted": "#626262",
        "success": "#35D87A",
        "swatches": ["#111111", "#E31B23", "#F8F8F8"],
    },
    "lufthansa": {
        "name": "Lufthansa",
        "shell": "#05164D",
        "sidebar": "#05164D",
        "sidebarActive": "#F9BA00",
        "primary": "#05164D",
        "primaryHover": "#0B2574",
        "accent": "#F9BA00",
        "card": "#F8FAFC",
        "border": "#D7DFEA",
        "text": "#07162D",
        "muted": "#5D6B7C",
        "success": "#35D87A",
        "swatches": ["#05164D", "#F9BA00", "#0B2574"],
    },
    "delta": {
        "name": "Delta",
        "shell": "#0B1F41",
        "sidebar": "#0B1F41",
        "sidebarActive": "#C8102E",
        "primary": "#0B1F41",
        "primaryHover": "#17376B",
        "accent": "#C8102E",
        "card": "#F8FAFC",
        "border": "#D7DFEA",
        "text": "#07162D",
        "muted": "#5D6B7C",
        "success": "#35D87A",
        "swatches": ["#0B1F41", "#C8102E", "#17376B"],
    },
    "britishairways": {
        "name": "British Airways",
        "shell": "#01295C",
        "sidebar": "#01295C",
        "sidebarActive": "#C8102E",
        "primary": "#01295C",
        "primaryHover": "#023B82",
        "accent": "#0072CE",
        "card": "#F8FAFC",
        "border": "#D7DFEA",
        "text": "#07162D",
        "muted": "#5D6B7C",
        "success": "#35D87A",
        "swatches": ["#01295C", "#C8102E", "#0072CE"],
    },
}
REFERENCE_ROUTE_OPTIONS = [
    ("EGLL", "LFPG", "London Heathrow", "Paris Charles de Gaulle", "Popular"),
    ("EDDF", "LEPA", "Frankfurt", "Palma de Mallorca", ""),
    ("EHAM", "LEMD", "Amsterdam", "Madrid", ""),
    ("LSZH", "LIRF", "Zurich", "Rome Fiumicino", ""),
    ("LOWW", "LTAI", "Vienna", "Antalya", ""),
]


def get_user_data_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    if sys.platform.startswith("win"):
        appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return appdata / APP_NAME
    xdg_data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return xdg_data_home / APP_NAME


def get_settings_path() -> Path:
    settings_dir = get_user_data_dir()
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir / SETTINGS_FILE_NAME


def get_default_announcements_base_dir() -> Path:
    if sys.platform.startswith("win"):
        appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return (
            appdata
            / "Microsoft Flight Simulator 2024"
            / "Packages"
            / "Community"
            / "FNX Announcements"
            / "announcements"
            / "JBU"
        )

    return get_user_data_dir() / "Announcements"


def get_secret_value(name: str) -> str:
    env_value = os.environ.get(name, "").strip()
    if env_value:
        return env_value

    try:
        secret_value = str(st.secrets.get(name, "")).strip()
        if secret_value:
            return secret_value
    except Exception:
        pass

    return ""


def load_saved_settings() -> dict[str, str]:
    settings_path = get_settings_path()
    if not settings_path.exists():
        return {}

    try:
        with open(settings_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    settings: dict[str, str] = {}
    for key in (
        "openweathermap_api_key",
        "elevenlabs_api_key",
        "announcements_base_dir",
        "sync_supabase_url",
        "sync_supabase_key",
        "sync_user_id",
        "sync_device_name",
    ):
        value = data.get(key, "")
        settings[key] = "" if value is None else str(value).strip()
    return settings


def save_user_settings(settings: dict[str, str]) -> None:
    clean_settings = {
        "openweathermap_api_key": str(settings.get("openweathermap_api_key", "")).strip(),
        "elevenlabs_api_key": str(settings.get("elevenlabs_api_key", "")).strip(),
        "announcements_base_dir": str(settings.get("announcements_base_dir", "")).strip(),
        "sync_supabase_url": str(settings.get("sync_supabase_url", "")).strip(),
        "sync_supabase_key": str(settings.get("sync_supabase_key", "")).strip(),
        "sync_user_id": str(settings.get("sync_user_id", "")).strip(),
        "sync_device_name": str(settings.get("sync_device_name", "")).strip(),
    }

    with open(get_settings_path(), "w", encoding="utf-8") as fh:
        json.dump(clean_settings, fh, indent=2)


def normalize_announcements_dir(raw_path: str) -> str:
    path_text = str(raw_path).strip()
    if not path_text:
        raise ValueError("Announcements folder is required.")

    announcements_path = Path(path_text).expanduser()
    announcements_path.mkdir(parents=True, exist_ok=True)
    return str(announcements_path)


def build_active_settings(saved_settings: dict[str, str]) -> dict[str, str]:
    return {
        "openweathermap_api_key": get_secret_value("OPENWEATHERMAP_API_KEY")
        or saved_settings.get("openweathermap_api_key", "").strip(),
        "elevenlabs_api_key": get_secret_value("ELEVENLABS_API_KEY")
        or saved_settings.get("elevenlabs_api_key", "").strip(),
        "announcements_base_dir": get_secret_value("A321_ANNOUNCEMENTS_DIR")
        or saved_settings.get("announcements_base_dir", "").strip(),
        "sync_supabase_url": get_secret_value("A321_SYNC_SUPABASE_URL")
        or saved_settings.get("sync_supabase_url", "").strip(),
        "sync_supabase_key": get_secret_value("A321_SYNC_SUPABASE_KEY")
        or saved_settings.get("sync_supabase_key", "").strip(),
        "sync_user_id": get_secret_value("A321_SYNC_USER_ID")
        or saved_settings.get("sync_user_id", "").strip(),
        "sync_device_name": get_secret_value("A321_SYNC_DEVICE_NAME")
        or saved_settings.get("sync_device_name", platform.node() or "Home PC").strip(),
    }


def has_required_settings(settings: dict[str, str]) -> bool:
    return all(
        str(settings.get(key, "")).strip()
        for key in ("openweathermap_api_key", "elevenlabs_api_key", "announcements_base_dir")
    )


def cloud_sync_configured(settings: dict[str, str]) -> bool:
    return all(
        str(settings.get(key, "")).strip()
        for key in ("sync_supabase_url", "sync_supabase_key", "sync_user_id")
    )


def configure_audio_backend() -> None:
    try:
        import imageio_ffmpeg

        AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass


def get_ffmpeg_executable() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg") or "ffmpeg"


def convert_mp3_bytes_to_ogg(audio_bytes: bytes) -> bytes:
    ffmpeg_executable = get_ffmpeg_executable()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        input_path = temp_path / "input.mp3"
        output_path = temp_path / "output.ogg"
        input_path.write_bytes(audio_bytes)

        command = [
            ffmpeg_executable,
            "-y",
            "-i",
            str(input_path),
            "-filter:a",
            "volume=10dB,loudnorm",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-c:a",
            "libvorbis",
            str(output_path),
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        if result.returncode != 0 or not output_path.exists():
            error_output = result.stderr.decode("utf-8", errors="ignore").strip()
            raise RuntimeError(error_output or "ffmpeg failed to convert the generated audio.")

        return output_path.read_bytes()


SETTINGS_PATH = get_settings_path()
SAVED_SETTINGS = load_saved_settings()
ACTIVE_SETTINGS = build_active_settings(SAVED_SETTINGS)
ANNOUNCEMENTS_BASE_DIR = ACTIVE_SETTINGS["announcements_base_dir"]
OPENWEATHERMAP_API_KEY = ACTIVE_SETTINGS["openweathermap_api_key"]
ELEVENLABS_API_KEY = ACTIVE_SETTINGS["elevenlabs_api_key"]
SETTINGS_REQUIRED = not has_required_settings(ACTIVE_SETTINGS)

if ANNOUNCEMENTS_BASE_DIR:
    os.makedirs(ANNOUNCEMENTS_BASE_DIR, exist_ok=True)
configure_audio_backend()

st.set_page_config(page_title="A321 Route Planner", page_icon="🛩", layout="wide")

st.markdown("""
<style>
:root {
    --color-shell: #011735;
    --color-sidebar: #011735;
    --color-sidebar-active: #082681;
    --color-primary: #021C48;
    --color-primary-hover: #062A65;
    --color-accent: #0B5CAD;
    --color-card: #F6F8FA;
    --color-border: #D7DFEA;
    --color-text: #07162D;
    --color-muted: #5D6B7C;
    --color-success: #35D87A;
    --color-board: #021937;
    --color-board-cell: #1D2637;
    --color-page: #EDF3FA;
    --a321-ink: var(--color-text);
    --a321-muted: var(--color-muted);
    --a321-line: var(--color-border);
}

html, body, input, textarea, select, button {
    font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif !important;
}

.stApp {
    background: var(--color-shell);
    color: var(--color-text);
}

[data-testid="stAppViewContainer"] {
    background: var(--color-shell);
}

[data-testid="stMain"] {
    background: var(--color-card);
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stSidebar"],
[data-testid="stVerticalBlock"],
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stElementContainer"] {
    opacity: 1 !important;
    filter: none !important;
    transition: none !important;
}

.stApp [disabled],
.stApp [aria-disabled="true"],
.stApp [data-disabled="true"] {
    opacity: 1 !important;
    filter: none !important;
}

[data-testid="stHeader"],
[data-testid="stToolbar"],
#MainMenu,
footer {
    visibility: hidden;
    height: 0;
}

.block-container {
    max-width: 1280px;
    padding: 12px 14px 20px;
}

h1, h2, h3, h4, h5, h6, p, label {
    color: var(--color-text);
    letter-spacing: 0;
}

h1 {
    font-size: 2rem;
    font-weight: 800;
}

h2, h3, h4 {
    font-weight: 760;
}

section[data-testid="stSidebar"] {
    width: 158px !important;
    min-width: 158px !important;
    background: linear-gradient(180deg, var(--color-sidebar) 0%, #00102B 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.12);
}

section[data-testid="stSidebar"] > div {
    width: 158px !important;
    padding: 14px 9px 12px;
    background: transparent;
}

[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] h3 {
    font-size: 0.95rem !important;
    line-height: 1.1;
    margin: 0.2rem 0 0.05rem;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: rgba(255,255,255,0.72) !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] > label {
    display: none;
}

[data-testid="stSidebar"] iframe {
    width: 100% !important;
    border: 0 !important;
}

[data-testid="stSidebar"] [role="radiogroup"] {
    gap: 4px;
}

[data-testid="stSidebar"] [role="radiogroup"] label {
    min-height: 36px;
    border-radius: 7px;
    padding: 7px 8px !important;
    margin: 1px 0;
    color: rgba(255,255,255,0.92) !important;
}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: var(--color-sidebar-active);
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.10);
}

[data-testid="stSidebar"] [role="radio"] {
    display: none;
}

[data-testid="stSidebar"] input[type="radio"],
[data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child,
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
    display: none !important;
}

[data-testid="stSidebar"] [role="radiogroup"] label p {
    font-size: 0.78rem !important;
    line-height: 1.28 !important;
    font-weight: 640 !important;
}

.a321-sidebar-brand {
    width: 54px;
    height: 48px;
    border-radius: 8px;
    display: grid;
    place-items: center;
    background: var(--color-sidebar-active);
    margin: 4px auto 12px;
}

.a321-sidebar-brand::before {
    content: "✈";
    color: #FFFFFF;
    font-size: 28px;
    line-height: 1;
    transform: rotate(-14deg);
}

.a321-sidebar-brand svg {
    display: none;
}

.a321-sidebar-status {
    border: 1px solid rgba(255,255,255,0.22);
    background: rgba(255,255,255,0.045);
    border-radius: 7px;
    padding: 10px 9px;
    margin-top: 24px;
    color: #FFFFFF;
    font-size: 0.72rem;
}

.a321-status-row {
    display: flex;
    align-items: center;
    gap: 7px;
    font-weight: 750;
    margin-bottom: 4px;
}

.a321-status-subrow {
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: rgba(255,255,255,0.78);
    font-size: 0.66rem;
}

.a321-dot-green,
.a321-dot-red {
    display: inline-block;
    width: 9px;
    height: 9px;
    border-radius: 999px;
}

.a321-dot-green { background: var(--color-success); }
.a321-dot-red { background: #EF4444; }

section[data-testid="stSidebar"] div.stButton > button {
    min-height: 36px !important;
    width: 100% !important;
    justify-content: flex-start !important;
    text-align: left !important;
    border: 0 !important;
    border-radius: 7px !important;
    padding: 7px 8px !important;
    margin: 1px 0 !important;
    background: transparent !important;
    color: rgba(255,255,255,0.94) !important;
    box-shadow: none !important;
    font-size: 0.78rem !important;
    font-weight: 740 !important;
}

section[data-testid="stSidebar"] div.stButton > button:hover {
    background: rgba(255,255,255,0.08) !important;
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"] div.stButton > button * {
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"],
[data-testid="stSidebar"],
[data-testid="stSidebarNav"] {
    display: none !important;
    width: 0 !important;
    min-width: 0 !important;
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main {
    margin-left: 0 !important;
}

.a321-page {
    background: var(--color-page);
    border-radius: 0 0 12px 12px;
    padding: 12px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,0.96);
    border: 1px solid var(--color-border) !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 24px rgba(1, 23, 53, 0.06);
}

div[data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 11px 12px;
}

div[data-testid="stVerticalBlock"]:has(.a321-card-title),
div[data-testid="stVerticalBlock"]:has(.a321-aircraft-card),
div[data-testid="stVerticalBlock"]:has(.a321-detail-table),
div[data-testid="stVerticalBlock"]:has(.a321-simbrief-title),
div[data-testid="stVerticalBlock"]:has(.a321-map-title) {
    background: #FFFFFF !important;
    border: 1px solid var(--color-border) !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 24px rgba(1, 23, 53, 0.06);
    padding: 11px 12px !important;
}

div[data-testid="stVerticalBlock"]:has(.a321-card-title) div[data-testid="stVerticalBlock"],
div[data-testid="stVerticalBlock"]:has(.a321-aircraft-card) div[data-testid="stVerticalBlock"],
div[data-testid="stVerticalBlock"]:has(.a321-detail-table) div[data-testid="stVerticalBlock"],
div[data-testid="stVerticalBlock"]:has(.a321-simbrief-title) div[data-testid="stVerticalBlock"],
div[data-testid="stVerticalBlock"]:has(.a321-map-title) div[data-testid="stVerticalBlock"] {
    border: 0 !important;
    box-shadow: none !important;
    padding: 0 !important;
}

.a321-dashboard-card-marker {
    display: none;
}

.a321-announcement-anchor {
    display: none;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.a321-dashboard-card-marker) {
    background:
        linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(248,250,252,0.96) 100%) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 26px rgba(1, 23, 53, 0.08) !important;
    overflow: hidden !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.a321-dashboard-card-marker) > div {
    padding: 13px 14px !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.a321-route-card-marker),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.a321-aircraft-card-marker) {
    min-height: 100% !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.a321-route-card-marker) input,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.a321-route-card-marker) [data-baseweb="select"] > div,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.a321-flight-details-card-marker) input,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.a321-simbrief-card-marker) input {
    background: #FFFFFF !important;
    border-color: var(--color-border) !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 2px rgba(1, 23, 53, 0.03) !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.a321-route-card-marker):focus-within,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.a321-flight-details-card-marker):focus-within,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.a321-simbrief-card-marker):focus-within {
    border-color: color-mix(in srgb, var(--color-accent) 42%, var(--color-border)) !important;
    box-shadow: 0 12px 30px rgba(1, 23, 53, 0.10), 0 0 0 1px color-mix(in srgb, var(--color-accent) 24%, transparent) !important;
}

div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .a321-dashboard-card-marker) {
    background:
        linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(248,250,252,0.97) 100%) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 26px rgba(1, 23, 53, 0.08) !important;
    padding: 13px 14px !important;
    overflow: hidden !important;
}

div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .a321-route-card-marker),
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .a321-aircraft-card-marker) {
    min-height: 232px !important;
}

div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .a321-flight-details-card-marker),
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .a321-simbrief-card-marker) {
    min-height: 420px !important;
}

div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .a321-flight-details-card-marker)
> div[data-testid="stElementContainer"]:has(.a321-announcement-anchor) {
    margin-top: auto !important;
}

div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .a321-dashboard-card-marker) input,
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .a321-dashboard-card-marker) [data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border-color: var(--color-border) !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 2px rgba(1, 23, 53, 0.03) !important;
}

div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .a321-route-card-marker):focus-within,
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .a321-flight-details-card-marker):focus-within,
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .a321-simbrief-card-marker):focus-within {
    border-color: color-mix(in srgb, var(--color-accent) 42%, var(--color-border)) !important;
    box-shadow: 0 12px 30px rgba(1, 23, 53, 0.10), 0 0 0 1px color-mix(in srgb, var(--color-accent) 24%, transparent) !important;
}

.a321-card-title {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--color-text);
    font-size: 1rem;
    font-weight: 800;
    margin-bottom: 10px;
}

.a321-page-header {
    margin: 8px 0 14px;
}

.a321-page-header h2 {
    margin: 0;
    color: var(--color-text);
    font-size: 1.55rem;
    line-height: 1.1;
    font-weight: 850;
}

.a321-page-header p {
    margin: 5px 0 0;
    color: var(--color-muted);
    font-size: 0.92rem;
    font-weight: 560;
}

.a321-empty-state {
    min-height: 92px;
    border: 1px dashed var(--color-border);
    border-radius: 10px;
    display: grid;
    place-items: center;
    text-align: center;
    color: var(--color-muted);
    background: rgba(246,248,250,0.72);
    padding: 14px;
}

.a321-mini-route {
    border: 1px solid var(--color-border);
    border-radius: 10px;
    padding: 12px;
    background: #FFFFFF;
    margin-bottom: 10px;
}

.a321-mini-route strong {
    display: block;
    color: var(--color-text);
    font-size: 1rem;
    margin-bottom: 4px;
}

.a321-mini-route span {
    color: var(--color-muted);
    font-size: 0.82rem;
}

.a321-number-badge {
    width: 25px;
    height: 25px;
    border-radius: 999px;
    background: var(--color-sidebar-active);
    color: #FFFFFF;
    display: inline-grid;
    place-items: center;
    font-size: 0.82rem;
    font-weight: 850;
}

.a321-route-row {
    display: grid;
    grid-template-columns: 96px 1fr auto;
    align-items: center;
    gap: 10px;
    min-height: 30px;
    padding: 6px 9px;
    border-bottom: 1px solid var(--color-border);
    font-size: 0.79rem;
}

.a321-route-row strong {
    color: var(--color-text);
    font-weight: 850;
}

.a321-route-row span {
    color: var(--color-sidebar-active);
}

.a321-badge {
    background: rgba(8, 38, 129, 0.12);
    color: var(--color-sidebar-active);
    border-radius: 999px;
    font-size: 0.68rem;
    font-weight: 800;
    padding: 3px 8px;
}

.a321-or-divider {
    width: 38px;
    height: 38px;
    border-radius: 999px;
    border: 1px solid var(--color-border);
    background: #FFFFFF;
    display: grid;
    place-items: center;
    color: var(--color-text);
    font-weight: 850;
    margin: 94px auto 0;
    box-shadow: 0 8px 18px rgba(1, 23, 53, 0.08);
}

.a321-aircraft-card {
    min-height: 190px;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid var(--color-border);
    background: #FFFFFF;
}

.a321-aircraft-image {
    height: 112px;
    background:
        linear-gradient(115deg, rgba(255,255,255,0.04), rgba(255,255,255,0.76)),
        linear-gradient(180deg, #D8E8F7 0%, #FFFFFF 54%, #C9D3DD 55%, #E8EDF3 100%);
    position: relative;
}

.a321-aircraft-image::before {
    content: "";
    position: absolute;
    left: 36px;
    top: 47px;
    width: 190px;
    height: 20px;
    border-radius: 999px 35px 35px 999px;
    background: #FFFFFF;
    box-shadow: inset 0 -3px 0 rgba(1,23,53,0.18), 0 9px 14px rgba(1,23,53,0.14);
}

.a321-aircraft-image::after {
    content: "A321";
    position: absolute;
    left: 154px;
    top: 51px;
    color: var(--color-accent);
    font-size: 0.8rem;
    font-weight: 850;
}

.a321-aircraft-wing {
    position: absolute;
    left: 92px;
    top: 62px;
    width: 58px;
    height: 22px;
    background: var(--color-sidebar-active);
    clip-path: polygon(0 0, 100% 22%, 72% 100%, 12% 74%);
    opacity: 0.88;
}

.a321-aircraft-tail {
    position: absolute;
    right: 32px;
    top: 27px;
    width: 26px;
    height: 48px;
    background: var(--color-accent);
    clip-path: polygon(16% 0, 100% 0, 100% 100%, 0 82%);
}

.a321-airline-logo-panel {
    height: 126px;
    background: #FFFFFF;
    display: grid;
    place-items: center;
    border-bottom: 1px solid var(--color-border);
    padding: 12px;
}

.a321-airline-logo-panel img {
    display: block;
    max-width: 92%;
    max-height: 96px;
    object-fit: contain;
}

.a321-aircraft-copy {
    padding: 10px 12px 12px;
}

.a321-aircraft-copy strong {
    display: block;
    color: var(--color-text);
    font-size: 0.96rem;
    margin-bottom: 4px;
}

.a321-aircraft-copy span {
    color: var(--color-muted);
    font-size: 0.78rem;
}

.a321-detail-table {
    width: 100%;
    border-collapse: collapse;
    overflow: hidden;
    border-radius: 8px;
    border: 1px solid var(--color-border);
    font-size: 0.76rem;
}

.a321-detail-table td {
    border: 1px solid var(--color-border);
    padding: 9px 10px;
    color: var(--color-text);
    background: rgba(255,255,255,0.64);
}

.a321-detail-table td:nth-child(odd) {
    width: 22%;
    font-weight: 800;
    background: rgba(246,248,250,0.78);
}

.a321-card-heading-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}

.a321-card-heading-row h3 {
    display: flex;
    align-items: center;
    gap: 9px;
    margin: 0;
    font-size: 1rem;
}

.a321-save-flight {
    color: var(--color-text);
    font-size: 0.74rem;
    font-weight: 760;
}

.a321-simbrief-title {
    display: flex;
    gap: 9px;
    align-items: flex-start;
    margin-bottom: 10px;
}

.a321-simbrief-title h3 {
    margin: 0;
    font-size: 1rem;
}

.a321-simbrief-title p {
    margin: 2px 0 0;
    color: var(--color-muted);
    font-size: 0.75rem;
}

.a321-departure-board {
    background: linear-gradient(180deg, var(--color-board) 0%, #00102B 100%);
    color: #F8FAFC;
    border-radius: 10px;
    padding: 17px 20px 13px;
    border: 1px solid rgba(255,255,255,0.12);
    box-shadow: 0 12px 28px rgba(1, 23, 53, 0.18);
    overflow: hidden;
    width: 100%;
}

.a321-board-title {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #FFFFFF;
    font-size: 0.78rem;
    font-weight: 850;
    letter-spacing: 0.035em;
    margin-bottom: 8px;
}

.a321-board-labels,
.a321-board-row {
    display: grid;
    grid-template-columns: minmax(102px, 0.9fr) minmax(250px, 2.2fr) minmax(140px, 1.1fr) minmax(90px, 0.7fr) minmax(170px, 1.3fr);
    gap: 10px;
    align-items: center;
}

.a321-board-labels {
    font-family: "SF Mono", "Cascadia Mono", "Menlo", monospace;
    color: rgba(255,255,255,0.78);
    font-size: 0.72rem;
    text-transform: uppercase;
    margin: 0 8px 7px;
}

.a321-board-row {
    font-family: "SF Mono", "Cascadia Mono", "Menlo", monospace;
    font-size: clamp(1.35rem, 2.25vw, 2rem);
    line-height: 1.05;
    letter-spacing: 0.11em;
    color: #F8FAFC;
    background:
        repeating-linear-gradient(to right, transparent, transparent 18px, rgba(255,255,255,0.09) 18px, rgba(255,255,255,0.09) 19px),
        linear-gradient(180deg, var(--color-board-cell), #101A2B);
    padding: 13px 16px;
    border-top: 1px solid rgba(255,255,255,0.13);
    border-bottom: 1px solid rgba(0,0,0,0.5);
    box-shadow: inset 0 -4px 0 rgba(0,0,0,0.18);
}

.a321-board-cell {
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: clip;
}

.a321-board-remarks {
    color: var(--color-success);
}

.a321-board-meta {
    margin: 10px 9px 0;
    font-family: "SF Mono", "Cascadia Mono", "Menlo", monospace;
    font-size: 0.72rem;
    color: rgba(255,255,255,0.82);
    display: flex;
    gap: 42px;
    flex-wrap: wrap;
}

.a321-board-meta strong {
    color: #FFFFFF;
}

.a321-route-line {
    text-align: center;
    font-size: 1.05rem;
    font-weight: 800;
    margin: 9px 0 2px;
    color: var(--color-text);
}

.a321-route-arrow {
    display: inline-block;
    padding: 0 14px;
    color: var(--color-muted);
    font-weight: 850;
}

.a321-map-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.a321-map-title {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--color-text);
    font-weight: 800;
    font-size: 0.9rem;
}

.a321-map-control-group {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--color-muted);
    font-size: 0.74rem;
}

.a321-app-footer {
    margin: 22px 0 72px;
    padding: 18px 16px 22px;
    border-top: 1px solid var(--color-border);
    color: var(--color-muted);
    text-align: center;
    font-size: 0.78rem;
    font-weight: 650;
}

div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid var(--color-border);
    padding: 10px 12px;
    border-radius: 9px;
    box-shadow: none;
}

div[data-testid="stMetricValue"] {
    color: var(--color-text) !important;
    font-weight: 800 !important;
    letter-spacing: 0 !important;
}

div[data-testid="stMetricLabel"] {
    color: var(--color-muted) !important;
}

div[data-testid="stDataFrame"] {
    border: 1px solid var(--color-border);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: none;
}

div.stButton > button,
div.stDownloadButton > button {
    border-radius: 7px !important;
    font-weight: 760 !important;
    border: 1px solid var(--color-border) !important;
    min-height: 36px !important;
    background: #FFFFFF !important;
    color: var(--color-text) !important;
    box-shadow: none !important;
}

div.stButton > button:hover,
div.stDownloadButton > button:hover {
    border-color: var(--color-accent) !important;
    color: var(--color-primary) !important;
}

button[data-testid="stBaseButton-primary"],
div.stButton button[data-testid="stBaseButton-primary"],
div.stLinkButton > a {
    border-radius: 7px !important;
    font-weight: 800 !important;
    min-height: 42px !important;
    background: var(--color-primary) !important;
    border: 1px solid var(--color-primary) !important;
    color: #FFFFFF !important;
    box-shadow: none !important;
}

button[data-testid="stBaseButton-primary"]:hover,
div.stButton button[data-testid="stBaseButton-primary"]:hover,
div.stLinkButton > a:hover {
    background: var(--color-primary-hover) !important;
    color: #FFFFFF !important;
}

button[data-testid="stBaseButton-primary"] *,
div.stButton button[data-testid="stBaseButton-primary"] *,
div.stLinkButton > a * {
    color: #FFFFFF !important;
}

div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
    border-radius: 7px !important;
    border: 1px solid var(--color-border) !important;
    background: #FFFFFF !important;
    color: var(--color-text) !important;
    min-height: 36px !important;
}

div[data-testid="stSelectbox"] > div {
    border-radius: 7px !important;
}

div[data-testid="stToggle"] label {
    color: var(--color-text) !important;
}

div[data-testid="stAlert"] {
    border-radius: 8px !important;
    border: 1px solid var(--color-border) !important;
}

div[data-testid="stForm"] {
    border: 0 !important;
    padding: 0 !important;
}

div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] {
    height: 0 !important;
    min-height: 0 !important;
    overflow: hidden !important;
    visibility: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
}

hr {
    margin: 0.75rem 0 !important;
    border-color: transparent !important;
}

@media (max-width: 900px) {
    section[data-testid="stSidebar"] {
        width: 128px !important;
        min-width: 128px !important;
    }
    .block-container {
        padding: 8px;
    }
    .a321-board-labels,
    .a321-board-row {
        grid-template-columns: 0.8fr 1.5fr 0.9fr 0.6fr 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

AIRLINE_NAMES = {
    "ACA": "Air Canada",
    "WJA": "WestJet",
    "UAL": "United Airlines",
    "AAL": "American Airlines",
    "DAL": "Delta Air Lines",
    "SWA": "Southwest Airlines",
    "BAW": "British Airways",
    "AFR": "Air France",
    "KLM": "KLM Royal Dutch Airlines",
    "DLH": "Lufthansa",
    "QTR": "Qatar Airways",
    "UAE": "Emirates",
    "QFA": "Qantas",
    "SIA": "Singapore Airlines",
    "RYR": "Ryanair",
    "JBU": "JetBlue",
}

_DIGITS = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"
}


def get_announcements_dir(airline_code: str):
    if not ANNOUNCEMENTS_BASE_DIR:
        raise ValueError("Announcements folder is not configured.")

    code = (airline_code or "DEFAULT").strip().upper()
    base_path = Path(ANNOUNCEMENTS_BASE_DIR).expanduser()
    if base_path.name.strip().upper() == code:
        path = base_path
    else:
        path = base_path / code
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def say_airline(code: str) -> str:
    c = (code or "").strip().upper()
    if not c:
        return "your airline"
    return AIRLINE_NAMES.get(
        c,
        " ".join(ch if ch.isalpha() else _DIGITS.get(ch, ch) for ch in c if ch.isalnum())
    )


def speak_flight_number(fltnum: str) -> str:
    s = re.sub(r"\D", "", (fltnum or ""))
    if not s:
        return "one eight four six"
    return " ".join(_DIGITS.get(ch, ch) for ch in s)


def build_dispatch_redirect(airline, fltnum, aircraft, orig, dest, passengers, departure_time_z=""):
    base = "https://dispatch.simbrief.com/options/custom"
    params = []

    if airline and airline.strip():
        params.append(f"airline={airline.strip()}")
    if fltnum and fltnum.strip():
        params.append(f"fltnum={fltnum.strip()}")
    if aircraft and aircraft.strip():
        params.append(f"type={aircraft.strip()}")
    if orig and len(orig.strip()) == 4:
        params.append(f"orig={orig.strip().upper()}")
    if dest and len(dest.strip()) == 4:
        params.append(f"dest={dest.strip().upper()}")
    if passengers and passengers.strip().isdigit():
        params.append(f"pax={passengers.strip()}")

    m = re.match(r"^\s*(\d{1,2}):(\d{2})z?\s*$", str(departure_time_z), flags=re.IGNORECASE)
    if m:
        params.append(f"deph={int(m.group(1)):02d}")
        params.append(f"depm={int(m.group(2)):02d}")

    return base + ("?" + "&".join(params) if params else "")


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def city_country(city, country):
    city = "" if pd.isna(city) else str(city).strip()
    country = "" if pd.isna(country) else str(country).strip()
    if city and country:
        return f"{city}, {country}"
    return city or country or ""


def normalize_search_text(value) -> str:
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text.casefold()).strip()


def estimate_block_minutes(distance_nm: float, avg_speed_kts: float = 450.0, fixed_buffer_min: int = 30):
    if pd.isna(distance_nm):
        return None
    enroute_minutes = (distance_nm / avg_speed_kts) * 60.0
    return int(round(enroute_minutes + fixed_buffer_min))


def minutes_to_hmm(m):
    if pd.isna(m):
        return ""
    m = int(m)
    h = m // 60
    mins = m % 60
    return f"{h}:{mins:02d}"


def duration_text_to_minutes(value) -> int | None:
    text = str(value or "").strip().lower()
    if not text:
        return None
    match = re.match(r"^(\d+):(\d{2})$", text)
    if match:
        return int(match.group(1)) * 60 + int(match.group(2))
    hour_match = re.search(r"(\d+)\s*h", text)
    minute_match = re.search(r"(\d+)\s*m", text)
    if hour_match or minute_match:
        hours = int(hour_match.group(1)) if hour_match else 0
        minutes = int(minute_match.group(1)) if minute_match else 0
        return hours * 60 + minutes
    numeric = re.search(r"\d+", text)
    return int(numeric.group(0)) if numeric else None


def estimated_arrival_from_departure(departure_time: str, duration_text: str, fallback: str = "Auto after SimBrief") -> str:
    dep_match = re.search(r"(\d{1,2}):(\d{2})", str(departure_time or ""))
    minutes = duration_text_to_minutes(duration_text)
    if not dep_match or minutes is None:
        return fallback
    departure_minutes = int(dep_match.group(1)) * 60 + int(dep_match.group(2))
    arrival_minutes = (departure_minutes + minutes) % (24 * 60)
    return f"{arrival_minutes // 60:02d}:{arrival_minutes % 60:02d} LT"


def current_departure_time() -> str:
    return datetime.now().strftime("%H:%M")


def render_departure_board(selected_row):
    if selected_row is None:
        return

    dep_time = str(selected_row.get("departure_time_z", "--:--") or "--:--").replace("z", "")
    arr_icao = str(selected_row.get("arrival_icao", "----") or "----")
    is_reference = str(selected_row.get("source", "")).lower() == "reference"
    arr_city = "PARIS CDG" if is_reference else str(
        selected_row.get("arr_city", "")
        or selected_row.get("arrival_city_country", "")
        or arr_icao
    ).upper()
    dep_icao = str(selected_row.get("departure_icao", "----") or "----")
    duration = str(selected_row.get("duration_minutes_or_text", "") or "")
    est_block = str(selected_row.get("estimated_block_time", "") or "")

    airline_code = airline_code_for_theme(active_theme_key())
    flight_num = current_flight_number()
    gate = "A21"
    status = "BOARDING"
    flight_display = f"{airline_code}{flight_num}"

    distance_text = (
        f"{selected_row.get('distance_nm', 0):.0f} NM"
        if pd.notna(selected_row.get("distance_nm", None))
        else ""
    )

    board_html = f"""
    <div class="a321-departure-board">
        <div class="a321-board-title">
            <svg width="18" height="18" viewBox="0 0 64 64" fill="none" aria-hidden="true">
                <path d="M8 34L56 14L49 27L58 31L56 37L46 36L34 52L28 50L32 35L17 39L8 34Z" fill="white"/>
            </svg>
            <span>SELECTED FLIGHT / BOARDING BOARD</span>
        </div>
        <div class="a321-board-labels">
            <div>Time</div><div>Destination</div><div>Flight</div><div>Gate</div><div>Status</div>
        </div>
        <div class="a321-board-row">
            <div class="a321-board-cell">{escape(dep_time)}</div>
            <div class="a321-board-cell">{escape(arr_city)}</div>
            <div class="a321-board-cell" data-a321-flight-designator="true">{escape(flight_display)}</div>
            <div class="a321-board-cell">{escape(gate)}</div>
            <div class="a321-board-cell a321-board-remarks">{escape(status)}</div>
        </div>
        <div class="a321-board-meta">
            <span><strong>From:</strong> {escape(dep_icao)}</span>
            <span><strong>To:</strong> {escape(arr_icao)}</span>
            <span><strong>Sched:</strong> {escape(duration)}</span>
            <span><strong>Est. Block:</strong> {escape(est_block)}</span>
            <span><strong>Distance:</strong> {escape(distance_text)}</span>
        </div>
    </div>
    """.strip()

    st.html(board_html)


def render_flight_details_table(route_row: dict | pd.Series | None, dep_info: dict | None, dest_info: dict | None) -> None:
    if route_row is None:
        st.info("Select one known route above or apply a custom airport pair.")
        return

    def row_get(key: str, fallback: str = "") -> str:
        try:
            value = route_row.get(key, fallback)
        except AttributeError:
            value = fallback
        if pd.isna(value):
            return fallback
        return str(value)

    dep_code = row_get("departure_icao")
    arr_code = row_get("arrival_icao")
    dep_place = row_get("departure_city_country") or city_country(
        (dep_info or {}).get("city", ""),
        (dep_info or {}).get("country", ""),
    )
    arr_place = row_get("arrival_city_country") or city_country(
        (dest_info or {}).get("city", ""),
        (dest_info or {}).get("country", ""),
    )
    distance_nm = row_get("distance_nm")
    if distance_nm:
        try:
            distance_nm = f"{float(distance_nm):.0f} NM"
        except Exception:
            pass

    is_reference = str(row_get("source", "")).lower() == "reference"
    flight_display = current_flight_display()
    dep_weather = format_airport_weather_summary(
        dep_info,
        OPENWEATHERMAP_API_KEY,
        "14°C, SCT 3500, BKN 12000, Q1018" if is_reference else "Add OpenWeather API key in Settings",
    )
    arr_weather = format_airport_weather_summary(
        dest_info,
        OPENWEATHERMAP_API_KEY,
        "16°C, FEW 3500, SCT 10000, Q1017" if is_reference else "Add OpenWeather API key in Settings",
    )
    if is_reference:
        rows = [
            ("Departure", "EGLL - London Heathrow", "Estimated Arrival Time", estimated_arrival_from_departure("10:30", "1h 15m")),
            ("Arrival", "LFPG - Paris Charles de Gaulle", "Distance", "214 NM"),
            ("Local Departure Time", "12 May 2024 10:30 LT", "Passenger Count", "180"),
            ("Flight Duration", "1h 15m", "Cruise Altitude", "FL340"),
            ("Weather (Departure)", dep_weather, "Route Type", "Direct"),
            ("Weather (Arrival)", arr_weather, "Airline / Callsign", flight_display),
        ]
    else:
        duration_text = row_get("duration_minutes_or_text")
        rows = [
            ("Departure", f"{dep_code} - {dep_place}", "Estimated Arrival Time", estimated_arrival_from_departure(row_get("departure_time_z"), duration_text, row_get("arrival_time_z", "Auto after SimBrief"))),
            ("Arrival", f"{arr_code} - {arr_place}", "Distance", distance_nm),
            ("Local Departure Time", f"{row_get('departure_time_z')} LT", "Passenger Count", st.session_state.get("pax_input", "175")),
            ("Flight Duration", duration_text, "Cruise Altitude", "FL340"),
            ("Weather (Departure)", dep_weather, "Route Type", "Direct"),
            ("Weather (Arrival)", arr_weather, "Airline / Callsign", flight_display),
        ]

    row_html_parts = []
    for label_a, value_a, label_b, value_b in rows:
        value_a_html = escape(value_a)
        value_b_html = escape(value_b)
        if label_a == "Airline / Callsign":
            value_a_html = f'<span data-a321-flight-designator="true">{escape(value_a)}</span>'
        if label_b == "Airline / Callsign":
            value_b_html = f'<span data-a321-flight-designator="true">{escape(value_b)}</span>'
        row_html_parts.append(
            "<tr>"
            f"<td>{escape(label_a)}</td><td>{value_a_html}</td>"
            f"<td>{escape(label_b)}</td><td>{value_b_html}</td>"
            "</tr>"
        )
    row_html = "\n".join(row_html_parts)
    st.html(f"<table class='a321-detail-table'>{row_html}</table>")


@st.cache_data(show_spinner=False)
def load_airports():
    if not os.path.exists(AIRPORTS_JSON):
        return pd.DataFrame(columns=["icao", "name", "city", "country", "lat", "lon", "tz"])

    with open(AIRPORTS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for icao, info in data.items():
        rows.append({
            "icao": str(icao).upper(),
            "name": info.get("name", ""),
            "city": info.get("city", ""),
            "country": info.get("country", ""),
            "lat": info.get("lat", None),
            "lon": info.get("lon", None),
            "tz": info.get("tz", ""),
        })

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["lat", "lon"]).copy()
    df["icao"] = df["icao"].astype(str).str.upper()
    return df


@st.cache_data(show_spinner=False)
def load_country_lookup() -> dict[str, str]:
    countries_path = APP_DIR / "countries.csv"
    if not countries_path.exists():
        return {}
    try:
        countries_df = pd.read_csv(countries_path)
    except Exception:
        return {}
    if not {"code", "name"}.issubset(countries_df.columns):
        return {}
    return {
        str(row["code"]).strip().upper(): str(row["name"]).strip()
        for _, row in countries_df.dropna(subset=["code", "name"]).iterrows()
    }


@st.cache_data(show_spinner=False)
def load_routes():
    if not os.path.exists(ROUTES_CSV):
        return pd.DataFrame()

    df = pd.read_csv(ROUTES_CSV)
    df.columns = [c.strip() for c in df.columns]

    df = df.rename(columns={
        "Departure ICAO": "departure_icao",
        "Departure Time": "departure_time_z",
        "Arrival ICAO": "arrival_icao",
        "Arrival Time": "arrival_time_z",
        "Flight Duration": "duration_minutes_or_text",
        "Duration": "duration_minutes_or_text",
    })

    required = [
        "departure_icao",
        "departure_time_z",
        "arrival_icao",
        "arrival_time_z",
        "duration_minutes_or_text",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return pd.DataFrame()

    if "flight_number" not in df.columns:
        df["flight_number"] = ""

    def parse_minutes(v):
        if pd.isna(v):
            return None
        s = str(v).strip()
        m = re.match(r"^(\d{1,2}):(\d{2})$", s)
        if m:
            return int(m.group(1)) * 60 + int(m.group(2))
        try:
            return int(float(s))
        except Exception:
            return None

    df["duration_minutes"] = df["duration_minutes_or_text"].apply(parse_minutes)
    df = df[df["duration_minutes"].notna()].copy()
    df["duration_minutes"] = df["duration_minutes"].astype(int)

    df["departure_icao"] = df["departure_icao"].astype(str).str.upper().str.strip()
    df["arrival_icao"] = df["arrival_icao"].astype(str).str.upper().str.strip()
    df["flight_number"] = df["flight_number"].astype(str)

    df["airline_code"] = (
        df["flight_number"]
        .str.extract(r"^([A-Za-z]{2,3})", expand=False)
        .fillna("")
        .str.upper()
    )

    df["flight_number_numeric"] = (
        df["flight_number"]
        .str.extract(r"(\d+)", expand=False)
        .fillna("")
    )

    df = df.reset_index(drop=True)
    df["route_id"] = df.index.astype(int)
    return df


def city_country_series(city: pd.Series, country: pd.Series) -> pd.Series:
    city_text = city.fillna("").astype(str).str.strip()
    country_text = country.fillna("").astype(str).str.strip()
    result = city_text.copy()
    has_city = city_text != ""
    has_country = country_text != ""
    result = result.mask(has_city & has_country, city_text + ", " + country_text)
    result = result.mask(~has_city & has_country, country_text)
    return result


@st.cache_data(show_spinner=False)
def prepare_routes_dataset(routes: pd.DataFrame, airports_df: pd.DataFrame, country_names: dict[str, str]) -> pd.DataFrame:
    if routes.empty:
        return routes.copy()

    prepared = routes.copy()
    if airports_df.empty:
        prepared["departure_city_country"] = ""
        prepared["arrival_city_country"] = ""
        prepared["departure_place"] = ""
        prepared["arrival_place"] = ""
        prepared["route_search_blob"] = prepared[["departure_icao", "arrival_icao"]].fillna("").astype(str).agg(" ".join, axis=1).map(normalize_search_text)
        prepared["distance_km"] = None
        prepared["distance_nm"] = None
        prepared["estimated_block_minutes"] = None
        prepared["estimated_block_time"] = ""
        return prepared

    airport_meta = airports_df[["icao", "name", "city", "country", "lat", "lon"]].copy()
    airport_meta["country_name"] = (
        airport_meta["country"]
        .fillna("")
        .astype(str)
        .str.upper()
        .map(country_names)
        .fillna(airport_meta["country"])
    )

    prepared = prepared.merge(
        airport_meta.rename(columns={
            "icao": "departure_icao",
            "name": "dep_name",
            "city": "dep_city",
            "country": "dep_country",
            "country_name": "dep_country_name",
            "lat": "dep_lat",
            "lon": "dep_lon",
        }),
        on="departure_icao",
        how="left",
    )

    prepared = prepared.merge(
        airport_meta.rename(columns={
            "icao": "arrival_icao",
            "name": "arr_name",
            "city": "arr_city",
            "country": "arr_country",
            "country_name": "arr_country_name",
            "lat": "arr_lat",
            "lon": "arr_lon",
        }),
        on="arrival_icao",
        how="left",
    )

    prepared["departure_city_country"] = city_country_series(prepared["dep_city"], prepared["dep_country"])
    prepared["arrival_city_country"] = city_country_series(prepared["arr_city"], prepared["arr_country"])
    prepared["departure_place"] = city_country_series(prepared["dep_city"], prepared["dep_country_name"].fillna(prepared["dep_country"]))
    prepared["arrival_place"] = city_country_series(prepared["arr_city"], prepared["arr_country_name"].fillna(prepared["arr_country"]))

    search_columns = [
        "departure_icao",
        "arrival_icao",
        "dep_name",
        "arr_name",
        "dep_city",
        "arr_city",
        "dep_country",
        "arr_country",
        "dep_country_name",
        "arr_country_name",
        "departure_time_z",
        "arrival_time_z",
        "duration_minutes_or_text",
    ]
    search_text = prepared[search_columns].fillna("").astype(str).agg(" ".join, axis=1)
    prepared["route_search_blob"] = search_text.map(normalize_search_text)

    coords = ["dep_lat", "dep_lon", "arr_lat", "arr_lon"]
    valid_coords = prepared[coords].notna().all(axis=1)
    prepared["distance_km"] = None
    if valid_coords.any():
        dep_lat = np.radians(prepared.loc[valid_coords, "dep_lat"].astype(float))
        dep_lon = np.radians(prepared.loc[valid_coords, "dep_lon"].astype(float))
        arr_lat = np.radians(prepared.loc[valid_coords, "arr_lat"].astype(float))
        arr_lon = np.radians(prepared.loc[valid_coords, "arr_lon"].astype(float))
        dlat = arr_lat - dep_lat
        dlon = arr_lon - dep_lon
        hav = np.sin(dlat / 2) ** 2 + np.cos(dep_lat) * np.cos(arr_lat) * np.sin(dlon / 2) ** 2
        prepared.loc[valid_coords, "distance_km"] = 6371.0 * 2 * np.arcsin(np.sqrt(hav))
    prepared["distance_nm"] = pd.to_numeric(prepared["distance_km"], errors="coerce") / 1.852
    prepared["estimated_block_minutes"] = prepared["distance_nm"].apply(estimate_block_minutes)
    prepared["estimated_block_time"] = prepared["estimated_block_minutes"].apply(minutes_to_hmm)
    return prepared


def lookup_airport(ap_df, icao):
    code = (icao or "").strip().upper()
    if not code or ap_df.empty:
        return None
    m = ap_df[ap_df["icao"] == code]
    return None if m.empty else m.iloc[0].to_dict()


def airport_display_label(icao: str, airport_lookup: dict[str, dict]) -> str:
    code = (icao or "").strip().upper()
    info = airport_lookup.get(code, {})
    name = str(info.get("name", "") or "").strip()
    place = city_country(info.get("city", ""), info.get("country", ""))

    if name and place:
        return f"{code} - {name} ({place})"
    if name:
        return f"{code} - {name}"
    if place:
        return f"{code} - {place}"
    return code


def sync_headers(settings: dict[str, str]) -> dict[str, str]:
    key = settings.get("sync_supabase_key", "").strip()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def selected_flight_payload(
    route_row: dict | pd.Series,
    dep_info: dict | None,
    dest_info: dict | None,
    source: str,
    planned_from_device: str,
) -> dict:
    def row_get(key: str, fallback=""):
        try:
            value = route_row.get(key, fallback)
        except AttributeError:
            value = fallback
        if pd.isna(value):
            return fallback
        return value

    dep_code = str(row_get("departure_icao", "")).strip().upper()
    arr_code = str(row_get("arrival_icao", "")).strip().upper()
    distance_nm = row_get("distance_nm", "")
    try:
        distance_nm = round(float(distance_nm))
    except Exception:
        distance_nm = None

    now_iso = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    return {
        "userId": ACTIVE_SETTINGS.get("sync_user_id", "").strip(),
        "source": source,
        "departureIcao": dep_code,
        "arrivalIcao": arr_code,
        "departureName": (dep_info or {}).get("name", ""),
        "arrivalName": (dest_info or {}).get("name", ""),
        "departureCity": (dep_info or {}).get("city", row_get("dep_city", "")),
        "arrivalCity": (dest_info or {}).get("city", row_get("arr_city", "")),
        "departureCountry": (dep_info or {}).get("country", row_get("dep_country", "")),
        "arrivalCountry": (dest_info or {}).get("country", row_get("arr_country", "")),
        "departureLat": (dep_info or {}).get("lat", row_get("dep_lat", None)),
        "departureLon": (dep_info or {}).get("lon", row_get("dep_lon", None)),
        "arrivalLat": (dest_info or {}).get("lat", row_get("arr_lat", None)),
        "arrivalLon": (dest_info or {}).get("lon", row_get("arr_lon", None)),
        "localDepartureTime": str(row_get("departure_time_z", "")),
        "flightDuration": str(row_get("duration_minutes_or_text", "")),
        "estimatedBlockTime": str(row_get("estimated_block_time", "")),
        "distanceNm": distance_nm,
        "passengerCount": st.session_state.get("pax_input", "175"),
        "cruiseAltitude": "FL340",
        "routeType": "Direct",
        "airline": airline_code_for_theme(active_theme_key()),
        "callsign": current_flight_display(),
        "flightNumber": current_flight_number(),
        "gate": "A21",
        "status": "BOARDING",
        "departureWeather": format_airport_weather_summary(dep_info, OPENWEATHERMAP_API_KEY, ""),
        "arrivalWeather": format_airport_weather_summary(dest_info, OPENWEATHERMAP_API_KEY, ""),
        "aircraftType": st.session_state.get("aircraft_select", "A321"),
        "plannedFromDevice": planned_from_device,
        "createdAt": now_iso,
        "updatedAt": now_iso,
    }


def sync_selected_flight_to_cloud(
    route_row: dict | pd.Series,
    dep_info: dict | None,
    dest_info: dict | None,
    source: str,
) -> None:
    if not cloud_sync_configured(ACTIVE_SETTINGS):
        return

    payload = selected_flight_payload(route_row, dep_info, dest_info, source, "desktop")
    url = ACTIVE_SETTINGS["sync_supabase_url"].rstrip("/") + "/rest/v1/selected_flights"
    try:
        response = requests.post(url, headers=sync_headers(ACTIVE_SETTINGS), json=payload, timeout=8)
        if response.ok:
            st.session_state["sync_notice"] = "Selected flight synced to cloud."
        else:
            st.session_state["sync_notice"] = f"Cloud sync failed: {response.status_code}"
    except Exception as exc:
        st.session_state["sync_notice"] = f"Cloud sync offline: {exc}"


def load_latest_selected_flight_from_cloud() -> dict | None:
    if not cloud_sync_configured(ACTIVE_SETTINGS):
        return None

    base_url = ACTIVE_SETTINGS["sync_supabase_url"].rstrip("/") + "/rest/v1/selected_flights"
    params = {
        "userId": f"eq.{ACTIVE_SETTINGS['sync_user_id']}",
        "order": "updatedAt.desc",
        "limit": "1",
    }
    try:
        response = requests.get(base_url, headers=sync_headers(ACTIVE_SETTINGS), params=params, timeout=8)
        if not response.ok:
            st.session_state["sync_notice"] = f"Cloud load failed: {response.status_code}"
            return None
        rows = response.json()
        return rows[0] if rows else None
    except Exception as exc:
        st.session_state["sync_notice"] = f"Cloud sync offline: {exc}"
        return None


@st.cache_data(show_spinner=False, ttl=300)
def get_openweather_current(lat, lon, api_key):
    if not api_key:
        return {"ok": False, "reason": "missing_key"}
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": float(lat),
                "lon": float(lon),
                "units": "metric",
                "appid": api_key,
            },
            timeout=2.5,
        )
        if response.ok:
            return {"ok": True, "data": response.json()}
        return {"ok": False, "reason": f"HTTP {response.status_code}"}
    except Exception as exc:
        return {"ok": False, "reason": str(exc)}


@st.cache_data(show_spinner=False, ttl=300)
def get_temperature(lat, lon, api_key):
    payload = get_openweather_current(lat, lon, api_key)
    if payload.get("ok"):
        try:
            return int(round(payload["data"]["main"]["temp"]))
        except Exception:
            pass
    return None


@st.cache_data(show_spinner=False, ttl=300)
def get_weather(lat, lon, api_key):
    payload = get_openweather_current(lat, lon, api_key)
    if payload.get("ok"):
        try:
            return payload["data"]["weather"][0]["main"]
        except Exception:
            pass
    return None


def format_wind_from_openweather(wind: dict) -> str:
    speed_mps = wind.get("speed")
    if speed_mps is None:
        return ""
    try:
        speed_kt = int(round(float(speed_mps) * 1.94384))
    except Exception:
        return ""

    deg = wind.get("deg")
    if deg is None:
        return f"Wind {speed_kt} kt"
    try:
        return f"Wind {int(round(float(deg))) % 360:03d}°/{speed_kt} kt"
    except Exception:
        return f"Wind {speed_kt} kt"


def format_airport_weather_summary(
    airport_info: dict | None,
    api_key: str,
    fallback: str = "Weather unavailable",
) -> str:
    if not airport_info:
        return fallback
    if not api_key:
        return fallback

    lat = airport_info.get("lat")
    lon = airport_info.get("lon")
    if lat in (None, "") or lon in (None, ""):
        return fallback

    payload = get_openweather_current(lat, lon, api_key)
    if not payload.get("ok"):
        return fallback

    data = payload.get("data", {})
    main = data.get("main", {})
    weather_rows = data.get("weather") or [{}]
    wind = data.get("wind") or {}
    clouds = data.get("clouds") or {}

    parts: list[str] = []
    temp = main.get("temp")
    if temp is not None:
        try:
            parts.append(f"{int(round(float(temp)))}°C")
        except Exception:
            pass

    description = str(weather_rows[0].get("description") or weather_rows[0].get("main") or "").strip()
    if description:
        parts.append(description.title())

    wind_text = format_wind_from_openweather(wind)
    if wind_text:
        parts.append(wind_text)

    cloud_cover = clouds.get("all")
    if cloud_cover is not None:
        try:
            parts.append(f"Clouds {int(round(float(cloud_cover)))}%")
        except Exception:
            pass

    pressure = main.get("pressure")
    if pressure is not None:
        try:
            parts.append(f"Q{int(round(float(pressure)))}")
        except Exception:
            pass

    return ", ".join(parts) if parts else fallback


def adjective_from_openweather(main: str) -> str:
    mapping = {
        "clouds": "cloudy",
        "clear": "clear",
        "rain": "rainy",
        "drizzle": "drizzly",
        "snow": "snowy",
        "thunderstorm": "stormy",
        "mist": "misty",
        "fog": "foggy",
        "haze": "hazy",
        "smoke": "smoky",
        "dust": "dusty",
        "sand": "sandy",
        "squall": "squally",
        "tornado": "tornadic",
        "ash": "volcanic ash",
    }
    w = (main or "").strip().lower()
    return mapping.get(w, w or "unknown")


def generate_audio(text, voice_id, filename):
    if not ELEVENLABS_API_KEY:
        st.error("Open App Settings from the menu and add your ElevenLabs API key.")
        return None

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    payload = {"text": text, "model_id": "eleven_multilingual_v2"}

    response = requests.post(url, json=payload, headers=headers, stream=True, timeout=30)
    if response.status_code != 200:
        st.error(f"Failed to generate audio for {filename}: {response.text}")
        return None

    save_dir = get_announcements_dir(st.session_state.get("airline_input", "DEFAULT"))
    output_path = os.path.join(save_dir, filename)
    try:
        ogg_bytes = convert_mp3_bytes_to_ogg(response.content)
    except Exception as exc:
        st.error(f"Failed to prepare audio for {filename}: {exc}")
        return None

    with open(output_path, "wb") as f:
        f.write(ogg_bytes)

    return response.content


def create_announcement_files(dep_icao_edit: str, dest_icao_edit: str, airline: str, fltnum: str, flight_time_text: str):
    dep_info = lookup_airport(airports, dep_icao_edit)
    dest_info = lookup_airport(airports, dest_icao_edit)

    if not dep_info or not dest_info:
        st.error("Departure or arrival airport not found in airports.json.")
        return []
    if not ELEVENLABS_API_KEY:
        st.error("Open Settings and add your ElevenLabs API key first.")
        return []

    est_tz = pytz.timezone("America/Toronto")
    current_time_est = datetime.now(est_tz).replace(tzinfo=None)
    current_time_str = current_time_est.strftime("%I:%M %p").lstrip("0")

    ete_str = flight_time_text or st.session_state.get("selected_duration") or "unknown"

    distance_km = haversine_km(dep_info["lat"], dep_info["lon"], dest_info["lat"], dest_info["lon"])
    distance_nm = distance_km / 1.852
    avg_speed_kts = 450
    flight_hours = distance_nm / avg_speed_kts + 0.5
    arrival_time_est = current_time_est + pd.Timedelta(hours=flight_hours)
    arrival_time_str = arrival_time_est.strftime("%I:%M %p").lstrip("0")

    temp_c = get_temperature(dest_info["lat"], dest_info["lon"], OPENWEATHERMAP_API_KEY)
    wx_main = get_weather(dest_info["lat"], dest_info["lon"], OPENWEATHERMAP_API_KEY)
    temp_str = f"{temp_c}" if temp_c is not None else "unknown"
    wx_adj = adjective_from_openweather(wx_main)

    airline_spoken = say_airline(airline)
    fltnum_spoken = speak_flight_number(fltnum)
    dest_city = dest_info.get("city", dest_info["icao"])
    dep_city = dep_info.get("city", dep_info["icao"])

    boarding_text = (
        f"Welcome aboard {airline_spoken} flight {fltnum_spoken} from {dep_city} to {dest_info['name']}. "
        f"The current local time is {current_time_str} and our estimated flight time today is {ete_str}. "
        f"The current temperature in {dest_city} is {temp_str} degrees centigrade and the weather is {wx_adj}. "
        "We are currently boarding all groups. Please have your boarding pass and identification ready. "
        f"We look forward to offering you a pleasant flight today aboard {airline_spoken}."
    )

    descent_text = (
        f"Ladies and gentlemen, as we start our descent into {dest_city}, please ensure your seat belts are fastened. "
        f"We are currently about seventy-five miles from {dest_info['name']} and should arrive in the next twenty to thirty minutes. "
        "Thank you."
    )

    landing_text = (
        f"Ladies and gentlemen, welcome to {dest_info['name']}, where the current local time is {arrival_time_str} "
        f"and the temperature is {temp_str} degrees centigrade. For your safety, please remain seated with your seatbelt fastened until "
        "the Captain turns off the Fasten Seatbelt sign. Remember to check your seat pocket and overhead bins for personal belongings. "
        f"Once again, thank you for choosing to fly with us today at {airline_spoken}; we look forward to seeing you again soon."
    )

    voice_id = "nPczCjzI2devNBz1zQrb"
    announcements_dir = get_announcements_dir(airline)
    files = [
        ("BoardingWelcome.ogg", generate_audio(boarding_text, voice_id, "BoardingWelcome.ogg")),
        ("DescentSeatbelts.ogg", generate_audio(descent_text, voice_id, "DescentSeatbelts.ogg")),
        ("AfterLanding.ogg", generate_audio(landing_text, voice_id, "AfterLanding.ogg")),
    ]
    return [
        (filename, audio_bytes, os.path.join(announcements_dir, filename))
        for filename, audio_bytes in files
        if audio_bytes
    ]


def render_route_map(dep_info, dest_info, map_style, height: int = 340):
    if not dep_info or not dest_info:
        return

    try:
        import pydeck as pdk
    except ImportError:
        st.warning("pydeck is not installed. Run: pip install pydeck")
        return

    points_df = pd.DataFrame([
        {
            "label": f"Departure: {dep_info.get('icao', '')} - {dep_info.get('city', '')}",
            "lat": dep_info["lat"],
            "lon": dep_info["lon"],
            "color": [53, 216, 122, 235],
        },
        {
            "label": f"Arrival: {dest_info.get('icao', '')} - {dest_info.get('city', '')}",
            "lat": dest_info["lat"],
            "lon": dest_info["lon"],
            "color": [239, 68, 68, 235],
        },
    ])

    is_reference_map = dep_info.get("icao") == "EGLL" and dest_info.get("icao") == "LFPG"
    dep_label = (
        "EGLL\nLondon Heathrow\n10:30 LT"
        if is_reference_map
        else f"{dep_info.get('icao', '')}\n{dep_info.get('name', dep_info.get('city', ''))}"
    )
    arr_label = (
        "LFPG\nParis CDG\n11:45 LT"
        if is_reference_map
        else f"{dest_info.get('icao', '')}\n{dest_info.get('name', dest_info.get('city', ''))}"
    )
    label_df = pd.DataFrame([
        {
            "text": dep_label,
            "lat": dep_info["lat"] + 0.18,
            "lon": dep_info["lon"] - 0.7,
            "color": [255, 255, 255, 245],
        },
        {
            "text": "DVR\nFL340" if is_reference_map else "FL340",
            "lat": (dep_info["lat"] + dest_info["lat"]) / 2 + 0.36,
            "lon": (dep_info["lon"] + dest_info["lon"]) / 2,
            "color": [255, 255, 255, 245],
        },
        {
            "text": arr_label,
            "lat": dest_info["lat"] - 0.16,
            "lon": dest_info["lon"] + 0.62,
            "color": [255, 255, 255, 245],
        },
    ])

    line_df = pd.DataFrame([
        {
            "start_lon": dep_info["lon"],
            "start_lat": dep_info["lat"],
            "end_lon": dest_info["lon"],
            "end_lat": dest_info["lat"],
        }
    ])

    center_lat = (dep_info["lat"] + dest_info["lat"]) / 2
    dep_lon = dep_info["lon"]
    dest_lon = dest_info["lon"]
    raw_lon_span = abs(dep_lon - dest_lon)
    lon_span = min(raw_lon_span, 360 - raw_lon_span)
    if raw_lon_span > 180:
        center_lon = ((dep_lon + dest_lon + 360) / 2) % 360
        if center_lon > 180:
            center_lon -= 360
    else:
        center_lon = (dep_lon + dest_lon) / 2

    lat_span = abs(dep_info["lat"] - dest_info["lat"])
    route_distance_km = haversine_km(dep_info["lat"], dep_lon, dest_info["lat"], dest_lon)
    route_span = max(lat_span, lon_span)
    if route_distance_km > 8500 or route_span > 100:
        route_zoom = 1.25
    elif route_distance_km > 4500 or route_span > 55:
        route_zoom = 1.75
    elif route_distance_km > 2200 or route_span > 28:
        route_zoom = 2.45
    elif route_distance_km > 900 or route_span > 12:
        route_zoom = 3.25
    else:
        route_zoom = 4.35

    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=points_df,
        get_position="[lon, lat]",
        get_fill_color="color",
        get_radius=30000,
        pickable=True,
    )

    line_layer = pdk.Layer(
        "LineLayer",
        data=line_df,
        get_source_position="[start_lon, start_lat]",
        get_target_position="[end_lon, end_lat]",
        get_color=[255, 132, 31, 245],
        get_width=6,
        pickable=False,
    )

    text_layer = pdk.Layer(
        "TextLayer",
        data=label_df,
        get_position="[lon, lat]",
        get_text="text",
        get_color="color",
        get_size=13,
        get_text_anchor="middle",
        get_alignment_baseline="center",
        pickable=False,
    )

    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=route_zoom,
        pitch=0,
    )

    deck = pdk.Deck(
        map_style=map_style,
        initial_view_state=view_state,
        layers=[line_layer, scatter_layer, text_layer],
        tooltip={"text": "{label}"},
    )

    st.pydeck_chart(deck, use_container_width=True, height=height)


def minutes_to_hhmm(m: int) -> str:
    h = m // 60
    mins = m % 60
    return f"{h:02d}:{mins:02d}"


def ceil_to_5(x: int) -> int:
    return ((x + 4) // 5) * 5


def sync_settings_form_state(active_settings: dict[str, str]) -> None:
    signature = json.dumps(active_settings, sort_keys=True)
    if st.session_state.get("_settings_form_signature") == signature:
        return

    st.session_state["settings_openweathermap_api_key"] = active_settings["openweathermap_api_key"]
    st.session_state["settings_elevenlabs_api_key"] = active_settings["elevenlabs_api_key"]
    st.session_state["settings_announcements_base_dir"] = (
        active_settings["announcements_base_dir"] or str(get_default_announcements_base_dir())
    )
    st.session_state["settings_sync_supabase_url"] = active_settings.get("sync_supabase_url", "")
    st.session_state["settings_sync_supabase_key"] = active_settings.get("sync_supabase_key", "")
    st.session_state["settings_sync_user_id"] = active_settings.get("sync_user_id", "")
    st.session_state["settings_sync_device_name"] = active_settings.get("sync_device_name", platform.node() or "Home PC")
    st.session_state["_settings_form_signature"] = signature


def render_settings_page(active_settings: dict[str, str], settings_required: bool) -> None:
    st.title("A321 Route Planner Settings")

    if settings_required:
        st.warning(
            "Before using the planner, add your OpenWeatherMap API key, ElevenLabs API key, "
            "and the folder where announcement files should be saved."
        )
    else:
        st.caption(
            "These settings are stored locally on this computer and will be reused automatically "
            "the next time the app opens."
        )

    st.info(f"Local settings file: {SETTINGS_PATH}")
    st.caption("Environment variables or Streamlit secrets still override the saved values if you use them.")

    st.text_input(
        "OpenWeatherMap API Key",
        key="settings_openweathermap_api_key",
        type="password",
        help="Used to fetch departure/arrival weather for Flight Details and the announcement scripts.",
    )
    st.text_input(
        "ElevenLabs API Key",
        key="settings_elevenlabs_api_key",
        type="password",
        help="Used to generate the announcement audio files.",
    )
    st.text_input(
        "Announcements Folder",
        key="settings_announcements_base_dir",
        help="Enter the exact folder where you want the announcement files saved. If you point to a parent Announcements folder, the app will create an airline subfolder automatically.",
    )
    st.caption(f"Suggested folder on this computer: {get_default_announcements_base_dir()}")
    st.markdown("### Cloud Sync")
    st.caption(
        "Optional. Add a Supabase-compatible REST endpoint and user id to sync selected flights, "
        "saved flights, theme preference, and mobile announcement jobs. Leave blank to keep using the app locally."
    )
    st.text_input(
        "Supabase Project URL",
        key="settings_sync_supabase_url",
        placeholder="https://your-project.supabase.co",
    )
    st.text_input(
        "Supabase Anon Key",
        key="settings_sync_supabase_key",
        type="password",
    )
    sync_id_col, sync_device_col = st.columns(2)
    with sync_id_col:
        st.text_input("Cloud User ID", key="settings_sync_user_id", placeholder="jacques")
    with sync_device_col:
        st.text_input("PC Device Name", key="settings_sync_device_name")
    save_clicked = st.button("Save Settings", key="save_app_settings", width="stretch")

    if save_clicked:
        weather_key = st.session_state["settings_openweathermap_api_key"].strip()
        elevenlabs_key = st.session_state["settings_elevenlabs_api_key"].strip()
        announcements_dir_raw = st.session_state["settings_announcements_base_dir"].strip()

        errors: list[str] = []
        normalized_announcements_dir = ""

        if not weather_key:
            errors.append("OpenWeatherMap API key is required.")
        if not elevenlabs_key:
            errors.append("ElevenLabs API key is required.")
        if not announcements_dir_raw:
            errors.append("Announcements folder is required.")
        else:
            try:
                normalized_announcements_dir = normalize_announcements_dir(announcements_dir_raw)
            except Exception as exc:
                errors.append(f"Could not create the announcements folder: {exc}")

        if errors:
            for error in errors:
                st.error(error)
        else:
            new_settings = {
                "openweathermap_api_key": weather_key,
                "elevenlabs_api_key": elevenlabs_key,
                "announcements_base_dir": normalized_announcements_dir,
                "sync_supabase_url": st.session_state["settings_sync_supabase_url"].strip(),
                "sync_supabase_key": st.session_state["settings_sync_supabase_key"].strip(),
                "sync_user_id": st.session_state["settings_sync_user_id"].strip(),
                "sync_device_name": st.session_state["settings_sync_device_name"].strip(),
            }
            save_user_settings(new_settings)
            st.session_state["_settings_form_signature"] = ""
            st.session_state["_quick_announcements_base_dir_sync"] = new_settings["announcements_base_dir"]
            st.session_state["_go_to_flight_planner"] = True
            st.session_state["_settings_saved_message"] = "Settings saved."
            st.rerun()

    status_col1, status_col2, status_col3, status_col4 = st.columns(4)
    with status_col1:
        st.caption("OpenWeatherMap")
        st.code("Configured" if active_settings["openweathermap_api_key"] else "Missing")
    with status_col2:
        st.caption("ElevenLabs")
        st.code("Configured" if active_settings["elevenlabs_api_key"] else "Missing")
    with status_col3:
        st.caption("Announcements Folder")
        st.code(active_settings["announcements_base_dir"] or "Missing")
    with status_col4:
        st.caption("Cloud Sync")
        st.code("Configured" if cloud_sync_configured(active_settings) else "Local only")


sync_settings_form_state(ACTIVE_SETTINGS)

if st.session_state.pop("_go_to_flight_planner", False) and not SETTINGS_REQUIRED:
    st.session_state["app_menu_choice"] = "Dashboard"

if st.session_state.pop("_go_to_settings", False):
    st.session_state["app_menu_choice"] = "Settings"

if "app_menu_choice" not in st.session_state:
    st.session_state["app_menu_choice"] = "Dashboard"

query_nav = st.query_params.get("nav", "")
if isinstance(query_nav, list):
    query_nav = query_nav[0] if query_nav else ""
if query_nav in MENU_OPTIONS:
    st.session_state["app_menu_choice"] = query_nav

MENU_LABELS = {
    "Dashboard": ("⌂", "Dashboard"),
    "Route Database": ("▣", "Route Database"),
    "Manual Planner": ("✎", "Manual Planner"),
    "Saved Flights": ("▱", "Saved Flights"),
    "Aircraft Setup": ("✈", "Aircraft Setup  A321"),
    "Performance": ("▥", "Performance"),
    "Weather": ("☼", "Weather"),
    "SimBrief": ("⛓", "SimBrief"),
    "Logs": ("▤", "Logs"),
    "Settings": ("⚙", "Settings"),
}


def render_sidebar_navigation() -> None:
    active = st.session_state.get("app_menu_choice", "Dashboard")
    active_key = "side_nav_" + re.sub(r"[^a-z0-9]+", "_", active.lower()).strip("_")
    st.markdown(
        f"""
        <style>
        section[data-testid="stSidebar"] div.st-key-{active_key} button {{
            background: var(--color-sidebar-active) !important;
            color: #FFFFFF !important;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.10) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    for index, option in enumerate(MENU_OPTIONS):
        if index == 9:
            st.markdown("---")
        icon, label = MENU_LABELS.get(option, ("•", option))
        nav_key = "side_nav_" + re.sub(r"[^a-z0-9]+", "_", option.lower()).strip("_")
        if st.button(f"{icon}  {label}", key=nav_key, width="stretch"):
            st.session_state["app_menu_choice"] = option
            st.query_params["nav"] = option

with st.sidebar:
    st.html(
        """
        <div class="a321-sidebar-brand">
            <svg width="34" height="34" viewBox="0 0 64 64" fill="none" aria-hidden="true">
                <path d="M8 34L56 14L49 27L58 31L56 37L46 36L34 52L28 50L32 35L17 39L8 34Z" fill="white"/>
            </svg>
        </div>
        """
    )
    render_sidebar_navigation()
    if SETTINGS_REQUIRED:
        st.caption("Settings needed for weather and audio generation.")
    else:
        st.empty()
    st.html(
        """
        <div class="a321-sidebar-status">
            <div class="a321-status-row"><span class="a321-dot-green"></span><span>MSFS Connected</span></div>
            <div class="a321-status-subrow"><span>Ready to fly</span><span>⌁</span></div>
        </div>
        """
    )

# ---------- Load data ----------
airports = load_airports()
country_lookup = load_country_lookup()
routes_df = prepare_routes_dataset(load_routes(), airports, country_lookup)

if routes_df.empty:
    st.error(f"Could not load route database or required columns from: {ROUTES_CSV}")
    st.stop()

airport_options = sorted(airports["icao"].dropna().astype(str).str.upper().unique().tolist())
airport_lookup_by_icao = {
    row["icao"]: row.to_dict()
    for _, row in airports.drop_duplicates(subset=["icao"]).iterrows()
}


def airport_search_options(query: str, limit: int = 60) -> tuple[list[str], dict[str, str]]:
    search = normalize_search_text(query)
    if not search:
        return [], {}
    required_terms = [term for term in search.split(" ") if term]
    source = airports.drop_duplicates(subset=["icao"]).copy()
    haystack = (
        source[["icao", "name", "city", "country"]]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .map(normalize_search_text)
    )
    mask = pd.Series(True, index=source.index)
    for term in required_terms:
        mask &= haystack.str.contains(term, regex=False, na=False)
    matches = source[mask].head(limit)
    labels: list[str] = []
    label_to_code: dict[str, str] = {}
    for _, row in matches.iterrows():
        code = str(row.get("icao", "") or "").strip().upper()
        if not code:
            continue
        place = city_country(row.get("city", ""), row.get("country", ""))
        name = str(row.get("name", "") or "").strip()
        label = f"{code} - {name}"
        if place:
            label += f" ({place})"
        labels.append(label)
        label_to_code[label] = code
    return labels, label_to_code


def render_airport_picker(label: str, query_key: str, choice_key: str, icao_key: str) -> str:
    st.text_input(label, key=query_key, placeholder="ICAO, city, airport, or country")
    query = st.session_state.get(query_key, "")
    labels, label_to_code = airport_search_options(query)
    current_code = str(st.session_state.get(icao_key, "") or "").strip().upper()
    current_label = ""
    for option_label, code in label_to_code.items():
        if code == current_code:
            current_label = option_label
            break
    options = [""] + labels
    index = options.index(current_label) if current_label in options else 0
    if st.session_state.get(choice_key) not in options:
        st.session_state[choice_key] = ""
    choice = st.selectbox(
        f"{label} match",
        options=options,
        index=index,
        key=choice_key,
        format_func=lambda value: "Select airport..." if value == "" else value,
        label_visibility="collapsed",
        disabled=not labels,
    )
    selected_code = label_to_code.get(choice, current_code)
    if selected_code:
        st.session_state[icao_key] = selected_code
    info = airport_lookup_by_icao.get(selected_code, {})
    st.caption((info or {}).get("name", "") or "Type more to find the airport.")
    return selected_code


def normalize_theme_key(value: str | None) -> str:
    key = re.sub(r"[^a-z0-9]", "", str(value or "").strip().lower())
    aliases = {
        "aircanada": "aircanada",
        "britishairways": "britishairways",
        "ba": "britishairways",
        "jetblue": "jetblue",
        "american": "american",
        "united": "united",
        "lufthansa": "lufthansa",
        "delta": "delta",
    }
    key = aliases.get(key, key)
    return key if key in AIRLINE_THEME_CONFIG else "jetblue"


def active_theme_key() -> str:
    return normalize_theme_key(st.session_state.get("airline_theme_key", "jetblue"))


def airline_code_for_theme(theme_key: str | None = None) -> str:
    return AIRLINE_THEME_CODES.get(normalize_theme_key(theme_key or active_theme_key()), "JBU")


def current_flight_number() -> str:
    raw = str(st.session_state.get("fltnum_input", "1846") or "1846")
    digits = re.sub(r"\D", "", raw) or "1846"
    return digits


def current_flight_display() -> str:
    return f"{airline_code_for_theme(active_theme_key())}{current_flight_number()}"


def parse_flight_designator(value: str | None) -> tuple[str, str]:
    match = re.match(r"^\s*([A-Za-z]{1,3})?\s*(\d+)\s*$", value or "")
    if match:
        return airline_code_for_theme(active_theme_key()), match.group(2) or "1846"
    return airline_code_for_theme(active_theme_key()), "1846"


def sync_airline_theme_state(theme_key: str | None, force: bool = False) -> None:
    normalized = normalize_theme_key(theme_key)
    airline_code = airline_code_for_theme(normalized)
    st.session_state["airline_theme_key"] = normalized
    st.session_state["airline_theme"] = AIRLINE_THEME_CONFIG[normalized]["name"]
    if force or st.session_state.get("airline_input") != airline_code:
        st.session_state["airline_input"] = airline_code
        st.session_state["fltnum_input"] = "1846"
        st.session_state["simbrief_flight_number"] = f"{airline_code}1846"


# ---------- Session state ----------
defaults = {
    "dep_icao": "",
    "dest_icao": "",
    "airline_input": "JBU",
    "fltnum_input": "1846",
    "simbrief_flight_number": "JBU1846",
    "pax_input": "180",
    "aircraft_select": "A321",
    "selected_duration": "",
    "selected_route_id": None,
    "custom_route_active": False,
    "custom_departure_choice": None,
    "custom_arrival_choice": None,
    "manual_departure_icao": "",
    "manual_arrival_icao": "",
    "manual_departure_query": "",
    "manual_arrival_query": "",
    "manual_departure_choice_label": "",
    "manual_arrival_choice_label": "",
    "custom_applied_departure_icao": "",
    "custom_applied_arrival_icao": "",
    "custom_departure_time": "",
    "airline_theme_key": "jetblue",
    "airline_theme": "JetBlue",
    "sync_notice": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.get("_blank_start_version") != "blank_routes_2026_06_28":
    if (
        st.session_state.get("dep_icao") == "EGLL"
        and st.session_state.get("dest_icao") == "LFPG"
        and st.session_state.get("selected_route_id") is None
        and not st.session_state.get("custom_route_active")
    ):
        st.session_state["dep_icao"] = ""
        st.session_state["dest_icao"] = ""
        st.session_state["selected_duration"] = ""
    if st.session_state.get("manual_departure_icao") == "EGLL" and st.session_state.get("manual_arrival_icao") == "LFPG":
        st.session_state["manual_departure_icao"] = ""
        st.session_state["manual_arrival_icao"] = ""
    st.session_state["_blank_start_version"] = "blank_routes_2026_06_28"

query_airline_theme = st.query_params.get("airline_theme", "")
if isinstance(query_airline_theme, list):
    query_airline_theme = query_airline_theme[0] if query_airline_theme else ""
if query_airline_theme:
    sync_airline_theme_state(str(query_airline_theme), force=True)
else:
    sync_airline_theme_state(st.session_state.get("airline_theme_key", "jetblue"))

if False and (
    cloud_sync_configured(ACTIVE_SETTINGS)
    and not st.session_state.get("_cloud_loaded_once")
    and not st.session_state.get("dep_icao")
    and not st.session_state.get("dest_icao")
):
    latest_cloud_flight = load_latest_selected_flight_from_cloud()
    st.session_state["_cloud_loaded_once"] = True
    if latest_cloud_flight:
        st.session_state["selected_route_id"] = None
        st.session_state["dep_icao"] = str(latest_cloud_flight.get("departureIcao", "")).upper()
        st.session_state["dest_icao"] = str(latest_cloud_flight.get("arrivalIcao", "")).upper()
        st.session_state["selected_duration"] = str(
            latest_cloud_flight.get("estimatedBlockTime")
            or latest_cloud_flight.get("flightDuration")
            or ""
        )
        st.session_state["custom_route_active"] = True
        st.session_state["custom_applied_departure_icao"] = st.session_state["dep_icao"]
        st.session_state["custom_applied_arrival_icao"] = st.session_state["dest_icao"]
        st.session_state["custom_departure_time"] = str(latest_cloud_flight.get("localDepartureTime", ""))
        if latest_cloud_flight.get("plannedFromDevice") == "mobile":
            st.session_state["sync_notice"] = "Loaded from mobile plan."


def apply_known_route(chosen):
    airline_code = airline_code_for_theme(active_theme_key())
    st.session_state["selected_route_id"] = chosen["route_id"]
    st.session_state["dep_icao"] = chosen["departure_icao"]
    st.session_state["dest_icao"] = chosen["arrival_icao"]
    st.session_state["airline_input"] = airline_code
    st.session_state["fltnum_input"] = "1846"
    st.session_state["simbrief_flight_number"] = f"{airline_code}1846"
    st.session_state["selected_duration"] = chosen["duration_minutes_or_text"]
    st.session_state["custom_route_active"] = False
    st.session_state["custom_applied_departure_icao"] = ""
    st.session_state["custom_applied_arrival_icao"] = ""
    st.session_state["custom_departure_time"] = ""
    dep_info = airport_lookup_by_icao.get(str(chosen["departure_icao"]).strip().upper())
    dest_info = airport_lookup_by_icao.get(str(chosen["arrival_icao"]).strip().upper())
    sync_selected_flight_to_cloud(chosen, dep_info, dest_info, "database")


def clear_active_route():
    airline_code = airline_code_for_theme(active_theme_key())
    st.session_state["selected_route_id"] = None
    st.session_state["dep_icao"] = ""
    st.session_state["dest_icao"] = ""
    st.session_state["airline_input"] = airline_code
    st.session_state["fltnum_input"] = "1846"
    st.session_state["simbrief_flight_number"] = f"{airline_code}1846"
    st.session_state["selected_duration"] = ""
    st.session_state["custom_route_active"] = False
    st.session_state["custom_applied_departure_icao"] = ""
    st.session_state["custom_applied_arrival_icao"] = ""
    st.session_state["custom_departure_time"] = ""


def reset_planner_state() -> None:
    clear_active_route()
    for key in (
        "dashboard_route_search_text",
        "dashboard_route_select_id",
        "manual_departure_icao",
        "manual_arrival_icao",
        "manual_departure_query",
        "manual_arrival_query",
        "manual_departure_choice_label",
        "manual_arrival_choice_label",
        "custom_departure_choice",
        "custom_arrival_choice",
        "_custom_route_message",
        "sync_notice",
    ):
        st.session_state[key] = None if key in {"dashboard_route_select_id", "custom_departure_choice", "custom_arrival_choice"} else ""
    st.session_state["_planner_reset_message"] = "Planner reset. No airports selected."


def swap_manual_airport_fields() -> None:
    for dep_key, arr_key in (
        ("manual_departure_icao", "manual_arrival_icao"),
        ("manual_departure_query", "manual_arrival_query"),
        ("manual_departure_choice_label", "manual_arrival_choice_label"),
    ):
        dep_value = st.session_state.get(dep_key, "")
        st.session_state[dep_key] = st.session_state.get(arr_key, "")
        st.session_state[arr_key] = dep_value


def apply_custom_route_pair(custom_dep: str, custom_arr: str) -> None:
    custom_dep = (custom_dep or "").strip().upper()
    custom_arr = (custom_arr or "").strip().upper()

    if not custom_dep or not custom_arr:
        st.warning("Choose both a departure and arrival airport.")
        return

    dep_info = airport_lookup_by_icao.get(custom_dep)
    dest_info = airport_lookup_by_icao.get(custom_arr)

    if not dep_info or not dest_info:
        st.error("Could not find both airports in the airport database.")
        return

    distance_km = haversine_km(dep_info["lat"], dep_info["lon"], dest_info["lat"], dest_info["lon"])
    estimated_minutes = estimate_block_minutes(distance_km / 1.852)

    st.session_state["selected_route_id"] = None
    st.session_state["dep_icao"] = custom_dep
    st.session_state["dest_icao"] = custom_arr
    st.session_state["selected_duration"] = minutes_to_hmm(estimated_minutes)
    st.session_state["custom_route_active"] = True
    st.session_state["custom_applied_departure_icao"] = custom_dep
    st.session_state["custom_applied_arrival_icao"] = custom_arr
    st.session_state["custom_departure_time"] = current_departure_time()
    route_payload = {
        "departure_icao": custom_dep,
        "arrival_icao": custom_arr,
        "departure_time_z": st.session_state["custom_departure_time"],
        "duration_minutes_or_text": minutes_to_hmm(estimated_minutes),
        "estimated_block_time": minutes_to_hmm(estimated_minutes),
        "distance_nm": distance_km / 1.852,
    }
    sync_selected_flight_to_cloud(route_payload, dep_info, dest_info, "manual")
    st.session_state["_custom_route_message"] = (
        f"Custom airport pair applied: {custom_dep} to {custom_arr}."
    )
    st.rerun()


def apply_reference_route_pair(dep_icao: str, arr_icao: str) -> None:
    dep_icao = dep_icao.strip().upper()
    arr_icao = arr_icao.strip().upper()
    dep_info = airport_lookup_by_icao.get(dep_icao)
    dest_info = airport_lookup_by_icao.get(arr_icao)
    if not dep_info or not dest_info:
        st.error("Could not find both airports in the airport database.")
        return

    st.session_state["selected_route_id"] = None
    st.session_state["dep_icao"] = dep_icao
    st.session_state["dest_icao"] = arr_icao
    st.session_state["selected_duration"] = "1h 15m" if (dep_icao, arr_icao) == ("EGLL", "LFPG") else st.session_state.get("selected_duration", "1h 15m")
    st.session_state["custom_route_active"] = False
    st.session_state["custom_applied_departure_icao"] = ""
    st.session_state["custom_applied_arrival_icao"] = ""
    st.session_state["custom_departure_time"] = ""
    st.session_state["_custom_route_message"] = f"Selected route applied: {dep_icao} to {arr_icao}."
    st.rerun()


def route_search_results(
    query: str = "",
    departure: str = "",
    arrival: str = "",
    country: str = "",
    duration_range: tuple[int, int] | None = None,
    sort_by: str = "Shortest duration",
) -> pd.DataFrame:
    filtered = routes_df
    query = (query or "").strip().upper()
    departure = (departure or "").strip().upper()
    arrival = (arrival or "").strip().upper()
    country = (country or "").strip().lower()

    if query:
        normalized_terms = [term for term in normalize_search_text(query).split(" ") if term]
        for term in normalized_terms:
            filtered = filtered[filtered["route_search_blob"].fillna("").str.contains(term, regex=False, na=False)]

    if departure:
        filtered = filtered[filtered["departure_icao"].str.contains(departure, na=False)]
    if arrival:
        filtered = filtered[filtered["arrival_icao"].str.contains(arrival, na=False)]
    if country:
        filtered = filtered[
            filtered["dep_country"].fillna("").str.lower().str.contains(country, na=False)
            | filtered["arr_country"].fillna("").str.lower().str.contains(country, na=False)
        ]
    if duration_range is not None:
        filtered = filtered[
            (filtered["duration_minutes"] >= duration_range[0])
            & (filtered["duration_minutes"] <= duration_range[1])
        ]

    sort_columns = {
        "Shortest duration": ["duration_minutes", "departure_icao", "arrival_icao"],
        "Longest duration": ["duration_minutes", "departure_icao", "arrival_icao"],
        "Departure ICAO": ["departure_icao", "arrival_icao", "duration_minutes"],
        "Arrival ICAO": ["arrival_icao", "departure_icao", "duration_minutes"],
        "Distance": ["distance_nm", "departure_icao", "arrival_icao"],
    }
    ascending = sort_by != "Longest duration"
    filtered = filtered.sort_values(sort_columns.get(sort_by, sort_columns["Shortest duration"]), ascending=ascending)
    return filtered.reset_index(drop=True)


def route_button_label(row: pd.Series) -> str:
    dep_place = str(row.get("departure_city_country", "") or "").split(",")[0]
    arr_place = str(row.get("arrival_city_country", "") or "").split(",")[0]
    distance = f"{row.get('distance_nm', 0):.0f} NM" if pd.notna(row.get("distance_nm", None)) else ""
    return (
        f"{row['departure_icao']} → {row['arrival_icao']}  "
        f"{dep_place} → {arr_place}  "
        f"{row['duration_minutes_or_text']}  {distance}"
    )


def route_select_label(row: pd.Series, index: int = 0) -> str:
    dep_place = str(row.get("departure_place", "") or row.get("departure_city_country", "") or row.get("dep_name", "") or "")
    arr_place = str(row.get("arrival_place", "") or row.get("arrival_city_country", "") or row.get("arr_name", "") or "")
    distance = f"{row.get('distance_nm', 0):.0f} NM" if pd.notna(row.get("distance_nm", None)) else ""
    dep_time = str(row.get("departure_time_z", "") or "").replace("z", "Z")
    return (
        f"{row['departure_icao']} → {row['arrival_icao']} | "
        f"{dep_place} → {arr_place} | "
        f"{row['duration_minutes_or_text']} | {distance} | Dep {dep_time} | #{index + 1}"
    )


@st.cache_data(show_spinner=False)
def build_route_select_options(routes_table: pd.DataFrame) -> tuple[list[str], list[int]]:
    option_rows = routes_table.sort_values(
        ["departure_icao", "arrival_icao", "departure_time_z", "route_id"],
        ascending=True,
    ).reset_index(drop=True)
    labels: list[str] = []
    route_ids: list[int] = []
    for index, (_, row) in enumerate(option_rows.iterrows()):
        labels.append(route_select_label(row, index))
        route_ids.append(int(row["route_id"]))
    return labels, route_ids


@st.cache_data(show_spinner=False, max_entries=256)
def build_dashboard_route_options(query: str, limit: int = 250) -> tuple[list[str], list[int], int]:
    query = (query or "").strip()
    if not query:
        return [], [], 0

    filtered = routes_df
    normalized_terms = [term for term in normalize_search_text(query).split(" ") if term]
    for term in normalized_terms:
        filtered = filtered[filtered["route_search_blob"].fillna("").str.contains(term, regex=False, na=False)]

    filtered = filtered.sort_values(
        ["departure_icao", "arrival_icao", "departure_time_z", "route_id"],
        ascending=True,
    ).reset_index(drop=True)
    total = len(filtered)
    option_rows = filtered.head(limit)
    labels: list[str] = []
    route_ids: list[int] = []
    for index, (_, row) in enumerate(option_rows.iterrows()):
        labels.append(route_select_label(row, index))
        route_ids.append(int(row["route_id"]))
    return labels, route_ids, total


def reset_dashboard_route_dropdown() -> None:
    st.session_state["dashboard_route_select_id"] = None
    st.session_state["_dashboard_route_applied_id"] = None


def commit_dashboard_route_search() -> None:
    st.session_state["route_search_committed"] = st.session_state.get("route_search_compact", "").strip()
    st.session_state["dashboard_route_select"] = None
    st.session_state["_dashboard_route_applied_id"] = None


def apply_dashboard_route_select_from_state() -> None:
    apply_dashboard_route_id_if_needed(st.session_state.get("dashboard_route_select_id"))


def apply_dashboard_route_id_if_needed(chosen_route_id) -> None:
    if chosen_route_id is None or st.session_state.get("_dashboard_route_applied_id") == chosen_route_id:
        return
    try:
        chosen_route_id = int(chosen_route_id)
    except Exception:
        return
    chosen_match = routes_df[routes_df["route_id"] == chosen_route_id]
    if chosen_match.empty:
        return
    st.session_state["_dashboard_route_applied_id"] = chosen_route_id
    apply_known_route(chosen_match.iloc[0])
    st.session_state["_custom_route_message"] = (
        f"Known route applied: {chosen_match.iloc[0]['departure_icao']} to {chosen_match.iloc[0]['arrival_icao']}."
    )


def apply_route_and_rerun(row: pd.Series) -> None:
    apply_known_route(row)
    st.session_state["_custom_route_message"] = (
        f"Known route applied: {row['departure_icao']} to {row['arrival_icao']}."
    )
    st.rerun()


def active_route_context():
    dep_code = str(st.session_state.get("dep_icao", "")).strip().upper()
    arr_code = str(st.session_state.get("dest_icao", "")).strip().upper()
    selected_route = None
    selected_route_id = st.session_state.get("selected_route_id")
    if selected_route_id is not None:
        match = routes_df[routes_df["route_id"] == selected_route_id]
        if not match.empty:
            candidate = match.iloc[0]
            if dep_code == str(candidate["departure_icao"]).strip().upper() and arr_code == str(candidate["arrival_icao"]).strip().upper():
                selected_route = candidate

    dep_info = lookup_airport(airports, dep_code) if dep_code else None
    arr_info = lookup_airport(airports, arr_code) if arr_code else None
    if selected_route is not None:
        dep_info = lookup_airport(airports, str(selected_route["departure_icao"]))
        arr_info = lookup_airport(airports, str(selected_route["arrival_icao"]))
    return selected_route, dep_info, arr_info, build_active_route_record(selected_route, dep_info, arr_info)


def active_route_text(active_route) -> str:
    if active_route is None:
        return "No active flight"
    try:
        dep = active_route.get("departure_icao", "")
        arr = active_route.get("arrival_icao", "")
        duration = active_route.get("duration_minutes_or_text", "")
        distance = active_route.get("distance_nm", "")
    except AttributeError:
        return "No active flight"
    if pd.notna(distance) and distance != "":
        try:
            distance = f"{float(distance):.0f} NM"
        except Exception:
            distance = str(distance)
    return f"{dep} → {arr} · {duration} · {distance}"


def render_page_header(title: str, helper: str) -> None:
    st.html(
        f"""
        <div class="a321-page-header">
            <h2>{escape(title)}</h2>
            <p>{escape(helper)}</p>
        </div>
        """
    )


def render_summary_metrics(active_route) -> None:
    if active_route is None:
        st.info("Plan or select a flight to populate this page.")
        return
    dep = active_route.get("departure_icao", "")
    arr = active_route.get("arrival_icao", "")
    duration = active_route.get("duration_minutes_or_text", "")
    block = active_route.get("estimated_block_time", "")
    distance = active_route.get("distance_nm", "")
    try:
        distance = f"{float(distance):.0f}"
    except Exception:
        distance = str(distance)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Route", f"{dep} → {arr}")
    c2.metric("Distance NM", distance)
    c3.metric("Duration", duration)
    c4.metric("Est. Block", block)


def build_active_route_record(selected_route, dep_info: dict | None, dest_info: dict | None) -> dict | pd.Series | None:
    if selected_route is not None:
        return selected_route
    if not dep_info or not dest_info:
        return None

    dep_code = str(st.session_state.get("dep_icao", "")).strip().upper()
    arr_code = str(st.session_state.get("dest_icao", "")).strip().upper()
    is_reference = dep_code == "EGLL" and arr_code == "LFPG" and not st.session_state.get("custom_route_active")
    if is_reference:
        return {
            "source": "reference",
            "departure_icao": "EGLL",
            "arrival_icao": "LFPG",
            "departure_time_z": "10:30",
            "arrival_time_z": "11:45",
            "duration_minutes_or_text": "1h 15m",
            "estimated_block_time": "1h 29m",
            "distance_nm": 214,
            "dep_city": "London",
            "arr_city": "Paris CDG",
            "departure_city_country": "London Heathrow",
            "arrival_city_country": "Paris Charles de Gaulle",
            "airline_code": airline_code_for_theme(active_theme_key()),
            "flight_number_numeric": current_flight_number(),
        }

    distance_nm = haversine_km(dep_info["lat"], dep_info["lon"], dest_info["lat"], dest_info["lon"]) / 1.852
    estimated_block = minutes_to_hmm(estimate_block_minutes(distance_nm))
    departure_time = (
        st.session_state.get("custom_departure_time")
        or st.session_state.get("selected_departure_time")
        or current_departure_time()
    )
    return {
        "source": "manual" if st.session_state.get("custom_route_active") else "database",
        "departure_icao": dep_code,
        "arrival_icao": arr_code,
        "departure_time_z": departure_time,
        "duration_minutes_or_text": st.session_state.get("selected_duration") or estimated_block,
        "estimated_block_time": estimated_block,
        "distance_nm": distance_nm,
        "dep_city": dep_info.get("city", ""),
        "arr_city": dest_info.get("city", ""),
        "departure_city_country": dep_info.get("name") or city_country(dep_info.get("city"), dep_info.get("country")),
        "arrival_city_country": dest_info.get("name") or city_country(dest_info.get("city"), dest_info.get("country")),
        "airline_code": airline_code_for_theme(active_theme_key()),
        "flight_number_numeric": "1846",
    }


def image_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def active_airline_logo_uri() -> str:
    logo_name = AIRLINE_THEME_LOGOS.get(active_theme_key(), AIRLINE_THEME_LOGOS["jetblue"])
    logo_path = APP_DIR / "assets" / "branding" / logo_name
    if not logo_path.exists():
        logo_path = APP_DIR / "assets" / "branding" / AIRLINE_THEME_LOGOS["jetblue"]
    return image_data_uri(logo_path) if logo_path.exists() else ""


def render_app_header() -> None:
    themes_json = json.dumps(AIRLINE_THEME_CONFIG)
    airline_codes_json = json.dumps(AIRLINE_THEME_CODES)
    logo_uris_json = json.dumps({
        key: image_data_uri(APP_DIR / "assets" / "branding" / logo_name)
        for key, logo_name in AIRLINE_THEME_LOGOS.items()
        if (APP_DIR / "assets" / "branding" / logo_name).exists()
    })
    theme_key = active_theme_key()
    components.html(
        f"""
        <!doctype html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
        :root {{
            --color-shell: #011735;
            --color-sidebar-active: #082681;
            --color-primary: #021C48;
            --color-primary-hover: #062A65;
            --color-accent: #0B5CAD;
            --color-border: #D7DFEA;
            --color-success: #35D87A;
        }}
        html, body {{
            margin: 0;
            padding: 0;
            background: transparent;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif;
        }}
        .a321-topbar {{
            height: 64px;
            box-sizing: border-box;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            padding: 0 14px 0 18px;
            color: #FFFFFF;
            background: var(--color-shell);
            border-radius: 0;
        }}
        .a321-brand {{
            display: flex;
            align-items: center;
            gap: 14px;
            min-width: 330px;
        }}
        .a321-plane-tile {{
            width: 58px;
            height: 42px;
            border-radius: 7px;
            display: grid;
            place-items: center;
            background: var(--color-sidebar-active);
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
        }}
        .a321-brand h1 {{
            margin: 0;
            color: #FFFFFF;
            font-size: 20px;
            line-height: 1.05;
            font-weight: 850;
            letter-spacing: 0;
        }}
        .a321-brand p {{
            margin: 3px 0 0;
            color: rgba(255,255,255,0.78);
            font-size: 12px;
            font-weight: 600;
        }}
        .a321-actions {{
            display: flex;
            align-items: center;
            gap: 18px;
            margin-left: auto;
        }}
        .a321-header-btn,
        .a321-theme-btn,
        .a321-profile-btn {{
            height: 36px;
            border: 1px solid rgba(255,255,255,0.26);
            background: transparent;
            color: #FFFFFF;
            border-radius: 7px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 0 10px;
            font-size: 12px;
            font-weight: 760;
            cursor: pointer;
            text-decoration: none;
        }}
        .a321-header-btn {{
            border-color: transparent;
            padding: 0 2px;
        }}
        .a321-header-btn:hover,
        .a321-theme-btn:hover,
        .a321-profile-btn:hover {{
            background: rgba(255,255,255,0.08);
        }}
        .a321-theme-btn {{
            min-width: 158px;
            justify-content: space-between;
        }}
        .a321-theme-left {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        .a321-profile-avatar {{
            width: 28px;
            height: 28px;
            border-radius: 999px;
            display: inline-grid;
            place-items: center;
            color: #07162D;
            background: linear-gradient(145deg, #F5D4A4, #B98655);
            border: 1px solid rgba(255,255,255,0.22);
            font-size: 12px;
            font-weight: 900;
        }}
        .a321-small-icon {{
            width: 16px;
            height: 16px;
            display: inline-block;
        }}
        </style>
        </head>
        <body>
        <div class="a321-topbar">
            <div class="a321-brand">
                <div class="a321-plane-tile">
                    <svg width="34" height="34" viewBox="0 0 64 64" fill="none" aria-hidden="true">
                        <path d="M8 34L56 14L49 27L58 31L56 37L46 36L34 52L28 50L32 35L17 39L8 34Z" fill="white"/>
                    </svg>
                </div>
                <div>
                    <h1>A321 Flight Planner</h1>
                    <p>MSFS Route Planning</p>
                </div>
            </div>
            <div class="a321-actions">
                <a class="a321-header-btn" id="a321-settings-btn" href="?nav=Settings" target="_top">
                    <svg class="a321-small-icon" viewBox="0 0 24 24" fill="none"><path d="M12 15.5A3.5 3.5 0 1 0 12 8a3.5 3.5 0 0 0 0 7.5Z" stroke="white" stroke-width="1.8"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.04.04a2 2 0 0 1-2.83 2.83l-.04-.04a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1.03 1.56V21a2 2 0 0 1-4 0v-.06a1.7 1.7 0 0 0-1.03-1.56 1.7 1.7 0 0 0-1.88.34l-.04.04a2 2 0 1 1-2.83-2.83l.04-.04A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.56-1.03H3a2 2 0 0 1 0-4h.06A1.7 1.7 0 0 0 4.6 8.94a1.7 1.7 0 0 0-.34-1.88l-.04-.04a2 2 0 1 1 2.83-2.83l.04.04a1.7 1.7 0 0 0 1.88.34H9a1.7 1.7 0 0 0 1-1.56V3a2 2 0 0 1 4 0v.06a1.7 1.7 0 0 0 1.03 1.56 1.7 1.7 0 0 0 1.88-.34l.04-.04a2 2 0 1 1 2.83 2.83l-.04.04a1.7 1.7 0 0 0-.34 1.88V9a1.7 1.7 0 0 0 1.56 1h.06a2 2 0 0 1 0 4h-.06A1.7 1.7 0 0 0 19.4 15Z" stroke="white" stroke-width="1.35"/></svg>
                    Settings
                </a>
                <button class="a321-theme-btn" id="a321-theme-button" type="button" aria-expanded="false">
                    <span class="a321-theme-left">
                        <svg class="a321-small-icon" viewBox="0 0 24 24" fill="none"><path d="M12 22a10 10 0 1 0 0-20 4.2 4.2 0 0 0-4 4.33c0 1.2.84 2.25 2.03 2.25h1.2c1.06 0 1.92.86 1.92 1.92 0 .82-.52 1.55-1.3 1.82l-.7.24a4.05 4.05 0 0 0-2.75 3.85C8.4 19.5 10 22 12 22Z" stroke="white" stroke-width="1.8"/><circle cx="7.6" cy="8.2" r="1" fill="white"/><circle cx="10.1" cy="5.6" r="1" fill="white"/><circle cx="14.1" cy="5.8" r="1" fill="white"/><circle cx="16.5" cy="8.8" r="1" fill="white"/></svg>
                        <span id="a321-theme-label">Airline Theme</span>
                    </span>
                    <svg width="13" height="13" viewBox="0 0 20 20" fill="none"><path d="M5 7.5L10 12.5L15 7.5" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </button>
                <button class="a321-header-btn" id="a321-help-btn" type="button">
                    <svg class="a321-small-icon" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="white" stroke-width="1.8"/><path d="M9.8 9a2.3 2.3 0 0 1 4.4.9c0 1.9-2.2 2.2-2.2 4" stroke="white" stroke-width="1.8" stroke-linecap="round"/><path d="M12 17.5h.01" stroke="white" stroke-width="2.4" stroke-linecap="round"/></svg>
                    Help
                </button>
                <button class="a321-profile-btn" type="button">
                    <span class="a321-profile-avatar">J</span>
                    <span>Capt. Jacques</span>
                    <svg width="12" height="12" viewBox="0 0 20 20" fill="none"><path d="M5 7.5L10 12.5L15 7.5" stroke="white" stroke-width="2" stroke-linecap="round"/></svg>
                </button>
            </div>
        </div>
        <script>
        const themes = {themes_json};
        const airlineCodes = {airline_codes_json};
        const logoUris = {logo_uris_json};
        const storageKey = "a321-airline-theme";
        const cssKeys = {{
            shell: "--color-shell",
            sidebar: "--color-sidebar",
            sidebarActive: "--color-sidebar-active",
            primary: "--color-primary",
            primaryHover: "--color-primary-hover",
            accent: "--color-accent",
            card: "--color-card",
            border: "--color-border",
            text: "--color-text",
            muted: "--color-muted",
            success: "--color-success"
        }};
        let activeTheme = "{theme_key}";
        if (!themes[activeTheme]) activeTheme = "jetblue";

        function applyTheme(key) {{
            const theme = themes[key] || themes.jetblue;
            const parentRoot = window.parent.document.documentElement;
            Object.entries(cssKeys).forEach(([themeKey, cssVar]) => {{
                parentRoot.style.setProperty(cssVar, theme[themeKey]);
                document.documentElement.style.setProperty(cssVar, theme[themeKey]);
            }});
            parentRoot.dataset.airlineTheme = key;
            localStorage.setItem(storageKey, key);
            window.parent.localStorage.setItem(storageKey, key);
            activeTheme = key;
            const label = document.getElementById("a321-theme-label");
            if (label) label.textContent = theme.name;
            updateAirlineBranding(key);
            updateFlightDesignators(key);
            renderMenu(false);
        }}

        function updateAirlineBranding(key) {{
            const theme = themes[key] || themes.jetblue;
            const logo = logoUris[key] || logoUris.jetblue || "";
            window.parent.document.querySelectorAll("img[data-a321-airline-logo='true']").forEach(img => {{
                if (logo) img.setAttribute("src", logo);
                img.setAttribute("alt", theme.name);
            }});
            window.parent.document.querySelectorAll("[data-a321-airline-name='true']").forEach(node => {{
                node.textContent = theme.name;
            }});
        }}

        function updateFlightDesignators(key) {{
            const code = airlineCodes[key] || "JBU";
            const value = `${{code}}1846`;
            window.parent.document.querySelectorAll('input[aria-label="Flight Number"], input[aria-label="Default callsign / flight number"]').forEach(input => {{
                input.value = value;
                input.dispatchEvent(new Event("input", {{ bubbles: true }}));
            }});
            window.parent.document.querySelectorAll('[data-a321-flight-designator="true"]').forEach(node => {{
                node.textContent = value;
            }});
        }}

        function syncThemeToStreamlit(key) {{
            const url = new URL(window.parent.location.href);
            url.searchParams.set("airline_theme", key);
            window.parent.setTimeout(() => {{
                window.parent.location.href = url.toString();
            }}, 120);
        }}

        function navigateApp(name) {{
            const url = new URL(window.parent.location.href);
            url.searchParams.set("nav", name);
            window.parent.location.href = url.toString();
        }}

        function menuHtml() {{
            return Object.entries(themes).map(([key, theme]) => {{
                const swatches = theme.swatches.map(color => `<span style="background:${{color}}"></span>`).join("");
                const check = key === activeTheme ? "✓" : "";
                return `<button type="button" data-theme="${{key}}">
                    <span class="swatches">${{swatches}}</span>
                    <span class="name">${{theme.name}}</span>
                    <span class="check">${{check}}</span>
                </button>`;
            }}).join("");
        }}

        function renderMenu(open = true) {{
            const parentDoc = window.parent.document;
            let menu = parentDoc.getElementById("a321-theme-floating-menu");
            if (!open) {{
                if (menu) menu.remove();
                document.getElementById("a321-theme-button")?.setAttribute("aria-expanded", "false");
                return;
            }}
            const button = document.getElementById("a321-theme-button");
            const frameRect = window.frameElement.getBoundingClientRect();
            const buttonRect = button.getBoundingClientRect();
            if (!menu) {{
                menu = parentDoc.createElement("div");
                menu.id = "a321-theme-floating-menu";
                parentDoc.body.appendChild(menu);
            }}
            menu.innerHTML = `<style>
                #a321-theme-floating-menu {{
                    position: fixed;
                    z-index: 999999;
                    width: 184px;
                    padding: 6px;
                    border-radius: 7px;
                    background: var(--color-primary);
                    border: 1px solid rgba(255,255,255,0.24);
                    box-shadow: 0 18px 44px rgba(0,0,0,0.34);
                    font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif;
                }}
                #a321-theme-floating-menu button {{
                    width: 100%;
                    height: 34px;
                    display: grid;
                    grid-template-columns: 38px 1fr 18px;
                    gap: 8px;
                    align-items: center;
                    border: 0;
                    border-radius: 5px;
                    background: transparent;
                    color: #fff;
                    cursor: pointer;
                    padding: 0 8px;
                    font-size: 12px;
                    font-weight: 650;
                    text-align: left;
                }}
                #a321-theme-floating-menu button:hover,
                #a321-theme-floating-menu button[data-theme="${{activeTheme}}"] {{
                    background: var(--color-sidebar-active);
                }}
                #a321-theme-floating-menu .swatches {{
                    display: flex;
                    align-items: center;
                    gap: 0;
                }}
                #a321-theme-floating-menu .swatches span {{
                    display: inline-block;
                    width: 13px;
                    height: 13px;
                    border: 1px solid rgba(255,255,255,0.35);
                }}
                #a321-theme-floating-menu .check {{
                    text-align: right;
                    font-weight: 900;
                }}
            </style>${{menuHtml()}}`;
            menu.style.left = `${{frameRect.left + buttonRect.left}}px`;
            menu.style.top = `${{frameRect.top + buttonRect.bottom + 6}}px`;
            menu.querySelectorAll("button[data-theme]").forEach(option => {{
                option.addEventListener("click", () => {{
                    applyTheme(option.dataset.theme);
                    syncThemeToStreamlit(option.dataset.theme);
                }});
            }});
            button.setAttribute("aria-expanded", "true");
        }}

        document.getElementById("a321-theme-button").addEventListener("click", event => {{
            event.stopPropagation();
            const menu = window.parent.document.getElementById("a321-theme-floating-menu");
            if (menu) renderMenu(false);
            else renderMenu(true);
        }});
        document.getElementById("a321-settings-btn").addEventListener("click", event => {{
            event.preventDefault();
            navigateApp("Settings");
        }});
        window.parent.document.addEventListener("click", event => {{
            const menu = window.parent.document.getElementById("a321-theme-floating-menu");
            if (menu && !menu.contains(event.target)) renderMenu(false);
        }});
        applyTheme(activeTheme);
        </script>
        </body>
        </html>
        """,
        height=66,
    )


def render_route_database_page() -> None:
    render_page_header("Route Database", "Browse known A321 routes and select one to populate the planner.")
    top1, top2, top3, top4, top5 = st.columns([1.4, 0.75, 0.75, 0.75, 0.9])
    with top1:
        query = st.text_input("Search", key="route_db_search", placeholder="ICAO, city, airport, country")
    with top2:
        departure = st.text_input("Departure ICAO", key="route_db_dep")
    with top3:
        arrival = st.text_input("Arrival ICAO", key="route_db_arr")
    with top4:
        country = st.text_input("Country / region", key="route_db_country")
    with top5:
        sort_by = st.selectbox(
            "Sort",
            ["Shortest duration", "Longest duration", "Departure ICAO", "Arrival ICAO", "Distance"],
            key="route_db_sort",
        )

    slider_max = ceil_to_5(int(routes_df["duration_minutes"].max()))
    duration_range = st.select_slider(
        "Estimated duration",
        options=list(range(0, slider_max + 1, 15)),
        value=(0, min(slider_max, 720)),
        format_func=minutes_to_hhmm,
        key="route_db_duration",
    )
    results = route_search_results(query, departure, arrival, country, duration_range, sort_by)

    table_col, preview_col = st.columns([2.1, 0.9], gap="small")
    with table_col:
        with st.container(border=True):
            st.html(f"<div class='a321-card-heading-row'><h3>Known Routes</h3><span class='a321-save-flight'>{len(results):,} matches</span></div>")
            if results.empty:
                st.html("<div class='a321-empty-state'>No known A321 routes match the current filters.</div>")
            else:
                table = results.head(300).copy()
                table.insert(0, "select", False)
                table["aircraft"] = "A321"
                table["notes"] = table["departure_icao"].astype(str) + " → " + table["arrival_icao"].astype(str)
                show_cols = [
                    "select",
                    "departure_icao",
                    "arrival_icao",
                    "departure_city_country",
                    "arrival_city_country",
                    "distance_nm",
                    "duration_minutes_or_text",
                    "aircraft",
                    "notes",
                ]
                edited = st.data_editor(
                    table[show_cols],
                    hide_index=True,
                    width="stretch",
                    key="route_db_editor",
                    column_config={
                        "select": st.column_config.CheckboxColumn("Select", default=False),
                        "departure_icao": "Departure ICAO",
                        "arrival_icao": "Arrival ICAO",
                        "departure_city_country": "Departure Airport",
                        "arrival_city_country": "Arrival Airport",
                        "distance_nm": st.column_config.NumberColumn("Distance NM", format="%.0f"),
                        "duration_minutes_or_text": "Estimated Duration",
                        "aircraft": "Aircraft",
                        "notes": "Notes / Popularity",
                    },
                    disabled=[c for c in show_cols if c != "select"],
                )
                selected_rows = edited[edited["select"] == True]
                action1, action2, action3 = st.columns(3)
                with action1:
                    if st.button("Use Route", key="route_db_use", width="stretch", type="primary"):
                        if selected_rows.empty:
                            st.warning("Select a route first.")
                        else:
                            row_index = selected_rows.index[0]
                            apply_route_and_rerun(results.head(300).iloc[row_index])
                with action2:
                    if st.button("Preview", key="route_db_preview", width="stretch"):
                        st.session_state["route_db_preview_index"] = int(selected_rows.index[0]) if not selected_rows.empty else 0
                with action3:
                    if st.button("Favorite", key="route_db_favorite", width="stretch"):
                        st.success("Favorite noted for this session.")

    with preview_col:
        with st.container(border=True):
            st.html("<div class='a321-card-heading-row'><h3>Route Preview</h3><span class='a321-save-flight'>A321</span></div>")
            if results.empty:
                st.html("<div class='a321-empty-state'>Search or filter to preview a route.</div>")
            else:
                preview_index = min(int(st.session_state.get("route_db_preview_index", 0)), len(results) - 1)
                preview = results.iloc[preview_index]
                dep_info = airport_lookup_by_icao.get(str(preview["departure_icao"]).upper())
                arr_info = airport_lookup_by_icao.get(str(preview["arrival_icao"]).upper())
                st.html(
                    f"""
                    <div class="a321-mini-route">
                        <strong>{escape(str(preview['departure_icao']))} → {escape(str(preview['arrival_icao']))}</strong>
                        <span>{escape(str(preview.get('departure_city_country', '')))} → {escape(str(preview.get('arrival_city_country', '')))}</span>
                    </div>
                    """
                )
                render_summary_metrics(build_active_route_record(preview, dep_info, arr_info))


def render_manual_planner_page() -> None:
    render_page_header("Manual Planner", "Create a flight manually using departure and arrival airports.")
    form_col, result_col = st.columns([1.05, 1.25], gap="small")
    with form_col:
        with st.container(border=True):
            st.html("<div class='a321-card-heading-row'><h3>Manual Route Builder</h3><span class='a321-save-flight'>Custom</span></div>")
            c1, c2 = st.columns(2)
            with c1:
                manual_page_dep = render_airport_picker(
                    "Departure airport",
                    "manual_departure_query",
                    "manual_departure_choice_label",
                    "manual_departure_icao",
                )
            with c2:
                manual_page_arr = render_airport_picker(
                    "Arrival airport",
                    "manual_arrival_query",
                    "manual_arrival_choice_label",
                    "manual_arrival_icao",
                )
            c3, c4 = st.columns(2)
            with c3:
                st.text_input("Flight number", key="simbrief_flight_number")
            with c4:
                st.text_input("Passenger count", key="pax_input")
            c5, c6 = st.columns(2)
            with c5:
                st.text_input("Cruise altitude", value="FL340", key="manual_cruise_altitude")
            with c6:
                st.selectbox("Route type", ["Direct", "Airway"], key="manual_route_type")
            swap_col, plan_col = st.columns([0.2, 0.8])
            with swap_col:
                st.button("⇄", key="manual_page_swap", width="stretch", on_click=swap_manual_airport_fields)
            with plan_col:
                if st.button("Plan Flight", key="manual_page_plan", width="stretch", type="primary"):
                    apply_custom_route_pair(manual_page_dep, manual_page_arr)

    selected_route, dep_info, arr_info, active_route = active_route_context()
    with result_col:
        with st.container(border=True):
            st.html("<div class='a321-card-heading-row'><h3>Planned Flight</h3><span class='a321-save-flight'>Use as Active Flight</span></div>")
            render_summary_metrics(active_route)
            if dep_info and arr_info:
                st.html(
                    f"""
                    <div class="a321-mini-route">
                        <strong>{escape(dep_info.get('icao', ''))} - {escape(dep_info.get('name', ''))}</strong>
                        <span>{escape(city_country(dep_info.get('city'), dep_info.get('country')))}</span>
                    </div>
                    <div class="a321-mini-route">
                        <strong>{escape(arr_info.get('icao', ''))} - {escape(arr_info.get('name', ''))}</strong>
                        <span>{escape(city_country(arr_info.get('city'), arr_info.get('country')))}</span>
                    </div>
                    """
                )
                if st.button("Use as Active Flight", key="manual_use_active", width="stretch", type="primary"):
                    st.success("This manual route is already active.")


def render_saved_flights_page() -> None:
    render_page_header("Saved Flights", "View and manage saved flight plans.")
    _, _, _, active_route = active_route_context()
    if "saved_flights" not in st.session_state:
        st.session_state["saved_flights"] = []

    toolbar1, toolbar2, toolbar3 = st.columns([1.4, 0.8, 0.8])
    with toolbar1:
        saved_search = st.text_input("Search saved flights", key="saved_search")
    with toolbar2:
        st.selectbox("Sort", ["Newest", "Oldest", "Route"], key="saved_sort")
    with toolbar3:
        if st.button("Save Active Flight", key="save_active_flight", width="stretch", type="primary"):
            if active_route is not None:
                saved = {
                    "route": f"{active_route.get('departure_icao')} → {active_route.get('arrival_icao')}",
                    "flight": st.session_state.get("simbrief_flight_number", "JBU1846"),
                    "passengers": st.session_state.get("pax_input", "180"),
                    "distance": active_route.get("distance_nm", ""),
                    "duration": active_route.get("duration_minutes_or_text", ""),
                    "saved": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "simbrief": "Ready",
                    "announcements": "Ready",
                }
                st.session_state["saved_flights"].insert(0, saved)
                st.success("Flight saved.")

    with st.container(border=True):
        rows = st.session_state["saved_flights"]
        if saved_search:
            rows = [row for row in rows if saved_search.lower() in " ".join(str(v) for v in row.values()).lower()]
        if not rows:
            st.html("<div class='a321-empty-state'>No saved flights yet. Save the active flight to build your list.</div>")
        else:
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            a1, a2, a3, a4 = st.columns(4)
            a1.button("Open", key="saved_open", width="stretch")
            a2.button("Duplicate", key="saved_duplicate", width="stretch")
            a3.button("Generate in SimBrief", key="saved_simbrief", width="stretch")
            a4.button("Generate Announcements", key="saved_announcements", width="stretch")


def render_aircraft_setup_page() -> None:
    render_page_header("Aircraft Setup", "Configure aircraft details and defaults for A321 operations.")
    top_col, settings_col = st.columns([0.9, 1.3], gap="small")
    with top_col:
        with st.container(border=True):
            st.html(
                f"""
                <div class="a321-aircraft-card">
                    <div class="a321-airline-logo-panel">
                        <img data-a321-airline-logo="true" src="{active_airline_logo_uri()}" alt="{escape(st.session_state.get('airline_theme', 'JetBlue'))}">
                    </div>
                    <div class="a321-aircraft-copy"><strong>Airbus A321-231</strong><span><span data-a321-airline-name="true">{escape(st.session_state.get('airline_theme', 'JetBlue'))}</span> · CFM56-5B3/P · A321 profile</span></div>
                </div>
                """
            )
            st.text_input("Registration / tail number", value="N321JB", key="aircraft_registration")
            st.button("Change Aircraft", key="aircraft_change", width="stretch")
    with settings_col:
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.markdown("### Default Flight Settings")
                st.text_input("Default passenger count", key="pax_input")
                st.text_input("Default cruise altitude", value="FL340", key="aircraft_cruise_default")
                st.text_input("Default callsign / flight number", key="simbrief_flight_number")
                st.text_input("Block time padding", value="14 minutes", key="aircraft_block_padding")
        with c2:
            with st.container(border=True):
                st.markdown("### Performance / Audio")
                st.text_input("Max passengers", value="220", key="aircraft_max_pax")
                st.text_input("Payload assumption", value="Standard cabin", key="aircraft_payload")
                st.text_input("Announcements profile", value="JetBlue", key="aircraft_audio_profile")
                st.text_input("Audio output folder", value=ACTIVE_SETTINGS["announcements_base_dir"] or str(get_default_announcements_base_dir()), key="aircraft_audio_folder")
        save_col, reset_col = st.columns(2)
        save_col.button("Save Changes", key="aircraft_save", width="stretch", type="primary")
        reset_col.button("Reset Defaults", key="aircraft_reset", width="stretch")


def render_performance_page() -> None:
    render_page_header("Performance", "Review route and aircraft planning performance.")
    _, dep_info, arr_info, active_route = active_route_context()
    render_summary_metrics(active_route)
    perf_col, aircraft_col = st.columns(2, gap="small")
    with perf_col:
        with st.container(border=True):
            st.markdown("### Route Performance")
            if active_route is not None:
                render_flight_details_table(active_route, dep_info, arr_info)
    with aircraft_col:
        with st.container(border=True):
            st.markdown("### Aircraft Planning Metrics")
            st.dataframe(
                pd.DataFrame(
                    [
                        ("Passenger Load", st.session_state.get("pax_input", "180")),
                        ("Payload Profile", "Standard cabin"),
                        ("Cruise Altitude", "FL340"),
                        ("Fuel Estimate", "Available after SimBrief"),
                        ("Performance Profile", "A321 CFM56"),
                    ],
                    columns=["Metric", "Value"],
                ),
                hide_index=True,
                width="stretch",
            )


def render_weather_page() -> None:
    render_page_header("Weather", "Review departure, enroute, and arrival weather.")
    _, dep_info, arr_info, active_route = active_route_context()
    wx_cols = st.columns(3, gap="small")
    for label, info in [("Departure Weather", dep_info), ("Arrival Weather", arr_info)]:
        with wx_cols[0 if label.startswith("Departure") else 1]:
            with st.container(border=True):
                st.markdown(f"### {label}")
                if info:
                    temp = get_temperature(info["lat"], info["lon"], OPENWEATHERMAP_API_KEY)
                    main = get_weather(info["lat"], info["lon"], OPENWEATHERMAP_API_KEY)
                    st.metric(info["icao"], f"{temp if temp is not None else '—'}°C")
                    st.caption(info.get("name", ""))
                    st.dataframe(
                        pd.DataFrame(
                            [
                                ("Weather", adjective_from_openweather(main)),
                                ("Wind", "Live METAR source pending"),
                                ("Visibility", "Live METAR source pending"),
                                ("Clouds", "Live METAR source pending"),
                                ("QNH", "Live METAR source pending"),
                            ],
                            columns=["Field", "Value"],
                        ),
                        hide_index=True,
                        width="stretch",
                    )
                else:
                    st.html("<div class='a321-empty-state'>No airport selected.</div>")
    with wx_cols[2]:
        with st.container(border=True):
            st.markdown("### Weather Impact Summary")
            st.write("Operational summary will populate from live weather when configured.")
            st.caption(active_route_text(active_route))


def render_simbrief_page() -> None:
    render_page_header("SimBrief", "Prepare and send the active flight to SimBrief.")
    _, dep_info, arr_info, active_route = active_route_context()
    form_col, summary_col = st.columns([1.1, 0.9], gap="small")
    with form_col:
        with st.container(border=True):
            st.markdown("### Dispatch Form")
            st.text_input("Departure ICAO", key="dep_icao")
            st.text_input("Arrival ICAO", key="dest_icao")
            combined_flight = st.text_input("Flight Number", key="simbrief_flight_number")
            airline, fltnum = parse_flight_designator(combined_flight)
            st.text_input("Passenger Count", key="pax_input")
            st.toggle("Include Fuel Planning", value=True, key="simbrief_page_fuel")
            st.toggle("Include Payload", value=True, key="simbrief_page_payload")
            st.toggle("Use Real Weather", value=True, key="simbrief_page_weather")
            st.text_area("Remarks", key="simbrief_remarks", placeholder="Optional dispatch remarks")
            url = build_dispatch_redirect(
                airline=airline,
                fltnum=fltnum,
                aircraft=st.session_state.get("aircraft_select", "A321"),
                orig=st.session_state.get("dep_icao", ""),
                dest=st.session_state.get("dest_icao", ""),
                passengers=st.session_state.get("pax_input", "180"),
            )
            st.link_button("Generate in SimBrief", url, width="stretch")
    with summary_col:
        with st.container(border=True):
            st.markdown("### Active Flight Summary")
            render_summary_metrics(active_route)
            st.info("Ready to dispatch." if active_route is not None else "Select or plan a flight first.")


def render_logs_page() -> None:
    render_page_header("Logs", "Review recent activity and system events.")
    _, _, _, active_route = active_route_context()
    log_rows = [
        (datetime.now().strftime("%Y-%m-%d %H:%M"), "Active flight loaded", "Flight", active_route_text(active_route), "Desktop", "OK"),
        (datetime.now().strftime("%Y-%m-%d %H:%M"), "Theme available", "Appearance", "Airline theme dropdown", "Desktop", "OK"),
        (datetime.now().strftime("%Y-%m-%d %H:%M"), "MSFS connected", "System", "Ready to fly", "Desktop", "OK"),
    ]
    search_col, type_col, date_col = st.columns([1.4, 0.8, 0.8])
    search_col.text_input("Search logs", key="logs_search")
    type_col.selectbox("Type", ["All", "Flight", "Appearance", "System", "Sync"], key="logs_type")
    date_col.text_input("Date", value=datetime.now().strftime("%Y-%m-%d"), key="logs_date")
    with st.container(border=True):
        st.dataframe(
            pd.DataFrame(log_rows, columns=["Timestamp", "Action / Event", "Category", "Related Flight", "Device", "Status"]),
            hide_index=True,
            width="stretch",
        )


def render_selected_non_dashboard_page(page_name: str) -> None:
    if page_name == "Route Database":
        render_route_database_page()
    elif page_name == "Manual Planner":
        render_manual_planner_page()
    elif page_name == "Saved Flights":
        render_saved_flights_page()
    elif page_name == "Aircraft Setup":
        render_aircraft_setup_page()
    elif page_name == "Performance":
        render_performance_page()
    elif page_name == "Weather":
        render_weather_page()
    elif page_name == "SimBrief":
        render_simbrief_page()
    elif page_name == "Logs":
        render_logs_page()


def render_app_footer() -> None:
    st.html(
        """
        <div class="a321-app-footer">
            Copyright Dr. Jacques Balayla, MD. 2026. All Rights Reserved. Not intended for real life use
        </div>
        """
    )


# ---------- Header ----------
render_app_header()

if st.session_state.pop("_settings_saved_message", ""):
    st.success("Settings saved.")

if custom_route_message := st.session_state.pop("_custom_route_message", ""):
    st.success(custom_route_message)

if planner_reset_message := st.session_state.pop("_planner_reset_message", ""):
    st.success(planner_reset_message)

if sync_notice := st.session_state.get("sync_notice", ""):
    st.info(sync_notice)

if SETTINGS_REQUIRED:
    st.warning("Settings are still needed for live weather and audio generation, but the planner is available.")

if st.session_state["app_menu_choice"] == "Settings":
    render_settings_page(ACTIVE_SETTINGS, SETTINGS_REQUIRED)
    render_app_footer()
    st.stop()

if st.session_state["app_menu_choice"] != "Dashboard":
    render_selected_non_dashboard_page(st.session_state["app_menu_choice"])
    render_app_footer()
    st.stop()

reset_spacer, reset_col = st.columns([0.82, 0.18], gap="small")
with reset_col:
    st.button("Reset Planner", key="reset_planner_button", width="stretch", on_click=reset_planner_state)

# ---------- Route selection ----------
route_col, or_col, manual_col, aircraft_col = st.columns([1.55, 0.13, 1.18, 0.86], gap="small")

with route_col:
    with st.container(border=True):
        st.html('<div class="a321-dashboard-card-marker a321-route-card-marker"></div><div class="a321-card-title"><span class="a321-number-badge">1</span><span>Known A321 Routes Database</span></div>')
        route_query = st.text_input(
            "Search known routes",
            key="dashboard_route_search_text",
            placeholder="Type ICAO, city, airport, or country...",
            label_visibility="collapsed",
            on_change=reset_dashboard_route_dropdown,
        )
        route_labels, route_ids, route_total = build_dashboard_route_options(route_query)
        route_label_by_id = dict(zip(route_ids, route_labels))
        current_route_select_id = st.session_state.get("dashboard_route_select_id")
        if current_route_select_id not in ([None] + route_ids):
            st.session_state["dashboard_route_select_id"] = None

        def route_option_label(value):
            if value is None:
                return "Choose a matching route..." if route_ids else "Type to search known routes..."
            try:
                return route_label_by_id.get(int(value), str(value))
            except Exception:
                return str(value)

        if route_query.strip():
            shown_count = min(route_total, len(route_ids))
            st.caption(f"{route_total:,} exact matches. Showing {shown_count:,}.")
        else:
            st.caption(f"{len(routes_df):,} known routes loaded. Type an ICAO like CYUL or a country like Turkey.")
        selected_route_id = st.selectbox(
            "Matching known routes",
            options=[None] + route_ids,
            format_func=route_option_label,
            key="dashboard_route_select_id",
            label_visibility="collapsed",
            disabled=not route_ids,
        )
        apply_dashboard_route_id_if_needed(selected_route_id)

with or_col:
    st.html('<div class="a321-or-divider">OR</div>')

with manual_col:
    with st.container(border=True):
        st.html('<div class="a321-dashboard-card-marker a321-route-card-marker"></div><div class="a321-card-title"><span class="a321-number-badge">2</span><span>Manual Airport Entry</span></div>')
        dep_entry_col, arr_entry_col = st.columns(2)
        with dep_entry_col:
            dashboard_manual_dep = render_airport_picker(
                "Departure airport",
                "manual_departure_query",
                "manual_departure_choice_label",
                "manual_departure_icao",
            )
        with arr_entry_col:
            dashboard_manual_arr = render_airport_picker(
                "Arrival airport",
                "manual_arrival_query",
                "manual_arrival_choice_label",
                "manual_arrival_icao",
            )
        swap_col, plan_col = st.columns([0.18, 0.82])
        with swap_col:
            st.button("⇄", key="swap_manual_airports", width="stretch", on_click=swap_manual_airport_fields)
        with plan_col:
            if st.button("Plan Flight", key="plan_manual_airports", width="stretch", type="primary"):
                apply_custom_route_pair(
                    dashboard_manual_dep,
                    dashboard_manual_arr,
                )

with aircraft_col:
    with st.container(border=True):
        st.html(
            f"""
            <div class="a321-dashboard-card-marker a321-aircraft-card-marker"></div>
            <div class="a321-aircraft-card">
                <div class="a321-airline-logo-panel">
                    <img data-a321-airline-logo="true" src="{active_airline_logo_uri()}" alt="{escape(st.session_state.get('airline_theme', 'JetBlue'))}">
                </div>
                <div class="a321-aircraft-copy">
                    <strong>Airbus A321-231</strong>
                    <span><span data-a321-airline-name="true">{escape(st.session_state.get('airline_theme', 'JetBlue'))}</span> · CFM56-5B3/P</span>
                </div>
            </div>
            """
        )
        aircraft_options = ["A321", "A320", "A319"]
        current_aircraft = st.session_state["aircraft_select"]
        aircraft_index = aircraft_options.index(current_aircraft) if current_aircraft in aircraft_options else 0
        st.session_state["aircraft_select"] = st.selectbox(
            "Change Aircraft",
            aircraft_options,
            index=aircraft_index,
            label_visibility="collapsed",
        )

# ---------- Selected flight state ----------
current_dep_code = str(st.session_state.get("dep_icao", "")).strip().upper()
current_dest_code = str(st.session_state.get("dest_icao", "")).strip().upper()

if st.session_state.get("custom_route_active"):
    custom_dep_code = str(st.session_state.get("custom_applied_departure_icao", "")).strip().upper()
    custom_dest_code = str(st.session_state.get("custom_applied_arrival_icao", "")).strip().upper()
    if current_dep_code != custom_dep_code or current_dest_code != custom_dest_code:
        st.session_state["custom_route_active"] = False
        st.session_state["custom_applied_departure_icao"] = ""
        st.session_state["custom_applied_arrival_icao"] = ""
        st.session_state["custom_departure_time"] = ""

selected = None
if st.session_state["selected_route_id"] is not None:
    m = routes_df[routes_df["route_id"] == st.session_state["selected_route_id"]]
    if not m.empty:
        candidate = m.iloc[0]
        if (
            current_dep_code == str(candidate["departure_icao"]).strip().upper()
            and current_dest_code == str(candidate["arrival_icao"]).strip().upper()
        ):
            selected = candidate
        else:
            st.session_state["selected_route_id"] = None
            if not st.session_state.get("custom_route_active"):
                st.session_state["selected_duration"] = ""

dep_lookup = lookup_airport(airports, current_dep_code) if current_dep_code else None
dest_lookup = lookup_airport(airports, current_dest_code) if current_dest_code else None
if selected is not None:
    dep_lookup = lookup_airport(airports, str(selected["departure_icao"]))
    dest_lookup = lookup_airport(airports, str(selected["arrival_icao"]))

active_route = build_active_route_record(selected, dep_lookup, dest_lookup)
dep_icao_edit = st.session_state["dep_icao"].strip().upper()
dest_icao_edit = st.session_state["dest_icao"].strip().upper()
aircraft = st.session_state["aircraft_select"]

flight_time_text = ""
if dep_lookup and dest_lookup:
    distance_km = haversine_km(dep_lookup["lat"], dep_lookup["lon"], dest_lookup["lat"], dest_lookup["lon"])
    distance_nm = distance_km / 1.852
    avg_speed_kts = 450
    flight_hours = distance_nm / avg_speed_kts + 0.5
    hours = int(flight_hours)
    minutes = int((flight_hours - hours) * 60)
    flight_time_text = (
        f"{hours} hour{'s' if hours != 1 else ''} and {minutes} minute{'s' if minutes != 1 else ''}"
        if hours > 0 else
        f"{minutes} minute{'s' if minutes != 1 else ''}"
    )

if active_route is None:
    st.info("Select one known route or plan a manual airport pair.")
else:
    render_departure_board(active_route)

details_col, simbrief_col = st.columns([2.1, 0.95], gap="small")

with details_col:
    with st.container(border=True):
        st.html(
            """
            <div class="a321-dashboard-card-marker a321-flight-details-card-marker"></div>
            <div class="a321-card-heading-row">
                <h3><span class="a321-number-badge">3</span><span>Flight Details</span></h3>
                <span class="a321-save-flight">▣&nbsp; Save Flight</span>
            </div>
            """
        )
        render_flight_details_table(active_route, dep_lookup, dest_lookup)
        st.html('<div class="a321-announcement-anchor"></div>')
        if st.button(
            "Generate Announcements",
            key="create_announcements_button",
            width="stretch",
            type="primary",
            disabled=not (dep_icao_edit and dest_icao_edit),
        ):
            announcement_airline, announcement_fltnum = parse_flight_designator(
                st.session_state.get("simbrief_flight_number", current_flight_display())
            )
            st.session_state["airline_input"] = announcement_airline
            st.session_state["fltnum_input"] = announcement_fltnum
            files = create_announcement_files(
                dep_icao_edit,
                dest_icao_edit,
                announcement_airline,
                announcement_fltnum,
                flight_time_text,
            )
            if files:
                st.success("Announcements generated.")
                for filename, audio_bytes, output_path in files:
                    st.audio(audio_bytes, format="audio/mp3")
                    st.caption(f"Saved to: {output_path}")

with simbrief_col:
    with st.container(border=True):
        st.html(
            """
            <div class="a321-dashboard-card-marker a321-simbrief-card-marker"></div>
            <div class="a321-simbrief-title">
                <span class="a321-number-badge">4</span>
                <div>
                    <h3>SimBrief Integration</h3>
                    <p>Send flight details to SimBrief to generate your OFP.</p>
                </div>
            </div>
            """
        )
        combined_flight = st.text_input("Flight Number", key="simbrief_flight_number")
        airline, fltnum = parse_flight_designator(combined_flight)
        st.toggle("Include Fuel Planning", value=True, key="simbrief_include_fuel")
        st.toggle("Include Payload", value=True, key="simbrief_include_payload")
        passengers = st.text_input("Passenger Count", key="pax_input")
        st.toggle("Use Real Weather", value=True, key="simbrief_real_weather")

        selected_departure_time = ""
        if active_route is not None:
            try:
                selected_departure_time = str(active_route.get("departure_time_z", ""))
            except AttributeError:
                selected_departure_time = ""

        if dep_icao_edit and dest_icao_edit and aircraft:
            simbrief_url = build_dispatch_redirect(
                airline=airline,
                fltnum=fltnum,
                aircraft=aircraft,
                orig=dep_icao_edit,
                dest=dest_icao_edit,
                passengers=passengers,
                departure_time_z=selected_departure_time,
            )
            st.link_button("Generate in SimBrief", simbrief_url, width="stretch")
            st.caption("Opens in your browser")
        else:
            st.warning("SimBrief appears after both airports are set.")

if st.session_state.get("_map_default_version") != "voyager_default_2026_06_28":
    st.session_state["map_style_choice"] = "Voyager"
    st.session_state["_map_default_version"] = "voyager_default_2026_06_28"
elif "map_style_choice" not in st.session_state:
    st.session_state["map_style_choice"] = "Voyager"

if "map_layer_choice" not in st.session_state:
    st.session_state["map_layer_choice"] = "High Altitude"
elif st.session_state["map_layer_choice"] not in (["High Altitude"] + list(MAP_STYLES.keys())):
    st.session_state["map_layer_choice"] = "High Altitude"

with st.container(border=True):
    map_title_col, map_control_col = st.columns([0.74, 0.26])
    with map_title_col:
        st.html(
            """
            <div class="a321-map-header">
                <div class="a321-map-title">
                    <span class="a321-number-badge">5</span>
                    <span>Voyager Map</span>
                </div>
            </div>
            """
        )
    with map_control_col:
        layer_choice = st.selectbox(
            "Map layer",
            options=["High Altitude"] + list(MAP_STYLES.keys()),
            key="map_layer_choice",
            label_visibility="collapsed",
        )
        st.session_state["map_style_choice"] = "Voyager" if layer_choice == "High Altitude" else layer_choice

    if dep_icao_edit and dest_icao_edit:
        dep_info = lookup_airport(airports, dep_icao_edit)
        dest_info = lookup_airport(airports, dest_icao_edit)

        if dep_info and dest_info:
            render_route_map(dep_info, dest_info, MAP_STYLES[st.session_state["map_style_choice"]], height=560)
        else:
            st.info("Map will appear when both airports are found.")
    else:
        st.info("Map will appear after you enter or apply both airports.")

render_app_footer()
