#!/bin/bash

set -e

echo "==================================="
echo "Stopping Data Lakehouse Platform"
echo "==================================="

# Цвета для вывода
RED='\033[0;31m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Остановка в обратном порядке

echo -e "${BLUE}Stopping BI Layer...${NC}"
if [ -d "03-bi" ]; then
    cd 03-bi
    docker-compose down
    cd ..
    echo -e "${GREEN}BI Layer stopped${NC}"
fi

echo -e "${BLUE}Stopping Data Platform...${NC}"
if [ -d "02-data-platform" ]; then
    cd 02-data-platform
    docker-compose down
    cd ..
    echo -e "${GREEN}Data Platform stopped${NC}"
fi

echo -e "${BLUE}Stopping Product Domain...${NC}"
if [ -d "01-product-domain" ]; then
    cd 01-product-domain
    docker-compose down
    cd ..
    echo -e "${GREEN}Product Domain stopped${NC}"
fi

echo -e "${BLUE}Stopping Storage Layer...${NC}"
if [ -d "00-storage" ]; then
    cd 00-storage
    docker-compose down
    cd ..
    echo -e "${GREEN}Storage Layer stopped${NC}"
fi

echo -e "\n${GREEN}All services stopped successfully!${NC}"