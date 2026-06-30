"""Надёжная отправка клавиш на Windows."""

from __future__ import annotations

import ctypes
import time

user32 = ctypes.windll.user32

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001

EXTENDED_KEYS = {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E, 0x5B, 0x5C, 0x5D}
MEDIA_VKS = {0xAD, 0xAE, 0xAF, 0xB0, 0xB1, 0xB3}

VK: dict[str, int] = {
    "backspace": 0x08, "tab": 0x09, "enter": 0x0D, "return": 0x0D,
    "shift": 0x10, "ctrl": 0x11, "control": 0x11, "alt": 0x12,
    "pause": 0x13, "capslock": 0x14, "esc": 0x1B, "escape": 0x1B, "space": 0x20,
    "pageup": 0x21, "pagedown": 0x22, "end": 0x23, "home": 0x24,
    "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "printscreen": 0x2C, "prtsc": 0x2C, "insert": 0x2D, "delete": 0x2E, "del": 0x2E,
    "win": 0x5B, "winleft": 0x5B, "lwin": 0x5B, "winright": 0x5C, "rwin": 0x5C,
    "apps": 0x5D, "menu": 0x5D,
    "volumeup": 0xAF, "volumedown": 0xAE, "volumemute": 0xAD,
    "playpause": 0xB3, "nexttrack": 0xB0, "prevtrack": 0xB1,
}
for i in range(12):
    VK[f"f{i + 1}"] = 0x70 + i
for i in range(26):
    VK[chr(ord("a") + i)] = 0x41 + i
for i in range(10):
    VK[str(i)] = 0x30 + i


def _to_vk(key: str) -> int:
    k = key.lower().strip()
    if k in VK:
        return VK[k]
    if len(k) == 1:
        return VK.get(k, ord(k.upper()))
    raise ValueError(f"Неизвестная клавиша: {key}")


def _key_event(vk: int, up: bool = False) -> None:
    scan = user32.MapVirtualKeyW(vk, 0)
    flags = KEYEVENTF_KEYUP if up else 0
    if vk in EXTENDED_KEYS or vk in MEDIA_VKS:
        flags |= KEYEVENTF_EXTENDEDKEY
    user32.keybd_event(ctypes.c_ubyte(vk & 0xFF), ctypes.c_ubyte(scan & 0xFF), flags, 0)


def press(key: str) -> None:
    vk = _to_vk(key)
    _key_event(vk, up=False)
    time.sleep(0.04)
    _key_event(vk, up=True)


def press_media(key: str) -> None:
    press(key)


def hotkey(keys: list[str]) -> None:
    vks = [_to_vk(k) for k in keys]
    for vk in vks:
        _key_event(vk, up=False)
        time.sleep(0.04)
    for vk in reversed(vks):
        _key_event(vk, up=True)
        time.sleep(0.04)


def show_desktop() -> None:
    hotkey(["win", "d"])