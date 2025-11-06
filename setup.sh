#!/bin/bash
set -e

# Install system dependencies for SPI and display libraries
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-dev

# Note: User must enable SPI via raspi-config manually
echo "Remember to enable SPI: sudo raspi-config -> Interface Options -> SPI -> Enable"
