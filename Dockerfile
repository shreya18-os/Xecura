FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Create data directory with proper permissions
RUN mkdir -p /app/data && chmod 777 /app/data

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY . .

# Set environment variable for data directory
ENV DATA_DIR=/app/data

# Run the bot
CMD ["python", "main.py"]
