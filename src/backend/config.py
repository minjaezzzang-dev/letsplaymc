import os
from dataclasses import dataclass, field
from pathlib import Path

from platformdirs import user_data_dir


@dataclass(frozen=True)
class Settings:
    app_name: str = "letsplaymc"
    data_dir: str = field(default_factory=lambda: user_data_dir("letsplaymc"))
    log_level: str = field(default_factory=lambda: os.getenv("LETSPLAYMC_LOG_LEVEL", "INFO").upper())
    request_timeout: int = field(default_factory=lambda: int(os.getenv("LETSPLAYMC_REQUEST_TIMEOUT", "30")))
    user_agent: str = "letsplaymc/0.1.0 (contact@letsplaymc.local)"
    default_min_memory: str = "2G"
    default_max_memory: str = "4G"
    server_types: tuple = field(default_factory=lambda: (
        "paper", "purpur", "folia", "velocity", "waterfall",
        "bukkit", "spigot", "fabric", "forge", "neoforge", "quilt", "vanilla",
    ))
    addon_loaders: tuple = field(default_factory=lambda: (
        "paper", "purpur", "folia", "velocity", "waterfall",
        "bukkit", "spigot", "fabric", "forge", "neoforge", "quilt",
    ))
    window_width: int = 1120
    window_height: int = 760
    window_min_width: int = 860
    window_min_height: int = 620

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir)

    @property
    def servers_dir(self) -> Path:
        return self.data_path / "servers"

    @property
    def runners_dir(self) -> Path:
        return self.data_path / "runners"

    @property
    def java_dir(self) -> Path:
        return self.data_path / "java"

    @property
    def git_dir(self) -> Path:
        return self.data_path / "git"

    @property
    def java_path(self) -> Path:
        stem = "java.exe" if os.name == "nt" else "java"
        return self.java_dir / "bin" / stem

    @property
    def git_path(self) -> Path:
        stem = "git.exe" if os.name == "nt" else "git"
        return self.git_dir / "cmd" / stem

    def server_runner_path(self, runner: str) -> Path:
        return self.runners_dir / f"{runner}.jar"

    def server_dir(self, name: str) -> Path:
        return self.servers_dir / name


settings = Settings()
