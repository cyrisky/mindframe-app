FROM python:3.9-slim

# Install WeasyPrint dependencies
RUN apt-get update && apt-get install -y \
    python3-dev python3-pip python3-cffi python3-brotli \
    libffi-dev libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p storage/pdfs storage/uploads storage/templates

# Set permissions
RUN chmod -R 755 storage/

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "--timeout", "120", "--keep-alive", "2", "app:app"]