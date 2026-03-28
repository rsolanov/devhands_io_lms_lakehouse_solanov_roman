#!/bin/bash

set -e

echo "==================================="
echo "Starting Data Lakehouse Platform"
echo "==================================="

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

COMPOSE_MODE=${COMPOSE_MODE:-online}

if [ "$COMPOSE_MODE" = "offline" ]; then
    COMPOSE_FLAGS="--pull never --no-build"
    echo -e "${YELLOW}[MODE] OFFLINE — using local images only${NC}"
else
    COMPOSE_FLAGS=""
    echo -e "${BLUE}[MODE] ONLINE — pulling images from registry if needed${NC}"
fi

if [ ! -d "$ROOT_DIR/00-storage" ] || [ ! -d "$ROOT_DIR/01-product-domain" ] || [ ! -d "$ROOT_DIR/02-data-platform" ]; then
    echo -e "${YELLOW}Error: Project directories not found!${NC}"
    echo "Please run this script from the project root directory."
    exit 1
fi

wait_for_http() {
    local service_name=$1
    local url=$2
    local max_attempts=${3:-30}
    local interval=${4:-10}
    local attempt=1

    echo -e "${BLUE}Waiting for $service_name...${NC}"
    while [ $attempt -le $max_attempts ]; do
        if curl -sf --max-time 3 "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}$service_name is ready.${NC}"
            return 0
        fi
        echo "  [$attempt/$max_attempts] Not ready yet..."
        sleep $interval
        attempt=$((attempt + 1))
    done
    echo -e "${YELLOW}Warning: $service_name did not become ready in time.${NC}"
    return 1
}

# 1. Storage Layer
echo -e "\n${BLUE}[1/4] Starting Storage Layer...${NC}"
cd "$ROOT_DIR/00-storage"
docker compose up -d $COMPOSE_FLAGS
cd "$ROOT_DIR"

wait_for_http "MinIO"      "http://localhost:9000/minio/health/live"
wait_for_http "Lakekeeper" "http://localhost:8181/health"

# 2. Product Domain
echo -e "\n${BLUE}[2/4] Starting Product Domain...${NC}"
cd "$ROOT_DIR/01-product-domain"
docker compose up -d $COMPOSE_FLAGS
cd "$ROOT_DIR"

wait_for_http "Spark Master"    "http://localhost:8080"
wait_for_http "Product Airflow" "http://localhost:8090/health"

# 3. Data Platform
echo -e "\n${BLUE}[3/4] Starting Data Platform...${NC}"
cd "$ROOT_DIR/02-data-platform"
docker compose up -d $COMPOSE_FLAGS
cd "$ROOT_DIR"

wait_for_http "Trino"            "http://localhost:8085/v1/info"
wait_for_http "Platform Airflow" "http://localhost:8091/health"

# 4. BI Layer
echo -e "\n${BLUE}[4/4] Starting BI Layer...${NC}"
cd "$ROOT_DIR/03-bi"
docker compose up -d $COMPOSE_FLAGS
cd "$ROOT_DIR"

wait_for_http "Superset" "http://localhost:8088/health" 36 10 || true

echo -e "\n${GREEN}==================================="
echo "Platform started successfully."
echo "===================================${NC}"

echo -e "\n${BLUE}Service endpoints:${NC}"
echo "┌──────────────────────┬──────────────────────────────┐"
echo "│ Service              │ URL                          │"
echo "├──────────────────────┼──────────────────────────────┤"
echo "│ MinIO Console        │ http://localhost:9001        │"
echo "│ Lakekeeper UI        │ http://localhost:8181        │"
echo "│ Spark Master UI      │ http://localhost:8080        │"
echo "│ Product Airflow      │ http://localhost:8090        │"
echo "│ Trino UI             │ http://localhost:8085        │"
echo "│ Platform Airflow     │ http://localhost:8091        │"
echo "│ Superset             │ http://localhost:8088        │"
echo "└──────────────────────┴──────────────────────────────┘"

echo -e "\n${BLUE}Default credentials:${NC}"
echo "  MinIO:            minioadmin / minioadmin"
echo "  Product Airflow:  admin / admin"
echo "  Platform Airflow: admin / admin"
echo "  Trino UI:         admin / -"
echo "  Superset:         admin / admin"

echo -e "\n${YELLOW}Note: Services may require an additional 1-2 minutes to become fully operational.${NC}"