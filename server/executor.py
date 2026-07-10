"""Выполнение действий кнопок Deck на Windows. Улучшенная версия с логированием и мощным macro."""

from __future__ import annotations

import ctypes
import io
import os
import subprocess
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any

import pyperclip

from . import keyboard_win
from .logger import logger
from .obs_ctrl import run_obs
from .yandex_music import run as run_yandex_music

SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "data" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def execute(action: dict[str, Any], settings: dict[str, Any] | None = None) -> dict[str, Any]:
    action_type = action.get("type", "")
    value = action.get("value", "")
    settings = settings or {}

    handlers = {
        "hotkey": _hotkey, "app": _app, "url": _url, "shell": _shell,
        "text": _text, "media": _media, "system": _system, "path": _path,
        "macro": _macro, "folder": _folder, "screenshot": _screenshot,
        "clipboard": _clipboard, "mouse": _mouse, "window": _window,
        "obs": _obs, "yandex": _yandex, "none": _none,
    }

    handler = handlers.get(action_type)
    if not handler:
        logger.warning("Неизвестный тип действия: {}", action_type)
        return {"ok": False, "message": f"Неизвестный тип: {action_type}"}

    try:
        logger.debug("▶️ Выполняю {} | value={}", action_type, str(value)[:100])
        result = handler(value, action, settings)
        if isinstance(result, dict):
            final = {"ok": True, **result}
        else:
            final = {"ok": True, "message": result}
        logger.info("✅ {} → {}", action_type, final.get("message", "")[:120])
        return final
    except Exception as e:
        logger.error("❌ Ошибка в {}: {}", action_type, e)
        logger.exception(e)
        return {"ok": False, "message": str(e)}


def _none(_value: Any, _action: dict, _settings: dict) -> str:
    return "Пустая кнопка"


def _hotkey(value: Any, _action: dict, _settings: dict) -> str:
    keys = _parse_keys(value)
    keyboard_win.hotkey(keys)
    return f"⌨️ {'+'.join(k.upper() for k in keys)}"


def _parse_keys(value: Any) -> list[str]:
    if isinstance(value, list):
        keys = [str(k).lower() for k in value]
    elif isinstance(value, str):
        keys = [k.strip().lower() for k in value.replace("+", " ").split() if k.strip()]
    else:
        raise ValueError("hotkey: укажите ctrl+shift+s или win,d")
    if not keys:
        raise ValueError("hotkey: пустой список клавиш")
    return keys


def _app(value: Any, _action: dict, _settings: dict) -> str:
    cmd = str(value).strip()
    if not cmd:
        raise ValueError("app: пустая команда")
    if cmd.startswith(("http://", "https://", "ms-")):
        webbrowser.open(cmd)
        return f"🌐 {cmd}"
    subprocess.Popen(cmd, shell=True)
    return f"▶️ {cmd}"


def _url(value: Any, _action: dict, _settings: dict) -> str:
    url = str(value).strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"🌐 {url}"


def _shell(value: Any, action: dict, _settings: dict) -> str:
    cmd = str(value).strip()
    if not cmd:
        raise ValueError("shell: пустая команда")
    timeout = int(action.get("timeout", 30))
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                            timeout=timeout, encoding="utf-8", errors="replace")
    out = (result.stdout or result.stderr or "(пусто)").strip()
    if len(out) > 500:
        out = out[:500] + "…"
    return f"$ {cmd}\n{out}" if out else f"$ {cmd}"


def _text(value: Any, _action: dict, _settings: dict) -> str:
    text = str(value)
    if not text:
        raise ValueError("text: пустой текст")
    pyperclip.copy(text)
    keyboard_win.hotkey(["ctrl", "v"])
    return f"📝 {len(text)} симв."


