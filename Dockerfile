# Use Python 3.11 slim image as base
# We need to pin to bookworm in ordere to get wkhtmltopdf in our apt repo https://packages.debian.org/bookworm/wkhtmltopdf https://tracker.debian.org/news/1612884/wkhtmltopdf-removed-from-testing/
FROM python:3.11-slim-bookworm

# Set working directory in container
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install wkhtmltopdf
RUN apt-get update && \
  apt-get install -y wkhtmltopdf && \
  rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY bcc_api.py .
COPY todo_receipts/ todo_receipts/
COPY mail_listener.py .

# Expose port 5000 (Flask default)
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Run the application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
