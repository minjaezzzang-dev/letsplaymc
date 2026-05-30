import json
import os
import shutil
from pathlib import Path
from urllib.request import Request, urlopen, urlretrieve

from backend.config import settings
from backend.log import logger
from path.path import get_os, get_java_path, get_git_path, UnknownOSError

JDK_URLS = {
    "windowsx64": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.11%2B10/OpenJDK21U-jdk_x64_windows_hotspot_21.0.11_10.zip",
    "windowsarm64": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.11%2B10/OpenJDK21U-jdk_arm64_windows_hotspot_21.0.11_10.zip",
    "linuxx64": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.11%2B10/OpenJDK21U-jdk_x64_linux_hotspot_21.0.11_10.tar.gz",
    "linuxarm64": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.11%2B10/OpenJDK21U-jdk_arm64_linux_hotspot_21.0.11_10.tar.gz",
    "macosarm64": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.11%2B10/OpenJDK21U-jdk_aarch64_macos_hotspot_21.0.11_10.tar.gz",
    "macosx64": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.11%2B10/OpenJDK21U-jdk_x64_macos_hotspot_21.0.11_10.tar.gz",
}


def setup_jdk() -> None:
    java_path = get_java_path()
    if java_path.exists():
        logger.info("Java already installed at %s", java_path)
        return

    os_name = get_os()
    logger.info("Detected OS: %s", os_name)

    if os_name not in JDK_URLS:
        raise UnknownOSError(f"Unsupported OS/Architecture: {os_name}")

    url = JDK_URLS[os_name]
    java_dir = java_path.parent.parent
    data_dir = java_dir.parent
    data_dir.mkdir(parents=True, exist_ok=True)

    ext = ".zip" if os_name.startswith("windows") else ".tar.gz"
    archive_path = data_dir / f"jdk_archive{ext}"

    try:
        logger.info("Downloading JDK 21 from %s", url)
        urlretrieve(url, archive_path)
        logger.info("Download completed")

        extract_temp_dir = data_dir / "java_temp"
        if extract_temp_dir.exists():
            shutil.rmtree(extract_temp_dir, ignore_errors=True)
        extract_temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Extracting JDK archive...")
        shutil.unpack_archive(archive_path, extract_temp_dir)

        extracted_contents = list(extract_temp_dir.iterdir())
        if not extracted_contents:
            raise RuntimeError("Extraction resulted in an empty folder")

        jdk_root = None
        for item in extracted_contents:
            if item.is_dir() and (item / "bin").exists():
                jdk_root = item
                break

        if not jdk_root:
            dirs = [d for d in extracted_contents if d.is_dir()]
            jdk_root = dirs[0] if dirs else extract_temp_dir

        logger.info("Moving JDK to %s", java_dir)
        if java_dir.exists():
            shutil.rmtree(java_dir, ignore_errors=True)
        shutil.move(str(jdk_root), str(java_dir))

        if not os_name.startswith("windows"):
            final_java_bin = java_dir / "bin" / "java"
            if final_java_bin.exists():
                final_java_bin.chmod(0o755)

    finally:
        if archive_path.exists():
            archive_path.unlink()
        temp_dir = data_dir / "java_temp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

    logger.info("JDK 21 setup completed")


def setup_git() -> None:
    git_path = get_git_path()
    if git_path.exists():
        logger.info("Git already installed at %s", git_path)
        return

    os_name = get_os()
    if not os_name.startswith("windows"):
        if shutil.which("git"):
            logger.info("System Git already available")
            return
        raise UnknownOSError("Automatic Git download is only configured for Windows")

    arch = "arm64" if os_name.endswith("arm64") else "64-bit"
    req = Request(
        "https://api.github.com/repos/git-for-windows/git/releases/latest",
        headers={"User-Agent": settings.user_agent},
    )
    with urlopen(req, timeout=settings.request_timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Failed to fetch Git release: {response.status}")
        release = json.loads(response.read().decode("utf-8"))

    asset = next(
        (
            a
            for a in release.get("assets", [])
            if a.get("name", "").startswith("MinGit-")
            and a.get("name", "").endswith(f"{arch}.zip")
            and "busybox" not in a.get("name", "").lower()
        ),
        None,
    )
    if asset is None:
        raise RuntimeError("No matching MinGit zip found in latest release")

    git_dir = git_path.parent.parent
    data_dir = git_dir.parent
    data_dir.mkdir(parents=True, exist_ok=True)
    archive_path = data_dir / "mingit.zip"
    extract_temp_dir = data_dir / "git_temp"

    try:
        logger.info("Downloading Git from %s", asset["browser_download_url"])
        urlretrieve(asset["browser_download_url"], archive_path)

        if extract_temp_dir.exists():
            shutil.rmtree(extract_temp_dir, ignore_errors=True)
        extract_temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Extracting Git archive...")
        shutil.unpack_archive(archive_path, extract_temp_dir)

        if git_dir.exists():
            shutil.rmtree(git_dir, ignore_errors=True)
        shutil.move(str(extract_temp_dir), str(git_dir))
    finally:
        if archive_path.exists():
            archive_path.unlink()
        if extract_temp_dir.exists():
            shutil.rmtree(extract_temp_dir, ignore_errors=True)

    logger.info("Git setup completed")


def setup_all() -> None:
    setup_jdk()
    setup_git()


if __name__ == "__main__":
    setup_all()
