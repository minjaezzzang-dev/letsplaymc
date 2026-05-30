import os
import platform
from pathlib import Path

from platformdirs import user_config_dir, user_data_dir

from backend.log import logger


class UnknownOSError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def get_config_dir() -> str:
    return user_config_dir("letsplaymc")


def get_data_dir() -> str:
    return user_data_dir("letsplaymc")


def get_os() -> str:
    system = platform.system()
    arch = "arm64" if platform.machine() == "arm64" else "x64"
    if system == "Windows":
        return "windows" + arch
    if system == "Linux":
        return "linux" + arch
    if system == "Darwin":
        return "macos" + arch
    raise UnknownOSError(f"Unknown OS: {system}")


def get_java_path() -> Path:
    stem = "java.exe" if os.name == "nt" else "java"
    return Path(get_data_dir()) / "java" / "bin" / stem


def get_git_path() -> Path:
    stem = "git.exe" if os.name == "nt" else "git"
    return Path(get_data_dir()) / "git" / "cmd" / stem


def get_server_runner_path(runner: str) -> Path:
    return Path(get_data_dir()) / "runners" / f"{runner}.jar"
