#!/usr/bin/env python3
"""
Cross-platform virtual environment setup script.
Works on Windows, macOS, and Linux.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print status."""
    print(f"\n{'=' * 60}")
    print(f"[*] {description}")
    print(f"{'=' * 60}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True)
        if result.returncode == 0:
            print(f"✓ {description} - OK")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} - FAILED")
        print(f"Error: {e}")
        return 1


def main():
    """Setup virtual environment and install requirements."""
    
    print("\n" + "=" * 60)
    print("Virtual Environment Setup")
    print(f"Platform: {platform.system()}")
    print("=" * 60)
    
    venv_dir = Path("venv")
    is_windows = sys.platform == "win32"
    
    # Step 1: Create venv
    print(f"\n[*] Creating virtual environment at '{venv_dir}'...")
    if run_command(f"{sys.executable} -m venv venv", "Create virtual environment") != 0:
        print("✗ Failed to create virtual environment")
        sys.exit(1)
    
    # Step 2: Get pip executable path
    if is_windows:
        pip_exe = venv_dir / "Scripts" / "pip.exe"
        activate_script = venv_dir / "Scripts" / "activate.bat"
        activate_cmd = str(activate_script)
    else:
        pip_exe = venv_dir / "bin" / "pip"
        activate_script = venv_dir / "bin" / "activate"
        activate_cmd = f"source {activate_script}"
    
    # Step 3: Upgrade pip
    print(f"\n[*] Upgrading pip...")
    pip_cmd = f"{pip_exe} install --upgrade pip"
    if run_command(pip_cmd, "Upgrade pip") != 0:
        print("✗ Failed to upgrade pip")
        sys.exit(1)
    
    # Step 4: Install requirements
    if Path("requirements.txt").exists():
        print(f"\n[*] Installing requirements from requirements.txt...")
        req_cmd = f"{pip_exe} install -r requirements.txt"
        if run_command(req_cmd, "Install requirements") != 0:
            print("✗ Failed to install requirements")
            sys.exit(1)
    else:
        print("\n[!] requirements.txt not found - skipping")
    
    # Step 5: Print success message
    print("\n" + "=" * 60)
    print("✓ Setup complete!")
    print("=" * 60)
    print(f"\nTo activate the virtual environment, run:")
    
    if is_windows:
        print(f"  .\\venv\\Scripts\\activate")
    else:
        print(f"  source venv/bin/activate")
    
    print(f"\nTo deactivate, run:")
    print(f"  deactivate")
    print()


if __name__ == "__main__":
    main()
