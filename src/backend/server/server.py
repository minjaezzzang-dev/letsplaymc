import os
import shutil
import signal
import threading
from collections import deque
from pathlib import Path
from subprocess import PIPE, Popen, STDOUT, run as subprocess_run

from backend.config import settings
from backend.log import logger
from backend.server.rcon import (
    close_rcon,
    extract_inventory,
    get_rcon,
    init_server_rcon,
    parse_player_list,
)
from path.path import get_java_path, get_server_runner_path
from .project import resolve_version, install_server

_running_servers: dict[str, dict] = {}
_console_buffers: dict[str, deque] = {}
_CONSOLE_MAX = 500


def _pipe_output(name: str, process: Popen) -> None:
    buf = _console_buffers.setdefault(name, deque(maxlen=_CONSOLE_MAX))
    for line in iter(process.stdout.readline, b""):
        decoded = line.decode("utf-8", errors="replace").rstrip()
        buf.append(decoded)
        logger.debug("[%s] %s", name, decoded)
    process.stdout.close()


def create_server(name: str, version: str = "latest", project: str = "paper", eula: bool = False, initialize: bool = False) -> None:
    project = project.lower()
    resolved_version = resolve_version(project, version)
    server_dir = settings.server_dir(name)
    if server_dir.exists():
        raise ValueError(f"Server {name} already exists")
    server_dir.mkdir(parents=True)

    cache_key = f"{project}-{resolved_version}"
    runner_cache = get_server_runner_path(cache_key)
    if not runner_cache.exists():
        logger.info("Installing %s %s", project, resolved_version)
        install_server(project, resolved_version)
    else:
        logger.info("Using cached %s", cache_key)

    runner = server_dir / f"{cache_key}.jar"
    shutil.copy(runner_cache, runner)

    if project in {"fabric", "forge", "neoforge", "quilt"}:
        (server_dir / "mods").mkdir(exist_ok=True)
    else:
        (server_dir / "plugins").mkdir(exist_ok=True)

    if eula:
        with open(server_dir / "eula.txt", "w") as f:
            f.write("eula=true")

    if project in {"forge", "neoforge"}:
        process = subprocess_run([str(get_java_path()), "-jar", runner.name, "--installServer"], cwd=server_dir)
        if process.returncode != 0:
            raise RuntimeError(f"Failed to install {project} {version}")

    if not initialize:
        return

    command = [str(get_java_path()), "-jar", runner.name]
    process = Popen(command, cwd=server_dir)
    process.wait()
    process.terminate()
    del process


def _build_java_command(server_dir: Path, min_memory: str, max_memory: str) -> list[str]:
    jars = [j for j in server_dir.glob("*.jar") if "installer" not in j.name.lower()]
    jar = jars[0] if jars else None
    if jar is None:
        raise FileNotFoundError("No server jar found")

    return [
        str(get_java_path()),
        f"-Xms{min_memory}",
        f"-Xmx{max_memory}",
        "-XX:+UseG1GC",
        "-XX:+ParallelRefProcEnabled",
        "-XX:MaxGCPauseMillis=200",
        "-XX:+UnlockExperimentalVMOptions",
        "-XX:+DisableExplicitGC",
        "-XX:+AlwaysPreTouch",
        "-XX:G1NewSizePercent=30",
        "-XX:G1MaxNewSizePercent=40",
        "-XX:G1HeapRegionSize=8M",
        "-XX:G1ReservePercent=20",
        "-XX:G1HeapWastePercent=5",
        "-XX:G1MixedGCCountTarget=4",
        "-XX:G1MixedGCLiveThresholdPercent=90",
        "-XX:G1RSetUpdatingPauseTimePercent=5",
        "-XX:SurvivorRatio=32",
        "-Dusing.aikars.flags=https://mcflags.emc.gs",
        "-Daikars.new.flags=true",
        "-jar",
        jar.name,
        "nogui",
    ]


def run_server(name: str, min_memory: str, max_memory: str) -> Popen:
    if name in _running_servers:
        raise RuntimeError(f"Server {name} is already running")

    server_dir = settings.server_dir(name)
    if not server_dir.is_dir():
        raise FileNotFoundError(f"Server {name} does not exist")

    user_jvm_args = server_dir / "user_jvm_args.txt"
    if user_jvm_args.exists():
        with open(user_jvm_args, "w", encoding="utf-8") as f:
            f.write(f"-Xms{min_memory}\n-Xmx{max_memory}\n")

    run_bat = server_dir / "run.bat"
    if run_bat.exists():
        process = Popen(["cmd", "/c", run_bat.name], cwd=server_dir, stdout=PIPE, stderr=STDOUT)
        _running_servers[name] = {"process": process, "memory": f"{min_memory}/{max_memory}"}
        threading.Thread(target=_pipe_output, args=(name, process), daemon=True).start()
        return process

    run_sh = server_dir / "run.sh"
    if run_sh.exists():
        process = Popen(["sh", run_sh.name], cwd=server_dir, stdout=PIPE, stderr=STDOUT)
        _running_servers[name] = {"process": process, "memory": f"{min_memory}/{max_memory}"}
        threading.Thread(target=_pipe_output, args=(name, process), daemon=True).start()
        return process

    init_server_rcon(name, str(server_dir))

    command = _build_java_command(server_dir, min_memory, max_memory)
    logger.info("Starting server %s", name)
    process = Popen(command, cwd=server_dir, stdout=PIPE, stderr=STDOUT)
    _running_servers[name] = {"process": process, "memory": f"{min_memory}/{max_memory}"}
    threading.Thread(target=_pipe_output, args=(name, process), daemon=True).start()
    return process


