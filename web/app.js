const $ = (sel) => document.querySelector(sel);

let config = null;
let info = null;
let pin = localStorage.getItem("deck_pin") || "";
let editMode = false;
let ws = null;
let activePageId = null;

const MEDIA_OPTIONS = [
  ["volume_up", "Громкость +"], ["volume_down", "Громкость -"], ["mute", "Mute"],
  ["play_pause", "Play/Pause"], ["next", "Следующий"], ["prev", "Предыдущий"],
  ["mic_mute", "Микрофон Win+Alt+K"],
];

const SYSTEM_OPTIONS = [
  ["show_desktop", "Показать рабочий стол (Win+D)"],
  ["lock", "Заблокировать ПК"], ["sleep", "Сон"],
  ["shutdown", "Выключение (60с)"], ["restart", "Перезагрузка (60с)"],
  ["cancel_shutdown", "Отменить выключение"],
  ["taskmgr", "Диспетчер задач"], ["explorer", "Проводник"],
  ["settings", "Параметры Windows"], ["empty_trash", "Очистить корзину"],
  ["active_window", "Активное окно"],
];

const WINDOW_OPTIONS = [
  ["close", "Закрыть (Alt+F4)"], ["minimize", "Свернуть"],
  ["maximize", "Развернуть"], ["switch", "Alt+Tab"],
  ["snap_left", "Прикрепить слева"], ["snap_right", "Прикрепить справа"],
];

const SCREENSHOT_OPTIONS = [
  ["screen", "Весь экран"], ["window", "Активное окно"], ["clipboard", "В буфер обмена"],
];

const CLIPBOARD_OPTIONS = [
  ["get", "Показать буфер"], ["clear", "Очистить"],
];

const MOUSE_OPTIONS = [
  ["click", "Левый клик"], ["right", "Правый клик"], ["double", "Двойной клик"],
];

const OBS_OPTIONS = [
  ["toggle_stream", "Стрим вкл/выкл"], ["start_stream", "Начать стрим"],
  ["stop_stream", "Остановить стрим"], ["toggle_record", "Запись вкл/выкл"],
  ["start_record", "Начать запись"], ["stop_record", "Остановить запись"],
];

const YANDEX_OPTIONS = [
  ["browser", "Открыть в браузере"], ["play_pause", "Play / Pause"],
  ["next", "Следующий"], ["prev", "Предыдущий"], ["like", "Лайк"],
  ["my_wave", "Моя волна"], ["collection", "Коллекция"], ["playlists", "Плейлисты"],
  ["history", "История"], ["charts", "Чарты"], ["podcasts", "Подкасты"],
  ["new_releases", "Новинки"], ["search", "Поиск (текст ниже)"],
];

const HOTKEY_PRESETS = [
  ["", "— вручную —"],
  ["win+d", "Win+D — рабочий стол"],
  ["alt+tab", "Alt+Tab"],
  ["ctrl+c", "Ctrl+C"], ["ctrl+v", "Ctrl+V"], ["ctrl+z", "Ctrl+Z"],
  ["ctrl+shift+esc", "Диспетчер задач"],
  ["win+l", "Блокировка"], ["win+e", "Проводник"],
  ["win+shift+s", "Скриншот Win11"], ["f5", "F5"], ["f11", "F11"],
  ["ctrl+shift+d", "Discord mute"], ["ctrl+shift+m", "Discord deafen"],
];

const TYPE_HINTS = {
  none: "—", hotkey: "ctrl+shift+s или win,d",
  app: "notepad или C:\\path\\app.exe", url: "https://youtube.com",
  shell: "echo hello", text: "Текст для ввода",
  media: "—", system: "—", window: "—", screenshot: "—",
  clipboard: "текст для копирования", mouse: "click или 500,300",
  obs: "toggle_stream", yandex: "play_pause или search",
  macro: '[{"type":"hotkey","value":"win+d"}]',
  folder: "ID страницы", path: "C:\\Users\\...\\Desktop",
};

