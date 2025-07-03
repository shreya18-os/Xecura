FROM python:3.9-slim

# Create a non-root user
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Set working directory
WORKDIR /app

# Create data directory with proper permissions
RUN mkdir -p /app/data && \
    chown -R botuser:botuser /app && \
    chmod -R 755 /app && \
    chmod 777 /app/data

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY . .
RUN chown -R botuser:botuser /app

# Set environment variables
ENV DATA_DIR=/app/data
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER botuser

# Run the bot
CMD ["python", "main.py"]
