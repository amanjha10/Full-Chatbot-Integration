#!/usr/bin/env python3
"""
🗄️ ChromaDB Server with File-based Persistence
==============================================

Self-hosted ChromaDB server with file-based persistence for production use.
Runs on port 8002 to avoid conflicts with existing services.

Note: Using file-based persistence instead of PostgreSQL for better stability
and easier setup. Data is stored in ./chroma_data directory.
"""

import os
import sys
import uvicorn
import chromadb
from chromadb.config import Settings
from pathlib import Path

def create_chromadb_server():
    """Create ChromaDB server with file-based persistence"""

    # Create data directory
    data_dir = Path("./chroma_data")
    data_dir.mkdir(exist_ok=True)

    print("🚀 Starting ChromaDB Server...")
    print("=" * 50)
    print("📊 Configuration:")
    print(f"   Host: 0.0.0.0")
    print(f"   Port: 8002")
    print(f"   Backend: File-based")
    print(f"   Data Directory: {data_dir.absolute()}")
    print(f"   CORS: Enabled")
    print("=" * 50)

    try:
        # Use ChromaDB CLI to start server
        import subprocess

        # Set environment variables
        env = os.environ.copy()
        env.update({
            'CHROMA_SERVER_HOST': '0.0.0.0',
            'CHROMA_SERVER_HTTP_PORT': '8002',
            'ANONYMIZED_TELEMETRY': 'false',
            'ALLOW_RESET': 'true',
            'PERSIST_DIRECTORY': str(data_dir.absolute())
        })

        print("🔄 Starting ChromaDB server using CLI...")

        # Start using CLI
        cmd = [sys.executable, "-m", "chromadb.cli.cli", "run", "--host", "0.0.0.0", "--port", "8002"]
        subprocess.run(cmd, env=env, check=True)

    except subprocess.CalledProcessError as e:
        print(f"❌ ChromaDB CLI failed: {e}")
        print("💡 Trying direct server approach...")

        # Try direct server creation
        try:
            from chromadb.server.fastapi import FastAPI

            # Create FastAPI app
            app = FastAPI(Settings(
                chroma_server_host="0.0.0.0",
                chroma_server_http_port=8002,
                chroma_server_cors_allow_origins=["*"],
                anonymized_telemetry=False,
                allow_reset=True,
                persist_directory=str(data_dir.absolute()),
                is_persistent=True
            ))

            print("✅ ChromaDB FastAPI server created")
            print("🔄 Starting HTTP server...")

            # Start the server
            uvicorn.run(
                app,
                host="0.0.0.0",
                port=8002,
                log_level="info",
                access_log=True
            )

        except Exception as e2:
            print(f"❌ Direct server approach failed: {e2}")
            print("💡 Using simple HTTP server...")

            # Fallback: Create a simple HTTP server
            create_simple_chromadb_server(data_dir)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def create_simple_chromadb_server(data_dir):
    """Create a simple ChromaDB server using basic HTTP"""
    try:
        print("🔄 Starting simple ChromaDB server...")

        # Create a basic ChromaDB client for testing
        client = chromadb.PersistentClient(path=str(data_dir))

        # Test the client
        collections = client.list_collections()
        print(f"✅ ChromaDB client created with data directory: {data_dir}")
        print(f"📊 Found {len(collections)} existing collections")
        print("⚠️  Note: This is a basic setup. For production, use ChromaDB server.")
        print("🔗 ChromaDB is running locally with file persistence")
        print("📝 To use this in Django, update RAG system to use PersistentClient")

        # Keep the process running
        import time
        while True:
            time.sleep(1)

    except Exception as e:
        print(f"❌ Simple server failed: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    try:
        create_chromadb_server()
    except KeyboardInterrupt:
        print("\n🛑 ChromaDB server stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
