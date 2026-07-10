"""Системная громкость Windows (Core Audio) — точный set/get 0–100."""

from __future__ import annotations

from typing import Any

from .logger import logger


def _ensure_com() -> None:
    """COM обязателен в worker-потоках FastAPI/asyncio.to_thread."""
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        try:
            import comtypes
            comtypes.CoInitialize()
        except Exception:
            pass


def _endpoint():
    """IAudioEndpointVolume через pycaw (новый API: device.EndpointVolume)."""
    _ensure_com()
    from pycaw.pycaw import AudioUtilities

    speakers = AudioUtilities.GetSpeakers()
    # pycaw 2024+: AudioDevice.EndpointVolume; старый: Activate(...)
    if hasattr(speakers, "EndpointVolume") and speakers.EndpointVolume is not None:
        return speakers.EndpointVolume
    from comtypes import CLSCTX_ALL
    from comtypes import cast, POINTER
    from pycaw.pycaw import IAudioEndpointVolume

    interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def get_volume() -> dict[str, Any]:
    """Текущая громкость 0–100 и mute."""
    try:
        vol = _endpoint()
        level = float(vol.GetMasterVolumeLevelScalar())
        muted = bool(vol.GetMute())
        return {
            "level": int(round(level * 100)),
            "muted": muted,
            "ok": True,
            "source": "coreaudio",
        }
    except Exception as e:
        logger.debug("get_volume fallback: {}", e)
        return {"level": 50, "muted": False, "ok": False, "source": "fallback"}


def set_volume(level: int | float) -> dict[str, Any]:
    """Установить громкость 0–100."""
    level = max(0, min(100, int(round(float(level)))))
    try:
        vol = _endpoint()
        vol.SetMasterVolumeLevelScalar(level / 100.0, None)
        if level > 0 and vol.GetMute():
            vol.SetMute(0, None)
        muted = bool(vol.GetMute())
        logger.info("🔊 Volume set → {}%", level)
        return {"level": level, "muted": muted, "ok": True, "message": f"🔊 {level}%"}
    except Exception as e:
        logger.warning("set_volume CoreAudio failed: {} — fallback keys", e)
        return _set_volume_keys(level)


def change_volume(delta: int) -> dict[str, Any]:
    """Изменить громкость на delta процентов."""
    cur = get_volume()
    if cur.get("ok"):
        return set_volume(cur["level"] + delta)
    from . import keyboard_win

    steps = max(1, min(20, abs(int(delta)) // 2))
    key = "volumeup" if delta > 0 else "volumedown"
    for _ in range(steps):
        keyboard_win.press(key)
    return {
        "level": cur.get("level", 50),
        "muted": False,
        "ok": True,
        "message": f"🔊 {'+' if delta > 0 else '-'}{abs(delta)}",
    }


def toggle_mute() -> dict[str, Any]:
    try:
        vol = _endpoint()
        current = bool(vol.GetMute())
        vol.SetMute(0 if current else 1, None)
        muted = not current
        level = int(round(float(vol.GetMasterVolumeLevelScalar()) * 100))
        msg = "🔇 Mute" if muted else f"🔊 Unmute · {level}%"
        logger.info(msg)
        return {"level": level, "muted": muted, "ok": True, "message": msg}
    except Exception as e:
        logger.warning("toggle_mute fallback: {}", e)
        from . import keyboard_win

        keyboard_win.press("volumemute")
        return {"level": 0, "muted": True, "ok": True, "message": "🔇 Mute toggle"}


def set_mute(muted: bool) -> dict[str, Any]:
    try:
        vol = _endpoint()
        vol.SetMute(1 if muted else 0, None)
        level = int(round(float(vol.GetMasterVolumeLevelScalar()) * 100))
        return {
            "level": level,
            "muted": muted,
            "ok": True,
            "message": "🔇 Mute" if muted else f"🔊 {level}%",
        }
    except Exception:
        return toggle_mute()


def _set_volume_keys(target: int) -> dict[str, Any]:
    from . import keyboard_win

    for _ in range(50):
        keyboard_win.press("volumedown")
    steps = max(0, min(50, target // 2))
    for _ in range(steps):
        keyboard_win.press("volumeup")
    return {"level": target, "muted": False, "ok": True, "message": f"🔊 ~{target}%", "source": "keys"}


def run_audio(action: str, value: Any = None) -> dict[str, Any]:
    key = (action or "").strip().lower()
    if key in ("get", "status", ""):
        st = get_volume()
        st["message"] = f"{'🔇' if st.get('muted') else '🔊'} {st.get('level', 0)}%"
        return st
    if key in ("set", "level", "volume"):
        return set_volume(value if value is not None else 50)
    if key in ("up", "volume_up", "+"):
        delta = int(value) if value not in (None, "") else 5
        return change_volume(abs(delta))
    if key in ("down", "volume_down", "-"):
        delta = int(value) if value not in (None, "") else 5
        return change_volume(-abs(delta))
    if key in ("mute", "toggle_mute"):
        return toggle_mute()
    if key == "mute_on":
        return set_mute(True)
    if key == "mute_off":
        return set_mute(False)
    # numeric string → absolute level
    try:
        return set_volume(float(key))
    except ValueError:
        pass
    raise ValueError(f"audio: неизвестное действие {key}")
