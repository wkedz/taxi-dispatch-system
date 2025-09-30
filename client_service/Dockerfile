FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir uv

RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /app
COPY client_service/ ./client_service/
COPY common/ ./common/
WORKDIR /app/client_service
RUN uv pip install --no-cache -e .

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app/

ARG UID=1000
ARG GID=1000
RUN groupadd -g ${GID} appgroup && useradd -u ${UID} -g appgroup -s /bin/sh -m appuser

WORKDIR /app

COPY --chown=${UID}:${GID} --from=builder /opt/venv /opt/venv
COPY --chown=${UID}:${GID} --from=builder /app /app
COPY --chown=${UID}:${GID} --from=builder /app/common/ /app/common

USER appuser

CMD ["uvicorn", "client_service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
