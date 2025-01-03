# Excel to Schemas User Manual

## Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
3. [Configuration](#configuration)
4. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.7 or higher
- Required Python packages:
  ```
  pandas >= 1.3.0
  pyodbc >= 4.0.30
  openpyxl >= 3.0.7
  sqlalchemy >= 1.4.0
  python-dotenv >= 0.19.0
  ```
- SQL Server database
- Docker
- Docker Compose

### Setup Steps

1. Clone the repository
2. Set up Python virtual environment:
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On Windows:
   .\venv\Scripts\activate
   # On Unix or MacOS:
   source venv/bin/activate

   # Verify activation (should show virtual environment path)
   which python
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Verify installation:
   ```bash
   pip list
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

### Using Docker Compose

1. Ensure Docker and Docker Compose are installed on your system.
2. Clone the repository and navigate to the project directory.
3. Update the `config.json` file with your Excel file path.
4. Build and start the containers:
   ```bash
   docker-compose up --build
   ```
5. The application will run and connect to the SQL Server container.

### Stopping the Containers

To stop the containers, run:
```bash
docker-compose down
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

## Configuration

### Database Settings
- Create a `config.ini` file in the project root
- Add your database connection details:
  ```ini
  [database]
  server=your_server
  database=your_db
  username=your_username
  password=your_password
  ```

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
