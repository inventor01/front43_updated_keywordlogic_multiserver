#!/usr/bin/env python3
"""
Configuration module for Pump.fun monitoring system
"""

import os
from typing import Optional

class Config:
    """Configuration class for system settings"""
    
    # Discord Configuration
    DISCORD_WEBHOOK_URL: str = os.getenv('DISCORD_WEBHOOK_URL', '')
    DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', os.getenv('DISCORD_BOT_TOKEN', ''))
    
    # API Configuration
    ALCHEMY_API_URL: str = os.getenv('ALCHEMY_API_URL', 'https://solana-mainnet.g.alchemy.com/v2/demo')
    BROWSERCAT_API_KEY: str = os.getenv('BROWSERCAT_API_KEY', '')
    
    # Monitoring Configuration
    SCRAPE_INTERVAL: float = float(os.getenv('SCRAPE_INTERVAL', '1.5'))
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    
    # File Paths
    WATCHLIST_FILE: str = os.getenv('WATCHLIST_FILE', 'watchlist.txt')
    LOG_FILE: str = os.getenv('LOG_FILE', 'pump_monitor.log')
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Rate Limiting
    RATE_LIMIT_DELAY: float = float(os.getenv('RATE_LIMIT_DELAY', '0.1'))
    
    # Memory Management
    MAX_SEEN_CONTRACTS: int = int(os.getenv('MAX_SEEN_CONTRACTS', '10000'))
    CLEANUP_INTERVAL: int = int(os.getenv('CLEANUP_INTERVAL', '3600'))
    
    # Detection Settings
    TOKEN_FRESHNESS_WINDOW: int = int(os.getenv('TOKEN_FRESHNESS_WINDOW', '180'))  # 3 minutes
    
    # PostgreSQL Database (Railway)
    DATABASE_URL: str = os.getenv('DATABASE_URL', '')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required_vars = ['DISCORD_WEBHOOK_URL']
        missing = [var for var in required_vars if not getattr(cls, var)]
        
        if missing:
            print(f"❌ Missing required environment variables: {missing}")
            return False
        
        return True
    
    @classmethod
    def get_database_config(cls) -> dict:
        """Get database configuration for Railway deployment"""
        if cls.DATABASE_URL:
            return {
                'database_url': cls.DATABASE_URL
            }
        return {}