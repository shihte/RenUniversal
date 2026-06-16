#!/bin/bash
# ==============================================================================
# RenUniversal Website Deployment & Preview Script
# ==============================================================================
# Usage:
#   ./deploy_website.sh --preview     - Start local preview server on port 8081
#   ./deploy_website.sh --push        - Deploy to GitHub Pages (gh-pages branch)
# ==============================================================================

set -e

WEBSITE_DIR="website"
DEPLOY_BRANCH="gh-pages"

# Check if directory exists
if [ ! -d "$WEBSITE_DIR" ]; then
    echo "Error: Website source directory '$WEBSITE_DIR' not found."
    exit 1
fi

if [ "$1" == "--preview" ]; then
    echo "=== Starting Local Website Preview Server ==="
    echo "URL: http://localhost:8081"
    echo "Press Ctrl+C to stop the server."
    echo "============================================="
    python3 -m http.server 8081 --directory "$WEBSITE_DIR"
    exit 0
fi

if [ "$1" == "--push" ]; then
    echo "=== Starting GitHub Pages Deployment ==="
    
    # Verify we are in a Git repo
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "Error: Not in a Git repository."
        exit 1
    fi
    
    # Get current repository origin URL
    REMOTE_URL=$(git config --get remote.origin.url || true)
    if [ -z "$REMOTE_URL" ]; then
        REMOTE_URL="git@github.com:shihte/RenUniversal.git"
    fi
    
    echo "Target Remote: $REMOTE_URL"
    echo "Target Branch: $DEPLOY_BRANCH"
    
    # Create temp workspace
    TEMP_WORKSPACE=$(mktemp -d)
    echo "Created temp workspace: $TEMP_WORKSPACE"
    
    # Copy assets
    cp -R "$WEBSITE_DIR"/* "$TEMP_WORKSPACE/"
    
    # Init temp repo and push
    cd "$TEMP_WORKSPACE"
    git init
    git checkout -b "$DEPLOY_BRANCH"
    git config user.name "RenUniversal Deployer"
    git config user.email "deploy@renuniversal.io"
    
    git add .
    git commit -m "Deploy website: $(date)"
    
    echo "Pushing changes to $DEPLOY_BRANCH branch..."
    git push --force "$REMOTE_URL" "$DEPLOY_BRANCH"
    
    # Clean up
    cd - >/dev/null
    rm -rf "$TEMP_WORKSPACE"
    
    echo "✓ Website successfully deployed to $DEPLOY_BRANCH!"
    exit 0
fi

# Default help output
echo "RenUniversal Website Helper"
echo "---------------------------"
echo "Options:"
echo "  ./deploy_website.sh --preview    - Launch local server at http://localhost:8081"
echo "  ./deploy_website.sh --push       - Build and deploy to GitHub Pages branch"
echo ""
exit 1
