#!/bin/bash
# this_file: scripts/build.sh

set -e

echo "🔧 Building multinpainter..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ src/*.egg-info/

# Install build dependencies
echo "📦 Installing build dependencies..."
python3 -m pip install --upgrade pip build twine

# Build the package
echo "🏗️ Building source distribution and wheel..."
python3 -m build

# Verify the built packages
echo "✅ Verifying built packages..."
python3 -m twine check dist/*

echo "✅ Build complete! Artifacts are in the 'dist/' directory."
ls -la dist/