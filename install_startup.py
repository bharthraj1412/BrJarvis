# install_startup.py
"""
Installs BR JARVIS MK37 into auto-startup on Linux and Windows.
- On Linux: Creates XDG Autostart entry (~/.config/autostart/br-jarvis.desktop)
  and systemd user service (~/.config/systemd/user/br-jarvis.service).
- On Windows: Creates silent VBScript launcher in Windows Startup folder.

Usage:
    python3 install_startup.py            # Install auto-startup
    python3 install_startup.py --remove   # Remove auto-startup
    python3 install_startup.py --status   # Check if installed
"""
import os
import sys
import platform
import subprocess
from pathlib import Path

_OS = platform.system()


def get_project_dir() -> Path:
    return Path(__file__).resolve().parent


def install_linux():
    project_dir = get_project_dir()
    py_exec = sys.executable
    start_py = project_dir / "start.py"

    # 1. Create XDG Autostart entry
    autostart_dir = Path.home() / ".config" / "autostart"
    autostart_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = autostart_dir / "br-jarvis.desktop"

    desktop_content = f"""[Desktop Entry]
Type=Application
Name=BR JARVIS MK37
Comment=BR JARVIS Autonomous AI Engine
Exec={py_exec} {start_py} voice
Path={project_dir}
Terminal=false
Categories=Utility;Automation;
X-GNOME-Autostart-enabled=true
"""
    desktop_file.write_text(desktop_content, encoding="utf-8")

    # 2. Create Systemd user service
    systemd_dir = Path.home() / ".config" / "systemd" / "user"
    systemd_dir.mkdir(parents=True, exist_ok=True)
    service_file = systemd_dir / "br-jarvis.service"

    service_content = f"""[Unit]
Description=BR JARVIS Autonomous AI Core Daemon
After=network.target sound.target

[Service]
Type=simple
WorkingDirectory={project_dir}
ExecStart={py_exec} {start_py} server
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
"""
    service_file.write_text(service_content, encoding="utf-8")

    # Enable systemd user service if systemctl is available
    try:
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
        subprocess.run(["systemctl", "--user", "enable", "br-jarvis.service"], capture_output=True)
    except Exception:
        pass

    print("=" * 55)
    print("  BR — Auto-Startup Installed (Linux)")
    print("=" * 55)
    print(f"  Desktop Autostart : {desktop_file}")
    print(f"  Systemd User Service : {service_file}")
    print(f"  Project Dir         : {project_dir}")
    print()
    print("  BR JARVIS will now start automatically when you log in.")
    print("=" * 55)


def install_windows():
    startup_dir = Path(os.environ.get(
        "APPDATA", Path.home() / "AppData" / "Roaming"
    )) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    project_dir = get_project_dir()
    bat_source = project_dir / "startup.bat"

    vbs_file = startup_dir / "BR.vbs"
    vbs_content = (
        f'Set WShell = CreateObject("WScript.Shell")\n'
        f'WShell.CurrentDirectory = "{project_dir}"\n'
        f'WShell.Run """{bat_source}"" --silent", 0, False\n'
    )

    bat_file = startup_dir / "BR.bat"
    bat_content = (
        f'@echo off\r\n'
        f'start "" /D "{project_dir}" /MIN "{bat_source}" --silent\r\n'
    )

    for legacy in ("JARVIS_MK37.vbs", "JARVIS_MK37.bat"):
        legacy_file = startup_dir / legacy
        if legacy_file.exists():
            legacy_file.unlink()

    vbs_file.write_text(vbs_content, encoding="utf-8")
    bat_file.write_text(bat_content, encoding="utf-8")

    print("=" * 55)
    print("  BR — Auto-Startup Installed (Windows)")
    print("=" * 55)
    print(f"  VBS Launcher: {vbs_file}")
    print(f"  BAT Fallback: {bat_file}")
    print("=" * 55)


def install():
    if _OS == "Linux":
        install_linux()
    else:
        install_windows()


def remove():
    if _OS == "Linux":
        desktop_file = Path.home() / ".config" / "autostart" / "br-jarvis.desktop"
        service_file = Path.home() / ".config" / "systemd" / "user" / "br-jarvis.service"
        if desktop_file.exists():
            desktop_file.unlink()
        if service_file.exists():
            service_file.unlink()
        try:
            subprocess.run(["systemctl", "--user", "disable", "br-jarvis.service"], capture_output=True)
        except Exception:
            pass
        print("[OK] BR Linux auto-startup removed.")
    else:
        startup_dir = Path(os.environ.get(
            "APPDATA", Path.home() / "AppData" / "Roaming"
        )) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        for name in ("BR.vbs", "BR.bat", "JARVIS_MK37.vbs", "JARVIS_MK37.bat"):
            f = startup_dir / name
            if f.exists():
                f.unlink()
        print("[OK] BR Windows auto-startup removed.")


def status():
    print("=" * 50)
    print(f"  BR — Auto-Startup Status ({_OS})")
    print("=" * 50)
    if _OS == "Linux":
        desktop_file = Path.home() / ".config" / "autostart" / "br-jarvis.desktop"
        service_file = Path.home() / ".config" / "systemd" / "user" / "br-jarvis.service"
        print(f"  Desktop entry: {'INSTALLED' if desktop_file.exists() else 'not found'}")
        print(f"  Systemd service: {'INSTALLED' if service_file.exists() else 'not found'}")
    else:
        startup_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        vbs = startup_dir / "BR.vbs"
        print(f"  Windows VBS: {'INSTALLED' if vbs.exists() else 'not found'}")
    print("=" * 50)


if __name__ == "__main__":
    if "--remove" in sys.argv or "--uninstall" in sys.argv:
        remove()
    elif "--status" in sys.argv:
        status()
    else:
        install()
