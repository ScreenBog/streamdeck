"""Чтение Now Playing из Windows Media Session (как плеер Windows)."""

from __future__ import annotations

import asyncio
from typing import Any


def get_media_info() -> dict[str, Any] | None:
    try:
        return asyncio.run(_read_media())
    except Exception:
        return None


async def _read_media() -> dict[str, Any] | None:
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as Manager,
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as Status,
    )

    manager = await Manager.request_async()
    session = manager.get_current_session()

    if not session:
        sessions = manager.get_sessions()
        for i in range(sessions.size):
            s = sessions[i]
            app_id = (s.source_app_user_model_id or "").lower()
            if any(k in app_id for k in ("yandex", "chrome", "edge", "firefox", "music")):
                session = s
                break
        if not session and sessions.size > 0:
            session = sessions[0]

    if not session:
        return None

    props = await session.try_get_media_properties_async()
    if not props:
        return None

    playback = session.get_playback_info()
    status = playback.playback_status if playback else None
    playing = status == Status.PLAYING if status is not None else False

    title = (props.title or "").strip()
    artist = (props.artist or "").strip()
    album = (props.album_title or "").strip()

    track = title
    if artist:
        track = f"{artist} — {title}" if title else artist

    return {
        "playing": playing,
        "title": title,
        "artist": artist,
        "album": album,
        "track": track or "—",
        "app": session.source_app_user_model_id or "",
    }


async def media_command(cmd: str) -> bool:
    """play, pause, next, prev через Windows Media API."""
    from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as Manager

    manager = await Manager.request_async()
    session = manager.get_current_session()
    if not session:
        sessions = manager.get_sessions()
        if sessions.size > 0:
            session = sessions[0]
    if not session:
        return False

    if cmd == "play_pause":
        await session.try_toggle_play_pause_async()
    elif cmd == "next":
        await session.try_skip_next_async()
    elif cmd == "prev":
        await session.try_skip_previous_async()
    else:
        return False
    return True