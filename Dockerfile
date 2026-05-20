# Dockerfile

FROM python:3.12-slim

# System deps + Node.js (needed for npm / OpenZeppelin contracts)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential python3-dev \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

# Install multiple solc versions so slither_runner can switch at runtime.
# 0.8.19 is the default; others cover common contract versions.
RUN solc-select install 0.4.26 \
    && solc-select install 0.5.17 \
    && solc-select install 0.6.12 \
    && solc-select install 0.7.6  \
    && solc-select install 0.8.0  \
    && solc-select install 0.8.19 \
    && solc-select use 0.8.19

# Install OpenZeppelin contracts globally so Slither can resolve
# @openzeppelin/... imports without needing npm install at scan time.
# The path /app/node_modules is added as a Slither remap in slither_runner.py.
RUN npm install --prefix /app @openzeppelin/contracts @openzeppelin/contracts-upgradeable

COPY app/ ./app/
COPY alembic.ini .

RUN useradd -m -u 1001 privascan
USER privascan

EXPOSE 8000