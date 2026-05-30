from os import name
from path.path import get_java_path
from ..path.path import get_user_data_path, get_server_runner_path
from .project import get_all_versions, install_server, get_server_runner_path
from pathlib import Path
import os
import shutil
from subprocess import Popen, run


def create_server(name: str, version: str = "latest", project: str = "paper", eula: bool = False):
    project = project.lower()
    dir = Path(get_user_data_path()) / "servers" / name
    if os.path.exists(dir):
        raise ValueError(f"Server {name} already exists")
    dir.mkdir(parents=True)
    if not os.path.exists(get_server_runner_path(f"{project}-{version}")):
        print(f"Installing {project}-{version}")
        install_server(project, version)
    else:
        print(f"Using cached {project}-{version}")
    runner = dir / f"{project}-{version}.jar"
    shutil.copy(get_server_runner_path(f"{project}-{version}"), runner)
    if project in {"fabric", "forge", "neoforge", "quilt"}:
        (dir / "mods").mkdir(exist_ok=True)
    else:
        (dir / "plugins").mkdir(exist_ok=True)
    if eula:
        with open(dir / "eula.txt", "w") as f:
            f.write("eula=true")

    if project in {"forge", "neoforge"}:
        process = run([get_java_path(), "-jar", runner.name, "--installServer"], cwd=dir)
        if process.returncode != 0:
            raise RuntimeError(f"Failed to install {project} {version}")
        return

    command = [get_java_path(), "-jar", runner.name]
    process = Popen(command, cwd=dir)
    process.wait()
    process.terminate()
    del process


def run_server(name: str, alwaysmemory, maxmemory):
    dir = Path(get_user_data_path()) / "servers" / name
    if not dir.is_dir():
        raise FileNotFoundError(f"Server {name} does not exist")

    user_jvm_args = dir / "user_jvm_args.txt"
    if user_jvm_args.exists():
        user_jvm_args.write_text(f"-Xms{alwaysmemory}\n-Xmx{maxmemory}\n", encoding="utf-8")

    run_bat = dir / "run.bat"
    if run_bat.exists():
        return Popen(["cmd", "/c", run_bat.name], cwd=dir)

    run_sh = dir / "run.sh"
    if run_sh.exists():
        return Popen(["sh", run_sh.name], cwd=dir)

    jars = [jar for jar in dir.glob("*.jar") if "installer" not in jar.name.lower()]
    jar = jars[0] if jars else None
    if jar is None:
        raise FileNotFoundError(f"No server jar found for {name}")

    command = [
        get_java_path(),
        f"-Xms{alwaysmemory}",
        f"-Xmx{maxmemory}",
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
    return Popen(command, cwd=dir)

def edit_properties(name: str, key: str, value: str):
    dir = Path(get_user_data_path()) / "servers" / name
    body = open(dir / "server.properties", "r").read().splitlines()
    new_body = []
    for line in body:
        if line.split("=")[0] == key:
            new_body.append(f"{key}={value}")
        else:
            new_body.append(line)
    open(dir / "server.properties", "w").write("\n".join(new_body))
 