def stop_server(name: str) -> None:
    close_rcon(name)
    entry = _running_servers.pop(name, None)
    if entry is None:
        logger.warning("Server %s is not running", name)
        return
    proc = entry["process"]
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM if os.name != "nt" else signal.CTRL_BREAK_EVENT)
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
            proc.wait()
    logger.info("Stopped server %s", name)


def restart_server(name: str, min_memory: str, max_memory: str) -> Popen:
    stop_server(name)
    return run_server(name, min_memory, max_memory)


def delete_server(name: str) -> None:
    stop_server(name)
    server_dir = settings.server_dir(name)
    if server_dir.exists():
        shutil.rmtree(server_dir, ignore_errors=True)
        logger.info("Deleted server %s", name)


def server_status(name: str) -> dict | None:
    server_dir = settings.server_dir(name)
    if not server_dir.is_dir():
        return None

    entry = _running_servers.get(name)
    running = entry is not None and entry["process"].poll() is None
    if entry and not running:
        _running_servers.pop(name, None)

    return {
        "running": running,
        "memory": entry["memory"] if entry else None,
    }


def list_servers() -> list[dict]:
    servers_dir = settings.servers_dir
    servers_dir.mkdir(parents=True, exist_ok=True)
    result = []
    for path in sorted(servers_dir.iterdir()):
        if not path.is_dir():
            continue
        jars = list(path.glob("*.jar"))
        server_type = jars[0].stem.split("-")[0] if jars else ""
        status_data = server_status(path.name)
        result.append({
            "name": path.name,
            "type": server_type,
            "files": len(list(path.iterdir())),
            "running": status_data["running"] if status_data else False,
        })
    return result


def get_console(name: str, tail: int = 50) -> list[str]:
    buf = _console_buffers.get(name, deque())
    return list(buf)[-tail:]


def send_command(name: str, command: str) -> None:
    entry = _running_servers.get(name)
    if entry is None or entry["process"].poll() is not None:
        raise RuntimeError(f"Server {name} is not running")
    stdin = entry["process"].stdin
    if stdin:
        stdin.write(f"{command}\n".encode("utf-8"))
        stdin.flush()
        logger.info("[%s] -> %s", name, command)


def get_online_players(name: str) -> list[dict]:
    rcon = get_rcon(name)
    if rcon is None:
        raise RuntimeError(f"RCON not available for server {name}")
    response = rcon.command("list")
    return parse_player_list(response)


def get_player_entity_data(name: str, player: str) -> str:
    rcon = get_rcon(name)
    if rcon is None:
        raise RuntimeError(f"RCON not available for server {name}")
    response = rcon.command(f"data get entity {player}")
    return response


def get_player_inventory(name: str, player: str) -> list[dict]:
    rcon = get_rcon(name)
    if rcon is None:
        raise RuntimeError(f"RCON not available for server {name}")
    response = rcon.command(f"data get entity {player} Inventory")
    return extract_inventory(response)


def list_addons(name: str) -> list[dict]:
    server_dir = settings.server_dir(name)
    if not server_dir.is_dir():
        raise FileNotFoundError(f"Server {name} does not exist")
    addons: list[dict] = []
    for folder in ("plugins", "mods"):
        dir_path = server_dir / folder
        if dir_path.is_dir():
            for f in sorted(dir_path.iterdir()):
                if f.suffix in (".jar", ".zip", ".disabled"):
                    addons.append({
                        "name": f.name,
                        "folder": folder,
                        "size": f.stat().st_size,
                    })
    return addons


def uninstall_addon(name: str, filename: str) -> None:
    server_dir = settings.server_dir(name)
    if not server_dir.is_dir():
        raise FileNotFoundError(f"Server {name} does not exist")
    for folder in ("plugins", "mods"):
        file_path = server_dir / folder / filename
        if file_path.exists():
            file_path.unlink()
            logger.info("Removed %s from %s", filename, name)
            return
    raise FileNotFoundError(f"Addon {filename} not found on server {name}")



