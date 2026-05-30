# pyrefly: ignore [missing-import]
import platform
# pyrefly: ignore [missing-import]
from platformdirs import user_config_dir, user_data_dir, user_cache_dir
from pathlib import Path

class UnknownOSError(BaseException):
    def __init__(self, message:str):
        self.message = message
    def __str__(self):
        return self.message

def get_config_dir():
    return user_config_dir("letsplaymc")


def get_data_dir():
    return user_data_dir("letsplaymc")

def get_os():
    match platform.system():
        case "Windows":
            return "windows" + ("arm64" if platform.machine() == "arm64" else "x64")
        case "Linux":
            return "linux" + ("arm64" if platform.machine() == "arm64" else "x64")
        case "Darwin":
            return "macos" + ("arm64" if platform.machine() == "arm64" else "x64") 
        case _:
            raise UnknownOSError(f"Unknown OS: {platform.system()}")

def get_java_path():
    return Path(get_data_dir()) / "java" / "bin" / ("java.exe" if get_os().startswith("windows") else "java")
def get_git_path():
    return Path(get_data_dir()) / "git" / "cmd" / ("git.exe" if get_os().startswith("windows") else "git")
def get_server_runner_path(runner: str):
    return Path(get_data_dir()) / "runners" / f"{runner}.jar"
