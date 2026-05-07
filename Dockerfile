FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

RUN solc-select install 0.8.19 && solc-select use 0.8.19

COPY app/ ./app/
COPY alembic.ini .

RUN useradd -m -u 1001 privascan
USER privascan

EXPOSE 8000
