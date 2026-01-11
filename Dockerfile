FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF generation and browser automation
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    wget \
    gnupg \
    unzip \
    curl \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=7000
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV FLASK_APP=app.py

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/resumes data/credentials logs

# Expose ports
EXPOSE 7000 5000

# Start both Flask and Streamlit
CMD ["sh", "-c", "python app.py & streamlit run streamlit_app.py --server.port=7000 --server.address=0.0.0.0"]
