import pyodbc
import logging
import time
import pandas as pd
from validation import error_handling_wrapper

@error_handling_wrapper
def connect_to_database(db_config):
    try:
        logging.info(f"Attempting to connect to SQL Server at {db_config['server']} with user {db_config['username']}")
        connection = pyodbc.connect(
            f"DRIVER={{{db_config['driver']}}};"
            f"SERVER={db_config['server']};"
            f"DATABASE={db_config['database']};"
            f"UID={db_config['username']};"
            f"PWD={db_config['password']};"
            "Timeout=30;"
        )
        logging.info("Connection successful!")
        return connection
    except pyodbc.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

@error_handling_wrapper
def create_sql_table(connection, table_name, schema, table_info):
    cursor = connection.cursor()
    
    table_name = table_name.replace(' ', '_')
    
    drop_table_query = f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name}"
    cursor.execute(drop_table_query)
    
    safe_schema = {}
    for col, dtype in schema.items():
        if col.lower() in ["dec", "und", "name", "nul", "len", "def", "desc"]:
            col = col + "_col"
        safe_schema[col] = dtype

    columns = [f"[{col}] {dtype}" for col, dtype in safe_schema.items()]
    
    if table_info and table_info.get('primary_keys'):
        pk_cols = [f"[{col}]" for col in table_info['primary_keys']]
        if pk_cols:
            pk_constraint = f"CONSTRAINT [PK_{table_name}] PRIMARY KEY ({','.join(pk_cols)})"
            columns.append(pk_constraint)
    
    create_table_query = f"""
    CREATE TABLE [{table_name}] (
        {','.join(columns)}
    )
    """
    
    logging.info(f"Creating table with query: {create_table_query}")
    cursor.execute(create_table_query)
    
    if table_info and table_info.get('description'):
        try:
            desc_query = f"""
            EXEC sp_addextendedproperty 
            @name = N'MS_Description',
            @value = N'{table_info['description']}',
            @level0type = N'SCHEMA', @level0name = 'dbo',
            @level1type = N'TABLE', @level1name = N'{table_name}'
            """
            cursor.execute(desc_query)
        except Exception as e:
            logging.warning(f"Could not add table description: {e}")
    
    connection.commit()
    logging.info(f"Table '{table_name}' created successfully!")

@error_handling_wrapper
def insert_data_into_table(connection, table_name, df, batch_size=1000, progress_callback=None):
    from validation import clean_data_for_sql
    
    cursor = connection.cursor()
    df = clean_data_for_sql(df)  # Clean data before insertion
    
    columns = ", ".join([f"[{col}]" for col in df.columns])
    placeholders = ", ".join(["?" for _ in df.columns])
    insert_query = f"INSERT INTO [{table_name}] ({columns}) VALUES ({placeholders})"
    
    connection.autocommit = False
    total_records = len(df)
    start_time = time.time()
    
    try:
        for start in range(0, total_records, batch_size):
            batch = df.iloc[start:start + batch_size]
            for index, row in batch.iterrows():
                # Convert row to list and handle None values
                values = [None if pd.isna(v) else v for v in row]
                cursor.execute(insert_query, values)
            
            connection.commit()
            progress = (start + len(batch)) / total_records * 100
            if progress_callback:
                progress_callback(progress)
            
            current_batch = start // batch_size + 1
            total_batches = total_records // batch_size + 1
            logging.info(f"Inserted batch {current_batch} of {total_batches}")
            logging.info(f"Progress: {progress:.2f}%")
        
        end_time = time.time()
        logging.info(f"Data inserted into table '{table_name}' successfully!")
        logging.info(f"Total records inserted: {total_records}")
        logging.info(f"Total time taken: {end_time - start_time:.2f} seconds")
    except pyodbc.Error as e:
        connection.rollback()
        logging.error(f"Error inserting data: {e}")
        # Save the state for recovery
        save_failed_batch(batch)
    finally:
        connection.autocommit = True

def save_failed_batch(batch):
    # Save the failed batch to a file for recovery
    batch.to_csv("failed_batch.csv", index=False)
    logging.info("Failed batch saved for recovery.")

def generate_sql_script(table_name, schema, table_info, data_df):
    """Generate SQL script for table creation and data insertion"""
    sql_script = []
    
    # Drop table if exists
    sql_script.append(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name};")
    sql_script.append("GO")
    sql_script.append("")
    
    # Create table
    columns = [f"[{col}] {dtype}" for col, dtype in schema.items()]
    if table_info and table_info.get('primary_keys'):
        pk_cols = [f"[{col}]" for col in table_info['primary_keys']]
        if pk_cols:
            pk_constraint = f"CONSTRAINT [PK_{table_name}] PRIMARY KEY ({','.join(pk_cols)})"
            columns.append(pk_constraint)
    
    create_table = f"""CREATE TABLE [{table_name}] (
    {',\n    '.join(columns)}
);"""
    sql_script.append(create_table)
    sql_script.append("GO")
    sql_script.append("")
    
    # Add table description
    if table_info and table_info.get('description'):
        desc_query = f"""EXEC sp_addextendedproperty 
@name = N'MS_Description',
@value = N'{table_info['description']}',
@level0type = N'SCHEMA', @level0name = 'dbo',
@level1type = N'TABLE', @level1name = N'{table_name}';"""
        sql_script.append(desc_query)
        sql_script.append("GO")
        sql_script.append("")
    
    # Insert data
    if not data_df.empty:
        sql_script.append(f"-- Insert data into {table_name}")
        columns = ", ".join([f"[{col}]" for col in data_df.columns])
        for _, row in data_df.iterrows():
            values = []
            for val in row:
                if pd.isna(val):
                    values.append("NULL")
                elif isinstance(val, (int, float)):
                    values.append(str(val))
                else:
                    values.append(f"N'{str(val).replace(chr(39), chr(39)+chr(39))}'")
            values_str = ", ".join(values)
            sql_script.append(f"INSERT INTO [{table_name}] ({columns}) VALUES ({values_str});")
        sql_script.append("GO")
        sql_script.append("")
    
    return "\n".join(sql_script)
