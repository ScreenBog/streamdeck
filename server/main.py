"""Deck — браузерный Stream Deck с агентом на ПК. Улучшенная версия с логированием."""

from __future__ import annotations

import asyncio
import json
import socket
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .executor import execute
from .logger import logger, setup_logging
from .store import ensure_config, load_config, save_config
from .yandex_music import run as yandex_run

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"
LOG_PATH = ROOT / "data" / "logs" / "deck.log"

app = FastAPI(title="Deck", version="1.0.0")
config: dict[str, Any] = ensure_config()
clients: set[WebSocket] = set()


class ConfigUpdate(BaseModel):
    config: dict[str, Any]


class ActionRequest(BaseModel):
    buttonId: str
    pageId: str | None = None


class YandexRequest(BaseModel):
    action: str = "play_pause"
    query: str = ""


class AudioRequest(BaseModel):
    action: str = "get"  # get | set | up | down | mute | mute_on | mute_off
    value: float | int | None = None  # level 0-100 or delta


def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def check_pin(pin: str | None) -> None:
    expected = config.get("settings", {}).get("pin", "")
    if expected and pin != expected:
        logger.warning("Неверный PIN при доступе к API")
        raise HTTPException(401, "Неверный PIN")


def find_button(page_id: str, button_id: str) -> dict | None:
    for page in config.get("pages", []):
        if page["id"] != page_id:
            continue
        for btn in page.get("buttons", []):
            if btn["id"] == button_id:
                return btn
    return None


async def broadcast(message: dict[str, Any]) -> None:
    dead: list[WebSocket] = []
    data = json.dumps(message, ensure_ascii=False)
    for ws in clients:
        try:
            await ws.send_text(data)
        except Exception as e:
            logger.debug("WS клиент отвалился: {}", e)
            dead.append(ws)
    for ws in dead:
        clients.discard(ws)


@app.get("/api/info")
def api_info():
    s = config.get("settings", {})
    return {
        "title": s.get("title", "Deck"),
        "gridCols": s.get("gridCols", 5),
        "gridRows": s.get("gridRows", 3),
        "theme": s.get("theme", "dark"),
        "authRequired": bool(s.get("pin")),
        "lanIp": get_lan_ip(),
        "port": s.get("port", 8765),
    }


@app.get("/api/config")
def api_get_config(x_deck_pin: str | None = Header(None)):
    check_pin(x_deck_pin)
    return config


@app.put("/api/config")
async def api_put_config(body: ConfigUpdate, x_deck_pin: str | None = Header(None)):
    global config
    check_pin(x_deck_pin)
    config = body.config
    save_config(config)
    await broadcast({"type": "config", "config": config})
    logger.info("Конфиг обновлён через API")
    return {"ok": True}


@app.get("/api/status")
def api_status():
    from .audio_ctrl import get_volume
    from .yandex_music import get_status as ym_status

    out: dict[str, Any] = {"cpu": 0, "ram": 0, "online": True}
    try:
        import psutil
        out["cpu"] = round(psutil.cpu_percent(interval=0.05), 1)
        out["ram"] = round(psutil.virtual_memory().percent, 1)
    except Exception:
        pass
    try:
        out["audio"] = get_volume()
    except Exception:
        out["audio"] = {"level": 50, "muted": False, "ok": False}
    try:
        out["now"] = ym_status()
    except Exception:
        out["now"] = None
    return out


@app.get("/api/audio")
def api_audio_get(x_deck_pin: str | None = Header(None)):
    check_pin(x_deck_pin)
    from .audio_ctrl import get_volume
    return get_volume()


@app.post("/api/audio")
async def api_audio_post(body: AudioRequest, x_deck_pin: str | None = Header(None)):
    check_pin(x_deck_pin)
    from .audio_ctrl import run_audio

    result = await asyncio.to_thread(run_audio, body.action, body.value)
    await broadcast({"type": "audio", "audio": result})
    return result


