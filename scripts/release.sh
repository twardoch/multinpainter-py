#!/bin/bash
# this_file: scripts/release.sh

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.2.3"
    exit 1
fi

VERSION=$1

echo "🚀 Preparing release for version $VERSION"

# Validate version format (basic semver check)
if [[ ! $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][a-zA-Z0-9]+)*$ ]]; then
    echo "❌ Invalid version format. Use semantic versioning (e.g., 1.2.3)"
    exit 1
fi

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  You are not on the main branch. Current branch: $CURRENT_BRANCH"
    read -p "Do you want to continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Release cancelled"
        exit 1
    fi
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Working directory is not clean. Please commit or stash changes first."
    git status --short
    exit 1
fi

# Run tests
echo "🧪 Running tests before release..."
./scripts/test.sh

# Run build
echo "🔧 Building package..."
./scripts/build.sh

# Create and push git tag
echo "🏷️  Creating git tag v$VERSION"
git tag -a "v$VERSION" -m "Release version $VERSION"

echo "📤 Pushing tag to origin..."
git push origin "v$VERSION"

echo "✅ Release $VERSION completed!"
echo "🔍 Check GitHub Actions for automated release process"
echo "📦 GitHub Release will be created automatically with binaries"