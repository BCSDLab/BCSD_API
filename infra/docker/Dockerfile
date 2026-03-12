FROM python:3.12-slim AS deps

WORKDIR /build
COPY pyproject.toml .
RUN mkdir -p src/bcsd_api && touch src/bcsd_api/__init__.py && \
    pip install --no-cache-dir .

FROM python:3.12-slim

RUN groupadd -r app && useradd -r -g app app

ENV TZ=Asia/Seoul

WORKDIR /app

COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir --no-deps .

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/openapi.json')"

CMD ["uvicorn", "bcsd_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
