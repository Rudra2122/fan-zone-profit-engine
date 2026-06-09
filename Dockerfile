# Node stage — provides the runtime that hosts MongoDB's MCP server.
FROM node:20-slim AS node

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Bring Node + npm over from the node image so the app can spawn the MongoDB
# MCP server (the partner integration) as a stdio child process at runtime.
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
    && npm install -g mongodb-mcp-server@latest

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# Single worker: each worker hosts one MCP (node) subprocess; threads handle
# concurrency. Cloud Run sets $PORT (8080).
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 120 main:app
