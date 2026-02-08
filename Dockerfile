# Dockerfile
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy only requirements first (for caching)
COPY pyproject.toml ./
COPY modules/module_05_ir_normalization/__version__.py ./modules/module_05_ir_normalization/

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir build && \
    pip install --no-cache-dir .

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 pfcv && \
    mkdir -p /data /cache && \
    chown -R pfcv:pfcv /data /cache

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/pfcv-ir /usr/local/bin/

# Copy application code
WORKDIR /app
COPY --chown=pfcv:pfcv modules/module_05_ir_normalization ./module_05_ir_normalization/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PFCV_CACHE_DIR=/cache \
    PFCV_DATA_DIR=/data

# Switch to non-root user
USER pfcv

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD pfcv-ir --version || exit 1

# Default command
ENTRYPOINT ["pfcv-ir"]
CMD ["--help"]

# Labels
LABEL org.opencontainers.image.title="PFCV Module 05: IR Normalization"
LABEL org.opencontainers.image.description="Transform raw interface artifacts into canonical IR"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="PFCV Authors <team@pfcv.dev>"
LABEL org.opencontainers.image.url="https://pfcv.dev"
LABEL org.opencontainers.image.source="https://github.com/pfcv/pfcv"
