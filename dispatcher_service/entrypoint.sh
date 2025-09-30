#!/bin/bash
set -e

TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")


# Default values if variables are empty
[[ -z "$DB_VERSION" ]] && DB_VERSION="EMPTY"
[[ -z "$HEAD_VERSION" ]] && HEAD_VERSION="EMPTY"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function timestamp_echo {
  echo -e "$TIMESTAMP : $*"
}

function exec_command {
  timestamp_echo "Executing command: $*"
  exec "$@"
}

function wait_for_db {
  local host=$1
  local port=$2
  timestamp_echo "Waiting for database at $host:$port..."
  count=0
  while ! nc -z $host $port; do
    sleep 0.1
    count=$((count + 1))
    if [ $count -ge 300 ]; then
      timestamp_echo "Error: Timeout while waiting for database at $host:$port"
      exit 1
    fi
  done
  timestamp_echo "Database at $host:$port is available"
}

function upgrade_to_head_if_needed {
  # It shoyuld no be done like this.
  # Upgrade should be done manually by operator.
  # This is just for demo purposes.
  # In production, automatic migrations can lead to data loss.
  DB_VERSION=$(alembic current | cut -d ' ' -f 1)
  HEAD_VERSION=$(alembic heads | cut -d ' ' -f 1)
  if [ "$DB_VERSION" != "$HEAD_VERSION" ]; then
    timestamp_echo "${YELLOW}Upgrading database schema from ${DB_VERSION} to ${HEAD_VERSION}...${NC}"
    alembic upgrade head
    DB_VERSION=$(alembic current | cut -d ' ' -f 1)
    timestamp_echo "${GREEN}Database schema upgraded successfully to version ${DB_VERSION}!${NC}"
  fi
}

function main {
  timestamp_echo "Main function executed"
  wait_for_db $POSTGRES_HOST $POSTGRES_PORT

  if [ "$1" = 'alembic' ]; then
    timestamp_echo "Running alembic command..."
    exec_command "$@"
    exit 0
  fi
  cd /app/dispatcher_service
  upgrade_to_head_if_needed
  exec_command "$@"
}

main "$@"
