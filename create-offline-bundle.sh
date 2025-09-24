#!/bin/bash
# create-offline-bundle.sh
# Creates a complete offline deployment bundle for the Avaya PDT Tool

set -e

BUNDLE_NAME="avaya-pdt-offline-$(date +%Y%m%d-%H%M%S)"
CONTAINER_IMAGE="avaya-pdt-ubi7:latest"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Creating Offline Deployment Bundle${NC}"
echo "=============================================="

# Check if podman is available
if ! command -v podman &> /dev/null; then
    echo -e "${RED}Error: Podman is not installed${NC}"
    exit 1
fi

# Check if container image exists
if ! podman image exists "$CONTAINER_IMAGE"; then
    echo -e "${YELLOW}Container image not found. Building...${NC}"
    if [ ! -f "Dockerfile.ubi7" ]; then
        echo -e "${RED}Error: Dockerfile.ubi7 not found${NC}"
        exit 1
    fi
    podman build -f Dockerfile.ubi7 -t "$CONTAINER_IMAGE" .
fi

# Create bundle directory
echo -e "${YELLOW}Creating bundle directory...${NC}"
mkdir -p "$BUNDLE_NAME"

# Copy project files (excluding git and other unwanted files)
echo -e "${YELLOW}Copying project files...${NC}"
rsync -av --exclude='.git' --exclude='*.tar*' --exclude='avaya-pdt-offline-*' \
    . "$BUNDLE_NAME/project/"

# Export container image
echo -e "${YELLOW}Exporting container image...${NC}"
podman save -o "$BUNDLE_NAME/avaya-pdt-ubi7.tar" "$CONTAINER_IMAGE"

# Compress the container image to save space
echo -e "${YELLOW}Compressing container image...${NC}"
gzip "$BUNDLE_NAME/avaya-pdt-ubi7.tar"

# Create deployment script
echo -e "${YELLOW}Creating deployment script...${NC}"
cat > "$BUNDLE_NAME/deploy.sh" << 'EOF'
#!/bin/bash
# Offline deployment script for Avaya PDT Tool

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Deploying Avaya PDT Tool Offline${NC}"
echo "=================================="

# Check if podman is installed
if ! command -v podman &> /dev/null; then
    echo -e "${RED}Error: Podman is not installed on this system${NC}"
    echo "Please install podman first:"
    echo "  sudo dnf install -y podman"
    exit 1
fi

# Import container image
echo -e "${YELLOW}Importing container image...${NC}"
if [ -f "avaya-pdt-ubi7.tar.gz" ]; then
    gunzip avaya-pdt-ubi7.tar.gz
fi

podman load -i avaya-pdt-ubi7.tar

# Verify import
echo -e "${YELLOW}Verifying container import...${NC}"
if podman image exists avaya-pdt-ubi7:latest; then
    echo -e "${GREEN}Container image imported successfully${NC}"
else
    echo -e "${RED}Error: Container image import failed${NC}"
    exit 1
fi

# Make scripts executable
chmod +x project/run-pdt-podman.sh

# Create output directories
mkdir -p project/output
mkdir -p project/pdt-tool-logs
mkdir -p project/phone-configs

echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Usage:"
echo "  cd project"
echo "  ./run-pdt-podman.sh sample.csv    # Run with CSV file"
echo "  ./run-pdt-podman.sh               # Run interactively"
echo ""
echo "Or run manually:"
echo "  podman run -it --rm --network host -v \$(pwd):/app:Z avaya-pdt-ubi7:latest python3 pdt_tool.py"
EOF

chmod +x "$BUNDLE_NAME/deploy.sh"

# Create README for offline deployment
cat > "$BUNDLE_NAME/README-OFFLINE.md" << EOF
# Avaya PDT Tool - Offline Deployment

This bundle contains everything needed to run the Avaya PDT Tool on an offline RHEL 9 system.

## Contents
- \`project/\` - Complete project source code and dependencies
- \`avaya-pdt-ubi7.tar.gz\` - Container image (compressed)
- \`deploy.sh\` - Automated deployment script
- \`README-OFFLINE.md\` - This file

## Prerequisites
- RHEL 9 system with Podman installed
- Network access to Avaya phones (for SSH connections)

## Quick Start
1. Transfer this entire bundle to your offline system
2. Extract if compressed: \`tar -xzf avaya-pdt-offline-bundle.tar.gz\`
3. Run deployment: \`./deploy.sh\`
4. Use the tool: \`cd project && ./run-pdt-podman.sh sample.csv\`

## Manual Installation
If the deployment script doesn't work:

1. Import container: \`podman load -i avaya-pdt-ubi7.tar\` (uncompress first if needed)
2. Run container: \`podman run -it --rm --network host -v \$(pwd)/project:/app:Z avaya-pdt-ubi7:latest python3 pdt_tool.py\`

## Bundle Created
- Date: $(date)
- System: $(uname -a)
- Podman Version: $(podman --version)
- Container Image: $CONTAINER_IMAGE

For detailed instructions, see project/OFFLINE-DEPLOYMENT-GUIDE.md
EOF

# Calculate sizes
IMAGE_SIZE=$(du -h "$BUNDLE_NAME/avaya-pdt-ubi7.tar.gz" | cut -f1)
TOTAL_SIZE=$(du -sh "$BUNDLE_NAME" | cut -f1)

# Create final archive
echo -e "${YELLOW}Creating final archive...${NC}"
tar -czf "$BUNDLE_NAME.tar.gz" "$BUNDLE_NAME/"

ARCHIVE_SIZE=$(du -h "$BUNDLE_NAME.tar.gz" | cut -f1)

echo -e "${GREEN}Offline bundle created successfully!${NC}"
echo "=============================================="
echo "Bundle: $BUNDLE_NAME.tar.gz"
echo "Container image size: $IMAGE_SIZE"
echo "Bundle directory size: $TOTAL_SIZE"
echo "Final archive size: $ARCHIVE_SIZE"
echo ""
echo "Transfer this file to your offline system and extract:"
echo "  tar -xzf $BUNDLE_NAME.tar.gz"
echo "  cd $BUNDLE_NAME"
echo "  ./deploy.sh"

# Optional: Clean up bundle directory
read -p "Remove bundle directory? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$BUNDLE_NAME"
    echo "Bundle directory removed. Archive preserved."
fi