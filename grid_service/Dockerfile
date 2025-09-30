FROM python:3.12-slim

RUN pip install --no-cache-dir uv
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
ENV PYTHONPATH=/app

ARG UID=1000
ARG GID=1000
RUN groupadd -g ${GID} appgroup && useradd -u ${UID} -g appgroup -s /bin/sh -m appuser


WORKDIR /app
COPY --chown=${UID}:${GID} grid_service/ /app/grid_service/
COPY --chown=${UID}:${GID} common/ /app/common/
RUN uv pip install --no-cache -e /app/grid_service

EXPOSE 8082
CMD ["uvicorn", "grid_service.app.main:app", "--host", "0.0.0.0", "--port", "8082"]
