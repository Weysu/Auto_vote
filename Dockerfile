# ── Stage 1 : builder ────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2 : runtime ────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"
# Browsers seront installés dans /opt/playwright plutôt que dans ~/.cache
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

# Copie du venv compilé
COPY --from=builder /opt/venv /opt/venv

# Dépendances système requises par Chromium sur Debian slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        libnss3 \
        libnspr4 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libdbus-1-3 \
        libexpat1 \
        libxcb1 \
        libxkbcommon0 \
        libx11-6 \
        libxcomposite1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libpango-1.0-0 \
        libcairo2 \
        libasound2 \
        libatspi2.0-0 \
        fonts-liberation \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Installation du browser Chromium uniquement
RUN playwright install --with-deps chromium

WORKDIR /app

COPY src/ src/
COPY config.yaml .

CMD ["python", "src/main.py"]
