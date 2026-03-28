#!/bin/bash

echo "=========================================="
echo "Data Lakehouse Platform — Service Status"
echo "=========================================="

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

check_http() {
    local name=$1
    local url=$2
    if curl -sf --max-time 3 "$url" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $name"
    else
        echo -e "  ${RED}✗${NC} $name — not available ($url)"
    fi
}

check_container() {
    local container=$1
    local name=$2
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo -e "  ${GREEN}✓${NC} $name"
    else
        echo -e "  ${RED}✗${NC} $name — container not running"
    fi
}

echo -e "\n${BLUE}Storage Layer${NC}"
check_http      "MinIO API"        "http://localhost:9000/minio/health/live"
check_http      "MinIO Console"    "http://localhost:9001"
check_container "postgres-metastore"  "PostgreSQL (Lakekeeper metastore)"
check_http      "Lakekeeper"       "http://localhost:8181/health"

echo -e "\n${BLUE}Product Domain${NC}"
check_http      "Spark Master UI"  "http://localhost:8080"
check_container "product-spark-master" "Spark Master"
check_http      "Product Airflow"  "http://localhost:8090/health"

echo -e "\n${BLUE}Data Platform${NC}"
check_http      "Trino"            "http://localhost:8085/v1/info"
check_container "platform-trino-coordinator" "Trino Coordinator"
check_container "platform-dbt"     "dbt"
check_http      "Platform Airflow" "http://localhost:8091/health"

echo -e "\n${BLUE}BI Layer${NC}"
check_http      "Superset"         "http://localhost:8088/health"

echo -e "\n${BLUE}Docker Resources${NC}"
echo "  Running containers : $(docker ps -q | wc -l | tr -d ' ')"
echo "  Lakehouse networks : $(docker network ls | grep -c lakehouse || true)"