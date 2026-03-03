#!/usr/bin/env bash
set -e

echo ">>> Configuring Environment"
export DEBIAN_FRONTEND=noninteractive
export TZ=Europe/Rome
ln -fs /usr/share/zoneinfo/Europe/Rome /etc/localtime
apt-get update
apt-get install -y tzdata
dpkg-reconfigure --frontend noninteractive tzdata

echo ">>> Installing Required Packages"
apt-get update
apt-get install -y \
    ffmpeg \
    curl \
    ca-certificates \
    git \
    xz-utils

echo ">>> Cleaning"
apt-get clean
rm -rf /var/lib/apt/lists/*

echo ">>> Setup Completed!"
