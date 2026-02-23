#!/bin/bash

# Clone only the chirp directory from the repository
REPO_URL="https://github.com/kk7ds/chirp"
TARGET_DIR="chirp"

# Create a temporary directory for the sparse checkout
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Initialize git repository
git init
git remote add origin "$REPO_URL"

# Enable sparse checkout
git config core.sparseCheckout true

# Specify which directory to checkout
echo "$TARGET_DIR/" >> .git/info/sparse-checkout

# Pull the specific directory
git pull origin master

# Move the chirp directory to the original location
mv "$TARGET_DIR" "$OLDPWD/"

# Clean up
cd "$OLDPWD"
rm -rf "$TEMP_DIR"

echo "Successfully cloned $TARGET_DIR directory to $(pwd)/$TARGET_DIR"
