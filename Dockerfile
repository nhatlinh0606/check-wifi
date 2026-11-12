# Multi-stage Dockerfile for TP-Link Router Discovery & Recovery Dashboard

# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend Runtime
FROM python:3.12-slim
WORKDIR /app

# Install system network utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    iproute2 \
    iputils-ping \
    network-manager \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY config/ ./config/
COPY modules/ ./modules/
COPY backend/ ./backend/
COPY router_tool.py ./
RUN mkdir -p reports

# Copy compiled frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose web dashboard port
EXPOSE 8000

ENV HOST=0.0.0.0
ENV PORT=8000

CMD ["python3", "-m", "backend.main"]
