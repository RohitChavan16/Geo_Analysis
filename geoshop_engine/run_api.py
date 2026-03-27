#!/usr/bin/env python3
"""
GeoShop Engine API Server

Starts the FastAPI server for the GeoShop Engine.
"""

import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Start the FastAPI server."""
    port = int(os.getenv("APP_PORT", 8000))
    host = os.getenv("APP_HOST", "0.0.0.0")

    print("🚀 Starting GeoShop Engine API Server")
    print(f"📍 Server will be available at: http://localhost:{port}")
    print(f"📖 API documentation at: http://localhost:{port}/docs")
    print()

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )

if __name__ == "__main__":
    main()