def _media(value: Any, _action: dict, _settings: dict) -> str:
    actions = {
        "volume_up": (lambda: [keyboard_win.press("volumeup") for _ in range(3)], "🔊 +"),
        "volume_down": (lambda: [keyboard_win.press("volumedown") for _ in range(3)], "🔉 -"),
        "mute": (lambda: keyboard_win.press("volumemute"), "🔇 Mute"),
        "play_pause": (lambda: keyboard_win.press("playpause"), "⏯ Play/Pause"),
        "next": (lambda: keyboard_win.press("nexttrack"), "⏭ Next"),
        "prev": (lambda: keyboard_win.press("prevtrack"), "⏮ Prev"),
        "mic_mute": (lambda: keyboard_win.hotkey(["win", "alt", "k"]), "🎤 Mic toggle"),
    }
    key = str(value).strip().lower()
    if key not in actions:
        raise ValueError(f"media: неизвестное действие {key}")
    actions[key][0]()
    return actions[key][1]


def _system(value: Any, _action: dict, _settings: dict) -> str | dict:
    key = str(value).strip().lower()
    if key == "show_desktop":
        keyboard_win.show_desktop()
        return "🖥 Рабочий стол"
    if key == "lock":
        ctypes.windll.user32.LockWorkStation()
        return "🔒 Заблокирован"
    if key == "sleep":
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "😴 Сон"
    if key == "shutdown":
        subprocess.run(["shutdown", "/s", "/t", "60"], check=False)
        return "⏻ Выключение через 60с"
    if key == "restart":
        subprocess.run(["shutdown", "/r", "/t", "60"], check=False)
        return "🔄 Перезагрузка через 60с"
    if key == "cancel_shutdown":
        subprocess.run(["shutdown", "/a"], check=False)
        return "✅ Отмена выключения"
    if key == "taskmgr":
        subprocess.Popen("taskmgr", shell=True)
        return "📋 Диспетчер задач"
    if key == "explorer":
        subprocess.Popen("explorer", shell=True)
        return "📁 Проводник"
    if key == "settings":
        os.startfile("ms-settings:")
        return "⚙️ Параметры"
    if key == "empty_trash":
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x00000007)
        return "🗑 Корзина очищена"
    if key == "active_window":
        return {"message": f"🪟 {_active_window_title()}"}
    raise ValueError(f"system: неизвестное действие {key}")


def _active_window_title() -> str:
    try:
        import pygetwindow as gw
        win = gw.getActiveWindow()
        return win.title if win and win.title else "—"
    except Exception:
        return "—"


def _path(value: Any, _action: dict, _settings: dict) -> str:
    path = os.path.expandvars(os.path.expanduser(str(value).strip().strip('"')))
    if not os.path.exists(path):
        raise FileNotFoundError(f"Путь не найден: {path}")
    os.startfile(path)
    return f"📂 {path}"


def _macro(value: Any, action: dict, settings: dict) -> str:
    steps = value if isinstance(value, list) else action.get("steps", [])
    if not steps:
        raise ValueError("macro: пустой список шагов")

    results = []
    for idx, step in enumerate(steps):
        if isinstance(step, str):
            time.sleep(float(step) / 1000)
            logger.debug("  macro[{}]: задержка {} мс", idx, step)
            continue

        delay = step.get("delay", 0)
        if delay:
            time.sleep(delay / 1000)

        repeat = int(step.get("repeat", 1))
        for r in range(repeat):
            sub = execute(step, settings)
            if sub.get("navigate"):
                return sub.get("message", "")
            msg = sub.get("message", "")
            if not sub.get("ok", True):
                logger.warning("  macro[{}][repeat {}] ошибка: {}", idx, r, msg)
            else:
                logger.debug("  macro[{}][repeat {}] → {}", idx, r, msg[:80] if msg else "")
            results.append(msg)

    final_msg = " → ".join(r for r in results if r)[:200]
    logger.success("Macro выполнен: {}", final_msg)
    return final_msg


def _folder(value: Any, _action: dict, _settings: dict) -> dict:
    page_id = str(value).strip()
    if not page_id:
        raise ValueError("folder: укажите ID страницы")
    return {"message": f"📁 {page_id}", "navigate": page_id}


