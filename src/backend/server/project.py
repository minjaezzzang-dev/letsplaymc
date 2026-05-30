import urllib.request
import json
import re
import os
from pathlib import Path
from subprocess import run

from path.path import get_git_path, get_java_path, get_server_runner_path

API_URLS = {
    "bukkit": "https://hub.spigotmc.org/versions/",
    "spigot": "https://hub.spigotmc.org/versions/",
    "paper": "https://fill.papermc.io/v3/projects/paper",
    "velocity": "https://fill.papermc.io/v3/projects/velocity",
    "folia": "https://fill.papermc.io/v3/projects/folia",
    "waterfall": "https://fill.papermc.io/v3/projects/waterfall",
    "purpur": "https://api.purpurmc.org/v2/purpur",
    "vanilla": "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json",
    "fabric": "https://meta.fabricmc.net/v2/versions/game",
    "forge": "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml",
    "neoforge": "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml",
    "quilt": "https://meta.quiltmc.org/v3/versions/game",
}
def get_all_versions(project: str = "paper", stable_only: bool = True) -> list:
    """
    Fetches all available versions for a given project or URL.
    Supports PaperMC projects, Purpur, Mojang Vanilla, NeoForge, and Sponge.
    
    Args:
        project (str): Project identifier in API_URLS (e.g. 'paper', 'sponge') or a custom URL.
        stable_only (bool): If True, filters out non-stable builds (pre-releases, snapshots, etc.).
        
    Returns:
        list: A list of version strings.
    """
    # If project is defined in API_URLS, use it; otherwise assume it's a raw URL
    url = API_URLS.get(project.lower(), project)
    
    # Define headers (User-Agent is required by PaperMC and standard for others)
    headers = {
        "User-Agent": "letsplaymc-launcher/1.0.0 (contact@letsplaymc.local)"
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                print(f"Failed to fetch versions from {url}. Status: {response.status}")
                return []
                
            response_content = response.read()
            all_versions = []

            if "hub.spigotmc.org" in url:
                body = response_content.decode("utf-8", errors="ignore")
                versions = re.findall(r'href="([^"]+)\.json"', body)
                for v in versions:
                    if not re.match(r"^\d+(?:\.\d+)+(?:-(?:pre|rc)\d+)?$", v):
                        continue
                    if stable_only and ("-pre" in v or "-rc" in v):
                        continue
                    all_versions.append(v)

                def version_key(value: str):
                    return [int(part) for part in re.findall(r"\d+", value)]

                return sorted(set(all_versions), key=version_key, reverse=True)
            
            # 1. XML / Maven Metadata (e.g. NeoForge)
            if url.endswith(".xml") or "maven-metadata.xml" in url:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response_content)
                versions_list = [v.text for v in root.findall(".//version")]
                
                # Maven versions are listed oldest to newest. We reverse it for newest first.
                versions_list.reverse()
                
                for v in versions_list:
                    if stable_only and "-" in v and "minecraftforge" not in url:
                        continue
                    all_versions.append(v)
            
            # 2. JSON-based APIs
            else:
                data = json.loads(response_content.decode("utf-8"))
                
                # A. Mojang Vanilla Manifest
                if "mojang.com" in url or "piston-meta" in url:
                    versions_list = data.get("versions", [])
                    for v_info in versions_list:
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

                # C. Purpur API
                elif "purpurmc.org" in url:
                    versions_list = data.get("versions", [])
                    for v in versions_list:
                        if stable_only and "-" in v:
                            continue
                        all_versions.append(v)
                
                # D. PaperMC API (default fallback)
                else:
                    versions_data = data.get("versions", {})
                    for group, group_versions in versions_data.items():
                        if isinstance(group_versions, list):
                            for v in group_versions:
                                if stable_only and "-" in v:
                                    continue
                                all_versions.append(v)
                            
            return all_versions
            
    except Exception as e:
        print(f"Error occurred while retrieving versions: {e}")
        return []

HEADERS = {
    "User-Agent": "letsplaymc-installer/1.0.0 (contact@letsplaymc.local)"
}


def read_json(url: str):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as response:
        if response.status != 200:
            raise RuntimeError(f"Failed to fetch {url}. Status: {response.status}")
        return json.loads(response.read().decode("utf-8"))


