import os
import pandas as pd
import logging
from validation import error_handling_wrapper

def validate_column_order(df, expected_columns):
    """ตรวจสอบชื่อและลำดับของคอลัมน์ให้ตรงกับโครงสร้างที่คาดหวัง"""
    actual_columns = df.columns.tolist()
    validation_errors = []
    
    # ตรวจสอบว่ามีคอลัมน์ที่จำเป็นหรือไม่
    for col in expected_columns:
        if col not in actual_columns:
            validation_errors.append(f"ขาดคอลัมน์ที่จำเป็น: {col}")
    
    # ตรวจสอบลำดับของคอลัมน์
    for i, (expected, actual) in enumerate(zip(expected_columns, actual_columns)):
        if expected != actual:
            validation_errors.append(f"ลำดับคอลัมน์ไม่ตรงกันที่ตำแหน่ง {i+1}: คาดหวัง '{expected}', ได้รับ '{actual}'")
    
    return validation_errors

@error_handling_wrapper
def read_excel_file(file_path):
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ไม่พบไฟล์: {file_path}")
            
        # อ่านไฟล์ Excel
        xls = pd.ExcelFile(file_path)
        if not xls.sheet_names:
            raise ValueError("ไฟล์ Excel ไม่มีชีต")
            
        # กำหนดคอลัมน์ที่คาดหวังตามลำดับ
        expected_columns = [
            'Back', 'Key', 'No', 'Name', 'Nul', 'Type', 'Len', 'Dec', 'Und', 'Def', 'Desc', 'Note', 'TableCode', 'TableName', 'TableDesc', 'TableNote'
        ]
        
        df_dict = {}
        
        for sheet_name in xls.sheet_names:
            try:
                # อ่านชีต Excel
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # ตรวจสอบว่าจำนวนคอลัมน์ตรงกับจำนวนที่คาดหวังหรือไม่
                if len(df.columns) != len(expected_columns):
                    logging.warning(f"ชีต {sheet_name} มีจำนวนคอลัมน์ที่ไม่คาดหวัง: {len(df.columns)}")
                    continue
                
                # เปลี่ยนชื่อคอลัมน์ให้ตรงกับชื่อที่คาดหวัง
                df.columns = expected_columns
                
                # ตรวจสอบโครงสร้างของคอลัมน์
                validation_errors = validate_column_order(df, expected_columns)
                if validation_errors:
                    logging.warning(f"ชีต {sheet_name} มีข้อผิดพลาดในการตรวจสอบ:")
                    for error in validation_errors:
                        logging.warning(f"  {error}")
                    continue
                
                # ลบแถวที่ 'Name' ว่างเปล่า
                df = df.dropna(subset=['Name'])
                
                if df.empty:
                    logging.warning(f"ชีต {sheet_name} ไม่มีข้อมูลที่ถูกต้องหลังจากการกรอง")
                    continue
                
                # จัดเรียงตามดัชนีและรีเซ็ต
                df = df.reset_index(drop=True)
                
                # ตรวจสอบให้แน่ใจว่ามีคอลัมน์ที่คาดหวังทั้งหมด
                for col in expected_columns:
                    if col not in df.columns:
                        df[col] = None
                
                df_dict[sheet_name] = df
                logging.info(f"ชีต {sheet_name} โหลดสำเร็จด้วย {len(df)} คอลัมน์ที่ถูกต้อง")
                logging.info(f"ตรวจสอบลำดับคอลัมน์: {', '.join(df.columns)}")
                
            except Exception as e:
                logging.error(f"เกิดข้อผิดพลาดในการอ่านชีต {sheet_name}: {e}")
                continue
        
        if not df_dict:
            raise ValueError("ไม่พบชีตที่ถูกต้องในไฟล์ Excel")
            
        return df_dict
        
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์ Excel: {e}")
        raise
