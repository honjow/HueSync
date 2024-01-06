#!/bin/bash

# check if jq is installed
if ! [ -x "$(command -v jq)" ]; then
  echo 'Error: jq is not installed.' >&2
  exit 1
fi

# Download latest release
RELEASE=$(curl -s 'https://api.github.com/repos/honjow/ayaled/releases/latest')
RELEASE_VERSION=$(echo "$RELEASE" | jq -r '.tag_name')
RELEASE_URL=$(echo "$RELEASE" | jq -r '.assets[0].browser_download_url')
curl -L -o /tmp/ayaled.tar.gz "$RELEASE_URL"

echo "Installing ayaled $RELEASE_VERSION"

# remove old version
chmod -R 777 ${HOME}/homebrew/plugins
rm -rf ${HOME}/homebrew/plugins/ayaled

# Extract
tar -xzf /tmp/ayaled.tar.gz -C ${HOME}/homebrew/plugins

# Cleanup
rm -f /tmp/ayaled.tar.gz

echo "ayaled $RELEASE_VERSION installed"

# restart plugin_loader
sudo systemctl restart plugin_loader.service
