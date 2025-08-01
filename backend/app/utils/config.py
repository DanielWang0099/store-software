"""
Configuration settings for the loyalty system
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Tienda Loyalty System"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./loyalty_system.db"
    
    # Receipt monitoring settings
    receipt_monitor_enabled: bool = True
    receipt_folder_path: str = "C:/Windows/System32/spool/PRINTERS"
    receipt_match_window_seconds: int = 30
    
    # WebSocket settings
    websocket_ping_interval: int = 20
    websocket_ping_timeout: int = 60
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # Loyalty points settings
    points_per_dollar: int = 1
    bonus_threshold_100: int = 10
    bonus_threshold_250: int = 25
    bonus_threshold_500: int = 50
    
    # Tablet UI settings
    tablet_idle_timeout_seconds: int = 30
    tablet_form_timeout_seconds: int = 120
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
settings = Settings()
