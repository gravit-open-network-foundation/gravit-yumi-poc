# Multi-stage build to optimize image size
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy from builder
COPY --from=builder /root/.local /root/.local

# Copy source code
COPY src/ ./src/
COPY examples/ ./examples/
COPY tests/ ./tests/
COPY scripts/ ./scripts/

# Configure PATH and PYTHONPATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Create a non-root user
RUN useradd -m -u 1000 gravit && chown -R gravit:gravit /app
USER gravit

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080 8081

# Start the API server
CMD ["python", "-m", "src.api"]
