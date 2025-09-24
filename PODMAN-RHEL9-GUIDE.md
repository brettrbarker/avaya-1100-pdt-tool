# Running Avaya PDT Tool with Podman on RHEL 9

This guide provides instructions for running the Avaya 1100 PDT Tool in a RHEL UBI 7 container using Podman on RHEL 9.

## Prerequisites

1. **RHEL 9 system** with Podman installed
2. **Network access** to the Avaya phones you want to manage
3. **Root or sudo access** for container operations

## Install Podman (if not already installed)

```bash
sudo dnf install -y podman podman-compose
```

## Build and Run Instructions

### Method 1: Using Podman directly

1. **Clone or copy the project to your RHEL 9 system:**
   ```bash
   git clone <your-repo-url>
   cd avaya-1100-pdt-tool
   ```

2. **Build the container image:**
   ```bash
   podman build -f Dockerfile.ubi7 -t avaya-pdt-ubi7 .
   ```

3. **Run the container interactively:**
   ```bash
   podman run -it --rm \
     --network host \
     -v $(pwd):/app:Z \
     -v $(pwd)/output:/app/output:Z \
     --name avaya-pdt-tool \
     avaya-pdt-ubi7
   ```

4. **Inside the container, run the PDT tool:**
   ```bash
   cd /app
   python3 pdt_tool.py -f sample.csv
   ```

### Method 2: Using Podman Compose

1. **Build and run with compose:**
   ```bash
   podman-compose -f docker-compose.ubi7.yml up --build
   ```

2. **Execute the tool in the running container:**
   ```bash
   podman-compose -f docker-compose.ubi7.yml exec avaya-pdt-tool python3 pdt_tool.py -f sample.csv
   ```

### Method 3: One-liner for quick execution

```bash
podman run -it --rm --network host -v $(pwd):/app:Z avaya-pdt-ubi7 python3 pdt_tool.py -f sample.csv
```

## Important Podman-specific Notes

### SELinux Context
- The `:Z` flag in volume mounts automatically sets the correct SELinux context for container access
- This is crucial on RHEL 9 where SELinux is enforced by default

### Network Access
- `--network host` allows the container to access your network directly for SSH connections to Avaya phones
- This is necessary since the tool needs to SSH to phone IP addresses on your network

### File Permissions
- Output files created by the container will be owned by the container user
- You may need to adjust ownership after running:
  ```bash
  sudo chown -R $(id -u):$(id -g) output/
  ```

## Running as a Service (Optional)

If you want to run this as a systemd service, create a service file:

```bash
sudo tee /etc/systemd/system/avaya-pdt.service > /dev/null <<EOF
[Unit]
Description=Avaya PDT Tool Container
After=network-online.target
Wants=network-online.target

[Service]
Type=forking
RemainAfterExit=yes
WorkingDirectory=/path/to/avaya-1100-pdt-tool
ExecStart=/usr/bin/podman run -d --name avaya-pdt-tool --network host -v %i:/app:Z avaya-pdt-ubi7 tail -f /dev/null
ExecStop=/usr/bin/podman stop avaya-pdt-tool
ExecStopPost=/usr/bin/podman rm avaya-pdt-tool

[Install]
WantedBy=multi-user.target
EOF
```

Then enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable avaya-pdt.service
sudo systemctl start avaya-pdt.service
```

## Troubleshooting

### Container Build Issues
```bash
# Clean up build cache
podman system prune -a

# Rebuild with no cache
podman build --no-cache -f Dockerfile.ubi7 -t avaya-pdt-ubi7 .
```

### Network Connectivity Issues
```bash
# Test network connectivity from container
podman run -it --rm --network host avaya-pdt-ubi7 ping <phone-ip>

# Check if SSH port is accessible
podman run -it --rm --network host avaya-pdt-ubi7 telnet <phone-ip> 22
```

### Permission Issues
```bash
# Run with user namespace mapping
podman run -it --rm --userns=keep-id --network host -v $(pwd):/app:Z avaya-pdt-ubi7
```

### SELinux Issues
```bash
# Check SELinux denials
sudo ausearch -m avc -ts recent | grep podman

# Set SELinux to permissive (temporary)
sudo setenforce 0

# Re-enable after testing
sudo setenforce 1
```

## Example Usage Session

```bash
# 1. Build the container
podman build -f Dockerfile.ubi7 -t avaya-pdt-ubi7 .

# 2. Run interactively
podman run -it --rm --network host -v $(pwd):/app:Z avaya-pdt-ubi7

# 3. Inside container - run the tool
cd /app
python3 pdt_tool.py -f sample.csv

# 4. Follow the interactive menu to:
#    - Set SSH credentials for phones
#    - Choose actions (ping, screen grab, factory reset, etc.)
#    - View results in generated output files
```

## Output Files Location

All output files (logs, CSV exports, phone configs) will be saved to your host filesystem in:
- `./pdt-tool-logs/` - Log files
- `./phone-configs/` - Generated phone configuration files
- `./` - CSV export files

The files will persist after the container stops due to volume mounting.