#!/usr/bin/env python3
"""
Simple ChromaDB Server Startup Script
"""
import os
import sys
import uvicorn
from pathlib import Path

def start_chromadb_server():
    """Start ChromaDB server with proper configuration"""
    
    # Set up paths
    data_dir = Path("./chroma_data")
    data_dir.mkdir(exist_ok=True)
    
    print("🚀 Starting ChromaDB Server...")
    print("=" * 50)
    print(f"📊 Configuration:")
    print(f"   Host: localhost")
    print(f"   Port: 8002")
    print(f"   Data Directory: {data_dir.absolute()}")
    print("=" * 50)
    
    try:
        # Import ChromaDB components
        import chromadb
        from chromadb.config import Settings
        
        # Create settings
        settings = Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            persist_directory=str(data_dir.absolute()),
            is_persistent=True
        )
        
        print("✅ ChromaDB settings configured")
        
        # Try to create a simple persistent client first to test
        test_client = chromadb.PersistentClient(path=str(data_dir.absolute()))
        collections = test_client.list_collections()
        print(f"✅ Local ChromaDB working - {len(collections)} collections found")
        
        # Now try to start the server
        try:
            from chromadb.server.fastapi import FastAPI
            
            # Create the FastAPI app
            app = FastAPI(settings)
            print("✅ ChromaDB FastAPI app created")
            
            # Get the actual FastAPI app instance
            fastapi_app = app.app()
            
            print("🔄 Starting HTTP server...")
            
            # Start the server
            uvicorn.run(
                fastapi_app,
                host="localhost",
                port=8002,
                log_level="info"
            )
            
        except Exception as server_error:
            print(f"❌ Server startup failed: {server_error}")
            print("💡 The local persistent client is working fine though!")
            return False
            
    except Exception as e:
        print(f"❌ ChromaDB initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    start_chromadb_server()
