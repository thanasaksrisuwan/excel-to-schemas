import pandas as pd
import logging
import numpy as np
import re
from typing import Optional

def error_handling_wrapper(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"เกิดข้อผิดพลาดใน {func.__name__}: {e}", exc_info=True)
            return None
    return wrapper

@error_handling_wrapper
def validate_and_clean_data(df):
    if df is None:
        raise ValueError("ไม่มีข้อมูลให้ตรวจสอบ")
        
    if df.empty:
        raise ValueError("DataFrame ว่างเปล่า")
    
    # ทำสำเนาเพื่อหลีกเลี่ยงการแก้ไขต้นฉบับ
    df = df.copy()
    
    # ตรวจสอบคอลัมน์ที่จำเป็น
    required_columns = ['Key', 'Name', 'Nul', 'Type', 'Len', 'Dec', 'Def', 'Desc']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"ขาดคอลัมน์ที่จำเป็น: {', '.join(missing_columns)}")
    
    # ตรวจสอบประเภทข้อมูล
    valid_types = ['int', 'bigint', 'nvarchar', 'varchar', 'nchar', 'char', 'datetime', 'decimal', 'float', 'bit']
    if not df['Type'].str.lower().isin(valid_types).all():
        invalid_types = df[~df['Type'].str.lower().isin(valid_types)]['Type'].unique()
        logging.warning(f"พบประเภทข้อมูลที่ไม่ถูกต้อง: {invalid_types}")
    
    # ตรวจสอบความยาวสำหรับประเภทสตริง
    string_types = ['nvarchar', 'varchar', 'nchar', 'char']
    string_rows = df['Type'].str.lower().isin(string_types)
    if not df.loc[string_rows, 'Len'].apply(lambda x: pd.isna(x) or (isinstance(x, (int, float)) and x > 0)).all():
        logging.warning("พบค่าความยาวที่ไม่ถูกต้องสำหรับประเภทสตริง")
    
    # จัดการ nullability
    df['is_nullable'] = df['Nul'].apply(lambda x: str(x).upper() == 'Y' if pd.notnull(x) else False)
    
    # จัดการ primary key
    df['is_primary_key'] = df['Key'].apply(lambda x: str(x).upper() == 'PK' if pd.notnull(x) else False)
    
    # จัดการ foreign key
    df['is_foreign_key'] = df['Key'].apply(lambda x: str(x).upper() == 'FK' if pd.notnull(x) else False)
    
    # Handle special characters in 'Name' column
    df['Name'] = df['Name'].apply(lambda x: re.sub(r'[^a-zA-Z0-9_]', '', str(x)))
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['Name'])
    
    # Format cleanup process
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    
    logging.info("การตรวจสอบและทำความสะอาดข้อมูลเสร็จสิ้น")
    return df

@error_handling_wrapper
def map_data_types(df):
    type_mapping = {
        'int': 'INT',
        'bigint': 'BIGINT',
        'nvarchar': 'NVARCHAR',
        'varchar': 'VARCHAR',
        'nchar': 'NCHAR',
        'char': 'CHAR',
        'datetime': 'DATETIME',
        'decimal': 'DECIMAL',
        'float': 'FLOAT',
        'bit': 'BIT'
    }
    
    schema = {}
    for _, row in df.iterrows():
        col_name = row['Name']
        sql_type = str(row['Type']).lower()
        length = int(row['Len']) if pd.notnull(row['Len']) else None
        nullable = row['Nul'].upper() == 'Y' if pd.notnull(row['Nul']) else True
        
        # จัดการกรณีประเภท SQL เฉพาะ
        if sql_type in ['nvarchar', 'varchar', 'nchar', 'char']:
            # ตรวจสอบให้แน่ใจว่าความยาวถูกต้อง
            if not length or not isinstance(length, int) or length <= 0:
                length = 'MAX'
            type_def = f"{type_mapping[sql_type]}({length})"
        elif sql_type == 'decimal':
            # ใช้ precision และ scale เริ่มต้นถ้าไม่ได้ระบุ
            precision = int(length) if length and isinstance(length, int) else 18
            scale = int(row['Dec']) if pd.notnull(row.get('Dec')) else 0
            if scale > precision:
                scale = precision
            type_def = f"{type_mapping[sql_type]}({precision},{scale})"
        elif sql_type == 'int':
            # ตรวจสอบว่าความยาวบ่งบอกถึง bigint หรือไม่
            if length and isinstance(length, int) and length > 9:
                type_def = 'BIGINT'
            else:
                type_def = type_mapping[sql_type]
        else:
            type_def = type_mapping.get(sql_type, 'NVARCHAR(MAX)')
        
        # เพิ่ม nullability
        type_def += " NULL" if nullable else " NOT NULL"
        
        # เพิ่มค่าเริ่มต้นถ้าระบุ
        if pd.notnull(row.get('Def')):
            default_value = row['Def']
            if sql_type in ['nvarchar', 'varchar', 'nchar', 'char']:
                default_value = f"N'{default_value}'"
            elif sql_type == 'bit':
                default_value = '1' if default_value.upper() == 'Y' else '0'
            else:
                default_value = f"'{default_value}'"
            type_def += f" DEFAULT {default_value}"
            
        schema[col_name] = type_def
        logging.debug(f"คอลัมน์ {col_name}: {type_def}")
        
    logging.info("การแมปประเภทข้อมูลเสร็จสิ้น")
    return schema

