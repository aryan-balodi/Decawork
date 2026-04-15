#!/bin/bash
# IT Agent: VPS Setup Script
# Run this on your AWS t2.micro or GCP e2-micro instance to prepare it for deployment.

set -e

echo "🚀 Starting VPS Setup..."

# 1. Create a 2GB Swapfile (CRITICAL for 1GB RAM instances so Chromium doesn't crash)
if [ -f /swapfile ]; then
    echo "✅ Swapfile already exists."
else
    echo "🛠 Creating 2GB Swapfile..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    
    # Make swap permanent across reboots
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "✅ Swapfile created and enabled!"
fi

# 2. Install Docker and Docker Compose
echo "🛠 Installing Docker environment..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Setup proper repository
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-compose

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add current user to docker group (so you don't need 'sudo docker')
sudo usermod -aG docker $USER

echo "✅ Docker installed successfully."
echo ""
echo "🎉 Setup Complete! Next steps:"
echo "1. Run 'newgrp docker' or log out and log back in to apply Docker permissions."
echo "2. Add your environment variables to a '.env' file."
echo "3. Run 'docker-compose up -d' to start the agent!"
