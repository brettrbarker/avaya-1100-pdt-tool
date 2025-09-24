# Offline Container Deployment Guide

This guide explains how to build the Avaya PDT Tool container on an online system and deploy it to an offline RHEL 9 system using Podman.

## Overview

This process involves:
1. Building the container on an online system
2. Exporting the container image to a tar file
3. Transferring the tar file to the offline system
4. Importing and running the container on the offline system

## Part 1: Build on Online System

### Prerequisites for Online System
- RHEL 9, Fedora, or any Linux system with Podman
- Internet connectivity
- This project's source code

### Steps on Online System

1. **Install Podman (if needed):**
   ```bash
   sudo dnf install -y podman
   ```

2. **Build the container image:**
   ```bash
   cd /path/to/avaya-1100-pdt-tool
   podman build -f Dockerfile.ubi7 -t avaya-pdt-ubi7:latest .
   ```

3. **Export the container image to a tar file:**
   ```bash
   podman save -o avaya-pdt-ubi7.tar avaya-pdt-ubi7:latest
   ```

4. **Optional: Compress the tar file to save space:**
   ```bash
   gzip avaya-pdt-ubi7.tar
   # This creates avaya-pdt-ubi7.tar.gz
   ```

5. **Verify the export:**
   ```bash
   ls -lh avaya-pdt-ubi7.tar*
   # Should show the exported file(s)
   ```

## Part 2: Transfer to Offline System

### Transfer Methods

Choose the method that works for your environment:

#### Method 1: USB Drive
```bash
# Copy to USB drive
cp avaya-pdt-ubi7.tar.gz /media/usb-drive/

# On offline system, copy from USB
cp /media/usb-drive/avaya-pdt-ubi7.tar.gz /tmp/
```

#### Method 2: Network Transfer (if limited network access)
```bash
# Using SCP (if SSH access available)
scp avaya-pdt-ubi7.tar.gz user@offline-system:/tmp/

# Using rsync
rsync -av avaya-pdt-ubi7.tar.gz user@offline-system:/tmp/
```

#### Method 3: CD/DVD
```bash
# Burn to disc or copy to mounted disc
```

## Part 3: Deploy on Offline System

### Prerequisites for Offline System
- RHEL 9 with Podman installed
- The transferred container tar file
- Project source code (CSV files, etc.)

### Steps on Offline System

1. **Install Podman (if not already installed):**
   ```bash
   # If you have access to RHEL repositories
   sudo dnf install -y podman

   # If completely offline, you'll need to install from RPM files
   # (See "Completely Offline Setup" section below)
   ```

2. **Import the container image:**
   ```bash
   # If you compressed the file
   gunzip avaya-pdt-ubi7.tar.gz

   # Import the image
   podman load -i avaya-pdt-ubi7.tar
   ```

3. **Verify the image was imported:**
   ```bash
   podman images | grep avaya-pdt
   ```

4. **Run the container:**
   ```bash
   # Navigate to your project directory with CSV files
   cd /path/to/avaya-1100-pdt-tool

   # Run the container
   podman run -it --rm \
     --network host \
     -v $(pwd):/app:Z \
     -v $(pwd)/output:/app/output:Z \
     avaya-pdt-ubi7:latest \
     python3 pdt_tool.py -f sample.csv
   ```

## Completely Offline Setup

If your offline system has no package repositories, you'll need to also transfer Podman:

### On Online System - Prepare Podman RPMs

1. **Download Podman and dependencies:**
   ```bash
   # Create directory for RPMs
   mkdir podman-rpms
   cd podman-rpms

   # Download podman and all dependencies
   sudo dnf download --resolve --alldeps podman

   # Also download podman-compose if needed
   sudo dnf download --resolve --alldeps podman-compose
   ```

2. **Transfer RPMs along with container:**
   ```bash
   tar -czf offline-deployment.tar.gz avaya-pdt-ubi7.tar podman-rpms/
   ```

### On Offline System - Install Podman

1. **Extract and install:**
   ```bash
   tar -xzf offline-deployment.tar.gz

   # Install Podman RPMs
   sudo rpm -ivh podman-rpms/*.rpm

   # Or use dnf localinstall
   sudo dnf localinstall podman-rpms/*.rpm
   ```

## Alternative: Container Bundle Approach

For maximum portability, you can create a complete bundle:

### Create Deployment Bundle

```bash
#!/bin/bash
# create-offline-bundle.sh

# Create bundle directory
mkdir -p avaya-pdt-offline-bundle

# Copy project files
cp -r . avaya-pdt-offline-bundle/project/

# Export container
podman save -o avaya-pdt-offline-bundle/avaya-pdt-ubi7.tar avaya-pdt-ubi7:latest

# Create deployment script
cat > avaya-pdt-offline-bundle/deploy.sh << 'EOF'
#!/bin/bash
echo "Deploying Avaya PDT Tool..."

# Import container
podman load -i avaya-pdt-ubi7.tar

# Make run script executable
chmod +x project/run-pdt-podman.sh

echo "Deployment complete!"
echo "Usage: cd project && ./run-pdt-podman.sh sample.csv"
EOF

chmod +x avaya-pdt-offline-bundle/deploy.sh

# Create archive
tar -czf avaya-pdt-offline-bundle.tar.gz avaya-pdt-offline-bundle/

echo "Offline bundle created: avaya-pdt-offline-bundle.tar.gz"
```

### Deploy Bundle on Offline System

```bash
# Extract bundle
tar -xzf avaya-pdt-offline-bundle.tar.gz
cd avaya-pdt-offline-bundle

# Run deployment
./deploy.sh

# Use the tool
cd project
./run-pdt-podman.sh sample.csv
```

## Updating the Offline Container

When you need to update:

1. **On online system:** Rebuild and export new version
2. **Transfer new tar file** to offline system
3. **On offline system:** Remove old image and import new one

```bash
# Remove old image
podman rmi avaya-pdt-ubi7:latest

# Import new image
podman load -i avaya-pdt-ubi7-new.tar
```

## Storage Considerations

- **Container image size:** ~500MB-1GB (typical for UBI 7 + Python dependencies)
- **Compressed size:** ~200-400MB (depending on compression)
- **Transfer time:** Varies by method (USB ~1-2 minutes, network depends on bandwidth)

## Security Notes

- Container images are read-only and immutable
- No additional security risks from offline deployment
- Same network isolation and SELinux protections apply
- Verify checksums if transferring over untrusted networks:

```bash
# On online system
sha256sum avaya-pdt-ubi7.tar.gz > checksum.txt

# On offline system
sha256sum -c checksum.txt
```

This approach gives you complete control over your deployment while maintaining security and functionality.