#!/usr/bin/env bash
set -e

echo ">>> Configuring Environment"
export DEBIAN_FRONTEND=noninteractive
export TZ=Europe/Rome

echo ">>> Installing Required Packages"
apt-get update
apt-get install -y --no-install-recommends \
    tzdata \
    ffmpeg \
    python3 \
    curl \
    ca-certificates \
    git \
    openssh-client \
    xz-utils

ln -fs /usr/share/zoneinfo/Europe/Rome /etc/localtime
dpkg-reconfigure --frontend noninteractive tzdata

echo ">>> Cleaning"
apt-get clean
rm -rf /var/lib/apt/lists/*

echo ">>> Checking Tools"
ffmpeg -version | head -n 1
ffprobe -version | head -n 1
python3 --version

echo ">>> Setup Completed!"