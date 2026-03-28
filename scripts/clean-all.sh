#!/bin/bash

set -e

echo "=========================================="
echo "Cleaning Data Lakehouse Platform"
echo "=========================================="

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${RED}WARNING: This will remove all containers, volumes, and data!${NC}"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Operation cancelled."
    exit 0
fi

"$SCRIPT_DIR/stop-all.sh"

echo -e "\n${YELLOW}Removing volumes...${NC}"

for layer in "03-bi" "02-data-platform" "01-product-domain" "00-storage"; do
    if [ -d "$ROOT_DIR/$layer" ]; then
        cd "$ROOT_DIR/$layer"
        docker compose down -v 2>/dev/null || true
        cd "$ROOT_DIR"
    fi
done

echo -e "${YELLOW}Removing network...${NC}"
docker network rm lakehouse-shared 2>/dev/null || true

echo -e "\n${GREEN}Cleanup completed.${NC}"
echo "To start fresh: ./scripts/setup-network.sh && ./scripts/start-all.sh"