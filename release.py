import os
import json
import shutil
import hashlib
import subprocess
from datetime import datetime
from version import VERSION, get_version_info, validate_version, increment_version, update_version_file

def generate_checksum(file_path):
    """Generate SHA256 checksum for a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def git_command(command):
    """Execute git command and return output"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")
        raise

def update_changelog(version, changes=None):
    """Update CHANGELOG.md with new version"""
    today = datetime.now().strftime('%Y-%m-%d')
    new_version_entry = f"\n## [{version}] - {today}\n\n"
    if changes:
        new_version_entry += changes + "\n"
    
    try:
        with open('CHANGELOG.md', 'r') as f:
            content = f.read()
        
        # Insert after first # Changelog line
        updated_content = content.replace(
            "# Changelog\n",
            f"# Changelog\n{new_version_entry}"
        )
        
        with open('CHANGELOG.md', 'w') as f:
            f.write(updated_content)
    except FileNotFoundError:
        with open('CHANGELOG.md', 'w') as f:
            f.write(f"# Changelog\n{new_version_entry}")

def prompt_version_increment():
    """Prompt user for version increment type"""
    current_version = VERSION
    print(f"\nCurrent version: {current_version}")
    print("Choose version increment:")
    print("[1] Major (X.0.0)")
    print("[2] Minor (0.X.0)")
    print("[3] Patch (0.0.X)")
    print("[4] Manual input")
    
    choice = input("Select option (1-4): ")
    
    if choice == '1':
        new_version = increment_version(current_version, 'major')
    elif choice == '2':
        new_version = increment_version(current_version, 'minor')
    elif choice == '3':
        new_version = increment_version(current_version, 'patch')
    elif choice == '4':
        new_version = input("Enter new version (x.y.z): ")
        validate_version(new_version)
    else:
        raise ValueError("Invalid choice")
    
    return new_version

def compile_to_exe():
    """Compile the application to a portable executable using PyInstaller"""
    try:
        subprocess.run([
            "pyinstaller",
            "--onefile",
            "--noconsole",  # Hide console window
            "--clean",      # Clean PyInstaller cache
            "--name", "Excel to Schemas",  # Set output exe name
            "main.py"
        ], check=True)
        print("Executable compiled successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed: {e}")
        raise

def create_release():
    """Create a new release package with validation, checksums, and executable"""
    # Prompt for version increment
    new_version = prompt_version_increment()
    
    # Get current branch
    current_branch = git_command("git rev-parse --abbrev-ref HEAD")
    
    # Update version and changelog
    update_version_file(new_version)
    update_changelog(new_version)
    
    # Git operations
    git_command("git add version.py CHANGELOG.md")
    git_command(f'git commit -m "chore: release version {new_version}"')
    git_command(f"git tag v{new_version}")
    git_command(f"git push origin {current_branch}")
    git_command(f"git push origin v{new_version}")
    
    # Get updated version info
    version_info = get_version_info()
    version = version_info['version']
    
    # Validate version
    validate_version(version)
    
    # Create release directory
    release_dir = f"dist/excel_to_schemas_v{version}"
    os.makedirs(release_dir, exist_ok=True)
    
    # Required files
    required_files = [
        'main.py',
        'gui.py',
        'database.py',
        'excel.py',
        'validation.py',
        'version.py',
        'requirements.txt'
    ]
    
    # Optional files
    optional_files = [
        'README.md',
        'LICENSE'
    ]
    
    # Validate required files exist
    missing_required = [f for f in required_files if not os.path.exists(f)]
    if missing_required:
        raise FileNotFoundError(f"Missing required files: {', '.join(missing_required)}")
    
    # Collect all available files
    files_to_copy = required_files + [f for f in optional_files if os.path.exists(f)]
    
    # Copy files and generate checksums
    checksums = {}
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, release_dir)
            checksums[file] = generate_checksum(os.path.join(release_dir, file))
    
    # Compile to executable
    compile_to_exe()

    # Move executable to release directory
    exe_path = os.path.join("dist", "main.exe")
    if os.path.exists(exe_path):
        shutil.move(exe_path, release_dir)
        checksums["main.exe"] = generate_checksum(os.path.join(release_dir, "main.exe"))

    # Create release info
    release_info = {
        'version': version,
        'release_date': datetime.now().strftime('%Y-%m-%d'),
        'files': files_to_copy,
        'checksums': checksums
    }
    
    # Save release info
    with open(os.path.join(release_dir, 'release_info.json'), 'w') as f:
        json.dump(release_info, f, indent=4)
    
    # Create artifacts
    artifacts_dir = "dist/artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)
    
    archive_path = shutil.make_archive(
        os.path.join(artifacts_dir, f"excel_to_schemas_v{version}"),
        'zip',
        release_dir
    )
    
    print(f"Release v{version} created successfully!")
    print(f"Archive created at: {archive_path}")
    return archive_path

if __name__ == "__main__":
    create_release()
