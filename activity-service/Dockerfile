FROM python:3.12-slim-bullseye

# ROOT SECTION: System setup
# Create group and user named appuser. Install system packages
RUN groupadd -r appuser -g 1001 && \
    useradd -r -u 1001 -g appuser -s /sbin/nologin -c "Application user" appuser && \
    mkdir -p /home/appuser && \
    chown appuser:appuser /home/appuser && \
    chmod 755 /home/appuser && \
    apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

WORKDIR /app

# Copy files as root
COPY requirements.txt requirements.txt
COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock
COPY README.md README.md
COPY ./app ./app

ARG AZURE_ARTIFACTS_URL
ARG AZURE_PAT
ARG ITAAP_PYTHON_UTILS_VERSION=PYTHON_UTIL_VERSION_PLACEHOLDER
COPY wheels/itaap_python_utils-1.0.58-py3-none-any.whl /tmp/
RUN uv pip install --system /tmp/itaap_python_utils-1.0.58-py3-none-any.whl && \
    uv pip install --system .
# Lock down permissions and switch to appuser
RUN chmod -R 444 ./app && \
    find ./app -type d -exec chmod 555 {} \; && \
    chown -R root:appuser ./app && \
    chmod 444 requirements.txt && \
    chmod 444 pyproject.toml && \
    chmod 444 uv.lock && \
    chmod 444 README.md && \
    chown root:appuser requirements.txt && \
    chown root:appuser pyproject.toml && \
    chown root:appuser uv.lock && \
    chown root:appuser README.md

USER appuser

ENTRYPOINT ["python", "-m", "app.main"]