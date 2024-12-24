# Excel to Schemas

A Python tool to convert Excel spreadsheets into SQL Server database schemas.

## Features

- Converts Excel (.xlsx) files to SQL database schemas
- Supports basic data types and constraints
- Generates CREATE TABLE statements
- Handles primary key and nullable columns

## Prerequisites

- Python 3.7 or higher
- pandas library
- SQL Server database

## Required Packages

- pandas >= 1.3.0
- pyodbc >= 4.0.30
- openpyxl >= 3.0.7
- sqlalchemy >= 1.4.0
- python-dotenv >= 0.19.0

## Quick Start

1. Clone the repository
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Unix or MacOS:
   source venv/bin/activate
   ```
3. Install dependencies: `pip install -r requirements.txt`
4. Configure your database connection
5. Run: `python excel_to_schema.py <excel_file>`

## Using Docker Compose

### Prerequisites

- Docker
- Docker Compose

### Setup Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/excel-to-schemas.git
   cd excel-to-schemas
   ```

2. Update the `config.json` file with your Excel file path.

3. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

4. The application will run and connect to the SQL Server container.

### Stopping the Containers

To stop the containers, run:
```bash
docker-compose down
```

## Documentation

- [User Manual](docs/user_manual.md)
- [Project Requirements](docs/Project_requirent.md)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request