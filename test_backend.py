#!/usr/bin/env python
"""
Quick test script to verify the backend starts correctly
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_imports():
    """Test that all imports work correctly"""
    try:
        print("Testing imports...")
        
        # Test FastAPI import
        from fastapi import FastAPI
        print("✅ FastAPI import successful")
        
        # Test Socket.IO import
        import socketio
        print("✅ Socket.IO import successful")
        
        # Test our modules
        from app.models.database import init_db
        print("✅ Database module import successful")
        
        from app.services.websocket_manager import WebSocketManager
        print("✅ WebSocket manager import successful")
        
        from app.utils.config import Settings
        print("✅ Config import successful")
        
        # Test settings loading
        settings = Settings()
        print(f"✅ Settings loaded - Debug: {settings.debug}, Port: {settings.port}")
        
        # Test database initialization
        print("Testing database initialization...")
        await init_db()
        print("✅ Database initialization successful")
        
        print("\n🎉 All tests passed! The backend should start correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_imports())
    sys.exit(0 if success else 1)
