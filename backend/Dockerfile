FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to latest version
RUN pip install --upgrade pip

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python packages and upgrade to latest versions
RUN pip install --no-cache-dir -r requirements.txt

# Verify installed versions
RUN echo "=== Installed Package Versions ===" && \
    pip list | grep -E "Django|channels|daphne|psycopg2|redis|pytest|websockets"

# Copy project files
COPY . .

# Run migrations and collect static files on startup
CMD ["sh", "-c", "python manage.py migrate && daphne -b 0.0.0.0 -p 8000 config.asgi:application"]
