import os
import logging
import json
import pandas as pd
from database import connect_to_database, create_sql_table
from excel import read_excel_file
from validation import validate_and_clean_data, map_data_types

def load_config():
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
            return config
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in configuration file: {e}")
        raise
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        raise

def process_sheet(config):
    """Process sheet and return dictionary with processed data"""
    df_dict = read_excel_file(config['file_path'])
    if not df_dict:
        raise ValueError("No valid sheets found in Excel file")

    selected_sheet = config.get('selected_sheet')
    if not selected_sheet or selected_sheet not in df_dict:
        selected_sheet = list(df_dict.keys())[0]
        logging.info(f"Using first available sheet: {selected_sheet}")

    df = df_dict[selected_sheet]
    if df is None or df.empty:
        raise ValueError(f"No valid data found in sheet: {selected_sheet}")

    df = validate_and_clean_data(df)
    if df is None or df.empty:
        raise ValueError("Data validation failed")

    schema = map_data_types(df)
    if not schema:
        raise ValueError("Failed to map data types")

    # Get table info
    from validation import get_table_info
    table_info = get_table_info(df)
    if not table_info:
        raise ValueError("Failed to get table information")

    # Use table name from table_info
    table_name = table_info['name']
    if not table_name:
        table_name = selected_sheet.replace(' ', '_')

    return {
        'df': df,
        'schema': schema,
        'table_info': table_info,
        'table_name': table_name
    }

def main(progress_callback=None):
    try:
        config = load_config()
        validate_config(config)

        # Configure logging with a more robust configuration
        logging.basicConfig(
            level=getattr(logging, config.get('log_level', 'INFO')),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('app.log'),
                logging.StreamHandler()
            ]
        )

        if not config['file_path']:
            logging.error("No Excel file path specified")
            return

        logging.info("Starting the Excel to Schemas project")

        if config.get('export_type') == 'script':
            # Generate SQL script
            from database import generate_sql_script
            result = process_sheet(config)
            sql_script = generate_sql_script(
                result['table_name'],
                result['schema'],
                result['table_info'],
                result['df']
            )
            return {'sql_script': sql_script}
        else:
            # Create table in database
            connection = connect_to_database(config['database'])
            if not connection:
                raise ConnectionError("Failed to connect to database")

            result = process_sheet(config)
            create_sql_table(connection, result['table_name'], result['schema'], result['table_info'])

    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logging.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logging.error(f"Application error: {e}")
        raise

def validate_config(config):
    required_fields = ['database', 'file_path', 'batch_size', 'timeout', 'retry_attempts', 'log_level']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required configuration field: {field}")
    
    # Only validate file path if it's not empty
    if config['file_path']:
        if not os.path.exists(config['file_path']):  # Removed extra parenthesis
            raise ValueError(f"Excel file not found: {config['file_path']}")
    else:
        logging.warning("No Excel file path specified in configuration")

if __name__ == "__main__":
    # Launch GUI if running directly
    try:
        from gui import ExcelToSchemasGUI
        import tkinter as tk
        root = tk.Tk()
        app = ExcelToSchemasGUI(root)
        root.mainloop()
    except Exception as e:
        # Fallback to command line if GUI fails
        print(f"GUI failed to start: {e}. Falling back to command line mode.")
        main()