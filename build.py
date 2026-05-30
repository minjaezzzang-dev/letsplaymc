# LetsPlayMC Nuitka build script
#
# Usage:
#   python build.py          # production build
#   python build.py --debug  # debug build with console

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT = ROOT / "dist"

MACOS_ICON = ROOT / "assets" / "icon.icns"
WINDOWS_ICON = ROOT / "assets" / "icon.ico"


def build(debug: bool = False) -> None:
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--enable-plugin=tk-inter",
        "--include-package=backend",
        "--include-module=webview",
        "--include-module=platformdirs",
        "--output-dir=str(OUT)",
        "--clean-cache=all",
        "--remove-output",
    ]

    if debug:
        cmd.append("--debug")
        cmd.append("--console")
    else:
        cmd.append("--disable-console")
        cmd.append("--windows-uac-admin")

    icon = MACOS_ICON if sys.platform == "darwin" else WINDOWS_ICON
    if icon.exists():
        cmd.append(f"--icon={icon}")

    cmd.append(str(SRC / "main.py"))

    print(f"[build] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        sys.exit(result.returncode)
    print(f"[build] Done — binary in {OUT}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build LetsPlayMC with Nuitka")
    parser.add_argument("--debug", action="store_true", help="Debug build with console window")
    args = parser.parse_args()
    build(debug=args.debug)


if __name__ == "__main__":
    main()
