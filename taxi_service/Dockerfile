FROM python:3.12-slim AS builder
RUN pip install --no-cache-dir uv
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /app

COPY taxi_service/pyproject.toml /app/taxi_service/pyproject.toml
COPY common/pyproject.toml /app/common/pyproject.toml
COPY common/ /app/common/
COPY pyproject.toml ./

WORKDIR /app/taxi_service
RUN uv pip install --no-cache -e /app/common \
 && uv pip install --no-cache -e .

FROM python:3.12-slim AS prod

ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
ENV PYTHONPATH=/app/taxi_service

ARG UID=1000
ARG GID=1000
RUN groupadd -g ${GID} appgroup && useradd -u ${UID} -g appgroup -s /bin/sh -m appuser

WORKDIR /app
RUN chown ${UID}:${GID} /app

COPY --chown=${UID}:${GID} --from=builder /opt/venv /opt/venv

COPY --chown=${UID}:${GID} taxi_service/ /app/taxi_service/
COPY --chown=${UID}:${GID} common/ /app/common/

USER appuser

EXPOSE 8081
CMD ["uvicorn", "taxi_service.app.main:app", "--host", "0.0.0.0", "--port", "8081"]