def clean_data_for_sql(df):
    """ทำความสะอาดและเตรียมข้อมูลสำหรับการแทรก SQL"""
    for column in df.columns:
        # แทนที่ NaN ด้วย None สำหรับ SQL NULL
        df[column] = df[column].replace({np.nan: None})
        
        # แปลงคอลัมน์ float ที่ควรเป็น int
        if df[column].dtype == 'float64':
            try:
                # ตรวจสอบว่าค่าที่ไม่ใช่ null ทั้งหมดเป็นจำนวนเต็มหรือไม่
                if df[column].dropna().apply(lambda x: float(x).is_integer()).all():
                    df[column] = df[column].apply(lambda x: int(x) if pd.notnull(x) else None)
            except:
                pass
    
    return df

@error_handling_wrapper
def get_table_info(df):
    """ดึงข้อมูลตารางจาก DataFrame"""
    try:
        # รับค่าที่ไม่ใช่ null แรกสำหรับข้อมูลตาราง
        table_info = {
            'code': df['TableCode'].iloc[0] if not df['TableCode'].isna().all() else '',
            'name': df['TableName'].iloc[0] if not df['TableName'].isna().all() else '',
            'description': df['TableDesc'].iloc[0] if 'TableDesc' in df.columns and not df['TableDesc'].isna().all() else '',
            'note': df['TableNote'].iloc[0] if 'TableNote' in df.columns and not df['TableNote'].isna().all() else '',
            'primary_keys': df[df['Key'].str.upper() == 'PK']['Name'].tolist() if not df['Key'].isna().all() else [],
            'foreign_keys': df[df['Key'].str.upper() == 'FK']['Name'].tolist() if not df['Key'].isna().all() else []
        }
        
        # ตรวจสอบข้อมูลตาราง
        if not table_info['name']:
            logging.warning("ไม่พบชื่อตาราง จะใช้ชื่อชีตแทน")
        
        logging.info(f"ดึงข้อมูลตาราง: {table_info['name']}")
        return table_info
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลตาราง: {e}")
        return {
            'code': '',
            'name': '',
            'description': '',
            'note': '',
            'primary_keys': [],
            'foreign_keys': []
        }

def generate_schema(df: pd.DataFrame) -> str:
    # Columns that are not part of the SQL schema
    non_sql_columns = ['Back', 'No', 'Dec', 'Und', 'Note', 'TableCode', 'TableDesc', 'TableNote']
    
    # Extract table information
    table_info = {}
    for _, row in df.iterrows():
        if pd.notna(row['TableName']) and pd.notna(row['TableCode']):
            table_info = {
                'name': row['TableName'],
                'code': row['TableCode'],
                'desc': row['TableDesc'] if pd.notna(row['TableDesc']) else ''
            }
            break

    # Generate CREATE TABLE statement
    sql_parts = [f"CREATE TABLE {table_info['name']} ("]
    
    # Process columns
    columns = []
    type_mapping = {
        'int': 'INT',
        'bigint': 'BIGINT',
        'nvarchar': 'NVARCHAR',
        'varchar': 'VARCHAR',
        'nchar': 'NCHAR',
        'char': 'CHAR',
        'datetime': 'DATETIME',
        'decimal': 'DECIMAL',
        'float': 'FLOAT',
        'bit': 'BIT'
    }
    for _, row in df.iterrows():
        if pd.isna(row['Name']) or row['Name'] == 'TableName' or row['Name'] in non_sql_columns:
            continue
            
        column_name = re.sub(r'[^a-zA-Z0-9_]', '', str(row['Name']))
        sql_type = type_mapping.get(str(row['Type']).lower(), 'NVARCHAR')
        
        # Parse length and decimal precision
        if pd.isna(row['Len']) and pd.isna(row['Dec']):
            sql_type = sql_type
        elif sql_type.lower() == 'decimal' and not pd.isna(row['Dec']):
            sql_type = f"{sql_type}({int(row['Len'])}, {int(row['Dec'])})"
        elif not pd.isna(row['Len']):
            sql_type = f"{sql_type}({int(row['Len'])})"
        
        # Build column definition
        column_def = [f"[{column_name}]", sql_type]
        
        # Add NULL/NOT NULL constraint
        is_nullable = str(row['Nul']).upper() == 'Y'
        column_def.append('NULL' if is_nullable else 'NOT NULL')
        
        # Handle default value
        if pd.notna(row['Def']): 
            default_value = row['Def']
            if sql_type in ['NVARCHAR', 'VARCHAR', 'NCHAR', 'CHAR']:
                default_value = f"N'{default_value}'"
            elif sql_type == 'BIT':
                default_value = '1' if default_value.upper() == 'Y' else '0'
            else:
                default_value = f"'{default_value}'"
            column_def.append(f"DEFAULT {default_value}")
        
        columns.append(f"    {' '.join(column_def)}")
    
    # Add columns to SQL
    sql_parts.append(',\n'.join(columns))
    
    sql_parts.append(");")
    
    # Add column descriptions
    for _, row in df.iterrows():
        if pd.notna(row['Name']) and pd.notna(row['Desc']) and row['Name'] != 'TableName' and row['Name'] not in non_sql_columns:
            column_name = re.sub(r'[^a-zA-Z0-9_]', '', str(row['Name']))
            sql_parts.append(f"\nEXEC sp_addextendedproperty")
            sql_parts.append(f"    @name = N'MS_Description',")
            sql_parts.append(f"    @value = N'{row['Desc']}',")
            sql_parts.append(f"    @level0type = N'Schema', @level0name = dbo,")
            sql_parts.append(f"    @level1type = N'Table', @level1name = {table_info['name']},")
            sql_parts.append(f"    @level2type = N'Column', @level2name = {column_name};")
    
    return '\n'.join(sql_parts)
