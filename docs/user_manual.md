# Excel to Schemas User Manual

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Usage](#usage)
4. [Advanced Features](#advanced-features)
5. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.7 or higher
- SQL Server 2016 or higher
- ODBC Driver 17 for SQL Server

### Setup Steps

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd excel-to-schemas
   ```

2. Create a virtual environment:

   ```bash
   python -m venv env
   ```

3. Activate the virtual environment:
   - Windows:

     ```bash
     .\env\Scripts\activate
     ```

   - Unix/MacOS:

     ```bash
     source env/bin/activate
     ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Database Settings

1. Open `config.json` and configure your database connection:

   ```json
   {
     "database": {
       "driver": "ODBC Driver 17 for SQL Server",
       "server": "your_server_name",
       "database": "your_database_name",
       "username": "your_username",
       "password": "your_password"
     }
   }
   ```

### Excel File Settings

1. Configure the Excel file path in `config.json`:

   ```json
   {
     "file_path": "path_to_your_excel_file.xlsx"
   }
   ```

### Performance Settings

1. Adjust batch size and timeout settings in `config.json`:

   ```json
   {
     "batch_size": 1000,
     "timeout": 30,
     "retry_attempts": 3
   }
   ```

## Usage

### Basic Operation

1. Prepare your Excel file with proper column headers
2. Update the configuration file with your settings
3. Run the application:

   ```bash
   python main.py
   ```

### Excel File Requirements

- Supported formats: .xlsx, .xls
- First row must contain column headers
- Supported data types:
  - Text (converts to VARCHAR)
  - Numbers (converts to INT/FLOAT)
  - Dates (converts to DATETIME)
  - Boolean (converts to BIT)

### Monitoring Progress

- Real-time progress updates appear in the console
- Detailed logs are written to `app.log`
- Import summary is generated after completion

### Sheet Selection

1. When running the application, you'll be prompted to select sheets:

   ```bash
   Available sheets in your Excel file:
   1. Sheet1
   2. Sheet2
   3. Sheet3

   Select sheets to process:
   [A] All sheets
   [S] Select specific sheets
   [1-3] Enter sheet numbers
   Your choice: 
   ```

2. Selection options:
   - Type 'A' for all sheets
   - Type 'S' to select multiple sheets (comma-separated numbers)
   - Type individual sheet numbers (1-N)

3. Only valid sheets containing the required schema format will be processed

4. Invalid sheets will be skipped with a warning message

## Advanced Features

### Error Recovery

- Failed imports are automatically saved
- Recovery process:
  1. Fix the issue that caused the failure
  2. Restart the application
  3. Failed records will be automatically processed

### Batch Processing

- Large files are processed in batches
- Default batch size: 1000 records
- Adjustable through `config.json`

### Data Validation

- Automatic data type detection
- Null value handling
- Duplicate record detection
- Special character handling

## Troubleshooting

### Common Issues

#### Database Connection Failed

1. Verify SQL Server is running
2. Check connection string in `config.json`
3. Confirm network connectivity
4. Verify user permissions

#### Excel File Errors

1. Verify file exists at configured path
2. Check file permissions
3. Ensure file is not open in another application
4. Validate file format (.xlsx or .xls)

#### Import Failures

1. Check `app.log` for detailed error messages
2. Verify data types match expected format
3. Look for special characters or invalid data
4. Confirm sufficient database permissions

### Error Messages

#### "File not found"

- Verify the file path in `config.json`
- Check if the file exists
- Ensure proper permissions

#### "Database connection error"

- Verify SQL Server is running
- Check credentials
- Confirm network connectivity

#### "Invalid data type"

- Check Excel column data types
- Verify data format
- Clean data if necessary

### Support

For additional support:

1. Check the logs in `app.log`
2. Review the documentation
3. Submit an issue on the project repository

## Best Practices

1. Always backup your database before large imports
2. Test with a small dataset first
3. Monitor system resources during large imports
4. Keep Excel files properly formatted
5. Regularly check logs for warnings or errors
