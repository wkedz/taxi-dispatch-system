FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir uv

RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /app
COPY pyproject.toml ./
COPY dispatcher_service/ ./dispatcher_service/
COPY common/ ./common/
WORKDIR /app/dispatcher_service
RUN uv pip install --no-cache -e .

FROM python:3.12-slim AS prod

ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
ENV PYTHONPATH=/app/

RUN apt-get update && apt-get install -y --no-install-recommends curl netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

ARG UID=1000
ARG GID=1000
RUN groupadd -g ${GID} appgroup && useradd -u ${UID} -g appgroup -s /bin/sh -m appuser

WORKDIR /app
RUN chown ${UID}:${GID} /app

COPY --chown=${UID}:${GID} --from=builder /opt/venv /opt/venv
COPY --chown=${UID}:${GID} dispatcher_service/ ./dispatcher_service/
COPY --chown=${UID}:${GID} common/ ./common/

USER appuser

ENTRYPOINT ["/app/dispatcher_service/entrypoint.sh"]
CMD ["uvicorn", "dispatcher_service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
