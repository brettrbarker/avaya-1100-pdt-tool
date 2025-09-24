#!/bin/bash
# offline-deploy.sh
# Simple deployment script for offline systems

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Avaya PDT Tool - Simple Offline Deploy${NC}"
echo "======================================"

# Check for container tar file
if [ ! -f "avaya-pdt-ubi7.tar" ] && [ ! -f "avaya-pdt-ubi7.tar.gz" ]; then
    echo -e "${RED}Error: Container image file not found${NC}"
    echo "Expected: avaya-pdt-ubi7.tar or avaya-pdt-ubi7.tar.gz"
    exit 1
fi

# Check if podman is installed
if ! command -v podman &> /dev/null; then
    echo -e "${RED}Error: Podman is not installed${NC}"
    echo "Install with: sudo dnf install -y podman"
    exit 1
fi

# Decompress if needed
if [ -f "avaya-pdt-ubi7.tar.gz" ]; then
    echo -e "${YELLOW}Decompressing container image...${NC}"
    gunzip avaya-pdt-ubi7.tar.gz
fi

# Import container
echo -e "${YELLOW}Importing container image...${NC}"
podman load -i avaya-pdt-ubi7.tar

# Verify import
if podman image exists avaya-pdt-ubi7:latest; then
    echo -e "${GREEN}Container imported successfully!${NC}"
    podman images | grep avaya-pdt
else
    echo -e "${RED}Error: Container import failed${NC}"
    exit 1
fi

echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "You can now run the tool with:"
echo "  podman run -it --rm --network host -v \$(pwd):/app:Z avaya-pdt-ubi7:latest python3 pdt_tool.py -f sample.csv"