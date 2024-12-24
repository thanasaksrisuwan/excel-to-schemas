VERSION = '1.0.0'
RELEASE_DATE = '2024-01-20'
APP_NAME = 'Excel to Schemas'

def get_version_info():
    return {
        'version': VERSION,
        'release_date': RELEASE_DATE,
        'app_name': APP_NAME,
        'description': 'Excel Schema to SQL Database Tool'
    }

def format_version_string():
    return f"{APP_NAME} v{VERSION}"
