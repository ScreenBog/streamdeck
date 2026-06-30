"""Управление OBS через WebSocket 5.x."""

from __future__ import annotations

import json
import uuid
from typing import Any

OBS_ACTIONS = {
    "start_stream": ("StartStream", {}),
    "stop_stream": ("StopStream", {}),
    "toggle_stream": ("ToggleStream", {}),
    "start_record": ("StartRecord", {}),
    "stop_record": ("StopRecord", {}),
    "toggle_record": ("ToggleRecord", {}),
    "pause_record": ("PauseRecord", {}),
    "resume_record": ("ResumeRecord", {}),
}


def run_obs(action: str, settings: dict[str, Any] | None = None) -> str:
    try:
        import websocket
    except ImportError:
        raise RuntimeError("Установите: pip install websocket-client")

    settings = settings or {}
    host = settings.get("host", "localhost")
    port = int(settings.get("port", 4455))
    password = settings.get("password", "")

    if action.startswith("scene:"):
        scene_name = action[6:].strip()
        req_type, data = "SetCurrentProgramScene", {"sceneName": scene_name}
    elif action in OBS_ACTIONS:
        req_type, data = OBS_ACTIONS[action]
    else:
        raise ValueError(f"OBS: неизвестное действие {action}")

    ws = websocket.create_connection(f"ws://{host}:{port}", timeout=3)
    try:
        hello = json.loads(ws.recv())
        auth_payload: dict[str, Any] = {"op": 1, "d": {"rpcVersion": 1}}
        auth_info = hello.get("d", {}).get("authentication")
        if auth_info and password:
            import base64
            import hashlib

            secret = base64.b64encode(
                hashlib.sha256(
                    (password + auth_info["salt"]).encode()
                ).digest()
            ).decode()
            secret = base64.b64encode(
                hashlib.sha256((secret + auth_info["challenge"]).encode()).digest()
            ).decode()
            auth_payload["d"]["authentication"] = secret
            auth_payload["d"]["eventSubscriptions"] = 0
        elif auth_info and not password:
            raise RuntimeError("OBS требует пароль — укажите в настройках Deck")

        ws.send(json.dumps(auth_payload))
        identified = json.loads(ws.recv())
        if identified.get("op") != 2:
            raise RuntimeError("OBS: не удалось подключиться")

        req_id = str(uuid.uuid4())
        ws.send(json.dumps({"op": 6, "d": {"requestType": req_type, "requestId": req_id, "requestData": data}}))
        resp = json.loads(ws.recv())
        status = resp.get("d", {}).get("requestStatus", {})
        if not status.get("result", False):
            comment = status.get("comment", "ошибка")
            raise RuntimeError(f"OBS: {comment}")
        return f"🎬 OBS: {action}"
    finally:
        ws.close()