def download_file(url: str, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as response, destination.open("wb") as file:
        if response.status != 200:
            raise RuntimeError(f"Failed to download {url}. Status: {response.status}")
        # Keep memory usage low while downloading big server jars.
        while chunk := response.read(1024 * 1024):
            file.write(chunk)


def resolve_version(project: str, version: str) -> str:
    if version != "latest":
        return version
    versions = get_all_versions(project)
    if not versions:
        raise ValueError(f"No versions found for {project}")
    return versions[0]


def papermc_download_url(project: str, version: str) -> str:
    builds = read_json(f"{API_URLS[project]}/versions/{version}/builds")
    if isinstance(builds, dict):
        builds = builds.get("builds", [])

    # Prefer release builds, then fall back to anything downloadable.
    preferred_channels = {"stable", "recommended"}
    for build in builds:
        if str(build.get("channel", "")).lower() in preferred_channels:
            download = build.get("downloads", {}).get("server:default", {})
            if download.get("url"):
                return download["url"]

    for build in builds:
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


def latest_fabric_component(component: str) -> str:
    versions = read_json(f"https://meta.fabricmc.net/v2/versions/{component}")
    for version in versions:
        if version.get("stable", True):
            return version["version"]
    return versions[0]["version"]


def fabric_download_url(version: str) -> str:
    loader_version = latest_fabric_component("loader")
    installer_version = latest_fabric_component("installer")
    return (
        "https://meta.fabricmc.net/v2/versions/loader/"
        f"{version}/{loader_version}/{installer_version}/server/jar"
    )


def latest_quilt_component(component: str) -> str:
    versions = read_json(f"https://meta.quiltmc.org/v3/versions/{component}")
    for version in versions:
        if version.get("stable", True):
            return version["version"]
    return versions[0]["version"]


def quilt_download_url(version: str) -> str:
    loader_version = latest_quilt_component("loader")
    installer_version = latest_quilt_component("installer")
    return (
        "https://meta.quiltmc.org/v3/versions/loader/"
        f"{version}/{loader_version}/{installer_version}/server/jar"
    )


def latest_maven_version(metadata_url: str, minecraft_version: str) -> str:
    import xml.etree.ElementTree as ET

    req = urllib.request.Request(metadata_url, headers=HEADERS)
    with urllib.request.urlopen(req) as response:
        if response.status != 200:
            raise RuntimeError(f"Failed to fetch {metadata_url}. Status: {response.status}")
        root = ET.fromstring(response.read())

    versions = [
        version.text
        for version in root.findall(".//version")
        if version.text and version.text.startswith(f"{minecraft_version}-")
    ]
    if not versions:
        raise ValueError(f"No loader version found for Minecraft {minecraft_version}")
    return versions[-1]


def latest_neoforge_version(minecraft_version: str) -> str:
    import xml.etree.ElementTree as ET

    parts = minecraft_version.split(".")
    if len(parts) < 2 or parts[0] != "1":
        return minecraft_version

    prefix = ".".join(parts[1:]) + "."
    req = urllib.request.Request(API_URLS["neoforge"], headers=HEADERS)
    with urllib.request.urlopen(req) as response:
        if response.status != 200:
            raise RuntimeError(f"Failed to fetch {API_URLS['neoforge']}. Status: {response.status}")
        root = ET.fromstring(response.read())

    versions = [
        version.text
        for version in root.findall(".//version")
        if version.text and version.text.startswith(prefix)
    ]
    if not versions:
        raise ValueError(f"No NeoForge version found for Minecraft {minecraft_version}")
    return versions[-1]


def forge_download_url(version: str) -> str:
    forge_version = version if "-" in version else latest_maven_version(API_URLS["forge"], version)
    return (
        "https://maven.minecraftforge.net/net/minecraftforge/forge/"
        f"{forge_version}/forge-{forge_version}-installer.jar"
    )


def neoforge_download_url(version: str) -> str:
    neoforge_version = latest_neoforge_version(version)
    base_url = API_URLS["neoforge"].removesuffix("/maven-metadata.xml")
    return f"{base_url}/{neoforge_version}/neoforge-{neoforge_version}-installer.jar"


def buildtools_server(project: str, version: str, destination: Path):
    build_dir = destination.parent / "buildtools" / f"{project}-{version}"
    build_dir.mkdir(parents=True, exist_ok=True)

    buildtools = build_dir / "BuildTools.jar"
    if not buildtools.exists():
        download_file(
            "https://hub.spigotmc.org/jenkins/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar",
            buildtools,
        )

    compile_target = "craftbukkit" if project == "bukkit" else "spigot"
    command = [get_java_path(), "-jar", buildtools.name, "--rev", version, "--compile", compile_target]
    env = os.environ.copy()
    git_path = get_git_path()
    if git_path.exists():
        env["PATH"] = f"{git_path.parent}{os.pathsep}{env.get('PATH', '')}"

    process = run(command, cwd=build_dir, env=env)
    if process.returncode != 0:
        raise RuntimeError(f"BuildTools failed for {project} {version}")

    prefix = "craftbukkit" if project == "bukkit" else "spigot"
    jars = sorted(build_dir.glob(f"{prefix}-*.jar"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not jars:
        raise FileNotFoundError(f"BuildTools did not create a {project} jar")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(jars[0].read_bytes())
    return destination


def install_server(project: str, version: str):
    project = project.lower()
    requested_version = version
    version = resolve_version(project, version)
    destination = get_server_runner_path(f"{project}-{requested_version}")

    if project in {"bukkit", "spigot"}:
        return buildtools_server(project, version, destination)

    match project:
        case "paper" | "velocity" | "folia" | "waterfall":
            download_url = papermc_download_url(project, version)
        case "purpur":
            download_url = f"{API_URLS['purpur']}/{version}/latest/download"
        case "vanilla":
            download_url = vanilla_download_url(version)
        case "fabric":
            download_url = fabric_download_url(version)
        case "quilt":
            download_url = quilt_download_url(version)
        case "forge":
            download_url = forge_download_url(version)
        case "neoforge":
            download_url = neoforge_download_url(version)
        case _:   
            raise ValueError(f"Unknown project: {project}")

    download_file(download_url, destination)
    return destination
