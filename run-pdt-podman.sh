#!/bin/bash
# Avaya PDT Tool - Podman Runner Script for RHEL 9
# Usage: ./run-pdt-podman.sh [csv-file]

set -e

CONTAINER_NAME="avaya-pdt-ubi7"
IMAGE_NAME="avaya-pdt-ubi7"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Avaya 1100 PDT Tool - Podman Runner${NC}"
echo "================================================"

# Check if podman is installed
if ! command -v podman &> /dev/null; then
    echo -e "${RED}Error: Podman is not installed.${NC}"
    echo "Install with: sudo dnf install -y podman"
    exit 1
fi

# Check if image exists, build if not
if ! podman image exists "$IMAGE_NAME"; then
    echo -e "${YELLOW}Container image not found. Building...${NC}"
    if [ -f "$SCRIPT_DIR/Dockerfile.ubi7" ]; then
        podman build -f "$SCRIPT_DIR/Dockerfile.ubi7" -t "$IMAGE_NAME" "$SCRIPT_DIR"
    else
        echo -e "${RED}Error: Dockerfile.ubi7 not found in $SCRIPT_DIR${NC}"
        exit 1
    fi
fi

# Create output directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/output"

# Determine CSV file to use
CSV_FILE=""
if [ $# -eq 1 ]; then
    if [ -f "$1" ]; then
        CSV_FILE="$1"
        echo -e "${GREEN}Using CSV file: $CSV_FILE${NC}"
    else
        echo -e "${RED}Error: CSV file '$1' not found${NC}"
        exit 1
    fi
elif [ -f "$SCRIPT_DIR/sample.csv" ]; then
    CSV_FILE="sample.csv"
    echo -e "${YELLOW}Using default CSV file: $CSV_FILE${NC}"
else
    echo -e "${YELLOW}No CSV file specified and sample.csv not found${NC}"
    echo "The tool will run in interactive mode"
fi

echo "================================================"
echo -e "${GREEN}Starting container...${NC}"

# Run the container
if [ -n "$CSV_FILE" ]; then
    # Run with CSV file
    podman run -it --rm \
        --network host \
        --name "$CONTAINER_NAME-$(date +%s)" \
        -v "$SCRIPT_DIR:/app:Z" \
        -v "$SCRIPT_DIR/output:/app/output:Z" \
        -w /app \
        "$IMAGE_NAME" \
        python3 pdt_tool.py -f "$CSV_FILE"
else
    # Run without CSV file (interactive mode)
    podman run -it --rm \
        --network host \
        --name "$CONTAINER_NAME-$(date +%s)" \
        -v "$SCRIPT_DIR:/app:Z" \
        -v "$SCRIPT_DIR/output:/app/output:Z" \
        -w /app \
        "$IMAGE_NAME" \
        python3 pdt_tool.py
fi

echo -e "${GREEN}Container execution completed.${NC}"
echo "Check the output directory for generated files:"
echo "  - Logs: ./pdt-tool-logs/"
echo "  - Configs: ./phone-configs/"
echo "  - CSV exports: ./"