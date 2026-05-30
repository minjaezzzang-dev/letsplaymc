import json
import urllib.parse
import urllib.request
from pathlib import Path

from ..path.path import get_user_data_path


API_URL = "https://api.modrinth.com/v2"
HEADERS = {
    "User-Agent": "letsplaymc-launcher/1.0.0 (contact@letsplaymc.local)",
}
MOD_LOADERS = {"fabric", "forge", "neoforge", "quilt"}
PLUGIN_LOADERS = {"bukkit", "spigot", "paper", "purpur", "folia", "velocity", "waterfall"}


def read_json(url: str):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as response:
        if response.status != 200:
            raise RuntimeError(f"Modrinth request failed: {response.status}")
        return json.loads(response.read().decode("utf-8"))


def download_file(url: str, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as response, destination.open("wb") as file:
        if response.status != 200:
            raise RuntimeError(f"Modrinth download failed: {response.status}")
        while chunk := response.read(1024 * 1024):
            file.write(chunk)


def search_project(query: str, loader: str = "paper", game_version: str | None = None, limit: int = 10):
    facets = [["project_type:mod"], ["server_side!=unsupported"]]
    if loader:
        facets.append([f"categories:{loader}"])
    if game_version:
        facets.append([f"versions:{game_version}"])

    params = urllib.parse.urlencode(
        {
            "query": query,
            "facets": json.dumps(facets),
            "index": "downloads",
            "limit": limit,
        }
    )
    return read_json(f"{API_URL}/search?{params}").get("hits", [])


def get_project_versions(project: str, loader: str = "paper", game_version: str | None = None):
    params = {"include_changelog": "false"}
    if loader:
        params["loaders"] = json.dumps([loader])
    if game_version:
        params["game_versions"] = json.dumps([game_version])

    encoded_project = urllib.parse.quote(project, safe="")
    query = urllib.parse.urlencode(params)
    return read_json(f"{API_URL}/project/{encoded_project}/version?{query}")


def get_install_folder(loader: str):
    loader = loader.lower()
    if loader in MOD_LOADERS:
        return "mods"
    if loader in PLUGIN_LOADERS:
        return "plugins"
    raise ValueError(f"Unsupported loader: {loader}")


def download_plugin(server: str, query: str, loader: str = "paper", game_version: str | None = None):
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

    file = next((file for file in files if file.get("primary")), files[0])
    server_dir = Path(get_user_data_path()) / "servers" / server
    if not server_dir.is_dir():
        raise FileNotFoundError(f"Server {server} does not exist")

    destination = server_dir / get_install_folder(loader) / file["filename"]
    download_file(file["url"], destination)
    return destination
