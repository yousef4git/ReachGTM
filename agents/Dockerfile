FROM python:3.11-slim AS builder
WORKDIR /build
COPY agents/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim AS production
RUN useradd -m -u 1001 appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY shared/ ./shared/
COPY agents/ ./agents/
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"
CMD ["uvicorn", "agents.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
