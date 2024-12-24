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

def process_sheets(config):
    """Process multiple sheets and return results"""
    results = []
    
    df_dict = read_excel_file(config['file_path'])
    if not df_dict:
        raise ValueError("No valid sheets found in Excel file")

    selected_sheets = config.get('selected_sheets', [])
    if not selected_sheets:
        selected_sheets = [list(df_dict.keys())[0]]
        logging.info(f"No sheets selected, using first available sheet: {selected_sheets[0]}")

    total_sheets = len(selected_sheets)
    for i, sheet_name in enumerate(selected_sheets):
        if sheet_name not in df_dict:
            logging.warning(f"Sheet not found or invalid: {sheet_name}")
            continue

        logging.info(f"Processing sheet {i+1}/{total_sheets}: {sheet_name}")
        df = df_dict[sheet_name]
        
        if df is None or df.empty:
            logging.warning(f"No valid data found in sheet: {sheet_name}")
            continue

        df = validate_and_clean_data(df)
        if df is None or df.empty:
            logging.warning(f"Data validation failed for sheet: {sheet_name}")
            continue

        schema = map_data_types(df)
        if not schema:
            logging.warning(f"Failed to map data types for sheet: {sheet_name}")
            continue

        # Get table info
        from validation import get_table_info
        table_info = get_table_info(df)
        if not table_info:
            logging.warning(f"Failed to get table information for sheet: {sheet_name}")
            continue

        # Use table name from table_info or fallback to sheet name
        table_name = table_info['name'] or sheet_name.replace(' ', '_')

        results.append({
            'sheet_name': sheet_name,
            'df': df,
            'schema': schema,
            'table_info': table_info,
            'table_name': table_name
        })

        if config.get('progress_callback'):
            progress = ((i + 1) / total_sheets) * 100
            config['progress_callback'](progress)

    return results

def main(progress_callback=None):
    try:
        config = load_config()
        validate_config(config)
        
        if progress_callback:
            config['progress_callback'] = progress_callback

        # Update to use new logging setup
        from log import setup_logging
        setup_logging(
            log_level=getattr(logging, config.get('log_level', 'INFO'))
        )

        if not config['file_path']:
            logging.error("No Excel file path specified")
            return

        logging.info("Starting the Excel to Schemas project")
        results = process_sheets(config)
        
        if not results:
            raise ValueError("No sheets were successfully processed")

        if config.get('export_type') == 'script':
            # Generate SQL scripts for all sheets
            from database import generate_sql_script
            scripts = {}
            for result in results:
                sql_script = generate_sql_script(
                    result['table_name'],
                    result['schema'],
                    result['table_info'],
                    result['df']
                )
                scripts[result['sheet_name']] = sql_script
            return {'sql_scripts': scripts}
        else:
            # Create tables in database
            connection = connect_to_database(config['database'])
            if not connection:
                raise ConnectionError("Failed to connect to database")

            for result in results:
                create_sql_table(
                    connection, 
                    result['table_name'],
                    result['schema'],
                    result['table_info']
                )

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

import tkinter as tk
from gui import ExcelToSchemasGUI
from config_manager import ConfigManager
from log import setup_logging
import logging
from validation import generate_schema
import sys

def process_command_line(config_manager):
    """Handle command line processing when GUI fails"""
    try:
        logging.info("Falling back to command line processing")
        config = config_manager.config
        
        if not config.get('file_path'):
            logging.error("No Excel file path specified in config")
            return 1
            
        results = process_sheets(config)
        if not results:
            logging.error("No sheets were processed")
            return 1
            
        if config.get('export_type') == 'script':
            for result in results:
                sheet_name = result['sheet_name']
                sql_script = generate_schema(result['df'])
                output_path = f"{sheet_name}.sql"
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(sql_script)
                logging.info(f"Generated SQL script: {output_path}")
        else:
            connection = connect_to_database(config['database'])
            if not connection:
                logging.error("Failed to connect to database")
                return 1
                
            for result in results:
                create_sql_table(
                    connection,
                    result['table_name'],
                    result['schema'],
                    result['table_info']
                )
            connection.close()
            logging.info("Command line processing completed successfully")
            
    except Exception as e:
        logging.error(f"Command line processing failed: {e}")
        return 1
    return 0

def main():
    try:
        # Initialize config manager first
        config_manager = ConfigManager()
        
        # Setup logging with config manager
        logger = setup_logging(config_manager)
        
        try:
            root = tk.Tk()
            app = ExcelToSchemasGUI(root, config_manager)
            root.mainloop()
        except Exception as e:
            logging.error(f"GUI failed to start: {e}. Falling back to command line mode.")
            return process_command_line(config_manager)
            
    except Exception as e:
        print(f"Application error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())