FROM python:3.12.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    S10_ENVIRONMENT=production \
    S10_ALLOWED_HOSTS=localhost,127.0.0.1

WORKDIR /app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install ".[production,service]"

COPY scripts/15_s10_service.py ./scripts/15_s10_service.py
COPY artifacts/releases/s10_production_2026-08-16.joblib ./artifacts/releases/s10_production_2026-08-16.joblib
COPY reports/vs_epl_krls/s10_product ./reports/vs_epl_krls/s10_product
COPY reports/vs_epl_krls/s10_selection/selection_manifest_h1.json ./reports/vs_epl_krls/s10_selection/selection_manifest_h1.json

USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/v1/health/live', timeout=2)"]
CMD ["python", "scripts/15_s10_service.py", "--host", "0.0.0.0", "--port", "8000"]
