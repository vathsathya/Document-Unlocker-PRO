import os
import sys
import platform
import subprocess
import shutil

def run_command(command, description):
    print(f"--- {description} ---")
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during {description}: {e}")
        sys.exit(1)

def main():
    current_os = platform.system()
    venv_path = ".venv"
    if current_os == "Windows":
        python_exe = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        python_exe = os.path.join(venv_path, "bin", "python3")

    if os.path.exists(python_exe) and sys.executable != os.path.abspath(python_exe):
        print(f"Switching to Virtual Environment: {python_exe}")
        os.execv(python_exe, [python_exe] + sys.argv)

    print(f"Starting Smart Build for {current_os}...")

    # 1. Install Dependencies
    pip_cmd = sys.executable.replace("python", "pip")
    deps = ["PyQt6", "PyInstaller", "msoffcrypto-tool", "pikepdf", "cryptography", "psutil", "pyopencl", "numba"]
    run_command(f"{pip_cmd} install {' '.join(deps)}", "Updating Dependencies")

    # 2. PyInstaller
    import PyInstaller.__main__
    icon_path = os.path.join("icons", "icons.png")
    args = [
        "main.py",
        "--onefile",
        "--windowed",
        "--add-data=icons/icons.png:icons",
        "--add-data=dictionaries:dictionaries",
        "--add-data=src:src", # Include the modular source
        "--name=DocumentUnlockerPRO",
        "--clean",
    ]
    if os.path.exists(icon_path):
        args.append(f"--icon={icon_path}")

    print(f"--- Launching PyInstaller ---")
    PyInstaller.__main__.run(args)
    print("\nBUILD COMPLETE!")

if __name__ == "__main__":
    main()
