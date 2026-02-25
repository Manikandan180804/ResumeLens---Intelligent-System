#!/usr/bin/env bash
# Render build script
set -e

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

echo "==> Build complete!"
