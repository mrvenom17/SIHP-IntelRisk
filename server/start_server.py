#!/usr/bin/env python3
"""
Script to start the SIEM Server
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    try:
        import fastapi
        import uvicorn
        import pydantic
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Installing requirements...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ])
            print("✅ Requirements installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install requirements: {e}")
            return False

def check_environment():
    """Check if environment variables are set"""
    env_file = Path("..") / ".env"
    if env_file.exists():
        print("✅ .env file found")
        return True
    else:
        print("⚠️ .env file not found - some features may not work")
        return True

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting SIEM Server...")
    print("=" * 50)

    # Already in server directory

    # Check requirements
    if not check_requirements():
        return False

    # Check environment
    if not check_environment():
        return False

    print("📡 Starting server on http://localhost:8000")
    print("📋 API Documentation: http://localhost:8000/docs")
    print("🔗 Alternative docs: http://localhost:8000/redoc")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)

    try:
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False

    return True

if __name__ == "__main__":
    start_server()
