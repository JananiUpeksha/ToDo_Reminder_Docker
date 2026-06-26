# ---- Stage 1: builder ----
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- Stage 2: final ----
FROM python:3.12-slim

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser worker.py .

ENV PATH=/home/appuser/.local/bin:$PATH
# Without this, Python buffers stdout when not attached to a terminal,
# so print() statements can sit invisible for a long time before flushing.
# This is a very common "my container logs are empty" gotcha.
ENV PYTHONUNBUFFERED=1

USER appuser

CMD ["python", "worker.py"]
