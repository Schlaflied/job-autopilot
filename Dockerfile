FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# git: for pip installs
# netcat: for connectivity checks
# build-essential: for compiling python extensions
# chromium: optionally for headless if needed locally (though we use host usually)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV CDP_HOST=host.docker.internal
ENV FLASK_APP=app.py

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create active directories
RUN mkdir -p data/db data/logs .gemini

# Expose ports
EXPOSE 8501 5000

# Start script
# Launches Flask (API) and Streamlit (Frontend)
CMD ["sh", "-c", "python app.py & streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0"]