const SELECT_TYPES = {
  media: MEDIA_OPTIONS, system: SYSTEM_OPTIONS, window: WINDOW_OPTIONS,
  screenshot: SCREENSHOT_OPTIONS, clipboard: CLIPBOARD_OPTIONS,
  mouse: MOUSE_OPTIONS, obs: OBS_OPTIONS, yandex: YANDEX_OPTIONS,
};

const PAGE_THEMES = {
  yandex: { accent: "#ffcc00", glow: "rgba(255,204,0,0.4)", mark: "♫", bodyClass: "theme-yandex" },
  stream: { accent: "#ff4466", glow: "rgba(255,68,102,0.35)", mark: "●", bodyClass: "theme-stream" },
  default: { accent: "#7c6cf0", glow: "rgba(124,108,240,0.45)", mark: "◆", bodyClass: "" },
};

async function api(path, opts = {}) {
  const headers = { "Content-Type": "application/json", ...opts.headers };
  if (pin) headers["X-Deck-Pin"] = pin;
  const res = await fetch(path, { ...opts, headers });
  if (res.status === 401) { logout(); throw new Error("auth"); }
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function logout() {
  pin = "";
  localStorage.removeItem("deck_pin");
  showAuth();
}

function showAuth() {
  $("#auth-screen").classList.remove("hidden");
  $("#app").classList.add("hidden");
}

function showApp() {
  $("#auth-screen").classList.add("hidden");
  $("#app").classList.remove("hidden");
}

function toast(msg, ms = 2800) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.remove("hidden");
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.add("hidden"), ms);
}

function setConnStatus(online) {
  const el = $("#conn-status");
  el.className = "status " + (online ? "online" : "offline");
  el.title = online ? "Подключено" : "Нет связи";
}

function getPageTheme(page) {
  const key = page?.theme || "default";
  return PAGE_THEMES[key] || PAGE_THEMES.default;
}

function applyPageTheme() {
  const page = getActivePage();
  const theme = getPageTheme(page);
  document.body.className = theme.bodyClass;
  document.documentElement.style.setProperty("--page-accent", theme.accent);
  document.documentElement.style.setProperty("--page-glow", theme.glow);
  $("#brand-mark").textContent = theme.mark;
  const isMusic = page?.layout === "music" || page?.theme === "yandex";
  $("#music-bar").classList.toggle("hidden", !isMusic || page?.layout === "music");
}

function renderPage() {
  const page = getActivePage();
  const chassis = document.querySelector(".deck-chassis");
  const full = $("#music-full-panel");
  if (page?.layout === "music") {
    chassis?.classList.add("hidden");
    full?.classList.remove("hidden");
    pollYmNow();
  } else {
    chassis?.classList.remove("hidden");
    full?.classList.add("hidden");
    renderGrid();
  }
}

function navigateToPage(pageId) {
  if (!config.pages.find((p) => p.id === pageId)) return;
  activePageId = pageId;
  config.activePage = pageId;
  renderTabs();
  applyPageTheme();
  applyCustomize();
  renderPage();
}

function getActivePage() {
  return config.pages.find((p) => p.id === activePageId) || config.pages[0];
}

function renderTabs() {
  const nav = $("#page-tabs");
  nav.innerHTML = "";
  config.pages.forEach((page) => {
    const btn = document.createElement("button");
    const yandex = page.theme === "yandex" ? " yandex-tab" : "";
    btn.className = "page-tab" + yandex + (page.id === activePageId ? " active" : "");
    btn.textContent = page.name;
    btn.onclick = () => navigateToPage(page.id);
    nav.appendChild(btn);
  });
}

