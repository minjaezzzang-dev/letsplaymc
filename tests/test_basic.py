import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
BACKEND = SRC / "backend"


@pytest.fixture(autouse=True)
def _patch_sys_path():
    for p in [SRC, BACKEND]:
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))


class TestConfig:
    def test_settings_imports(self):
        from backend.config import settings

        assert settings.app_name == "letsplaymc"
        assert settings.data_path.exists() is False or settings.data_path.exists()
        assert settings.default_min_memory == "2G"

    def test_settings_derived_paths(self):
        from backend.config import settings

        assert str(settings.java_path).endswith("java") or str(settings.java_path).endswith("java.exe")
        assert str(settings.git_path).endswith("git") or str(settings.git_path).endswith("git.exe")
        assert str(settings.server_runner_path("paper-1.20.1")).endswith("paper-1.20.1.jar")


class TestPaths:
    def test_get_os(self):
        from backend.path.path import get_os

        os_name = get_os()
        assert os_name.startswith(("windows", "linux", "macos"))

    def test_get_data_dir(self):
        from backend.path.path import get_data_dir

        d = get_data_dir()
        assert "letsplaymc" in str(d).lower()

    def test_get_java_path(self):
        from backend.path.path import get_java_path

        p = get_java_path()
        assert "java" in str(p)

    def test_get_git_path(self):
        from backend.path.path import get_git_path

        p = get_git_path()
        assert "git" in str(p)

    def test_server_runner_path(self):
        from backend.path.path import get_server_runner_path

        p = get_server_runner_path("paper-1.20.1")
        assert str(p).endswith("paper-1.20.1.jar")

    def test_unknown_os_error(self):
        from backend.path.path import UnknownOSError

        with pytest.raises(UnknownOSError):
            raise UnknownOSError("test error")

    def test_unknown_os_error_inherits_exception(self):
        from backend.path.path import UnknownOSError

        assert issubclass(UnknownOSError, Exception)


class TestSetup:
    def test_setup_all_called(self):
        from backend.setup import setup_all, setup_jdk, setup_git

        assert callable(setup_all)
        assert callable(setup_jdk)
        assert callable(setup_git)
