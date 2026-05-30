from path.path import get_os, get_java_path, get_server_runner_path, UnknownOSError
import os
import shutil
from urllib.request import urlretrieve
from pathlib import Path

def setup_jdk():
    # Verify if Java already exists at the expected path
    java_path = get_java_path()
    if java_path.exists():
        print(f"Java already installed at: {java_path}")
        return

    os_name = get_os()
    print(f"Detected OS: {os_name}")

    urls = {
        "windowsx64": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.11%2B10/OpenJDK21U-jdk_x64_windows_hotspot_21.0.11_10.zip",
        "windowsarm64": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.11%2B10/OpenJDK21U-jdk_arm64_windows_hotspot_21.0.11_10.zip",
        "linuxx64": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.11%2B10/OpenJDK21U-jdk_x64_linux_hotspot_21.0.11_10.tar.gz",
        "linuxarm64": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.11%2B10/OpenJDK21U-jdk_arm64_linux_hotspot_21.0.11_10.tar.gz",
        "macosarm64": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.11%2B10/OpenJDK21U-jdk_aarch64_macos_hotspot_21.0.11_10.tar.gz",
        "macosx64": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.11%2B10/OpenJDK21U-jdk_x64_macos_hotspot_21.0.11_10.tar.gz"
    }

    if os_name not in urls:
        raise UnknownOSError(f"Unsupported or unknown OS/Architecture: {os_name}")

    url = urls[os_name]
    java_dir = java_path.parent.parent
    data_dir = java_dir.parent
    data_dir.mkdir(parents=True, exist_ok=True)

    ext = ".zip" if os_name.startswith("windows") else ".tar.gz"
    archive_path = data_dir / f"jdk_archive{ext}"
    try:
        print(f"Downloading JDK 21 from: {url}")
        print("Please wait, this might take a moment...")
        urlretrieve(url, archive_path)
        print("Download completed.")

        # Create temp folder for extraction
        extract_temp_dir = data_dir / "java_temp"
        if extract_temp_dir.exists():
            shutil.rmtree(extract_temp_dir, ignore_errors=True)
        extract_temp_dir.mkdir(parents=True, exist_ok=True)

        print("Extracting JDK archive...")
        shutil.unpack_archive(archive_path, extract_temp_dir)

        # Locate root folder of the JDK inside extract_temp_dir
        extracted_contents = list(extract_temp_dir.iterdir())
        if not extracted_contents:
            raise RuntimeError("Extraction resulted in an empty folder.")

        jdk_root = None
        for item in extracted_contents:
            if item.is_dir():
                if (item / "bin").exists():
                    jdk_root = item
                    break

        if not jdk_root:
            dirs = [x for x in extracted_contents if x.is_dir()]
            jdk_root = dirs[0] if dirs else extract_temp_dir

        print(f"Moving JDK files to: {java_dir}")
        if java_dir.exists():
            shutil.rmtree(java_dir, ignore_errors=True)
        
        shutil.move(str(jdk_root), str(java_dir))
        print("JDK moved successfully.")

        # If on Unix, ensure the java binary is executable
        if not os_name.startswith("windows"):
            try:
                final_java_bin = java_dir / "bin" / "java"
                if final_java_bin.exists():
                    final_java_bin.chmod(0o755)
                    print("Set executable permission on java binary.")
            except Exception as e:
                print(f"Warning: Could not set executable permission: {e}")

    finally:
        # Clean up temporary archive and folder
        if archive_path.exists():
            archive_path.unlink()
        extract_temp_dir = data_dir / "java_temp"
        if extract_temp_dir.exists():
            shutil.rmtree(extract_temp_dir, ignore_errors=True)

    print("JDK 21 Setup completed successfully!")
setup_jdk()