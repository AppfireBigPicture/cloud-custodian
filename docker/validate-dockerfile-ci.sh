#!/bin/bash

# Dockerfile validation script for Ubuntu 22.04
# Performs linting, security scanning, build verification, and layer analysis.

set -e  # Exit immediately on error

# Configuration
DOCKERFILE="Dockerfile"
IMAGE_NAME="validated-image:latest"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Ensure required tools are installed
install_dependencies() {
    echo "🔍 Checking required tools..."

    if ! command_exists hadolint; then
        echo "⚙️ Installing Hadolint..."
        wget -qO /usr/local/bin/hadolint https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64
        chmod +x /usr/local/bin/hadolint
    fi

    if ! command_exists trivy; then
        echo "⚙️ Installing Trivy..."
        sudo apt update && sudo apt install -y trivy
    fi

    if ! command_exists dive; then
        echo "⚙️ Installing Dive..."
        sudo add-apt-repository -y ppa:wagoodman/dive
        sudo apt update && sudo apt install -y dive
    fi

    echo "✅ All dependencies are installed."
}

# Lint Dockerfile
lint_dockerfile() {
    echo "🔍 Linting Dockerfile..."
    hadolint "$DOCKERFILE" || { echo "❌ Hadolint found issues!"; exit 1; }
    echo "✅ Dockerfile is clean."
}

# Build Docker image
build_docker_image() {
    echo "🔨 Building Docker image..."
    DOCKER_BUILDKIT=1 docker build -t "$IMAGE_NAME" -f "$DOCKERFILE" . || { echo "❌ Build failed!"; exit 1; }
    echo "✅ Image built successfully."
}

# Scan image for vulnerabilities
scan_image() {
    echo "🛡️ Scanning image for vulnerabilities..."
    trivy image "$IMAGE_NAME" || { echo "❌ Security issues detected!"; exit 1; }
    echo "✅ No critical vulnerabilities found."
}

# Analyze image layers
analyze_layers() {
    echo "🔍 Analyzing image layers..."
    dive "$IMAGE_NAME" || { echo "❌ Inefficient layers detected!"; exit 1; }
    echo "✅ Image layers are optimized."
}

# Run all checks
main() {
    install_dependencies
    lint_dockerfile
    build_docker_image
    scan_image
    analyze_layers
    echo "🎉 Dockerfile validation complete!"
}

main
