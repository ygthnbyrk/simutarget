#!/bin/bash
# SimuTarget.ai Quick Start Script

echo "🎯 SimuTarget.ai Setup"
echo "======================"

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
echo "Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Copy env file if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OPENAI_API_KEY"
echo "2. Start Qdrant: docker-compose up -d qdrant"
echo "3. Run API: uvicorn src.api.main:app --reload"
echo ""
echo "API will be available at http://localhost:8000/docs"
