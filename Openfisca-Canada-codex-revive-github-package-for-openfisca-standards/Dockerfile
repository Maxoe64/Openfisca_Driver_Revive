FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /openfisca
COPY . /openfisca

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 5000

CMD ["python", "-m", "app.server", "--host", "0.0.0.0", "--port", "5000"]
