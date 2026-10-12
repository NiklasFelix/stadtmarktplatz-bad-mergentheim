FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Abhängigkeiten zuerst, damit der Layer beim Codeändern erhalten bleibt.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY referenz ./referenz

# daten/ wird als Volume gemountet (Pool + Queue), arbeitsdaten/ ist flüchtig.
RUN mkdir -p /app/daten /app/arbeitsdaten \
    && useradd --create-home --uid 10001 orkan \
    && chown -R orkan:orkan /app
USER orkan

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/status').read()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
