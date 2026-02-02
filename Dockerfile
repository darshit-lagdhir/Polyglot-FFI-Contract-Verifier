# Dockerfile
FROM python:3.11-slim

LABEL maintainer="darshit@example.com"
LABEL description="Polyglot FFI Contract Verifier"
LABEL version="1.0.0"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libclang-dev \
    clang \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt* requirements-dev.txt* ./

# Install Python dependencies
# We use '*' in COPY to make the files optional during build if they don't exist yet
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
RUN if [ -f requirements-dev.txt ]; then pip install --no-cache-dir -r requirements-dev.txt; else pip install pytest pytest-cov pytest-timeout; fi

# Copy source code
COPY . .

# Install package in editable mode
RUN pip install -e .

# Set up entrypoint
ENTRYPOINT ["polyglot-verify"]
CMD ["--help"]
