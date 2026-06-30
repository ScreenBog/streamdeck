"""Хранение конфигурации Deck."""

from __future__ import annotations

import json
import secrets
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONFIG_PATH = DATA_DIR / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "settings": {
        "pin": "",
        "port": 8765,
        "gridCols": 5,
        "gridRows": 3,
        "theme": "dark",
        "title": "My Deck",
    },
    "activePage": "main",
    "pages": [
        {
            "id": "main",
            "name": "Главная",
            "buttons": [
                {
                    "id": "b1",
                    "col": 0,
                    "row": 0,
                    "label": "Chrome",
                    "icon": "🌐",
                    "color": "#1e3a5f",
                    "action": {
                        "type": "app",
                        "value": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    },
                },
                {
                    "id": "b2",
                    "col": 1,
                    "row": 0,
                    "label": "Discord",
                    "icon": "💬",
                    "color": "#5865f2",
                    "action": {"type": "app", "value": "discord"},
                },
                {
                    "id": "b3",
                    "col": 2,
                    "row": 0,
                    "label": "Vol +",
                    "icon": "🔊",
                    "color": "#2d4a22",
                    "action": {"type": "media", "value": "volume_up"},
                },
                {
                    "id": "b4",
                    "col": 3,
                    "row": 0,
                    "label": "Mute",
                    "icon": "🔇",
                    "color": "#4a2d2d",
                    "action": {"type": "media", "value": "mute"},
                },
                {
                    "id": "b5",
                    "col": 4,
                    "row": 0,
                    "label": "Play",
                    "icon": "⏯",
                    "color": "#3d2d4a",
                    "action": {"type": "media", "value": "play_pause"},
                },
                {
                    "id": "b6",
                    "col": 0,
                    "row": 1,
                    "label": "Win+D",
                    "icon": "🖥",
                    "color": "#2a2a3a",
                    "action": {"type": "hotkey", "value": ["win", "d"]},
                },
                {
                    "id": "b7",
                    "col": 1,
                    "row": 1,
                    "label": "Alt+Tab",
                    "icon": "⇥",
                    "color": "#2a2a3a",
                    "action": {"type": "hotkey", "value": ["alt", "tab"]},
                },
                {
                    "id": "b8",
                    "col": 2,
                    "row": 1,
                    "label": "OBS",
                    "icon": "🎬",
                    "color": "#1a1a2e",
                    "action": {"type": "app", "value": r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"},
                },
                {
                    "id": "b9",
                    "col": 3,
                    "row": 1,
                    "label": "YouTube",
                    "icon": "▶️",
                    "color": "#5c1a1a",
                    "action": {"type": "url", "value": "https://youtube.com"},
                },
                {
                    "id": "b10",
                    "col": 4,
                    "row": 1,
                    "label": "Lock",
                    "icon": "🔒",
                    "color": "#3a2a1a",
                    "action": {"type": "system", "value": "lock"},
                },
            ],
        }
    ],
}


def ensure_config() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        cfg = deepcopy(DEFAULT_CONFIG)
        cfg["settings"]["pin"] = "".join(str(secrets.randbelow(10)) for _ in range(6))
        save_config(cfg)
        return cfg
    return load_config()


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def new_button_id() -> str:
    return f"btn_{uuid.uuid4().hex[:8]}"


def new_page_id() -> str:
    return f"page_{uuid.uuid4().hex[:8]}"