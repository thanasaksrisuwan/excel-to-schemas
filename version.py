import re
from datetime import datetime

VERSION = '1.0.2'
RELEASE_DATE = datetime.now().strftime('%Y-%m-%d')
APP_NAME = 'Excel to Schemas'

def validate_version(version_str):
    pattern = r'^\d+\.\d+\.\d+$'
    if not re.match(pattern, version_str):
        raise ValueError(f"Invalid version format: {version_str}")
    return True

def increment_version(current_version, increment_type='patch'):
    major, minor, patch = map(int, current_version.split('.'))
    if increment_type == 'major':
        return f"{major + 1}.0.0"
    elif increment_type == 'minor':
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"

def get_version_info():
    return {
        'version': VERSION,
        'release_date': RELEASE_DATE,
        'app_name': APP_NAME,
        'description': 'Excel Schema to SQL Database Tool'
    }

def format_version_string():
    return f"{APP_NAME} v{VERSION}"

def update_version_file(new_version):
    """Update VERSION in this file"""
    with open(__file__, 'r') as f:
        content = f.read()
    
    # Update version
    new_content = re.sub(
        r"VERSION = '[0-9]+\.[0-9]+\.[0-9]+'",
        f"VERSION = '{new_version}'",
        content
    )
    
    # Update release date
    new_content = re.sub(
        r"RELEASE_DATE = '[0-9]{4}-[0-9]{2}-[0-9]{2}'",
        f"RELEASE_DATE = '{datetime.now().strftime('%Y-%m-%d')}'",
        new_content
    )
    
    with open(__file__, 'w') as f:
        f.write(new_content)
