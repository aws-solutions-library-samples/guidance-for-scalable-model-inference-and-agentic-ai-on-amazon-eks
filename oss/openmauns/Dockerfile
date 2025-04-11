FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Clone the repository
RUN git clone https://github.com/mannaandpoem/OpenManus.git .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install

# Create config directory and copy example config
RUN mkdir -p config && \
    cp config/config.example.toml config/config.toml

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port for FastAPI (if needed)
EXPOSE 8000

# Create a volume for configuration
VOLUME /app/config

# Set entrypoint
ENTRYPOINT ["python", "main.py"]

# Default command (can be overridden)
CMD []
