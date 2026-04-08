"""
Hospital Management - Django launcher
=====================================
Script de khoi chay web app Django thuan.
"""

import subprocess
import sys
import webbrowser


def print_banner():
    print(
        """
Hospital Management System
==========================
Khoi chay Django web app tai http://127.0.0.1:8000
"""
    )


def check_dependencies():
    required = ["django", "widget_tweaks", "rest_framework"]
    missing = []

    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"Thieu packages: {', '.join(missing)}")
        print("Cai dat bang: pip install -r requirements.txt")
        return False

    return True


def run_migrations():
    try:
        subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    print_banner()

    if not check_dependencies():
        sys.exit(1)

    if not run_migrations():
        print("Chay migrate that bai.")
        sys.exit(1)

    webbrowser.open("http://127.0.0.1:8000/")
    subprocess.run([sys.executable, "manage.py", "runserver", "127.0.0.1:8000"])


if __name__ == "__main__":
    main()
