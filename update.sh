#!/bin/bash

# Update and publish script for ktml-agent
# This script updates the version in pyproject.toml and __init__.py,
# builds the package, and uploads it to PyPI

# Get new version from user
echo "Current version in pyproject.toml:"
grep "version = " pyproject.toml

read -p "Enter new version (e.g., 0.1.1): " NEW_VERSION

if [ -z "$NEW_VERSION" ]; then
    echo "❌ No version provided"
    exit 1
fi

# Update version in pyproject.toml
sed -i.bak "s/version = \"[0-9.]*\"/version = \"$NEW_VERSION\"/" pyproject.toml

# Update version in __init__.py (add __version__ if it doesn't exist)
if grep -q "__version__" src/ai_kernel/__init__.py; then
    sed -i.bak "s/__version__ = \"[0-9.]*\"/__version__ = \"$NEW_VERSION\"/" src/ai_kernel/__init__.py
else
    echo "__version__ = \"$NEW_VERSION\"" >> src/ai_kernel/__init__.py
fi

echo "✓ Updated version to $NEW_VERSION"

# Clean old builds
echo "Cleaning old builds..."
rm -rf build/ dist/ *.egg-info src/*.egg-info

# Build
echo "Building package..."
python -m build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

# Upload
echo "Uploading to PyPI..."
python -m twine upload dist/*

if [ $? -ne 0 ]; then
    echo "❌ Upload failed"
    exit 1
fi

echo "✅ Published version $NEW_VERSION to PyPI!"
echo "Users can install with: pip install ktml-agent"
echo "Users can update with: pip install --upgrade ktml-agent"

# Clean up backup files
rm -f pyproject.toml.bak src/ai_kernel/__init__.py.bak

echo "🎉 Done!"
