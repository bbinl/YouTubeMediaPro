FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    Flask==3.0.0 \
    Flask-SQLAlchemy==3.1.1 \
    Werkzeug==3.0.1 \
    gunicorn==21.2.0 \
    yt-dlp>=2024.01.01 \
    ffmpeg-python==0.2.0 \
    psycopg2-binary==2.9.9 \
    email-validator==2.1.0 \
    SQLAlchemy==2.0.23

# Copy application code
COPY . .

# Create downloads directory
RUN mkdir -p downloads

# Expose port (Railway will set PORT env var)
EXPOSE 5000

# Start command
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --timeout 120 main:app