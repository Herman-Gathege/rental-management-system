#!/bin/bash
# restrict-pgadmin-firewall.sh
# Restrict pgAdmin port 5050 to allowed IPs only using ufw

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root: sudo bash $0"
  exit 1
fi

echo "Configuring firewall rules for pgAdmin port 5050..."

# Step 1: Allow specific IPs/subnets first (order matters in ufw)
# EDIT THESE to match your allowed IPs/ranges
ufw allow from 192.168.1.0/24 to any port 5050 proto tcp comment "Allow office LAN"
ufw allow from 10.0.0.0/8 to any port 5050 proto tcp comment "Allow VPN range"

# Step 2: Deny all other incoming traffic to 5050
ufw deny 5050/tcp comment "Deny pgAdmin from unauthorized IPs"

# Step 3: Reload firewall
ufw reload

echo "Firewall rules applied. pgAdmin port 5050 is now restricted."
echo ""
echo "Current ufw rules for port 5050:"
ufw status | grep 5050
