# Excel to Schemas User Manual

## Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
3. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.7 or higher
- pandas library
- SQL Server database

### Setup Steps

1. Clone the repository
2. Install required Python packages:

   ```bash
   pip install pandas pyodbc
   ```

## Usage

### Basic Operation

1. Prepare your Excel file following the schema format
2. Update the connection string in the script:

   ```python
   conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=your_db;UID=your_username;PWD=your_password')
   ```

3. Run the script with your Excel file:

   ```bash
   python excel_to_schema.py path/to/your/excel_file.xlsx
   ```

### Excel File Format

- Must be .xlsx format
- First row contains column headers
- Required columns:
  - Table names
  - Column names
  - Data types
  - Nullable flags
  - Primary key indicators

## Troubleshooting

### Common Issues

#### Database Connection Failed

- Verify SQL Server connection string
- Check network connectivity
- Confirm user permissions

#### Excel File Errors

- Ensure file is in .xlsx format
- Verify column headers match expected format
- Check for missing required columns

### Support

For issues, please check:
1. Console error messages
2. SQL Server error logs
3. Project repository issues page
