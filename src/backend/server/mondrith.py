import json
import urllib.parse
import urllib.request
from pathlib import Path

from backend.config import settings
from backend.log import logger
from path.path import get_data_dir

API_URL = "https://api.modrinth.com/v2"

MOD_LOADERS = {"fabric", "forge", "neoforge", "quilt"}
PLUGIN_LOADERS = {"bukkit", "spigot", "paper", "purpur", "folia", "velocity", "waterfall"}


def _request(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": settings.user_agent})
    with urllib.request.urlopen(req, timeout=settings.request_timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Modrinth request failed: {response.status}")
        return json.loads(response.read().decode("utf-8"))


def search_project(query: str, loader: str = "paper", game_version=None, limit: int = 10):
    facets = [["project_type:mod"], ["server_side!=unsupported"]]
    if loader:
        facets.append([f"categories:{loader}"])
    if game_version:
        facets.append([f"versions:{game_version}"])

    params = urllib.parse.urlencode({
        "query": query,
        "facets": json.dumps(facets),
        "index": "downloads",
        "limit": limit,
    })
    logger.debug("Searching Modrinth: %s", query)
    return _request(f"{API_URL}/search?{params}").get("hits", [])


def get_project_versions(project: str, loader: str = "paper", game_version=None):
    params = {"include_changelog": "false"}
    if loader:
        params["loaders"] = json.dumps([loader])
    if game_version:
        params["game_versions"] = json.dumps([game_version])

    encoded_project = urllib.parse.quote(project, safe="")
    query = urllib.parse.urlencode(params)
    return _request(f"{API_URL}/project/{encoded_project}/version?{query}")


def get_install_folder(loader: str) -> str:
    loader = loader.lower()
    if loader in MOD_LOADERS:
        return "mods"
    if loader in PLUGIN_LOADERS:
        return "plugins"
    raise ValueError(f"Unsupported loader: {loader}")


def download_plugin(server: str, query: str, loader: str = "paper", game_version=None) -> Path:
    loader = loader.lower()
    projects = search_project(query, loader, game_version, 1)
    if not projects:
        raise ValueError(f"No Modrinth project found for {query}")

    project = projects[0]
    versions = get_project_versions(project["project_id"], loader, game_version)
    if not versions:
        raise ValueError(f"No compatible version found for {project['title']}")

    files = versions[0].get("files", [])
    if not files:
        raise ValueError(f"No downloadable files found for {project['title']}")

    file = next((f for f in files if f.get("primary")), files[0])
    server_dir = settings.server_dir(server)
    if not server_dir.is_dir():
        raise FileNotFoundError(f"Server {server} does not exist")

    destination = server_dir / get_install_folder(loader) / file["filename"]
    destination.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading %s -> %s", file["url"], destination)
    req = urllib.request.Request(file["url"], headers={"User-Agent": settings.user_agent})
    with urllib.request.urlopen(req, timeout=settings.request_timeout) as resp, destination.open("wb") as f:
        if resp.status != 200:
            raise RuntimeError(f"Modrinth download failed: {resp.status}")
        while chunk := resp.read(1024 * 1024):
            f.write(chunk)

    logger.info("Installed %s on %s", file["filename"], server)
    return destination
