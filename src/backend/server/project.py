import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from subprocess import run as subprocess_run
from typing import Any
from urllib.request import Request, urlopen

from backend.config import settings
from backend.log import logger
from path.path import get_git_path, get_java_path, get_server_runner_path

API_URLS: dict[str, str] = {
    "bukkit": "https://hub.spigotmc.org/versions/",
    "spigot": "https://hub.spigotmc.org/versions/",
    "paper": "https://api.papermc.io/v2/projects/paper",
    "velocity": "https://api.papermc.io/v2/projects/velocity",
    "folia": "https://api.papermc.io/v2/projects/folia",
    "waterfall": "https://api.papermc.io/v2/projects/waterfall",
    "purpur": "https://api.purpurmc.org/v2/purpur",
    "vanilla": "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json",
    "fabric": "https://meta.fabricmc.net/v2/versions/game",
    "forge": "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml",
    "neoforge": "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml",
    "quilt": "https://meta.quiltmc.org/v3/versions/game",
}

HEADERS: dict[str, str] = {
    "User-Agent": settings.user_agent,
}


def _request(url: str) -> Any:
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=settings.request_timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Request to {url} failed with status {response.status}")
        return response.read()


def read_json(url: str) -> Any:
    raw = _request(url)
    return json.loads(raw.decode("utf-8"))


def download_file(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=settings.request_timeout) as response, destination.open("wb") as f:
        if response.status != 200:
            raise RuntimeError(f"Download from {url} failed with status {response.status}")
        while chunk := response.read(1024 * 1024):
            f.write(chunk)
    logger.info("Downloaded %s (%s)", destination.name, url)
    return destination


def get_all_versions(project: str = "paper", stable_only: bool = True) -> list[str]:
    url = API_URLS.get(project.lower(), project)
    logger.debug("Fetching versions from %s", url)

    try:
        raw = _request(url)
        all_versions: list[str] = []

        if "hub.spigotmc.org" in url:
            body = raw.decode("utf-8", errors="ignore")
            versions = re.findall(r'href="([^"]+)\.json"', body)
            for v in versions:
                if not re.match(r"^\d+(?:\.\d+)+(?:-(?:pre|rc)\d+)?$", v):
                    continue
                if stable_only and ("-pre" in v or "-rc" in v):
                    continue
                all_versions.append(v)

            def version_key(value: str) -> list[int]:
                return [int(part) for part in re.findall(r"\d+", value)]

            return sorted(set(all_versions), key=version_key, reverse=True)

        if url.endswith(".xml") or "maven-metadata.xml" in url:
            root = ET.fromstring(raw)
            versions_list = [v.text for v in root.findall(".//version") if v.text]
            versions_list.reverse()
            for v in versions_list:
                if stable_only and "-" in v and "minecraftforge" not in url:
                    continue
                all_versions.append(v)
            return all_versions

        data = json.loads(raw.decode("utf-8"))

        if "mojang.com" in url or "piston-meta" in url:
            for v_info in data.get("versions", []):
                v_id = v_info.get("id")
                v_type = v_info.get("type")
                if v_id:
                    if stable_only and v_type != "release":
                        continue
                    all_versions.append(v_id)

        elif "meta.fabricmc.net" in url or "meta.quiltmc.org" in url:
            for v_info in data:
                v_id = v_info.get("version")
                if v_id:
                    if stable_only and not v_info.get("stable", False):
                        continue
                    all_versions.append(v_id)

        elif "purpurmc.org" in url:
            for v in data.get("versions", []):
                if stable_only and "-" in v:
                    continue
                all_versions.append(v)

        else:
            versions_data = data.get("versions", [])
            if isinstance(versions_data, list):
                for v in versions_data:
                    if isinstance(v, str):
                        if stable_only and "-" in v:
                            continue
                        all_versions.append(v)

        return all_versions

    except Exception as exc:
        logger.warning("Failed to fetch versions from %s: %s", url, exc)
        return []


def resolve_version(project: str, version: str) -> str:
    if version != "latest":
        return version
    versions = get_all_versions(project)
    if not versions:
        raise ValueError(f"No versions found for {project}")
    resolved = versions[0]
    logger.info("Resolved latest %s -> %s", project, resolved)
    return resolved


def papermc_download_url(project: str, version: str) -> str:
    builds = read_json(f"{API_URLS[project]}/versions/{version}/builds")
    if isinstance(builds, dict):
        builds_list = builds.get("builds", [])
    else:
        builds_list = builds

    preferred_channels = {"stable", "recommended"}
    for build in builds_list:
        if str(build.get("channel", "")).lower() in preferred_channels:
            download = build.get("downloads", {}).get("server:default", {})
            if download.get("url"):
                logger.debug("Found stable build for %s %s", project, version)
                return download["url"]

    for build in builds_list:
        download = build.get("downloads", {}).get("server:default", {})
        if download.get("url"):
            return download["url"]

    raise ValueError(f"No downloadable build found for {project} {version}")


