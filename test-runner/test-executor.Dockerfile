FROM python:3.12.9-alpine

# Install build dependencies for psutil
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers \
    python3-dev

# Install all test dependencies once
RUN pip install --no-cache-dir \
    hypothesis \
    pytest \
    memory-profiler \
    psutil

# Remove build dependencies to keep image small
RUN apk del gcc musl-dev linux-headers python3-dev

WORKDIR /test

# Default command that will be overridden
CMD ["python", "test_code.py"]
