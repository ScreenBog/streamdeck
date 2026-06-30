"""Яндекс Музыка — браузер, одно окно, Windows Media API."""

from __future__ import annotations

import os
import subprocess
import time
import webbrowser
from pathlib import Path
from urllib.parse import quote

import pyperclip

from . import keyboard_win
from .media_session import get_media_info, media_command

WEB_BASE = "https://music.yandex.ru"
MY_WAVE_URL = f"{WEB_BASE}/radio/user/onyourwave"

BROWSER_CANDIDATES = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]

WINDOW_KEYS = (
    "яндекс музыка",
    "yandex music",
    "music.yandex.ru",
    "yandex.ru",
)

_last_url = ""


def run(action: str, value: str = "", settings: dict | None = None) -> str:
    settings = settings or {}
    key = (action or "open").strip().lower()
    query = (value or "").strip()

    if key in ("open", "web", "browser"):
        return _ensure_browser(WEB_BASE, "🌐 Плеер", settings)
    if key == "play_pause":
        return _media_ctrl("⏯ Play/Pause", "play_pause", lambda: keyboard_win.press("space"))
    if key == "next":
        return _media_ctrl("⏭ Следующий", "next", lambda: keyboard_win.hotkey(["ctrl", "right"]))
    if key == "prev":
        return _media_ctrl("⏮ Предыдущий", "prev", lambda: keyboard_win.hotkey(["ctrl", "left"]))
    if key == "like":
        return _media_ctrl("❤️ Лайк", None, lambda: keyboard_win.hotkey(["ctrl", "l"]))
    if key == "shuffle":
        return _media_ctrl("🔀 Шаффл", None, lambda: keyboard_win.press("s"))
    if key == "volume_up":
        keyboard_win.press_media("volumeup")
        return "🔊 +"
    if key == "volume_down":
        keyboard_win.press_media("volumedown")
        return "🔉 -"
    if key == "mute":
        keyboard_win.press_media("volumemute")
        return "🔇 Mute"
    if key == "my_wave":
        return _open_page(MY_WAVE_URL, "🎲 Моя волна", settings, play=True)
    if key == "collection":
        return _open_page(f"{WEB_BASE}/collection", "❤️ Коллекция", settings)
    if key == "playlists":
        return _open_page(f"{WEB_BASE}/playlists", "📋 Плейлисты", settings)
    if key == "history":
        return _open_page(f"{WEB_BASE}/history", "🕐 История", settings)
    if key == "charts":
        return _open_page(f"{WEB_BASE}/charts", "📈 Чарты", settings)
    if key == "podcasts":
        return _open_page(f"{WEB_BASE}/podcasts", "🎙 Подкасты", settings)
    if key == "kids":
        return _open_page(f"{WEB_BASE}/kids", "👶 Детям", settings)
    if key == "new_releases":
        return _open_page(f"{WEB_BASE}/new-releases", "🆕 Новинки", settings)
    if key == "search":
        q = query or "плейлист дня"
        return _open_page(f"{WEB_BASE}/search?text={quote(q)}", f"🔍 {q}", settings)
    if key == "focus":
        if _focus_browser():
            return "🎯 Окно в фокусе"
        return _ensure_browser(WEB_BASE, "🌐 Открыт браузер", settings)
    raise ValueError(f"Яндекс Музыка: неизвестное действие {key}")


def get_status() -> dict:
    info = get_media_info()
    if info and info.get("track") and info["track"] != "—":
        return {
            "playing": info.get("playing", False),
            "track": info["track"],
            "title": info.get("title", ""),
            "artist": info.get("artist", ""),
            "album": info.get("album", ""),
            "raw": info.get("app", ""),
            "source": "windows",
        }

    if _focus_browser():
        pass

    return {
        "playing": False,
        "track": "Нажми «Открыть плеер»",
        "title": "",
        "artist": "",
        "album": "",
        "raw": "",
        "source": "none",
    }


def _media_ctrl(label: str, win_cmd: str | None, fallback) -> str:
    if win_cmd:
        try:
            import asyncio
            if asyncio.run(media_command(win_cmd)):
                return label
        except Exception:
            pass

    keyboard_win.press_media(
        "playpause" if win_cmd == "play_pause"
        else "nexttrack" if win_cmd == "next"
        else "prevtrack" if win_cmd == "prev"
        else "playpause"
    )

    if _focus_browser():
        try:
            fallback()
        except Exception:
            pass
    return label


def _open_page(url: str, label: str, settings: dict, play: bool = False) -> str:
    result = _ensure_browser(url, label, settings, navigate=True)
    if play:
        time.sleep(2.0)
        _media_ctrl("▶", "play_pause", lambda: keyboard_win.press("space"))
        return label + " · играет"
    return result


def _ensure_browser(url: str, label: str, settings: dict, navigate: bool = False) -> str:
    global _last_url

    if _focus_browser():
        if navigate and url != _last_url:
            _navigate(url)
            _last_url = url
        return label + " (то же окно)"

    _launch_browser(url, settings or {})
    _last_url = url
    time.sleep(0.8)
    _focus_browser()
    return label


def _navigate(url: str) -> None:
    keyboard_win.hotkey(["ctrl", "l"])
    time.sleep(0.25)
    pyperclip.copy(url)
    keyboard_win.hotkey(["ctrl", "v"])
    time.sleep(0.1)
    keyboard_win.press("enter")
    time.sleep(0.6)


def _launch_browser(url: str, settings: dict) -> None:
    if settings.get("yandex", {}).get("mode") == "app":
        app = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "YandexMusic" / "Яндекс Музыка.exe"
        if app.exists():
            subprocess.Popen(f'"{app}" "{url}"', shell=True)
            return

    exe = _find_browser(settings)
    if exe:
        subprocess.Popen([str(exe), f"--app={url}"], shell=False)
        return
    webbrowser.open(url)


def _find_browser(settings: dict | None = None) -> Path | None:
    pref = (settings or {}).get("yandex", {}).get("browser", "auto").lower()
    ordered = list(BROWSER_CANDIDATES)
    if pref == "edge":
        ordered.sort(key=lambda p: 0 if "edge" in str(p).lower() else 1)
    elif pref == "chrome":
        ordered.sort(key=lambda p: 0 if "chrome" in str(p).lower() else 1)
    for path in ordered:
        if path.exists():
            return path
    return None


def _focus_browser() -> bool:
    try:
        import pygetwindow as gw
    except ImportError:
        return False

    best = None
    for win in gw.getAllWindows():
        title = (win.title or "").strip().lower()
        if not title:
            continue
        if any(k in title for k in WINDOW_KEYS):
            best = win

    if not best:
        return False
    try:
        if best.isMinimized:
            best.restore()
        best.activate()
        time.sleep(0.35)
        return True
    except Exception:
        return False