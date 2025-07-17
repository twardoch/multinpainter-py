#!/bin/bash
# this_file: scripts/dev-setup.sh

set -e

echo "🔧 Setting up development environment for multinpainter..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
python3 -m pip install --upgrade pip

# Install package in development mode with testing dependencies
echo "📦 Installing package in development mode..."
python3 -m pip install -e .[testing]

# Install additional development tools
echo "🛠️  Installing development tools..."
python3 -m pip install black flake8 mypy pre-commit

# Install pre-commit hooks if .pre-commit-config.yaml exists
if [ -f ".pre-commit-config.yaml" ]; then
    echo "🪝 Installing pre-commit hooks..."
    pre-commit install
fi

echo "✅ Development environment setup complete!"
echo "🚀 To activate the environment: source venv/bin/activate"
echo "🧪 To run tests: ./scripts/test.sh"
echo "🔧 To build: ./scripts/build.sh"