function renderGrid() {
  const grid = $("#deck-grid");
  const s = config.settings;
  const cols = s.gridCols || 5;
  const rows = s.gridRows || 3;
  grid.style.gridTemplateColumns = `repeat(${cols}, var(--btn-size))`;
  grid.innerHTML = "";

  const page = getActivePage();
  const occupied = new Set();

  (page.buttons || []).forEach((btn) => {
    occupied.add(`${btn.col},${btn.row}`);
    grid.appendChild(makeButton(btn));
  });

  if (editMode) {
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (!occupied.has(`${c},${r}`)) {
          const empty = document.createElement("div");
          empty.className = "deck-btn empty";
          empty.onclick = () => openEditor(null, c, r);
          grid.appendChild(empty);
        }
      }
    }
  }
}

function makeButton(btn) {
  const el = document.createElement("button");
  const isFolder = btn.action?.type === "folder";
  const isYandex = btn.action?.type === "yandex";
  el.className = "deck-btn"
    + (editMode ? " edit-mode" : "")
    + (isFolder ? " folder-btn" : "")
    + (isYandex ? " yandex-btn" : "");
  el.style.background = btn.color || "#1a1a2e";
  let html = `<span class="icon">${esc(btn.icon || "⬛")}</span><span class="label">${esc(btn.label || "")}</span>`;
  if (editMode) html += `<span class="edit-badge">✏</span>`;
  if (isFolder) html += `<span class="folder-corner"></span>`;
  el.innerHTML = html;
  el.onclick = editMode ? () => openEditor(btn) : () => pressButton(btn);
  return el;
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

async function pressButton(btn) {
  document.querySelectorAll(".deck-btn").forEach((e) => e.classList.remove("pressed"));
  try {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "press", buttonId: btn.id, pageId: activePageId }));
    } else {
      const result = await api("/api/execute", {
        method: "POST",
        body: JSON.stringify({ buttonId: btn.id, pageId: activePageId }),
      });
      handlePressResult(btn.id, result);
    }
  } catch (e) {
    if (e.message !== "auth") toast("Ошибка выполнения");
  }
}

function handlePressResult(buttonId, result, navigate) {
  const page = getActivePage();
  const idx = (page.buttons || []).findIndex((b) => b.id === buttonId);
  const btns = document.querySelectorAll(".deck-btn:not(.empty)");
  if (btns[idx]) {
    btns[idx].classList.add("pressed");
    setTimeout(() => btns[idx]?.classList.remove("pressed"), 200);
  }
  const nav = navigate || result?.navigate;
  if (nav) navigateToPage(nav);
  if (result?.message) {
    toast(result.ok ? result.message : "⚠ " + result.message);
    if (result.message.includes("Музык") || result.message.includes("⏯") || result.message.includes("⏭") || result.message.includes("⏮") || result.message.includes("🟡")) {
      $("#music-bar-sub").textContent = result.message.replace(/^[^\s]+\s/, "");
    }
  }
}

async function execYandex(action, query = "") {
  try {
    const result = await api("/api/yandex", {
      method: "POST",
      body: JSON.stringify({ action, query }),
    });
    if (result?.message) {
      toast(result.message);
      const sub = result.message.replace(/^[^\s]+\s/, "");
      if ($("#music-bar-sub")) $("#music-bar-sub").textContent = sub;
      if ($("#ym-status")) $("#ym-status").textContent = sub;
    }
    if (result?.now) updateYmNow(result.now);
  } catch { toast("Ошибка Яндекс Музыки"); }
}

function updateYmNow(data) {
  const artist = data.artist || "";
  const title = data.title || data.track || "—";
  if ($("#ym-artist")) $("#ym-artist").textContent = artist || " ";
  if ($("#ym-track")) $("#ym-track").textContent = title;
  if ($("#music-bar-sub")) $("#music-bar-sub").textContent = data.track || title;
  const dot = $("#ym-playing-dot");
  if (dot) dot.classList.toggle("live", !!data.playing);
  if ($("#ym-status") && data.source === "windows") {
    const st = data.playing ? "Играет" : "Пауза";
    $("#ym-status").innerHTML = `<span id="ym-playing-dot" class="ym-dot${data.playing ? " live" : ""}"></span> ${st} · Windows Media`;
  }
}

