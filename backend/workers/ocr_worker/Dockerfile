FROM python:3.11-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY ../../shared/ /app/backend/shared/
COPY . /app/backend/workers/ocr_worker/
WORKDIR /app/backend/workers/ocr_worker
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
