#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: ./scripts/logs.sh [storage|product|platform|bi] [service_name]"
    echo ""
    echo "Examples:"
    echo "  ./scripts/logs.sh storage             # All storage services"
    echo "  ./scripts/logs.sh storage minio       # MinIO logs only"
    echo "  ./scripts/logs.sh product             # All product domain services"
    echo "  ./scripts/logs.sh platform trino      # Trino logs only"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

LAYER=$1
SERVICE=${2:-}

case $LAYER in
    storage)  TARGET="$ROOT_DIR/00-storage" ;;
    product)  TARGET="$ROOT_DIR/01-product-domain" ;;
    platform) TARGET="$ROOT_DIR/02-data-platform" ;;
    bi)       TARGET="$ROOT_DIR/03-bi" ;;
    *)
        echo "Unknown layer: $LAYER"
        echo "Available: storage, product, platform, bi"
        exit 1
        ;;
esac

cd "$TARGET"

if [ -z "$SERVICE" ]; then
    docker compose logs -f
else
    docker compose logs -f "$SERVICE"
fi