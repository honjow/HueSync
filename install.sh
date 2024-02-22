#!/bin/bash

# check if jq is installed
if ! [ -x "$(command -v jq)" ]; then
  echo 'Error: jq is not installed.' >&2
  exit 1
fi

# Download latest release
RELEASE=$(curl -s 'https://api.github.com/repos/honjow/HueSync/releases/latest')
RELEASE_VERSION=$(echo "$RELEASE" | jq -r '.tag_name')
RELEASE_URL=$(echo "$RELEASE" | jq -r '.assets[0].browser_download_url')
curl -L -o /tmp/HueSync.tar.gz "$RELEASE_URL"

echo "Installing HueSync $RELEASE_VERSION"

# remove old version
chmod -R 777 ${HOME}/homebrew/plugins
rm -rf ${HOME}/homebrew/plugins/ayaled
rm -rf ${HOME}/homebrew/plugins/HueSync

# Extract
tar -xzf /tmp/HueSync.tar.gz -C ${HOME}/homebrew/plugins

# Cleanup
rm -f /tmp/HueSync.tar.gz

echo "HueSync $RELEASE_VERSION installed"

# restart plugin_loader
sudo systemctl restart plugin_loader.service
