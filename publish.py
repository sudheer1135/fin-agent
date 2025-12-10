import os
import shutil
import subprocess
import sys
import re
from pathlib import Path

def clean_build_artifacts():
    """Clean up build artifacts."""
    print("Cleaning build artifacts...")
    patterns = ["dist", "build", "*.egg-info"]
    for pattern in patterns:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"Removed directory: {path}")
            else:
                os.remove(path)
                print(f"Removed file: {path}")

def increment_version(setup_py_path="setup.py"):
    """Increment the patch version in setup.py."""
    print("Updating version...")
    path = Path(setup_py_path)
    if not path.exists():
        print(f"Error: {setup_py_path} not found.")
        sys.exit(1)
        
    content = path.read_text(encoding="utf-8")
    # Match version="x.y.z"
    pattern = r'version="(\d+)\.(\d+)\.(\d+)"'
    match = re.search(pattern, content)
    
    if not match:
        print("Error: Could not find version string in setup.py (expected format: version=\"x.y.z\")")
        sys.exit(1)
    
    major, minor, patch = map(int, match.groups())
    new_patch = patch + 1
    new_version = f"{major}.{minor}.{new_patch}"
    
    new_content = re.sub(pattern, f'version="{new_version}"', content)
    path.write_text(new_content, encoding="utf-8")
    print(f"Bumped version from {major}.{minor}.{patch} to {new_version}")
    return new_version

def build_package():
    """Build the package."""
    print("Building package...")
    subprocess.check_call([sys.executable, "-m", "build"])

def upload_package(token):
    """Upload the package to PyPI."""
    print("Uploading to PyPI...")
    
    dist_files = [str(f) for f in Path("dist").glob("*")]
    if not dist_files:
        print("No distribution files found!")
        sys.exit(1)
        
    cmd = [
        sys.executable, "-m", "twine", "upload",
        "--username", "__token__",
        "--password", token
    ] + dist_files
    
    subprocess.check_call(cmd)

def main():
    token_file = Path(".pypitoken")
    if not token_file.exists():
        print("Error: .pypitoken file not found.")
        print("Please create a .pypitoken file containing your PyPI token.")
        sys.exit(1)

    token = token_file.read_text().strip()
    if not token:
        print("Error: .pypitoken file is empty.")
        sys.exit(1)

    try:
        clean_build_artifacts()
        increment_version()
        build_package()
        upload_package(token)
        print("\nSuccessfully published to PyPI!")
    except subprocess.CalledProcessError as e:
        print(f"\nError occurred: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
