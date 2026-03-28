#!/bin/bash

set -e

echo "=========================================="
echo "Setting up Lakehouse Network"
echo "=========================================="

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Создание общей сети
if docker network inspect lakehouse-shared >/dev/null 2>&1; then
    echo -e "${BLUE}Network 'lakehouse-shared' already exists${NC}"
else
    echo -e "${BLUE}Creating network 'lakehouse-shared'...${NC}"
    docker network create lakehouse-shared
    echo -e "${GREEN}Network created successfully!${NC}"
fi