#!/bin/bash

# Installation script for Spotify Analytics dependencies
# Run with: bash install_deps.sh

set -e  # Exit on error

echo "Installing core dependencies..."

# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install core data science packages
echo "Installing numpy and pandas..."
pip install numpy==1.26.4
pip install pandas==2.2.2

# Install visualization libraries
echo "Installing visualization libraries..."
pip install matplotlib==3.9.0
pip install seaborn==0.13.2
pip install plotly==5.22.0

# Install scientific computing
echo "Installing scipy and scikit-learn..."
pip install scipy==1.13.0
pip install scikit-learn==1.5.0

# Install Spotify API
echo "Installing Spotipy..."
pip install spotipy==2.24.0

# Install Streamlit
echo "Installing Streamlit..."
pip install streamlit==1.38.0

# Install utilities
echo "Installing utilities..."
pip install python-dotenv==1.0.1

# Install Jupyter
echo "Installing Jupyter..."
pip install jupyter==1.0.0
pip install notebook==7.2.0
pip install ipython==8.25.0

echo ""
echo "✓ Installation complete!"
echo ""
echo "To verify, run: python -c 'import pandas, numpy, matplotlib, seaborn, plotly; print(\"All packages imported successfully!\")'"