def _screenshot(value: Any, _action: dict, _settings: dict) -> str:
    mode = str(value or "screen").strip().lower()
    try:
        import mss
        from PIL import Image
    except ImportError:
        raise RuntimeError("pip install mss Pillow")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with mss.mss() as sct:
        if mode == "window":
            try:
                import pygetwindow as gw
                win = gw.getActiveWindow()
                if win:
                    region = {"left": max(win.left, 0), "top": max(win.top, 0),
                              "width": max(win.width, 1), "height": max(win.height, 1)}
                    shot = sct.grab(region)
                else:
                    shot = sct.grab(sct.monitors[1])
            except Exception:
                shot = sct.grab(sct.monitors[1])
        else:
            shot = sct.grab(sct.monitors[0])

        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        path = SCREENSHOT_DIR / f"deck_{ts}.png"
        img.save(path)
        if mode == "clipboard":
            try:
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                _image_to_clipboard(buf.getvalue())
                return "📸 В буфер обмена"
            except Exception:
                img.save(path)
                return f"📸 {path.name} (нужен pywin32 для буфера)"
        os.startfile(SCREENSHOT_DIR)
        return f"📸 {path.name}"


def _image_to_clipboard(png_bytes: bytes) -> None:
    import win32clipboard
    from PIL import Image
    img = Image.open(io.BytesIO(png_bytes))
    output = io.BytesIO()
    img.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()


def _clipboard(value: Any, _action: dict, _settings: dict) -> str:
    key = str(value or "get").strip().lower()
    if key == "get":
        data = pyperclip.paste()
        preview = (data[:80] + "…") if len(data) > 80 else data
        return f"📋 {preview or '(пусто)'}"
    if key == "clear":
        pyperclip.copy("")
        return "📋 Очищен"
    pyperclip.copy(str(value))
    return f"📋 Скопировано ({len(str(value))} симв.)"


def _mouse(value: Any, action: dict, _settings: dict) -> str:
    import pyautogui
    pyautogui.FAILSAFE = False
    key = str(value or "click").strip().lower()
    if key == "click":
        pyautogui.click()
        return "🖱 Клик"
    if key == "right":
        pyautogui.click(button="right")
        return "🖱 ПКМ"
    if key == "double":
        pyautogui.doubleClick()
        return "🖱 Двойной клик"
    if "," in key:
        x, y = [int(v.strip()) for v in key.split(",", 1)]
        pyautogui.click(x, y)
        return f"🖱 Клик {x},{y}"
    raise ValueError("mouse: click, right, double или x,y")


def _window(value: Any, _action: dict, _settings: dict) -> str:
    key = str(value).strip().lower()
    if key == "close":
        keyboard_win.hotkey(["alt", "f4"])
        return "✕ Закрыть окно"
    if key == "minimize":
        keyboard_win.hotkey(["win", "down"])
        return "🗕 Свернуть"
    if key == "maximize":
        keyboard_win.hotkey(["win", "up"])
        return "🗖 Развернуть"
    if key == "switch":
        keyboard_win.hotkey(["alt", "tab"])
        return "⇥ Переключить окно"
    if key == "snap_left":
        keyboard_win.hotkey(["win", "left"])
        return "◧ Слева"
    if key == "snap_right":
        keyboard_win.hotkey(["win", "right"])
        return "◨ Справа"
    raise ValueError(f"window: неизвестное {key}")


def _obs(value: Any, _action: dict, settings: dict) -> str:
    return run_obs(str(value).strip(), settings.get("obs"))


def _yandex(value: Any, action: dict, settings: dict) -> str:
    cmd = str(value or "open").strip()
    query = str(action.get("query", "")).strip()
    if cmd == "search" and not query and value not in ("search", "open", ""):
        query = str(value).strip()
        cmd = "search"
    return run_yandex_music(cmd, query, settings)