@app.get("/api/logs", response_class=PlainTextResponse)
def api_logs(lines: int = 100, x_deck_pin: str | None = Header(None)):
    check_pin(x_deck_pin)
    if not LOG_PATH.exists():
        return "Логов пока нет"
    try:
        with LOG_PATH.open(encoding="utf-8") as f:
            all_lines = f.readlines()
            return "".join(all_lines[-lines:])
    except Exception as e:
        logger.error("Ошибка чтения логов: {}", e)
        return f"Ошибка чтения логов: {e}"


@app.post("/api/auth")
def api_auth(pin: str):
    expected = config.get("settings", {}).get("pin", "")
    if not expected or pin == expected:
        return {"ok": True}
    logger.warning("Неудачная авторизация по PIN")
    raise HTTPException(401, "Неверный PIN")


@app.get("/api/yandex/now")
def api_yandex_now(x_deck_pin: str | None = Header(None)):
    check_pin(x_deck_pin)
    from .yandex_music import get_status
    return get_status()


@app.post("/api/yandex")
async def api_yandex(body: YandexRequest, x_deck_pin: str | None = Header(None)):
    check_pin(x_deck_pin)
    message = await asyncio.to_thread(yandex_run, body.action, body.query, config.get("settings", {}))
    from .yandex_music import get_status
    status = await asyncio.to_thread(get_status)
    result = {"ok": True, "message": message, "now": status}
    await broadcast({"type": "yandex", "result": result, "now": status})
    return result


@app.post("/api/execute")
async def api_execute(body: ActionRequest, x_deck_pin: str | None = Header(None)):
    check_pin(x_deck_pin)
    page_id = body.pageId or config.get("activePage", "")
    btn = find_button(page_id, body.buttonId)
    if not btn:
        logger.warning("Кнопка не найдена: page={}, button={}", page_id, body.buttonId)
        raise HTTPException(404, "Кнопка не найдена")

    result = await asyncio.to_thread(execute, btn.get("action", {}), config.get("settings", {}))
    event: dict[str, Any] = {
        "type": "pressed",
        "buttonId": body.buttonId,
        "pageId": page_id,
        "result": result,
    }
    if result.get("navigate"):
        event["navigate"] = result["navigate"]
    await broadcast(event)
    return result


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        await ws.send_text(json.dumps({"type": "config", "config": config}, ensure_ascii=False))
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "auth":
                pin = msg.get("pin", "")
                expected = config.get("settings", {}).get("pin", "")
                if expected and pin != expected:
                    await ws.send_text(json.dumps({"type": "auth_fail"}))
                    continue
                await ws.send_text(json.dumps({"type": "auth_ok"}))
                continue

            if msg.get("type") == "press":
                page_id = msg.get("pageId") or config.get("activePage", "")
                btn_id = msg.get("buttonId", "")
                btn = find_button(page_id, btn_id)
                if btn:
                    logger.info("WS press: page={}, button={}", page_id, btn_id)
                    result = await asyncio.to_thread(execute, btn.get("action", {}), config.get("settings", {}))
                    event: dict[str, Any] = {
                        "type": "pressed",
                        "buttonId": btn_id,
                        "pageId": page_id,
                        "result": result,
                    }
                    if result.get("navigate"):
                        event["navigate"] = result["navigate"]
                    await broadcast(event)
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(ws)


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


def run() -> None:
    global config
    setup_logging()
    config = ensure_config()
    port = int(config.get("settings", {}).get("port", 8765))
    pin = config.get("settings", {}).get("pin", "")
    ip = get_lan_ip()

    logger.info("╔══════════════════════════════════════╗")
    logger.info("║         DECK — Browser Stream Deck   ║")
    logger.info("╠══════════════════════════════════════╣")
    logger.info("║  Локально:  http://127.0.0.1:{}     ║", port)
    logger.info("║  С телефона: http://{}:{}  ║", ip, port)
    pin_label = pin if pin else "(отключён)"
    logger.info("║  PIN:        {:<24} ║", pin_label)
    logger.info("╚══════════════════════════════════════╝")

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


if __name__ == "__main__":
    run()
