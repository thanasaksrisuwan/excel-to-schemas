# Excel to SQL Schema Generator Requirements

## 1. Excel File Handling

- **File Format Support**
  - Read .xlsx format
  - Process single worksheet
  - Map predefined column headers
  - Support basic data types

## 2. Data Type Mapping

- **Supported Conversions**
  - nvarchar → NVARCHAR
  - int → INT
  - datetime → DATETIME
  - nchar → NCHAR
  - bit → BIT

## 3. Data Validation & Cleaning

- **Validation Features**
  - Validate required columns
  - Clean data (strip whitespace, handle nulls)
  - Map data types to SQL types

## 4. SQL Schema Generation

- **Table Operations**
  - Generate CREATE TABLE statements
  - Set primary key constraints
  - Handle nullable columns
  - Basic table creation

## 5. Error Management

- **Error Handling**
  - Basic error logging
  - Connection error detection
  - File format validation
  - Schema generation validation

## 6. Configuration

- **System Settings**
  - Database connection string
  - Excel file path
  - Basic logging settings

## 7. Output

- **Features**
  - SQL schema generation
  - Console status messages
  - Basic error reporting
  - Schema validation results

## 8. Sheet Selection Features

- **Interactive Sheet Selection**
  - Multiple selection modes (All/Single/Multiple)
  - Sheet validation before processing
  - Skip invalid sheets automatically
  - Clear feedback on sheet status
  - Remember last selection (optional)