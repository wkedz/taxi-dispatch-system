ifneq (,$(wildcard .env))
    include .env
    export $(shell sed 's/=.*//' .env)
endif


# ===== Phony =====
.PHONY: help install \
        run-all run-dispatcher run-taxi run-client run-grid stop-all \
        run-docker-all run-docker-dispatcher run-docker-taxi run-docker-client run-docker-grid stop-docker \
        run-rebuild run-docker-rebuild

help:
	@echo ""
	@echo "Targets:"
	@echo "  install                - zainstaluj pakiety do .venv (uv workspace)"
	@echo "  install-dev            - zainstaluj pakiety[dev] do .venv (uv workspace)"
	@echo ""
	@echo "  run-all                - uruchom WSZYSTKIE serwisy lokalnie (w tle)"
	@echo "  run-dispatcher         - uruchom Dispatcher lokalnie"
	@echo "  run-taxi               - uruchom Taxi lokalnie"
	@echo "  run-client             - uruchom Client Simulator lokalnie"
	@echo "  run-grid               - uruchom Grid lokalnie"
	@echo "  stop-all               - zatrzymaj wszystkie lokalne serwisy (uvicorn)"
	@echo ""
	@echo "  run-docker-all         - uruchom WSZYSTKIE serwisy w docker compose (-d)"
	@echo "  run-docker-dispatcher  - uruchom tylko Dispatcher w dockerze"
	@echo "  run-docker-taxi        - uruchom tylko Taxi w dockerze"
	@echo "  run-docker-client      - uruchom tylko Client Simulator w dockerze"
	@echo "  run-docker-grid        - uruchom tylko Grid w dockerze"
	@echo "  stop-docker            - docker compose down"
	@echo "  purge-docker           - usuwa wszystkie kontenery i wolumeny"
	@echo ""
	@echo "  run-rebuild            - przebuduj lokalne serwisy (reinstall w .venv)"
	@echo "  run-docker-rebuild     - przebuduj obrazy (docker compose build --no-cache)"
	@echo ""
	@echo "  run-tests              - uruchom testy (pytest) w .venv"

# ===== Install (uv workspace) =====
install:
	@echo ">>> Tworzę .venv i instaluję pakiety przez uv..."
	uv venv
	. .venv/bin/activate && \
	uv pip install -e ./common && \
	uv pip install -e ./dispatcher_service && \
	uv pip install -e ./taxi_service && \
	uv pip install -e ./client_service && \
	uv pip install -e ./grid_service;
	@echo ">>> Gotowe."

install-dev:
	uv venv
	. .venv/bin/activate && \
	uv pip install -e ./common && \
	uv pip install -e ./dispatcher_service[dev] && \
	uv pip install -e ./taxi_service[dev] && \
	uv pip install -e ./client_service && \
	uv pip install -e ./grid_service;
	@echo ">>> Gotowe."

# ===== Local runs =====
# Uwaga: uruchamiamy w tle (&). Użyj 'make stop-all' aby ubić lokalne uvicorny.

run-all: run-db run-dispatcher run-grid run-taxi run-client
	@echo ">>> Wszystkie lokalne serwisy odpalone (dispatcher, grid, taxi, client)."

# Start samej bazy Postgres (kontener docker compose)
run-db:
	@echo ">>> Uruchamiam Postgresa (docker compose, tylko db)"
	docker compose up -d database

# Dispatcher (lokalnie)
run-dispatcher:
	@echo ">>> Uruchamiam Dispatcher na :$(DISPATCHER_SERVICE_PORT)"
	. .venv/bin/activate && \
	POSTGRES_HOST=127.0.0.1 \
	DATABASE_URL=postgresql+psycopg2://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@127.0.0.1:$(POSTGRES_PORT)/$(POSTGRES_DB) \
	PUBLIC_CALLBACK_URL=http://127.0.0.1:$(TAXI_SERVICE_PORT)/assign \
	uvicorn dispatcher_service.app.main:app --port $(DISPATCHER_SERVICE_PORT) &

# Taxi (lokalnie)
run-taxi:
	@echo ">>> Uruchamiam Taxi na :$(TAXI_SERVICE_PORT)"
	. .venv/bin/activate && \
	DISPATCHER_BASE_URL=http://127.0.0.1:$(DISPATCHER_SERVICE_PORT) \
	PUBLIC_CALLBACK_URL=http://127.0.0.1:$(TAXI_SERVICE_PORT)/assign \
	uvicorn taxi_service.app.main:app --port $(TAXI_SERVICE_PORT) &

# Client Simulator (lokalnie)
run-client:
	@echo ">>> Uruchamiam Client Simulator na :$(CLIENT_SERVICE_PORT)"
	. .venv/bin/activate && \
	DISPATCHER_BASE_URL=http://127.0.0.1:$(DISPATCHER_SERVICE_PORT) \
	uvicorn client_service.app.main:app --port $(CLIENT_SERVICE_PORT) &

# Grid (lokalnie) - jeśli istnieje
run-grid:
	@echo ">>> Uruchamiam Grid na :$(GRID_SERVICE_PORT)"
	. .venv/bin/activate && \
	DISPATCHER_BASE_URL=http://127.0.0.1:$(DISPATCHER_SERVICE_PORT) \
	uvicorn grid_service.app.main:app --port $(GRID_SERVICE_PORT) &

# Stop lokalnych uvicornów
stop-all:
	@echo ">>> Zatrzymuję lokalne serwisy (uvicorn)..."
	-@pkill -f "uvicorn dispatcher_service.app.main:app" || true
	-@pkill -f "uvicorn taxi_service.app.main:app" || true
	-@pkill -f "uvicorn client_service.app.main:app" || true
	-@pkill -f "uvicorn grid_service.app.main:app" || true
	@echo ">>> Stop."

# ===== Docker runs =====

run-docker-all:
	@echo ">>> docker compose up -d (all)"
	docker compose up -d

run-docker-dispatcher:
	@echo ">>> docker compose up -d dispatcher"
	docker compose up -d dispatcher

run-docker-taxi:
	@echo ">>> docker compose up -d taxi"
	docker compose up -d taxi

run-docker-client:
	@echo ">>> docker compose up -d client"
	docker compose up -d client

run-docker-grid:
	@echo ">>> docker compose up -d grid"
	docker compose up -d grid

run-docker-db:
	@echo ">>> docker compose up -d database"
	docker compose up -d database

stop-docker:
	@echo ">>> docker compose down"
	docker compose down

purge-docker:
	@echo ">>> docker compose down -v --remove-orphans"
	docker compose down -v --remove-orphans

# ===== Rebuildy =====

# Lokalny „rebuild” = reinstall pakietów w .venv
run-rebuild: install
	@echo ">>> Lokalny rebuild zakończony."

# Docker rebuild
run-docker-rebuild:
	@echo ">>> docker compose build --no-cache"
	docker compose build --no-cache

# ==== TESTS =====

run-tests:
	@echo ">>> Uruchamiam testy (pytest) w .venv..."
	. .venv/bin/activate && \
	PYTHONPATH=. pytest dispatcher_service/tests/ && \
	PYTHONPATH=. pytest taxi_service/tests/;
	@echo ">>> Testy zakończone."