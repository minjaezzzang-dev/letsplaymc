from pathlib import Path
import sys
import threading

try:
    import webview
except ImportError:
    webview = None

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from backend.path.path import get_data_dir
from backend.server.mondrith import download_plugin, search_project
from backend.server.project import get_all_versions
from backend.server.server import create_server, run_server


HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LetsPlayMC</title>
  <style>
    :root {
      --bg: #f7f4ee;
      --panel: #ffffff;
      --ink: #171717;
      --muted: #66615a;
      --line: #ded8ce;
      --green: #24745a;
      --green-2: #dff3ea;
      --blue: #2f5f98;
      --amber: #b56d1b;
      --red: #aa3f3f;
      --shadow: 0 16px 45px rgba(42, 35, 26, 0.12);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background: var(--bg);
      font-family: Inter, Segoe UI, Arial, sans-serif;
      letter-spacing: 0;
    }

    button, input, select {
      font: inherit;
    }

    .app {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 248px 1fr;
    }

    aside {
      background: #20231f;
      color: #f8f5ed;
      padding: 24px 18px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      min-height: 48px;
    }

    .mark {
      width: 38px;
      height: 38px;
      border-radius: 8px;
      background:
        linear-gradient(90deg, transparent 47%, rgba(255,255,255,.18) 48% 52%, transparent 53%),
        linear-gradient(0deg, #6dbb66 0 52%, #7cc7d8 53% 100%);
      border: 2px solid rgba(255,255,255,.2);
      flex: 0 0 auto;
    }

    h1 {
      margin: 0;
      font-size: 20px;
      line-height: 1.1;
      font-weight: 760;
    }

    .nav {
      display: grid;
      gap: 8px;
    }

    .nav button {
      width: 100%;
      height: 42px;
      border: 0;
      border-radius: 8px;
      color: #ede8dc;
      background: transparent;
      text-align: left;
      padding: 0 12px;
      cursor: pointer;
    }

    .nav button.active {
      background: #eff4e7;
      color: #1f251c;
    }

    .side-foot {
      margin-top: auto;
      color: #bdb7aa;
      font-size: 12px;
      line-height: 1.5;
      overflow-wrap: anywhere;
    }

    main {
      padding: 28px;
      display: grid;
      gap: 18px;
      align-content: start;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      min-height: 48px;
    }

    .title {
      display: grid;
      gap: 3px;
    }

    .title h2 {
      margin: 0;
      font-size: 26px;
      line-height: 1.15;
    }

    .title span {
      color: var(--muted);
      font-size: 13px;
    }

    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .grid {
      display: grid;
      grid-template-columns: minmax(320px, 420px) minmax(360px, 1fr);
      gap: 18px;
      align-items: start;
    }

    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .section-head {
      height: 52px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 0 18px;
      border-bottom: 1px solid var(--line);
      background: #fbfaf6;
    }

    .section-head h3 {
      margin: 0;
      font-size: 15px;
    }

    .body {
      padding: 18px;
      display: grid;
      gap: 14px;
    }

    label {
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 650;
    }

    input, select {
      height: 40px;
      width: 100%;
      border: 1px solid #cfc8bc;
      border-radius: 7px;
      background: #fff;
      color: var(--ink);
      padding: 0 11px;
      outline: none;
    }

    input:focus, select:focus {
      border-color: var(--green);
      box-shadow: 0 0 0 3px var(--green-2);
    }

    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    .checkline {
      display: flex;
      align-items: center;
      gap: 9px;
      color: var(--ink);
      font-size: 13px;
      font-weight: 650;
      min-height: 30px;
    }

    .checkline input {
      width: 16px;
      height: 16px;
      flex: 0 0 auto;
    }

    .btn {
      height: 40px;
      border: 1px solid transparent;
      border-radius: 8px;
      padding: 0 14px;
      cursor: pointer;
      font-weight: 720;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      white-space: nowrap;
    }

    .btn.primary {
      background: var(--green);
      color: #fff;
    }

    .btn.secondary {
      background: #fff;
      border-color: #cfc8bc;
      color: var(--ink);
    }

    .btn.blue {
      background: var(--blue);
      color: #fff;
    }

    .btn:disabled {
      opacity: .56;
      cursor: default;
    }

    .server-list {
      display: grid;
      gap: 8px;
      max-height: 470px;
      overflow: auto;
    }

    .server {
      min-height: 58px;
      border: 1px solid var(--line);
      border-radius: 8px;
      display: grid;
      grid-template-columns: 1fr auto;
      align-items: center;
      gap: 12px;
      padding: 10px 12px;
      background: #fff;
    }

    .server strong {
      display: block;
      font-size: 14px;
      overflow-wrap: anywhere;
    }

    .server small {
      color: var(--muted);
      font-size: 12px;
    }

    .pill {
      height: 24px;
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 0 9px;
      background: #eef0ea;
      color: #3c4238;
      font-size: 12px;
      font-weight: 700;
    }

    .results {
      display: grid;
      gap: 8px;
      max-height: 310px;
      overflow: auto;
    }

    .result {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 11px 12px;
      background: #fff;
      display: grid;
      gap: 4px;
    }

    .result strong {
      font-size: 14px;
    }

    .result span {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }

    .status {
      min-height: 42px;
      border: 1px solid #d7d0c3;
      border-radius: 8px;
      padding: 11px 12px;
      background: #fffdf7;
      color: var(--muted);
      font-size: 13px;
      overflow-wrap: anywhere;
    }

    .status.ok {
      border-color: #b9d8c9;
      background: #f1fbf5;
      color: var(--green);
    }

    .status.err {
      border-color: #e0b7b7;
      background: #fff5f4;
      color: var(--red);
    }

    @media (max-width: 900px) {
      .app { grid-template-columns: 1fr; }
      aside {
        min-height: auto;
        padding: 16px;
      }
      .nav {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }
      .side-foot { display: none; }
      main { padding: 18px; }
      .topbar { align-items: stretch; flex-direction: column; }
      .actions { justify-content: stretch; }
      .actions .btn { flex: 1 1 auto; }
      .grid { grid-template-columns: 1fr; }
    }

    @media (max-width: 560px) {
      .row { grid-template-columns: 1fr; }
      .nav { grid-template-columns: 1fr; }
      .title h2 { font-size: 22px; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="brand">
        <div class="mark"></div>
        <h1>LetsPlayMC</h1>
      </div>
      <div class="nav">
        <button class="active" data-view="servers">Servers</button>
        <button data-view="addons">Add-ons</button>
        <button data-view="setup">Setup</button>
      </div>
      <div class="side-foot" id="dataDir">Loading...</div>
    </aside>

    <main>
      <div class="topbar">
        <div class="title">
          <h2 id="pageTitle">Servers</h2>
          <span id="pageSub">Create, launch, and tune local Minecraft servers.</span>
        </div>
        <div class="actions">
          <button class="btn secondary" onclick="refreshServers()">Refresh</button>
          <button class="btn primary" onclick="createServer()">Create Server</button>
        </div>
      </div>

      <div class="grid view" id="servers">
        <section>
          <div class="section-head"><h3>New Server</h3><span class="pill">Local</span></div>
          <div class="body">
            <label>Name<input id="serverName" placeholder="survival"></label>
            <div class="row">
              <label>Type<select id="serverType"></select></label>
              <label>Version<input id="serverVersion" value="latest"></label>
            </div>
            <label class="checkline"><input id="serverEula" type="checkbox"> Accept EULA</label>
            <button class="btn primary" onclick="createServer()">Create Server</button>
          </div>
        </section>

        <section>
          <div class="section-head"><h3>Server Library</h3><span class="pill" id="serverCount">0</span></div>
          <div class="body">
            <div class="row">
              <label>Initial Memory<input id="minMem" value="2G"></label>
              <label>Maximum Memory<input id="maxMem" value="4G"></label>
            </div>
            <div class="server-list" id="serverList"></div>
          </div>
        </section>
      </div>

      <div class="grid view" id="addons" hidden>
        <section>
          <div class="section-head"><h3>Install Add-on</h3><span class="pill">Modrinth</span></div>
          <div class="body">
            <label>Server<select id="addonServer"></select></label>
            <div class="row">
              <label>Loader<select id="addonLoader"></select></label>
              <label>Game Version<input id="addonVersion" placeholder="1.20.1"></label>
            </div>
            <label>Search<input id="addonQuery" placeholder="spark"></label>
            <div class="actions">
              <button class="btn secondary" onclick="searchAddons()">Search</button>
              <button class="btn blue" onclick="installAddon()">Install</button>
            </div>
          </div>
        </section>

        <section>
          <div class="section-head"><h3>Results</h3><span class="pill" id="resultCount">0</span></div>
          <div class="body">
            <div class="results" id="addonResults"></div>
          </div>
        </section>
      </div>

      <div class="grid view" id="setup" hidden>
        <section>
          <div class="section-head"><h3>Runtime</h3><span class="pill">Java + Git</span></div>
          <div class="body">
            <button class="btn primary" onclick="setupRuntime()">Install Runtime</button>
            <button class="btn secondary" onclick="showPaths()">Show Paths</button>
          </div>
        </section>

        <section>
          <div class="section-head"><h3>Status</h3><span class="pill">Ready</span></div>
          <div class="body">
            <div class="status" id="setupInfo">Runtime status will appear here.</div>
          </div>
        </section>
      </div>

      <div class="status" id="status">Ready.</div>
    </main>
  </div>

  <script>
    const serverTypes = ["paper", "purpur", "folia", "velocity", "waterfall", "bukkit", "spigot", "fabric", "forge", "neoforge", "quilt", "vanilla"];
    const addonLoaders = ["paper", "purpur", "folia", "velocity", "waterfall", "bukkit", "spigot", "fabric", "forge", "neoforge", "quilt"];

    function fillSelect(id, items) {
      const el = document.getElementById(id);
      el.innerHTML = items.map(item => `<option value="${item}">${item}</option>`).join("");
    }

    function setStatus(message, kind = "") {
      const el = document.getElementById("status");
      el.textContent = message;
      el.className = `status ${kind}`;
    }

    function apiCall(method, ...args) {
      setStatus("Working...");
      return window.pywebview.api[method](...args).then(result => {
        if (!result.ok) {
          setStatus(result.error || "Failed.", "err");
          return null;
        }
        setStatus(result.message || "Done.", "ok");
        return result.data;
      }).catch(error => {
        setStatus(String(error), "err");
        return null;
      });
    }

    function switchView(view) {
      document.querySelectorAll(".view").forEach(el => el.hidden = el.id !== view);
      document.querySelectorAll(".nav button").forEach(btn => btn.classList.toggle("active", btn.dataset.view === view));
      const titles = {
        servers: ["Servers", "Create, launch, and tune local Minecraft servers."],
        addons: ["Add-ons", "Search Modrinth and install files to the right folder."],
        setup: ["Setup", "Install Java and Git for server builds."]
      };
      document.getElementById("pageTitle").textContent = titles[view][0];
      document.getElementById("pageSub").textContent = titles[view][1];
    }

    function renderServers(servers) {
      const list = document.getElementById("serverList");
      const addonServer = document.getElementById("addonServer");
      document.getElementById("serverCount").textContent = servers.length;
      addonServer.innerHTML = servers.map(s => `<option value="${s.name}">${s.name}</option>`).join("");
      if (!servers.length) {
        list.innerHTML = `<div class="status">No servers yet.</div>`;
        return;
      }
      list.innerHTML = servers.map(s => `
        <div class="server">
          <div><strong>${s.name}</strong><small>${s.type || "server"} · ${s.files} files</small></div>
          <button class="btn primary" onclick="startServer('${s.name.replaceAll("'", "\\'")}')">Start</button>
        </div>
      `).join("");
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
      });
    }

    function searchAddons() {
      const query = document.getElementById("addonQuery").value.trim();
      const loader = document.getElementById("addonLoader").value;
      const version = document.getElementById("addonVersion").value.trim();
      apiCall("search_addons", {query, loader, version}).then(data => {
        if (!data) return;
        document.getElementById("resultCount").textContent = data.results.length;
        document.getElementById("addonResults").innerHTML = data.results.map(item => `
          <div class="result"><strong>${item.title}</strong><span>${item.description || ""}</span></div>
        `).join("") || `<div class="status">No results.</div>`;
      });
    }

    function installAddon() {
      const payload = {
        server: document.getElementById("addonServer").value,
        query: document.getElementById("addonQuery").value.trim(),
        loader: document.getElementById("addonLoader").value,
        version: document.getElementById("addonVersion").value.trim()
      };
      apiCall("install_addon", payload);
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
    def __init__(self):
        self.processes = {}

    def ok(self, message, data=None):
        return {"ok": True, "message": message, "data": data or {}}

    def fail(self, error):
        return {"ok": False, "error": str(error), "data": {}}

    def list_servers(self):
        try:
            base = Path(get_data_dir()) / "servers"
            base.mkdir(parents=True, exist_ok=True)
            servers = []
            for path in sorted(base.iterdir()):
                if not path.is_dir():
                    continue
                jars = list(path.glob("*.jar"))
                server_type = jars[0].stem.split("-")[0] if jars else ""
                servers.append({"name": path.name, "type": server_type, "files": len(list(path.iterdir()))})
            return self.ok("Servers refreshed.", {"servers": servers})
        except Exception as exc:
            return self.fail(exc)

    def create_server(self, payload):
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

    def start_server(self, payload):
        try:
            name = payload.get("name")
            process = run_server(name, payload.get("min_memory") or "2G", payload.get("max_memory") or "4G")
            self.processes[name] = process
            return self.ok(f"Started {name}.")
        except Exception as exc:
            return self.fail(exc)

    def search_addons(self, payload):
        try:
            results = search_project(
                payload.get("query", ""),
                payload.get("loader") or "paper",
                payload.get("version") or None,
                12,
            )
            compact = [
                {"title": item.get("title", ""), "description": item.get("description", "")}
                for item in results
            ]
            return self.ok("Search complete.", {"results": compact})
        except Exception as exc:
            return self.fail(exc)

    def install_addon(self, payload):
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

    def setup_runtime(self):
        try:
            from backend.setup import setup_all

            thread = threading.Thread(target=setup_all, daemon=True)
            thread.start()
            return self.ok("Runtime setup started.")
        except Exception as exc:
            return self.fail(exc)

    def paths(self):
        try:
            return self.ok("Paths loaded.", {"data_dir": str(get_data_dir())})
        except Exception as exc:
            return self.fail(exc)


def main():
    if webview is None:
        print("pywebview is not installed. Run: pip install pywebview")
        return

    window = webview.create_window("LetsPlayMC", html=HTML, js_api=Api(), width=1120, height=760, min_size=(860, 620))
    webview.start(debug=False)
    return window


if __name__ == "__main__":
    main()
