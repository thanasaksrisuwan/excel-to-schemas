FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including tk
RUN apt-get update && apt-get install -y \
    python3-tk \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
