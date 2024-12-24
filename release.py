import os
import json
import shutil
from datetime import datetime
from version import VERSION, get_version_info

def create_release():
    """Create a new release package"""
    # Get version info
    version_info = get_version_info()
    version = version_info['version']
    
    # Create release directory
    release_dir = f"dist/excel_to_schemas_v{version}"
    os.makedirs(release_dir, exist_ok=True)
    
    # Files to include in release
    files_to_copy = [
        'main.py',
        'gui.py',
        'database.py',
        'excel.py',
        'validation.py',
        'version.py',
        'requirements.txt',
        'README.md',
        'LICENSE'
    ]
    
    # Copy files
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, release_dir)
    
    # Create release info file
    release_info = {
        'version': version,
        'release_date': datetime.now().strftime('%Y-%m-%d'),
        'files': files_to_copy
    }
    
    with open(os.path.join(release_dir, 'release_info.json'), 'w') as f:
        json.dump(release_info, f, indent=4)
    
    # Create release artifacts directory
    artifacts_dir = "dist/artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)
    
    # Create ZIP archive with specific naming for GitHub release
    zip_name = f"excel_to_schemas_v{version}"
    archive_path = shutil.make_archive(
        os.path.join(artifacts_dir, zip_name),
        'zip',
        release_dir
    )
    
    print(f"Release v{version} created successfully!")
    print(f"Archive created at: {archive_path}")
    return archive_path

if __name__ == "__main__":
    create_release()
