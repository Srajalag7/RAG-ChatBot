"""
Vercel-compatible API handler for GitLab ChatBot
"""
import sys
import os
from pathlib import Path

# Add the parent directory to Python path so we can import from app
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Import the FastAPI app
from app.main import app

# Vercel expects the ASGI app to be available as 'app'
# This is the standard way to expose FastAPI apps on Vercel
