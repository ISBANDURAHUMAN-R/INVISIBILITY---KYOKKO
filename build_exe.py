"""
PROJECT KYOKKO
PyInstaller Build Script
Automated compilation into standalone Windows executable (KYOKKO.exe).
"""

import os
import shutil
import subprocess
import sys


def build():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    build_dir = os.path.join(base_dir, "build")

    print("==================================================================")
    print("                 BUILDING STANDALONE KYOKKO.EXE                   ")
    print("==================================================================")

    # Path to python interpreter in venv
    python_exe = sys.executable

    cmd = [
        python_exe,
        "-m",
        "PyInstaller",
        "--name=KYOKKO",
        "--noconfirm",
        "--clean",
        "--windowed", # Suppress console window in production
        f"--add-data={os.path.join(base_dir, 'ui', 'themes', 'style.qss')};ui/themes",
        f"--add-data={os.path.join(base_dir, 'assets')};assets",
        "--collect-data=mediapipe",
        "--collect-binaries=mediapipe",
        "--collect-submodules=mediapipe",
        "--collect-all=pyvirtualcam",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=cv2",
        "--hidden-import=sqlite3",
        "--hidden-import=numpy",
        os.path.join(base_dir, "main.py"),
    ]

    print("Executing PyInstaller command:")
    print(" ".join(cmd))
    print("\nCompiling... This may take 1-2 minutes.")

    result = subprocess.run(cmd, cwd=base_dir)

    if result.returncode == 0:
        exe_path = os.path.join(dist_dir, "KYOKKO", "KYOKKO.exe")
        print("\n==================================================================")
        print("                   BUILD SUCCEEDED SUCCESSFULLY!                  ")
        print(f"Standalone executable located at:\n{exe_path}")
        print("==================================================================")
    else:
        print(f"\n[ERROR] PyInstaller failed with exit code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()
