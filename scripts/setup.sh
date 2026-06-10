#!/bin/bash
set -e

echo "=== Gravit Epistemic Verifier - Setup Script ==="

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$python_version" < "3.10" ]]; then
    echo "Error: Python 3.10+ required. Found: $python_version"
    exit 1
fi
echo "✓ Python $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install -r examples/requirements.txt

# Install development dependencies
pip install pytest pytest-cov black ruff mypy

# Download models
echo "Downloading ML models..."
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print('✓ Model downloaded')
"

# Create necessary directories
mkdir -p logs proofs benchmarks/results

# Check Docker
if command -v docker &> /dev/null; then
    echo "✓ Docker found"
else
    echo "⚠ Docker not found - install for containerized deployment"
fi

# Run initial tests
echo "Running initial tests..."
pytest tests/ -v --tb=short

echo ""
echo "=== Setup Complete ==="
echo "Activate environment: source venv/bin/activate"
echo "Run tests: pytest tests/ -v"
