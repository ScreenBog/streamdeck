# Deck — браузерный Stream Deck

Управление ПК с телефона или планшета через браузер: горячие клавиши, приложения, OBS, Яндекс Музыка, скриншоты и макросы.

Работает на **Windows**. Сервер на ПК, UI — в любом браузере в локальной сети.

## Быстрый старт

```bash
pip install -r requirements.txt
python run.py
```

Открой на ПК: `http://127.0.0.1:8765`  
С телефона (та же Wi‑Fi): `http://<IP-ПК>:8765` — адрес печатается в консоли при старте.

### Автозапуск

```bat
install_autostart.bat
```

Остановка: `stop.bat` · удаление автозапуска: `uninstall_autostart.bat`

## Возможности

| Категория | Действия |
|-----------|----------|
| **Медиа** | громкость, mute, play/pause, next/prev, mute микрофона (Win+Alt+K) |
| **Система** | рабочий стол, lock, сон, shutdown/restart, корзина, Task Manager |
| **Окна** | close, snap left/right, Alt+Tab, minimize/maximize |
| **Hotkey / Macro** | любые сочетания + цепочки шагов с delay/repeat |
| **OBS** | стрим/запись через WebSocket (пароль в настройках) |
| **Яндекс Музыка** | плеер, поиск, волна, коллекция, like/dislike, now playing |
| **Прочее** | скриншоты, буфер, shell, URL, запуск приложений |

### Страницы

- **Главная** — быстрые действия
- **Стрим** — OBS + Discord mute/deaf
- **Я.Музыка** — полноэкранный плеер с Now Playing (Windows Media Session)

Режим ✏️: добавление/редактирование кнопок, страниц (тема `default` / `stream` / `yandex`).

## API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/info` | title, порт, LAN IP, нужен ли PIN |
| GET/PUT | `/api/config` | конфиг (заголовок `X-Deck-Pin`) |
| POST | `/api/execute` | `{ "buttonId", "pageId" }` |
| POST | `/api/yandex` | `{ "action", "query" }` |
| GET | `/api/yandex/now` | текущий трек |
| GET | `/api/status` | CPU / RAM |
| GET | `/api/logs?lines=200` | последние логи |
| WS | `/ws` | live-события (`press`, `config`, `yandex`) |

## Настройки

В UI → ⚙️:

- PIN (пусто = без пароля)
- сетка, цвета, скругление, glow
- OBS WebSocket password
- режим Я.Музыки: браузер (Chrome/Edge app window) или десктоп-приложение
- экспорт / импорт JSON, просмотр логов

Конфиг: `data/config.json` · логи: `data/logs/deck.log` · скрины: `data/screenshots/`

## Структура

```
streamdeck/
├── run.py                 # точка входа
├── requirements.txt
├── data/config.json
├── server/
│   ├── main.py            # FastAPI + WebSocket
│   ├── executor.py        # выполнение действий
│   ├── yandex_music.py    # Я.Музыка
│   ├── media_session.py   # Windows Now Playing
│   ├── obs_ctrl.py
│   ├── keyboard_win.py
│   ├── store.py
│   └── logger.py          # loguru
└── web/                   # UI (HTML/CSS/JS)
```

## Зависимости

Python 3.10+ · FastAPI · uvicorn · pyautogui · pywin32 · winsdk · mss · Pillow · loguru · …

```bash
pip install -r requirements.txt
```

## OBS

1. OBS → Инструменты → WebSocket Server Settings → Enable  
2. Скопируй пароль в настройки Deck  
3. Кнопки типа `obs` → `toggle_stream` / `toggle_record` / …

## Примечания

- Сервер слушает `0.0.0.0` — доступен в LAN. Для чужих сетей поставь PIN.
- Media-клавиши и фокус окон требуют, чтобы ПК не был заблокирован.
- Я.Музыка: предпочтительно Chrome/Edge; hotkeys (K/L/J/F/D/…) работают при фокусе на плеере.
