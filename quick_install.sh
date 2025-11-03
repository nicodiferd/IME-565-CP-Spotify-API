#!/bin/bash
# Quick minimal installation for Python 3.14 (use pre-built wheels only)

set -e

echo "Installing minimal dependencies (pre-built wheels only)..."

pip install --upgrade pip setuptools wheel

# Core packages with --only-binary to force pre-built wheels
pip install --only-binary=:all: \
    numpy \
    pandas \
    matplotlib \
    seaborn \
    plotly \
    scipy \
    scikit-learn \
    spotipy \
    streamlit \
    python-dotenv \
    jupyter \
    notebook \
    ipython || {
    echo ""
    echo "⚠️  Some packages don't have pre-built wheels for Python 3.14"
    echo "Please use Python 3.12 instead:"
    echo ""
    echo "  deactivate"
    echo "  rm -rf venv"
    echo "  python3.12 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  bash install_deps.sh"
    exit 1
}

echo ""
echo "✓ Installation complete!"