def vanilla_download_url(version: str) -> str:
    manifest = read_json(API_URLS["vanilla"])
    for version_info in manifest.get("versions", []):
        if version_info.get("id") == version:
            data = read_json(version_info["url"])
            return data["downloads"]["server"]["url"]
    raise ValueError(f"Unknown vanilla version: {version}")


def _latest_component(base_url: str, component: str) -> str:
    versions = read_json(f"{base_url}/versions/{component}")
    for v in versions:
        if v.get("stable", True):
            return v["version"]
    return versions[0]["version"]


def fabric_download_url(version: str) -> str:
    loader_version = _latest_component("https://meta.fabricmc.net/v2", "loader")
    installer_version = _latest_component("https://meta.fabricmc.net/v2", "installer")
    return (
        f"https://meta.fabricmc.net/v2/versions/loader/"
        f"{version}/{loader_version}/{installer_version}/server/jar"
    )


def quilt_download_url(version: str) -> str:
    loader_version = _latest_component("https://meta.quiltmc.org/v3", "loader")
    installer_version = _latest_component("https://meta.quiltmc.org/v3", "installer")
    return (
        f"https://meta.quiltmc.org/v3/versions/loader/"
        f"{version}/{loader_version}/{installer_version}/server/jar"
    )


def latest_maven_version(metadata_url: str, minecraft_version: str) -> str:
    raw = _request(metadata_url)
    root = ET.fromstring(raw)
    versions = [
        v.text
        for v in root.findall(".//version")
        if v.text and v.text.startswith(f"{minecraft_version}-")
    ]
    if not versions:
        raise ValueError(f"No loader version found for Minecraft {minecraft_version}")
    return versions[-1]


def latest_neoforge_version(minecraft_version: str) -> str:
    parts = minecraft_version.split(".")
    if len(parts) < 2 or parts[0] != "1":
        return minecraft_version

    prefix = ".".join(parts[1:]) + "."
    raw = _request(API_URLS["neoforge"])
    root = ET.fromstring(raw)
    versions = [
        v.text
        for v in root.findall(".//version")
        if v.text and v.text.startswith(prefix)
    ]
    if not versions:
        raise ValueError(f"No NeoForge version found for Minecraft {minecraft_version}")
    return versions[-1]


def forge_download_url(version: str) -> str:
    forge_version = version if "-" in version else latest_maven_version(API_URLS["forge"], version)
    return f"https://maven.minecraftforge.net/net/minecraftforge/forge/{forge_version}/forge-{forge_version}-installer.jar"


def neoforge_download_url(version: str) -> str:
    neoforge_version = latest_neoforge_version(version)
    base_url = API_URLS["neoforge"].removesuffix("/maven-metadata.xml")
    return f"{base_url}/{neoforge_version}/neoforge-{neoforge_version}-installer.jar"


def buildtools_server(project: str, version: str, destination: Path) -> Path:
    build_dir = destination.parent / "buildtools" / f"{project}-{version}"
    build_dir.mkdir(parents=True, exist_ok=True)

    buildtools = build_dir / "BuildTools.jar"
    if not buildtools.exists():
        download_file(
            "https://hub.spigotmc.org/jenkins/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar",
            buildtools,
        )

    compile_target = "craftbukkit" if project == "bukkit" else "spigot"
    command = [str(get_java_path()), "-jar", buildtools.name, "--rev", version, "--compile", compile_target]
    env = os.environ.copy()
    git_path = get_git_path()
    if git_path.exists():
        env["PATH"] = f"{git_path.parent}{os.pathsep}{env.get('PATH', '')}"

    logger.info("Running BuildTools for %s %s", project, version)
    process = subprocess_run(command, cwd=build_dir, env=env)
    if process.returncode != 0:
        raise RuntimeError(f"BuildTools failed for {project} {version}")

    prefix = "craftbukkit" if project == "bukkit" else "spigot"
    jars = sorted(build_dir.glob(f"{prefix}-*.jar"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not jars:
        raise FileNotFoundError(f"BuildTools did not create a {project} jar")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(jars[0].read_bytes())
    logger.info("Built %s %s -> %s", project, version, destination)
    return destination


def install_server(project: str, version: str) -> Path:
    project = project.lower()
    requested_version = version
    version = resolve_version(project, version)
    destination = get_server_runner_path(f"{project}-{requested_version}")

    if project in {"bukkit", "spigot"}:
        return buildtools_server(project, version, destination)

    if project in {"paper", "velocity", "folia", "waterfall"}:
        download_url = papermc_download_url(project, version)
    elif project == "purpur":
        download_url = f"{API_URLS['purpur']}/{version}/latest/download"
    elif project == "vanilla":
        download_url = vanilla_download_url(version)
    elif project == "fabric":
        download_url = fabric_download_url(version)
    elif project == "quilt":
        download_url = quilt_download_url(version)
    elif project == "forge":
        download_url = forge_download_url(version)
    elif project == "neoforge":
        download_url = neoforge_download_url(version)
    else:
        raise ValueError(f"Unknown project: {project}")

    logger.info("Installing %s %s", project, version)
    download_file(download_url, destination)
    return destination