function applyCustomize() {
  const c = config?.settings?.customize || {};
  const accent = c.accent || "#7c6cf0";
  const ymAccent = c.ymAccent || "#ffcc00";
  document.documentElement.style.setProperty("--accent", accent);
  if (getActivePage()?.theme !== "yandex") {
    document.documentElement.style.setProperty("--page-accent", accent);
    document.documentElement.style.setProperty("--page-glow", hexGlow(accent));
  }
  document.documentElement.style.setProperty("--ym-accent", ymAccent);
  document.documentElement.style.setProperty("--radius", (c.btnRadius || 16) + "px");
  document.body.classList.toggle("no-glow", c.glow === false);
  document.body.classList.toggle("compact", !!c.compact);
  const page = getActivePage();
  if (page?.theme === "yandex") {
    document.documentElement.style.setProperty("--page-accent", ymAccent);
    document.documentElement.style.setProperty("--page-glow", hexGlow(ymAccent));
  }
}

function hexGlow(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},0.4)`;
}

async function pollYmNow() {
  try {
    const data = await api("/api/yandex/now");
    updateYmNow(data);
  } catch { /* ignore */ }
}

let ymPollTimer = null;
function startYmPolling() {
  clearInterval(ymPollTimer);
  ymPollTimer = setInterval(() => {
    const page = getActivePage();
    if (page?.layout === "music" || page?.theme === "yandex") pollYmNow();
  }, 2000);
}

function applyConfig(newConfig) {
  config = newConfig;
  activePageId = config.activePage || config.pages[0]?.id;
  $("#deck-title").textContent = config.settings?.title || "Deck";
  renderTabs();
  applyPageTheme();
  applyCustomize();
  renderPage();
}

function connectWs() {
  if (ws) ws.close();
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.onopen = () => { setConnStatus(true); if (pin) ws.send(JSON.stringify({ type: "auth", pin })); };
  ws.onclose = () => { setConnStatus(false); setTimeout(connectWs, 3000); };
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.type === "config") applyConfig(msg.config);
    if (msg.type === "pressed") handlePressResult(msg.buttonId, msg.result, msg.navigate);
    if (msg.type === "yandex") {
      if (msg.result?.message) toast(msg.result.message);
      if (msg.now) updateYmNow(msg.now);
    }
    if (msg.type === "auth_fail") logout();
  };
}

async function saveConfig() {
  config.activePage = activePageId;
  await api("/api/config", { method: "PUT", body: JSON.stringify({ config }) });
  toast("Сохранено");
}

async function pollStatus() {
  try {
    const s = await fetch("/api/status").then((r) => r.json());
    $("#sys-status").textContent = `CPU ${s.cpu}% · RAM ${s.ram}%`;
  } catch { /* ignore */ }
}

/* Editor */
function updateValueField() {
  const type = $("#f-type").value;
  const input = $("#f-value");
  const area = $("#f-value-area");
  const select = $("#f-value-select");
  const label = $("#f-value-label");
  const presetRow = $("#f-preset-row");

  input.classList.add("hidden");
  area.classList.add("hidden");
  select.classList.add("hidden");
  presetRow.classList.toggle("hidden", type !== "hotkey");

  if (type === "yandex" && $("#f-value-select").value === "search") {
    label.textContent = "Поисковый запрос";
    input.classList.remove("hidden");
    input.placeholder = "название трека или исполнитель";
    return;
  }
  if (type === "folder") {
    label.textContent = "Страница";
    select.classList.remove("hidden");
    select.innerHTML = config.pages.map((p) => `<option value="${p.id}">${esc(p.name)}</option>`).join("");
    return;
  }
  if (SELECT_TYPES[type]) {
    label.textContent = "Действие";
    select.classList.remove("hidden");
    select.innerHTML = SELECT_TYPES[type].map(([v, t]) => `<option value="${v}">${t}</option>`).join("");
    return;
  }
  if (type === "macro") {
    label.textContent = "Шаги (JSON)";
    area.classList.remove("hidden");
    area.placeholder = '[{"type":"hotkey","value":"win+d","delay":100},{"type":"app","value":"notepad"}]';
    return;
  }
  if (["shell", "text", "clipboard"].includes(type)) {
    label.textContent = "Значение";
    area.classList.remove("hidden");
    return;
  }
  if (type === "none") { label.textContent = "—"; return; }
  label.textContent = "Значение";
  input.classList.remove("hidden");
  input.placeholder = TYPE_HINTS[type] || "";
}

function getValueFromForm() {
  const type = $("#f-type").value;
  if (type === "yandex") {
    const sel = $("#f-value-select").value;
    if (sel === "search") return $("#f-value").value.trim() || "search";
    return sel;
  }
  if (type === "folder" || SELECT_TYPES[type]) return $("#f-value-select").value;
  if (type === "macro") {
    const raw = $("#f-value-area").value.trim();
    return JSON.parse(raw);
  }
  if (["shell", "text"].includes(type) || (type === "clipboard" && !SELECT_TYPES.clipboard.find(([v]) => v === $("#f-value-select")?.value))) {
    return $("#f-value-area").value;
  }
  if (type === "clipboard" && $("#f-value-area").value && !$("#f-value-select").classList.contains("hidden")) {
    const sel = $("#f-value-select").value;
    if (sel === "get" || sel === "clear") return sel;
  }
  if (type === "hotkey") {
    const raw = $("#f-value").value.trim();
    if (raw.startsWith("[")) { try { return JSON.parse(raw); } catch { /* */ } }
    return raw.split(/[+,\s]+/).map((k) => k.trim().toLowerCase()).filter(Boolean);
  }
  return $("#f-value").value;
}

function setValueInForm(type, value, action = {}) {
  if (type === "yandex") {
    if (value === "search" && action.query) {
      $("#f-value-select").value = "search";
      $("#f-value").value = action.query;
      updateValueField();
      return;
    }
    if (value && !YANDEX_OPTIONS.find(([v]) => v === value)) {
      $("#f-value-select").value = "search";
      $("#f-value").value = value;
      updateValueField();
      return;
    }
  }
  if (type === "folder" || SELECT_TYPES[type]) {
    $("#f-value-select").value = value || "";
  } else if (type === "macro") {
    $("#f-value-area").value = Array.isArray(value) ? JSON.stringify(value, null, 2) : (value || "");
  } else if (["shell", "text"].includes(type)) {
    $("#f-value-area").value = value || "";
  } else if (type === "hotkey") {
    $("#f-value").value = Array.isArray(value) ? value.join("+") : (value || "");
  } else if (type === "clipboard" && value && value !== "get" && value !== "clear") {
    $("#f-value-area").value = value;
  } else {
    $("#f-value").value = value || "";
  }
}

function openEditor(btn, col, row) {
  $("#modal-overlay").classList.remove("hidden");
  $("#modal-title").textContent = btn ? "Редактировать кнопку" : "Новая кнопка";
  $("#btn-delete").classList.toggle("hidden", !btn);
  $("#f-preset").innerHTML = HOTKEY_PRESETS.map(([v, t]) => `<option value="${v}">${t}</option>`).join("");

  if (btn) {
    $("#f-id").value = btn.id;
    $("#f-label").value = btn.label || "";
    $("#f-icon").value = btn.icon || "";
    $("#f-color").value = btn.color || "#1a1a2e";
    $("#f-col").value = btn.col;
    $("#f-row").value = btn.row;
    const action = btn.action || { type: "none", value: "" };
    $("#f-type").value = action.type || "none";
    updateValueField();
    setValueInForm(action.type, action.value, action);
  } else {
    $("#f-id").value = "";
    $("#f-label").value = "";
    $("#f-icon").value = "⬛";
    $("#f-color").value = "#1a1a2e";
    $("#f-col").value = col;
    $("#f-row").value = row;
    $("#f-type").value = "app";
    updateValueField();
    $("#f-value").value = "";
  }
}

function closeEditor() { $("#modal-overlay").classList.add("hidden"); }
function uid() { return "btn_" + Math.random().toString(36).slice(2, 10); }

async function init() {
  info = await fetch("/api/info").then((r) => r.json());
  if (!info.authRequired) { pin = ""; localStorage.removeItem("deck_pin"); }
  if (info.authRequired && !pin) { showAuth(); return; }
  try {
    config = await api("/api/config");
    showApp();
    applyConfig(config);
    connectWs();
    pollStatus();
    setInterval(pollStatus, 5000);
    startYmPolling();
  } catch { showAuth(); }
}

$("#pin-submit").onclick = async () => {
  const val = $("#pin-input").value.trim();
  try {
    await fetch(`/api/auth?pin=${encodeURIComponent(val)}`).then((r) => { if (!r.ok) throw new Error(); return r.json(); });
    pin = val;
    localStorage.setItem("deck_pin", pin);
    $("#pin-error").classList.add("hidden");
    await init();
  } catch { $("#pin-error").classList.remove("hidden"); }
};
$("#pin-input").onkeydown = (e) => { if (e.key === "Enter") $("#pin-submit").click(); };

$("#btn-edit").onclick = () => {
  editMode = !editMode;
  $("#btn-edit").classList.toggle("active", editMode);
  $("#edit-bar").classList.toggle("hidden", !editMode);
  renderGrid();
};
$("#btn-done").onclick = () => {
  editMode = false;
  $("#btn-edit").classList.remove("active");
  $("#edit-bar").classList.add("hidden");
  renderGrid();
};

$("#btn-add").onclick = () => {
  const page = getActivePage();
  const cols = config.settings.gridCols || 5;
  const rows = config.settings.gridRows || 3;
  const occupied = new Set((page.buttons || []).map((b) => `${b.col},${b.row}`));
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++)
      if (!occupied.has(`${c},${r}`)) { openEditor(null, c, r); return; }
  toast("Сетка заполнена");
};

$("#btn-add-page").onclick = async () => {
  const name = prompt("Название страницы:", "Новая");
  if (!name) return;
  const id = "page_" + Math.random().toString(36).slice(2, 10);
  config.pages.push({ id, name, buttons: [] });
  navigateToPage(id);
  await saveConfig();
};

$("#f-type").onchange = updateValueField;
$("#f-value-select").onchange = () => {
  if ($("#f-type").value === "yandex") updateValueField();
};
$("#f-preset").onchange = () => {
  const v = $("#f-preset").value;
  if (v) $("#f-value").value = v;
};

$("#btn-form").onsubmit = async (e) => {
  e.preventDefault();
  const page = getActivePage();
  const id = $("#f-id").value || uid();
  let value;
  try { value = getValueFromForm(); } catch { toast("Ошибка в значении"); return; }
  const actionType = $("#f-type").value;
  const action = { type: actionType, value };
  if (actionType === "yandex" && $("#f-value-select").value === "search" && $("#f-value").value.trim()) {
    action.value = "search";
    action.query = $("#f-value").value.trim();
  }
  const btn = {
    id, col: +$("#f-col").value, row: +$("#f-row").value,
    label: $("#f-label").value.trim() || "Кнопка",
    icon: $("#f-icon").value.trim() || "⬛",
    color: $("#f-color").value,
    action,
  };
  const existing = page.buttons.findIndex((b) => b.id === id);
  const conflict = page.buttons.findIndex((b) => b.id !== id && b.col === btn.col && b.row === btn.row);
  if (conflict >= 0) page.buttons.splice(conflict, 1);
  if (existing >= 0) page.buttons[existing] = btn; else page.buttons.push(btn);
  closeEditor();
  await saveConfig();
  renderGrid();
};

$("#btn-delete").onclick = async () => {
  const id = $("#f-id").value;
  if (!id || !confirm("Удалить кнопку?")) return;
  getActivePage().buttons = getActivePage().buttons.filter((b) => b.id !== id);
  closeEditor();
  await saveConfig();
  renderGrid();
};
$("#btn-cancel").onclick = closeEditor;

$("#btn-settings").onclick = () => {
  const s = config.settings;
  $("#s-title").value = s.title || "";
  $("#s-cols").value = s.gridCols || 5;
  $("#s-rows").value = s.gridRows || 3;
  $("#s-pin").value = s.pin || "";
  $("#s-obs-pass").value = s.obs?.password || "";
  $("#s-ym-mode").value = s.yandex?.mode || "browser";
  $("#s-browser").value = s.yandex?.browser || "auto";
  const c = s.customize || {};
  $("#s-accent").value = c.accent || "#7c6cf0";
  $("#s-ym-accent").value = c.ymAccent || "#ffcc00";
  $("#s-radius").value = c.btnRadius || 16;
  $("#s-glow").checked = c.glow !== false;
  $("#s-compact").checked = !!c.compact;
  $("#settings-overlay").classList.remove("hidden");
};
$("#s-cancel").onclick = () => $("#settings-overlay").classList.add("hidden");

$("#settings-form").onsubmit = async (e) => {
  e.preventDefault();
  config.settings.title = $("#s-title").value.trim() || "Deck";
  config.settings.gridCols = Math.min(10, Math.max(1, +$("#s-cols").value));
  config.settings.gridRows = Math.min(10, Math.max(1, +$("#s-rows").value));
  const newPin = $("#s-pin").value.trim();
  config.settings.pin = newPin;
  config.settings.obs = {
    host: "localhost", port: 4455,
    password: $("#s-obs-pass").value.trim(),
  };
  config.settings.yandex = {
    mode: $("#s-ym-mode").value || "browser",
    browser: $("#s-browser").value || "auto",
  };
  config.settings.customize = {
    accent: $("#s-accent").value,
    ymAccent: $("#s-ym-accent").value,
    btnRadius: parseInt($("#s-radius").value, 10) || 16,
    glow: $("#s-glow").checked,
    compact: $("#s-compact").checked,
  };
  if (config.settings.yandex.browser !== "auto") {
    // stored server-side via env on next yandex open - pass in settings
  }
  if (newPin !== pin) {
    pin = newPin;
    if (pin) localStorage.setItem("deck_pin", pin); else localStorage.removeItem("deck_pin");
  }
  $("#settings-overlay").classList.add("hidden");
  await saveConfig();
  $("#deck-title").textContent = config.settings.title;
  applyCustomize();
  renderPage();
};

$("#s-export").onclick = () => {
  const blob = new Blob([JSON.stringify(config, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "deck-config.json";
  a.click();
};

$("#s-import").onchange = async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  try {
    config = JSON.parse(await file.text());
    activePageId = config.activePage || config.pages[0]?.id;
    await saveConfig();
    applyConfig(config);
    toast("Импортировано");
  } catch { toast("Ошибка JSON"); }
  e.target.value = "";
};

document.querySelectorAll("[data-ym]").forEach((el) => {
  el.addEventListener("click", () => execYandex(el.dataset.ym));
});

$("#ym-search-btn")?.addEventListener("click", () => {
  const q = $("#ym-search")?.value?.trim();
  if (q) execYandex("search", q);
});
$("#ym-search")?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("#ym-search-btn")?.click();
});

let lastVol = 50;
$("#ym-volume")?.addEventListener("change", (e) => {
  const v = parseInt(e.target.value, 10);
  const steps = Math.abs(v - lastVol);
  const action = v > lastVol ? "volume_up" : "volume_down";
  for (let i = 0; i < Math.min(steps, 15); i++) execYandex(action);
  lastVol = v;
});

init();