#!/bin/bash

# 🍯 Honeypot API Quick Start Script
# This script automates the setup process

set -e  # Exit on error

echo "🍯 =========================================="
echo "   Honeypot API Quick Start Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "📌 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Please install Python 3.9 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Found Python ${PYTHON_VERSION}${NC}"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi
echo ""

# Setup environment variables
echo "🔑 Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️  .env file created from template${NC}"
    echo ""
    echo "⚠️  IMPORTANT: You need to update .env with your API keys:"
    echo ""
    echo "1. GROQ_API_KEY - Get from: https://console.groq.com/keys"
    echo "2. HONEYPOT_API_KEY - Generate a secure random key"
    echo ""
    echo "Generating a secure HONEYPOT_API_KEY for you..."
    
    # Generate secure API key
    HONEYPOT_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your-secret-honeypot-key-12345/${HONEYPOT_KEY}/" .env
    else
        # Linux
        sed -i "s/your-secret-honeypot-key-12345/${HONEYPOT_KEY}/" .env
    fi
    
    echo -e "${GREEN}✅ Generated HONEYPOT_API_KEY: ${HONEYPOT_KEY}${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  You still need to add your GROQ_API_KEY to .env file${NC}"
    echo ""
    
    read -p "Press Enter to open .env file for editing..."
    
    # Open .env in default editor
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open .env
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        ${EDITOR:-nano} .env
    else
        notepad .env
    fi
    
    echo ""
    read -p "Have you added your GROQ_API_KEY to .env? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Please add your GROQ_API_KEY to .env and run this script again${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi
echo ""

# Verify Groq API key is set
source .env
if [ -z "$GROQ_API_KEY" ] || [ "$GROQ_API_KEY" == "gsk_your_groq_api_key_here" ]; then
    echo -e "${RED}❌ GROQ_API_KEY not set in .env file${NC}"
    echo "Please get your API key from: https://console.groq.com/keys"
    exit 1
fi

echo -e "${GREEN}✅ Environment variables configured${NC}"
echo ""

# Test if Groq API key is valid (optional)
echo "🧪 Testing Groq API connection..."
python3 -c "
from groq import Groq
import os
try:
    client = Groq(api_key='${GROQ_API_KEY}')
    response = client.chat.completions.create(
        messages=[{'role': 'user', 'content': 'test'}],
        model='llama-3.3-70b-versatile',
        max_tokens=5
    )
    print('✅ Groq API connection successful')
except Exception as e:
    print(f'❌ Groq API connection failed: {e}')
    exit(1)
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Groq API is working${NC}"
else
    echo -e "${RED}❌ Groq API connection failed${NC}"
    echo "Please check your GROQ_API_KEY in .env file"
    exit 1
fi
echo ""

# Ask user if they want to start the server
echo "🚀 Setup complete!"
echo ""
echo "Your API keys:"
echo "  HONEYPOT_API_KEY: ${HONEYPOT_API_KEY}"
echo "  GROQ_API_KEY: ${GROQ_API_KEY:0:20}..."
echo ""
read -p "Would you like to start the server now? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting Honeypot API server..."
    echo "Server will be available at: http://localhost:8000"
    echo "API Documentation: http://localhost:8000/docs"
    echo "Health Check: http://localhost:8000/health"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    python3 main.py
else
    echo ""
    echo "To start the server manually, run:"
    echo "  python3 main.py"
    echo ""
    echo "Or using uvicorn:"
    echo "  uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    echo ""
    echo "Next steps:"
    echo "  1. Start the server"
    echo "  2. Test with: python3 test_api.py"
    echo "  3. Deploy to Railway/Render/Fly.io"
    echo "  4. Submit to GUVI hackathon"
    echo ""
    echo -e "${GREEN}✅ Setup complete! Good luck with the hackathon! 🎉${NC}"
fi