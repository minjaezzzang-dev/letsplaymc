import sys
import threading
from pathlib import Path

try:
    import webview
except ImportError:
    webview = None

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
for p in [str(ROOT), str(BACKEND)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.config import settings
from backend.log import logger
from backend.path.path import get_data_dir
from backend.server.mondrith import download_plugin, search_project
from backend.server.server import (
    create_server,
    delete_server,
    get_console,
    get_online_players,
    get_player_entity_data,
    get_player_inventory,
    list_addons as list_addons_backend,
    list_servers as list_servers_backend,
    restart_server,
    run_server,
    send_command,
    server_status,
    stop_server,
    uninstall_addon as uninstall_addon_backend,
)
from path.path import get_server_runner_path


HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LetsPlayMC</title>
  <style>
    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    :root {
      --bg: #f0ece4;
      --surface: #ffffff;
      --surface-muted: #faf8f5;
      --ink: #1a1a1a;
      --ink-muted: #6b6560;
      --ink-dim: #938d86;
      --border: #e0d9d0;
      --border-focus: #2d7a5e;
      --green: #2a7d60;
      --green-light: #e8f5f0;
      --green-bright: #34a37e;
      --blue: #3366aa;
      --blue-light: #eaf1fa;
      --red: #c44f4f;
      --red-light: #fdf0ef;
      --amber: #b8862d;
      --amber-light: #fdf6e8;
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
      --shadow-md: 0 4px 12px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.04);
      --shadow-lg: 0 12px 40px rgba(0,0,0,0.1);
      --radius: 10px;
      --radius-sm: 6px;
      --radius-full: 9999px;
      --font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Roboto, Arial, sans-serif;
      --sidebar-w: 240px;
      --transition: 200ms cubic-bezier(0.4, 0, 0.2, 1);
    }

    html { height: 100%; }

    body {
      height: 100%;
      color: var(--ink);
      background: var(--bg);
      font-family: var(--font);
      font-size: 14px;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }

    button, input, select {
      font: inherit;
      color: inherit;
    }

    .app {
      height: 100vh;
      display: grid;
      grid-template-columns: var(--sidebar-w) 1fr;
    }

    aside {
      background: #1d211e;
      color: #f0ece1;
      padding: 0;
      display: flex;
      flex-direction: column;
      user-select: none;
    }

    .brand {
      padding: 24px 20px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }

    .mark {
      width: 34px;
      height: 34px;
      border-radius: 8px;
      background: linear-gradient(135deg, #5bbf5a 0%, #6bc9d6 100%);
      box-shadow: 0 2px 8px rgba(91,191,90,0.3);
      flex: 0 0 auto;
    }

    .brand-text {
      display: grid;
      gap: 1px;
    }

    .brand-text h1 {
      font-size: 17px;
      font-weight: 700;
      letter-spacing: -0.01em;
      color: #fff;
    }

    .brand-text span {
      font-size: 11px;
      color: rgba(255,255,255,0.45);
      font-weight: 500;
      letter-spacing: 0.02em;
      text-transform: uppercase;
    }

    .nav {
      padding: 14px 10px;
      display: grid;
      gap: 3px;
      flex: 1;
    }

    .nav button {
      height: 40px;
      border: 0;
      border-radius: 8px;
      background: transparent;
      color: rgba(255,255,255,0.6);
      text-align: left;
      padding: 0 12px;
      cursor: pointer;
      font-size: 13.5px;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 10px;
      transition: all var(--transition);
    }

    .nav button .nav-icon {
      width: 20px;
      height: 20px;
      border-radius: 5px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      flex: 0 0 auto;
      opacity: 0.6;
      transition: opacity var(--transition);
    }

    .nav button:hover {
      background: rgba(255,255,255,0.06);
      color: rgba(255,255,255,0.85);
    }

    .nav button:hover .nav-icon { opacity: 0.85; }

    .nav button.active {
      background: rgba(255,255,255,0.1);
      color: #fff;
    }

    .nav button.active .nav-icon { opacity: 1; }

    .side-foot {
      padding: 16px 20px;
      border-top: 1px solid rgba(255,255,255,0.06);
      color: rgba(255,255,255,0.3);
      font-size: 11px;
      line-height: 1.4;
      overflow-wrap: anywhere;
      word-break: break-all;
    }

    main {
      overflow-y: auto;
      padding: 28px 32px;
      display: grid;
      gap: 20px;
      align-content: start;
    }

    .topbar {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
    }

    .title h2 {
      font-size: 24px;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--ink);
    }

    .title p {
      color: var(--ink-muted);
      font-size: 13.5px;
      margin-top: 2px;
    }

    .actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      flex-shrink: 0;
    }

    .grid-2 {
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 20px;
      align-items: start;
    }

    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow-sm);
      overflow: hidden;
      transition: box-shadow var(--transition);
    }

    .card-header {
      padding: 14px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      border-bottom: 1px solid var(--border);
      background: var(--surface-muted);
    }

    .card-header h3 {
      font-size: 13.5px;
      font-weight: 650;
      color: var(--ink);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      height: 22px;
      border-radius: var(--radius-full);
      padding: 0 9px;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.01em;
      white-space: nowrap;
    }

    .badge-subtle {
      background: #eef0ec;
      color: #3c4238;
    }

    .badge-green {
      background: var(--green-light);
      color: var(--green);
    }

    .badge-blue {
      background: var(--blue-light);
      color: var(--blue);
    }

    .card-body {
      padding: 18px;
      display: grid;
      gap: 14px;
    }

    .field {
      display: grid;
      gap: 5px;
    }

    .field-label {
      font-size: 11.5px;
      font-weight: 600;
      color: var(--ink-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    input, select {
      height: 40px;
      width: 100%;
      border: 1.5px solid var(--border);
      border-radius: var(--radius-sm);
      background: var(--surface);
      padding: 0 12px;
      outline: none;
      transition: border-color var(--transition), box-shadow var(--transition);
      font-size: 13.5px;
    }

    input::placeholder { color: var(--ink-dim); }

    input:focus, select:focus {
      border-color: var(--border-focus);
      box-shadow: 0 0 0 3px rgba(42, 125, 96, 0.12);
    }

    .row-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    .checkbox-line {
      display: flex;
      align-items: center;
      gap: 10px;
      min-height: 34px;
      font-size: 13px;
      font-weight: 500;
    }

    .checkbox-line input[type="checkbox"] {
      width: 17px;
      height: 17px;
      flex: 0 0 auto;
      accent-color: var(--green);
      cursor: pointer;
    }

    .btn {
      height: 38px;
      border: 1.5px solid transparent;
      border-radius: var(--radius-sm);
      padding: 0 16px;
      cursor: pointer;
      font-weight: 600;
      font-size: 13px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      white-space: nowrap;
      transition: all var(--transition);
    }

    .btn:active {
      transform: scale(0.975);
    }

    .btn-primary {
      background: var(--green);
      color: #fff;
      border-color: var(--green);
    }

    .btn-primary:hover {
      background: var(--green-bright);
      border-color: var(--green-bright);
      box-shadow: 0 2px 8px rgba(42, 125, 96, 0.25);
    }

    .btn-secondary {
      background: var(--surface);
      border-color: var(--border);
      color: var(--ink);
    }

    .btn-secondary:hover {
      background: #f5f2ed;
      border-color: #ccc4b8;
    }

    .btn-blue {
      background: var(--blue);
      color: #fff;
      border-color: var(--blue);
    }

    .btn-blue:hover {
      background: #3d77c4;
      border-color: #3d77c4;
      box-shadow: 0 2px 8px rgba(51, 102, 170, 0.25);
    }

    .btn-danger {
      background: var(--red);
      color: #fff;
      border-color: var(--red);
    }

    .btn-danger:hover {
      background: #d65c5c;
      box-shadow: 0 2px 8px rgba(196, 79, 79, 0.25);
    }

    .btn:disabled {
      opacity: 0.45;
      cursor: not-allowed;
      transform: none !important;
    }

    .btn-sm {
      height: 32px;
      padding: 0 11px;
      font-size: 12px;
    }

    .server-list {
      display: grid;
      gap: 8px;
      max-height: 460px;
      overflow-y: auto;
      padding-right: 2px;
    }

    .server-list:empty::after {
      content: "No servers yet. Create one above.";
      display: block;
      color: var(--ink-dim);
      font-size: 13px;
      padding: 16px 0;
      text-align: center;
    }

    .server-item {
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 14px;
      background: var(--surface);
      transition: border-color var(--transition), box-shadow var(--transition);
    }

    .server-item:hover {
      border-color: #ccc4b8;
      box-shadow: var(--shadow-sm);
    }

    .server-info strong {
      display: block;
      font-size: 14px;
      font-weight: 600;
    }

    .server-info span {
      color: var(--ink-muted);
      font-size: 12px;
    }

    .server-actions {
      display: flex;
      gap: 6px;
      flex-shrink: 0;
    }

    .addon-results {
      display: grid;
      gap: 8px;
      max-height: 260px;
      overflow-y: auto;
      padding-right: 2px;
    }

    .addon-results:empty::after {
      content: "No results. Try a different search.";
      display: block;
      color: var(--ink-dim);
      font-size: 13px;
      padding: 16px 0;
      text-align: center;
    }

    .addon-item {
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 10px 12px;
      background: var(--surface);
      display: grid;
      gap: 2px;
    }

    .addon-item strong {
      font-size: 13px;
      font-weight: 600;
    }

    .addon-item .addon-meta {
      font-size: 11.5px;
      color: var(--ink-muted);
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }

    .addon-item p {
      color: var(--ink-muted);
      font-size: 12px;
      line-height: 1.35;
      overflow: hidden;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      margin-top: 2px;
    }

    .installed-addons {
      display: grid;
      gap: 4px;
      max-height: 180px;
      overflow-y: auto;
      padding-right: 2px;
    }

    .installed-addons:empty::after {
      content: "No addons installed.";
      display: block;
      color: var(--ink-dim);
      font-size: 12px;
      padding: 12px 0;
      text-align: center;
    }

    .installed-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 6px 10px;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      font-size: 12.5px;
      background: var(--surface);
    }

    .player-list {
      display: grid;
      gap: 6px;
      max-height: 300px;
      overflow-y: auto;
      padding-right: 2px;
    }

    .player-list:empty::after {
      content: "No players online.";
      display: block;
      color: var(--ink-dim);
      font-size: 13px;
      padding: 16px 0;
      text-align: center;
    }

    .player-item {
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 10px 12px;
      background: var(--surface);
      display: flex;
      align-items: center;
      justify-content: space-between;
      cursor: pointer;
      transition: border-color var(--transition), box-shadow var(--transition);
    }

    .player-item:hover {
      border-color: var(--green);
      box-shadow: 0 0 0 2px rgba(42,125,96,0.1);
    }

    .player-item.active {
      border-color: var(--green);
      background: var(--green-light);
    }

    .player-item .player-name {
      font-weight: 600;
      font-size: 13.5px;
    }

    .player-item .player-actions {
      display: flex;
      gap: 6px;
    }

    .player-data-box {
      background: #1a1d1a;
      color: #d4d0c8;
      font-family: Menlo, Consolas, monospace;
      font-size: 11.5px;
      line-height: 1.5;
      padding: 12px;
      border-radius: var(--radius-sm);
      white-space: pre-wrap;
      word-break: break-all;
      max-height: 240px;
      overflow: auto;
    }

    .inventory-grid {
      display: grid;
      grid-template-columns: repeat(9, 1fr);
      gap: 4px;
    }

    .inv-slot {
      aspect-ratio: 1;
      border: 1px solid var(--border);
      border-radius: 4px;
      background: var(--surface-muted);
      display: grid;
      place-items: center;
      font-size: 10px;
      text-align: center;
      padding: 2px;
      color: var(--ink-muted);
      word-break: break-all;
      line-height: 1.2;
      position: relative;
    }

    .inv-slot.has-item {
      background: var(--surface);
      border-color: var(--green);
      color: var(--ink);
      font-weight: 600;
    }

    .inv-slot .inv-count {
      position: absolute;
      bottom: 1px;
      right: 3px;
      font-size: 9px;
      font-weight: 700;
      color: var(--ink-muted);
    }

    .status-bar {
      min-height: 44px;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 11px 14px;
      background: var(--surface);
      color: var(--ink-muted);
      font-size: 13px;
      display: flex;
      align-items: center;
      gap: 10px;
      overflow-wrap: anywhere;
      word-break: break-word;
      transition: all var(--transition);
    }

    .status-bar .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid var(--border);
      border-top-color: var(--green);
      border-radius: 50%;
      flex: 0 0 auto;
    }

    .status-bar.ok {
      border-color: #c4ddd0;
      background: var(--green-light);
      color: var(--green);
    }

    .status-bar.err {
      border-color: #e5c7c7;
      background: var(--red-light);
      color: var(--red);
    }

    .status-bar.working {
      border-color: #d5cfc3;
      background: #fbfaf7;
      color: var(--ink-muted);
    }

    .setup-grid {
      display: grid;
      grid-template-columns: 1fr 1.2fr;
      gap: 20px;
      align-items: start;
    }

    .setup-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .spinner {
      display: inline-block;
      width: 16px;
      height: 16px;
      border: 2px solid var(--border);
      border-top-color: var(--green);
      border-radius: 50%;
      animation: spin 0.6s linear infinite;
    }

    .status-dot {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex: 0 0 auto;
    }

    .status-dot.running {
      background: #34a37e;
      box-shadow: 0 0 6px rgba(52,163,126,0.5);
    }

    .status-dot.stopped {
      background: #938d86;
    }

    .empty-state {
      display: grid;
      place-items: center;
      padding: 32px 16px;
      text-align: center;
      color: var(--ink-dim);
    }

    .empty-state p { font-size: 13px; }

    ::-webkit-scrollbar {
      width: 6px;
    }

    ::-webkit-scrollbar-track {
      background: transparent;
    }

    ::-webkit-scrollbar-thumb {
      background: #d5cfc5;
      border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
      background: #bdb6aa;
    }

    @media (max-width: 960px) {
      .app { grid-template-columns: 1fr; }
      aside {
        min-height: auto;
        flex-direction: row;
        align-items: center;
        padding: 0 16px;
        gap: 12px;
      }
      .brand { border: 0; padding: 12px 0; }
      .nav {
        flex: 1;
        padding: 0;
        grid-template-columns: repeat(3, 1fr);
      }
      .nav button { justify-content: center; }
      .side-foot { display: none; }
      main { padding: 20px; }
      .grid-2, .setup-grid { grid-template-columns: 1fr; }
      .topbar { flex-direction: column; }
    }

    @media (max-width: 520px) {
      .row-2 { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="brand">
        <div class="mark"></div>
        <div class="brand-text">
          <h1>LetsPlayMC</h1>
          <span>Server Manager</span>
        </div>
      </div>
      <div class="nav">
        <button class="active" data-view="servers">
          <span class="nav-icon">📦</span> Servers
        </button>
        <button data-view="console">
          <span class="nav-icon">💻</span> Console
        </button>
        <button data-view="players">
          <span class="nav-icon">👤</span> Players
        </button>
        <button data-view="addons">
          <span class="nav-icon">🔌</span> Add-ons
        </button>
        <button data-view="setup">
          <span class="nav-icon">⚙️</span> Setup
        </button>
      </div>
      <div class="side-foot" id="dataDir">Loading...</div>
    </aside>

    <main>
      <div class="topbar">
        <div class="title">
          <h2 id="pageTitle">Servers</h2>
          <p id="pageSub">Create, launch, and manage local Minecraft servers.</p>
        </div>
        <div class="actions">
          <button class="btn btn-secondary" onclick="refreshServers()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
            Refresh
          </button>
          <button class="btn btn-primary" onclick="createServer()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Create Server
          </button>
        </div>
      </div>

      <div class="grid-2 view" id="servers">
        <div class="card">
          <div class="card-header">
            <h3>New Server</h3>
            <span class="badge badge-subtle">Local</span>
          </div>
          <div class="card-body">
            <div class="field">
              <span class="field-label">Server Name</span>
              <input id="serverName" placeholder="e.g. survival-world">
            </div>
            <div class="row-2">
              <div class="field">
                <span class="field-label">Type</span>
                <select id="serverType"></select>
              </div>
              <div class="field">
                <span class="field-label">Version</span>
                <input id="serverVersion" value="latest" placeholder="latest">
              </div>
            </div>
            <label class="checkbox-line">
              <input id="serverEula" type="checkbox">
              I accept the <a href="#" onclick="event.preventDefault(); setStatus('Visit https://aka.ms/MinecraftEULA to view the EULA.', 'ok')" style="color:var(--green);text-decoration:underline;">Minecraft EULA</a>
            </label>
            <button class="btn btn-primary" onclick="createServer()" style="width:100%">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              Create Server
            </button>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h3>Server Library</h3>
            <span class="badge badge-subtle" id="serverCount">0</span>
          </div>
          <div class="card-body">
            <div class="row-2">
              <div class="field">
                <span class="field-label">Initial Memory</span>
                <input id="minMem" value="2G" placeholder="2G">
              </div>
              <div class="field">
                <span class="field-label">Max Memory</span>
                <input id="maxMem" value="4G" placeholder="4G">
              </div>
            </div>
            <div class="server-list" id="serverList"></div>
          </div>
        </div>
      </div>

      <div class="grid-2 view" id="players" hidden>
        <div class="card">
          <div class="card-header">
            <h3>Online Players</h3>
            <span class="badge badge-green" id="playerCount">0</span>
          </div>
          <div class="card-body">
            <div class="field">
              <span class="field-label">Server</span>
              <select id="playersServer" onchange="refreshPlayers()"></select>
            </div>
            <div class="player-list" id="playerList"></div>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <h3 id="playerDetailTitle">Player Details</h3>
            <span class="badge badge-subtle" id="playerDetailStatus">Select a player</span>
          </div>
          <div class="card-body">
            <div class="field">
              <span class="field-label">Entity Data</span>
              <div class="player-data-box" id="playerEntityData">Click a player to view their data.</div>
            </div>
            <div class="field">
              <span class="field-label">Inventory</span>
              <div id="playerInventory"><span style="color:var(--ink-dim);font-size:13px">No player selected.</span></div>
            </div>
          </div>
        </div>
      </div>

      <div class="grid-2 view" id="addons" hidden>
        <div class="card">
          <div class="card-header">
            <h3>Install Add-on</h3>
            <span class="badge badge-blue">Modrinth</span>
          </div>
          <div class="card-body">
            <div class="field">
              <span class="field-label">Target Server</span>
              <select id="addonServer" onchange="refreshInstalledAddons()"></select>
            </div>
            <div class="row-2">
              <div class="field">
                <span class="field-label">Loader</span>
                <select id="addonLoader"></select>
              </div>
              <div class="field">
                <span class="field-label">Game Version</span>
                <input id="addonVersion" placeholder="e.g. 1.20.1">
              </div>
            </div>
            <div class="field">
              <span class="field-label">Search Query</span>
              <input id="addonQuery" placeholder="e.g. spark, essentials, ...">
            </div>
            <div style="display:flex;gap:8px">
              <button class="btn btn-secondary" onclick="searchAddons()" style="flex:1">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                Search
              </button>
            </div>
            <hr style="border:none;border-top:1px solid var(--border);margin:4px 0">
            <div class="field" style="margin-top:4px">
              <span class="field-label" style="font-size:11px">Installed</span>
              <div class="installed-addons" id="installedAddons"></div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h3>Results</h3>
            <span class="badge badge-subtle" id="resultCount">0</span>
          </div>
          <div class="card-body">
            <div class="addon-results" id="addonResults"></div>
          </div>
        </div>
      </div>

      <div class="grid-2 view" id="console" hidden>
        <div class="card">
          <div class="card-header">
            <h3>Server Console</h3>
            <span class="badge badge-subtle" id="consoleStatus">Offline</span>
          </div>
          <div class="card-body">
            <div class="field">
              <span class="field-label">Select Server</span>
              <select id="consoleServer" onchange="switchConsoleServer()"></select>
            </div>
            <div style="display:flex;gap:8px;margin-top:4px">
              <button class="btn btn-primary btn-sm" onclick="startConsoleServer()" style="flex:1">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                Start
              </button>
              <button class="btn btn-secondary btn-sm" onclick="stopConsoleServer()" style="flex:1">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
                Stop
              </button>
              <button class="btn btn-secondary btn-sm" onclick="restartConsoleServer()" style="flex:1">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                Restart
              </button>
            </div>
          </div>
        </div>
        <div class="card" style="grid-column:1/-1">
          <div class="card-header">
            <h3>Output</h3>
            <span class="badge badge-subtle" id="consoleLineCount">0 lines</span>
          </div>
          <div class="card-body" style="padding:0">
            <pre id="consoleOutput" style="margin:0;padding:16px;font-family:Menlo,Consolas,monospace;font-size:12px;line-height:1.5;background:#1a1d1a;color:#d4d0c8;overflow:auto;max-height:400px;border-radius:0 0 var(--radius) var(--radius);white-space:pre-wrap;word-break:break-all">Server console output will appear here.</pre>
            <div style="display:flex;border-top:1px solid var(--border);padding:10px 14px;gap:8px;background:var(--surface-muted)">
              <input id="consoleCommand" placeholder="Type a command..." style="flex:1" onkeydown="if(event.key==='Enter')sendConsoleCommand()">
              <button class="btn btn-primary btn-sm" onclick="sendConsoleCommand()" style="flex-shrink:0">Send</button>
              <button class="btn btn-secondary btn-sm" onclick="clearConsole()" style="flex-shrink:0">Clear</button>
            </div>
          </div>
        </div>
      </div>

      <div class="setup-grid view" id="setup" hidden>
        <div class="card">
          <div class="card-header">
            <h3>Runtime</h3>
            <span class="badge badge-subtle">Java + Git</span>
          </div>
          <div class="card-body">
            <p style="color:var(--ink-muted);font-size:13px;line-height:1.5">
              LetsPlayMC needs Java 21 and Git to build and run Minecraft servers. If they aren't found, click below to install them automatically.
            </p>
            <div class="setup-actions">
              <button class="btn btn-primary" onclick="setupRuntime()">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                Install Runtime
              </button>
              <button class="btn btn-secondary" onclick="showPaths()">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                Show Paths
              </button>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h3>Status</h3>
            <span class="badge badge-green">Ready</span>
          </div>
          <div class="card-body">
            <div class="status-bar" id="setupInfo">Runtime status will appear here.</div>
          </div>
        </div>
      </div>

      <div class="status-bar" id="status">Ready.</div>
    </main>
  </div>

  <script>
    const serverTypes = ["paper", "purpur", "folia", "velocity", "waterfall", "bukkit", "spigot", "fabric", "forge", "neoforge", "quilt", "vanilla"];
    const addonLoaders = ["paper", "purpur", "folia", "velocity", "waterfall", "bukkit", "spigot", "fabric", "forge", "neoforge", "quilt"];

    let working = false;
    let consoleTimer = null;
    let pollingConsole = false;

    function fillSelect(id, items) {
      const el = document.getElementById(id);
      el.innerHTML = items.map(i => `<option value="${i}">${i}</option>`).join("");
    }

    function setStatus(message, kind = "") {
      const el = document.getElementById("status");
      el.textContent = message;
      el.className = "status-bar";
      if (kind) el.classList.add(kind);
    }

    function apiCall(method, ...args) {
      if (working) return Promise.resolve(null);
      working = true;
      const statusEl = document.getElementById("status");
      statusEl.className = "status-bar working";
      statusEl.innerHTML = '<span class="spinner"></span> Working...';
      return window.pywebview.api[method](...args).then(result => {
        working = false;
        if (!result.ok) {
          setStatus(result.error || "Something went wrong.", "err");
          return null;
        }
        setStatus(result.message || "Done.", "ok");
        return result.data;
      }).catch(error => {
        working = false;
        setStatus(String(error), "err");
        return null;
      });
    }

    function switchView(view) {
      document.querySelectorAll(".view").forEach(el => el.hidden = el.id !== view);
      document.querySelectorAll(".nav button").forEach(btn => btn.classList.toggle("active", btn.dataset.view === view));
      const titles = {
        servers: ["Servers", "Create, launch, and manage local Minecraft servers."],
        console: ["Console", "View live server output and run commands."],
        players: ["Players", "View online players and inspect their inventory."],
        addons: ["Add-ons", "Search Modrinth and install plugins or mods to your servers."],
        setup: ["Setup", "Install Java 21 and Git for server builds."]
      };
      document.getElementById("pageTitle").textContent = titles[view][0];
      document.getElementById("pageSub").textContent = titles[view][1];

      if (view === "console") {
        populateConsoleServers();
        switchConsoleServer();
      } else if (view === "players") {
        populatePlayerServers();
        refreshPlayers();
      } else if (view === "addons") {
        refreshInstalledAddons();
      } else {
        stopConsolePolling();
      }
    }

    function renderServers(servers) {
      const list = document.getElementById("serverList");
      const addonSelect = document.getElementById("addonServer");
      document.getElementById("serverCount").textContent = servers.length;
      addonSelect.innerHTML = servers.map(s => `<option value="${s.name}">${s.name}</option>`).join("");
      refreshInstalledAddons();
      if (!servers.length) {
        list.innerHTML = "";
        return;
      }

      const mem = {
        min: document.getElementById("minMem").value.trim() || "2G",
        max: document.getElementById("maxMem").value.trim() || "4G"
      };

      list.innerHTML = servers.map(s => {
        const safe = s.name.replaceAll("'", "\\'");
        const statusClass = s.running ? "running" : "stopped";
        const statusLabel = s.running ? "Running" : "Stopped";
        return `
          <div class="server-item">
            <div class="server-info">
              <strong>${escapeHtml(s.name)}</strong>
              <span style="display:flex;align-items:center;gap:6px">
                <span class="status-dot ${statusClass}"></span>
                ${statusLabel} &middot; ${escapeHtml(s.type || "server")} &middot; ${s.files} file${s.files !== 1 ? "s" : ""}
              </span>
            </div>
            <div class="server-actions">
              ${s.running ? `
                <button class="btn btn-secondary btn-sm" onclick="stopServer('${safe}',true)">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
                  Stop
                </button>
              ` : `
                <button class="btn btn-primary btn-sm" onclick="startServer('${safe}')">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                  Start
                </button>
              `}
              <button class="btn btn-secondary btn-sm" onclick="openConsole('${safe}')">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
                Logs
              </button>
              <button class="btn btn-danger btn-sm" onclick="deleteServer('${safe}')" ${s.running ? "disabled" : ""} style="background:transparent;color:var(--red);border-color:var(--red)">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
              </button>
            </div>
          </div>
        `;
      }).join("");
    }

    function escapeHtml(text) {
      const d = document.createElement("div");
      d.textContent = text;
      return d.innerHTML;
    }

    function refreshServers() {
      apiCall("list_servers").then(data => data && renderServers(data.servers));
    }

    function createServer() {
      const payload = {
        name: document.getElementById("serverName").value.trim(),
        project: document.getElementById("serverType").value,
        version: document.getElementById("serverVersion").value.trim() || "latest",
        eula: document.getElementById("serverEula").checked
      };
      apiCall("create_server", payload).then(data => data && refreshServers());
    }

    function startServer(name) {
      apiCall("start_server", {
        name,
        min_memory: document.getElementById("minMem").value.trim() || "2G",
        max_memory: document.getElementById("maxMem").value.trim() || "4G"
      }).then(() => refreshServers());
    }

    function stopServer(name, refresh = true) {
      apiCall("stop_server", {name}).then(() => refresh && refreshServers());
    }

    function deleteServer(name) {
      if (!confirm(`Delete server "${name}"? This cannot be undone.`)) return;
      apiCall("delete_server", {name}).then(() => refreshServers());
    }

    function openConsole(name) {
      switchView("console");
      const sel = document.getElementById("consoleServer");
      for (let i = 0; i < sel.options.length; i++) {
        if (sel.options[i].value === name) {
          sel.selectedIndex = i;
          break;
        }
      }
      switchConsoleServer();
    }

    function populateConsoleServers() {
      apiCall("list_servers").then(data => {
        if (!data) return;
        const sel = document.getElementById("consoleServer");
        sel.innerHTML = data.servers.map(s =>
          `<option value="${s.name}">${s.name}${s.running ? " (Running)" : ""}</option>`
        ).join("");
      });
    }

    function getConsoleServer() {
      return document.getElementById("consoleServer").value;
    }

    function switchConsoleServer() {
      stopConsolePolling();
      const name = getConsoleServer();
      if (!name) {
        document.getElementById("consoleOutput").textContent = "No server selected.";
        document.getElementById("consoleStatus").textContent = "Offline";
        return;
      }
      fetchConsole();
      startConsolePolling();
    }

    function fetchConsole() {
      const name = getConsoleServer();
      if (!name) return;
      pollingConsole = true;
      window.pywebview.api.get_console({name, tail: 100}).then(result => {
        if (!result.ok) return;
        const el = document.getElementById("consoleOutput");
        const lines = result.data.lines || [];
        el.textContent = lines.join("\n") || "[No output yet]";
        el.scrollTop = el.scrollHeight;
        document.getElementById("consoleLineCount").textContent = lines.length + " lines";
      });
      window.pywebview.api.server_status({name}).then(result => {
        if (!result.ok) return;
        const status = result.data.status;
        const badge = document.getElementById("consoleStatus");
        if (status && status.running) {
          badge.textContent = "Running" + (status.memory ? " (" + status.memory + ")" : "");
          badge.className = "badge badge-green";
        } else {
          badge.textContent = "Offline";
          badge.className = "badge badge-subtle";
        }
      });
    }

    function startConsolePolling() {
      stopConsolePolling();
      consoleTimer = setInterval(fetchConsole, 2000);
    }

    function stopConsolePolling() {
      if (consoleTimer) {
        clearInterval(consoleTimer);
        consoleTimer = null;
      }
      pollingConsole = false;
    }

    function startConsoleServer() {
      const name = getConsoleServer();
      if (!name) return;
      apiCall("start_server", {
        name,
        min_memory: document.getElementById("minMem").value.trim() || "2G",
        max_memory: document.getElementById("maxMem").value.trim() || "4G"
      }).then(() => {
        switchConsoleServer();
        populateConsoleServers();
        refreshServers();
      });
    }

    function stopConsoleServer() {
      const name = getConsoleServer();
      if (!name) return;
      apiCall("stop_server", {name}).then(() => {
        switchConsoleServer();
        populateConsoleServers();
        refreshServers();
      });
    }

    function restartConsoleServer() {
      const name = getConsoleServer();
      if (!name) return;
      apiCall("restart_server", {
        name,
        min_memory: document.getElementById("minMem").value.trim() || "2G",
        max_memory: document.getElementById("maxMem").value.trim() || "4G"
      }).then(() => {
        switchConsoleServer();
        populateConsoleServers();
        refreshServers();
      });
    }

    function sendConsoleCommand() {
      const name = getConsoleServer();
      const input = document.getElementById("consoleCommand");
      const cmd = input.value.trim();
      if (!name || !cmd) return;
      input.value = "";
      apiCall("send_command", {name, command: cmd});
    }

    function clearConsole() {
      const el = document.getElementById("consoleOutput");
      el.textContent = "[Console cleared]";
    }

    function populatePlayerServers() {
      apiCall("list_servers").then(data => {
        if (!data) return;
        const sel = document.getElementById("playersServer");
        sel.innerHTML = data.servers.map(s =>
          `<option value="${s.name}">${s.name}${s.running ? " (Running)" : ""}</option>`
        ).join("");
      });
    }

    function refreshPlayers() {
      const name = document.getElementById("playersServer").value;
      if (!name) {
        document.getElementById("playerList").innerHTML = "";
        document.getElementById("playerCount").textContent = "0";
        return;
      }
      window.pywebview.api.get_players({name}).then(result => {
        if (!result.ok) return;
        const players = result.data.players || [];
        document.getElementById("playerCount").textContent = players.length;
        const list = document.getElementById("playerList");
        list.innerHTML = players.map(p =>
          `<div class="player-item" onclick="selectPlayer('${escapeHtml(p.name)}')">
            <span class="player-name">${escapeHtml(p.name)}</span>
            <span class="player-actions">
              <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation();selectPlayer('${escapeHtml(p.name)}')">View</button>
            </span>
          </div>`
        ).join("");
      });
    }

    let selectedPlayer = "";

    function selectPlayer(player) {
      selectedPlayer = player;
      const name = document.getElementById("playersServer").value;
      if (!name || !player) return;

      document.getElementById("playerDetailTitle").textContent = player;
      document.getElementById("playerDetailStatus").textContent = "Loading...";

      window.pywebview.api.get_player_data({name, player}).then(result => {
        const el = document.getElementById("playerEntityData");
        if (result.ok) {
          el.textContent = result.data.data || "(no data)";
        } else {
          el.textContent = "Error: " + (result.error || "failed to fetch");
        }
      });

      window.pywebview.api.get_player_inventory({name, player}).then(result => {
        const container = document.getElementById("playerInventory");
        if (!result.ok) {
          container.innerHTML = '<span style="color:var(--red);font-size:13px">' + escapeHtml(result.error || "failed to fetch inventory") + '</span>';
          return;
        }
        const items = result.data.items || [];
        renderInventory(container, items);
      });

      document.getElementById("playerDetailStatus").textContent = "Online";
    }

    function renderInventory(container, items) {
      if (!items.length) {
        container.innerHTML = '<span style="color:var(--ink-dim);font-size:13px">Empty inventory.</span>';
        return;
      }
      const grid = document.createElement("div");
      grid.className = "inventory-grid";
      for (let i = 0; i < 41; i++) {
        const slot = document.createElement("div");
        slot.className = "inv-slot";
        const item = items.find(it => String(it.Slot) === String(i));
        if (item) {
          slot.classList.add("has-item");
          const short = item.id.replace("minecraft:", "");
          slot.textContent = short;
          const count = document.createElement("span");
          count.className = "inv-count";
          count.textContent = item.Count || "";
          slot.appendChild(count);
        }
        grid.appendChild(slot);
      }
      container.innerHTML = "";
      container.appendChild(grid);
    }

    function searchAddons() {
      const query = document.getElementById("addonQuery").value.trim();
      const loader = document.getElementById("addonLoader").value;
      const version = document.getElementById("addonVersion").value.trim();
      apiCall("search_addons", {query, loader, version}).then(data => {
        if (!data) return;
        document.getElementById("resultCount").textContent = data.results.length;
        const container = document.getElementById("addonResults");
        if (!data.results.length) {
          container.innerHTML = "";
          return;
        }
        const server = document.getElementById("addonServer").value;
        container.innerHTML = data.results.map(item => `
          <div class="addon-item">
            <strong>${escapeHtml(item.title)}</strong>
            ${item.author ? `<div class="addon-meta">
              <span>by ${escapeHtml(item.author)}</span>
              <span>${(item.downloads || 0).toLocaleString()} downloads</span>
              ${item.latest_version ? `<span>${escapeHtml(item.latest_version)}</span>` : ""}
            </div>` : ""}
            ${item.description ? `<p>${escapeHtml(item.description)}</p>` : ""}
            <div style="margin-top:4px">
              <button class="btn btn-primary btn-sm" onclick="installAddonFromResult('${escapeHtml(item.project_id)}')">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                Install
              </button>
            </div>
          </div>
        `).join("");
      });
    }

    function installAddonFromResult(projectId) {
      const server = document.getElementById("addonServer").value;
      if (!server) { setStatus("Select a server first.", "err"); return; }
      const loader = document.getElementById("addonLoader").value;
      const version = document.getElementById("addonVersion").value.trim();
      apiCall("install_addon", {
        server,
        query: projectId,
        loader,
        version: version || undefined
      }).then(() => {
        searchAddons();
        refreshInstalledAddons();
      });
    }

    function refreshInstalledAddons() {
      const name = document.getElementById("addonServer").value;
      if (!name) {
        document.getElementById("installedAddons").innerHTML = "";
        return;
      }
      window.pywebview.api.list_addons({name}).then(result => {
        if (!result.ok) return;
        const addons = result.data.addons || [];
        const container = document.getElementById("installedAddons");
        container.innerHTML = addons.map(a =>
          `<div class="installed-item">
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(a.name)}</span>
            <button class="btn btn-sm" style="background:transparent;color:var(--red);border-color:var(--red);flex-shrink:0;padding:0 8px;height:26px;font-size:11px" onclick="uninstallAddon('${escapeHtml(a.name)}')">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>`
        ).join("");
      });
    }

    function uninstallAddon(filename) {
      const name = document.getElementById("addonServer").value;
      if (!name || !filename) return;
      if (!confirm(`Remove "${filename}" from ${name}?`)) return;
      apiCall("uninstall_addon", {name, filename}).then(() => {
        refreshInstalledAddons();
      });
    }

    function setupRuntime() {
      apiCall("setup_runtime").then(showPaths);
    }

    function showPaths() {
      apiCall("paths").then(data => {
        if (!data) return;
        document.getElementById("setupInfo").textContent = `Data: ${data.data_dir}`;
        document.getElementById("dataDir").textContent = data.data_dir;
      });
    }

    document.querySelectorAll(".nav button").forEach(btn => {
      btn.addEventListener("click", () => switchView(btn.dataset.view));
    });

    fillSelect("serverType", serverTypes);
    fillSelect("addonLoader", addonLoaders);
    refreshServers();
    showPaths();
  </script>
</body>
</html>
"""


class Api:
    def __init__(self) -> None:
        pass

    def ok(self, message: str, data: object = None) -> dict:
        return {"ok": True, "message": message, "data": data or {}}

    def fail(self, error: Exception) -> dict:
        logger.error("API error: %s", error)
        return {"ok": False, "error": str(error), "data": {}}

    def list_servers(self) -> dict:
        try:
            servers = list_servers_backend()
            return self.ok("Servers refreshed.", {"servers": servers})
        except Exception as exc:
            return self.fail(exc)

    def create_server(self, payload: dict) -> dict:
        try:
            name = payload.get("name", "").strip()
            if not name:
                raise ValueError("Server name is required.")
            create_server(
                name,
                payload.get("version") or "latest",
                payload.get("project") or "paper",
                bool(payload.get("eula")),
            )
            return self.ok(f"Created {name}.")
        except Exception as exc:
            return self.fail(exc)

    def start_server(self, payload: dict) -> dict:
        try:
            name = payload.get("name")
            run_server(
                name,
                payload.get("min_memory") or settings.default_min_memory,
                payload.get("max_memory") or settings.default_max_memory,
            )
            return self.ok(f"Started {name}.")
        except Exception as exc:
            return self.fail(exc)

    def stop_server(self, payload: dict) -> dict:
        try:
            stop_server(payload.get("name"))
            return self.ok(f"Stopped {payload.get('name')}.")
        except Exception as exc:
            return self.fail(exc)

    def restart_server(self, payload: dict) -> dict:
        try:
            restart_server(
                payload.get("name"),
                payload.get("min_memory") or settings.default_min_memory,
                payload.get("max_memory") or settings.default_max_memory,
            )
            return self.ok(f"Restarted {payload.get('name')}.")
        except Exception as exc:
            return self.fail(exc)

    def delete_server(self, payload: dict) -> dict:
        try:
            delete_server(payload.get("name"))
            return self.ok(f"Deleted {payload.get('name')}.")
        except Exception as exc:
            return self.fail(exc)

    def server_status(self, payload: dict) -> dict:
        try:
            status = server_status(payload.get("name"))
            return self.ok("Status retrieved.", {"status": status})
        except Exception as exc:
            return self.fail(exc)

    def get_console(self, payload: dict) -> dict:
        try:
            lines = get_console(payload.get("name"), payload.get("tail", 50))
            return self.ok("Console retrieved.", {"lines": lines})
        except Exception as exc:
            return self.fail(exc)

    def send_command(self, payload: dict) -> dict:
        try:
            send_command(payload.get("name"), payload.get("command", ""))
            return self.ok("Command sent.")
        except Exception as exc:
            return self.fail(exc)

    def get_players(self, payload: dict) -> dict:
        try:
            players = get_online_players(payload.get("name", ""))
            return self.ok("Players retrieved.", {"players": players})
        except Exception as exc:
            return self.fail(exc)

    def get_player_data(self, payload: dict) -> dict:
        try:
            data = get_player_entity_data(
                payload.get("name", ""),
                payload.get("player", ""),
            )
            return self.ok("Player data retrieved.", {"data": data})
        except Exception as exc:
            return self.fail(exc)

    def get_player_inventory(self, payload: dict) -> dict:
        try:
            items = get_player_inventory(
                payload.get("name", ""),
                payload.get("player", ""),
            )
            return self.ok("Inventory retrieved.", {"items": items})
        except Exception as exc:
            return self.fail(exc)

    def list_addons(self, payload: dict) -> dict:
        try:
            addons = list_addons_backend(payload.get("name", ""))
            return self.ok("Addons listed.", {"addons": addons})
        except Exception as exc:
            return self.fail(exc)

    def uninstall_addon(self, payload: dict) -> dict:
        try:
            uninstall_addon_backend(
                payload.get("name", ""),
                payload.get("filename", ""),
            )
            return self.ok(f"Removed {payload.get('filename')}.")
        except Exception as exc:
            return self.fail(exc)

    def search_addons(self, payload: dict) -> dict:
        try:
            results = search_project(
                payload.get("query", ""),
                payload.get("loader") or "paper",
                payload.get("version") or None,
                12,
            )
            compact = [
                {
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "project_id": item.get("project_id", ""),
                    "author": item.get("author", ""),
                    "downloads": item.get("downloads", 0),
                    "icon_url": item.get("icon_url", ""),
                    "latest_version": item.get("latest_version", ""),
                }
                for item in results
            ]
            return self.ok("Search complete.", {"results": compact})
        except Exception as exc:
            return self.fail(exc)

    def install_addon(self, payload: dict) -> dict:
        try:
            destination = download_plugin(
                payload.get("server", ""),
                payload.get("query", ""),
                payload.get("loader") or "paper",
                payload.get("version") or None,
            )
            return self.ok(f"Installed {destination.name}.", {"path": str(destination)})
        except Exception as exc:
            return self.fail(exc)

    def setup_runtime(self) -> dict:
        try:
            from backend.setup import setup_all

            thread = threading.Thread(target=setup_all, daemon=True)
            thread.start()
            return self.ok("Runtime setup started.")
        except Exception as exc:
            return self.fail(exc)

    def paths(self) -> dict:
        try:
            return self.ok("Paths loaded.", {"data_dir": str(get_data_dir())})
        except Exception as exc:
            return self.fail(exc)


def main() -> object:
    if webview is None:
        logger.error("pywebview not installed. Run: pip install pywebview")
        return

    window = webview.create_window(
        "LetsPlayMC",
        html=HTML,
        js_api=Api(),
        width=settings.window_width,
        height=settings.window_height,
        min_size=(settings.window_min_width, settings.window_min_height),
    )
    logger.info("Starting LetsPlayMC (%sx%s)", settings.window_width, settings.window_height)
    webview.start(debug=False)
    return window


if __name__ == "__main__":
    main()
