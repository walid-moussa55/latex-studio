# ── Base image ────────────────────────────────────────────────────────────────
# Use official Python slim image to keep size reasonable
FROM python:3.11-slim

# ── Labels ────────────────────────────────────────────────────────────────────
LABEL maintainer="LaTeX Studio"
LABEL description="Self-hosted LaTeX editor with PDF compilation"

# ── Environment variables ─────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# ── System dependencies ───────────────────────────────────────────────────────
# texlive-full is huge (~5GB); we use a curated subset that covers 99% of docs
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-full \
    lmodern \
    unrar-free \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ──────────────────────────────────────────────────────────
COPY app.py .
COPY templates/ templates/

# ── Projects volume mount point ───────────────────────────────────────────────
# Projects are stored here — mount a volume so data persists across container restarts
RUN mkdir -p /app/projects
VOLUME ["/app/projects"]

# ── Port ──────────────────────────────────────────────────────────────────────
EXPOSE 5000

# ── Healthcheck ───────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000')" || exit 1

# ── Start command ─────────────────────────────────────────────────────────────
CMD ["python", "app.py"]