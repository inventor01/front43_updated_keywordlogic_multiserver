"""
Trading settings and configuration management
"""

import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import os

logger = logging.getLogger(__name__)

@dataclass
class TradingSettings:
    """Trading configuration settings"""
    max_slippage: float = 5.0  # Maximum slippage percentage
    default_amount: float = 0.01  # Default SOL amount to trade
    gas_fee: float = 0.001  # Gas fee in SOL
    priority_fee: int = 100000  # Priority fee in lamports
    auto_approve: bool = False  # Auto-approve trades
    stop_loss_percentage: float = 10.0  # Stop loss percentage
    take_profit_percentage: float = 50.0  # Take profit percentage
    max_daily_trades: int = 10  # Maximum trades per day
    min_liquidity: float = 1000.0  # Minimum liquidity in USD
    enabled: bool = True  # Trading enabled/disabled

class TradingSettingsManager:
    """Manager for trading settings"""
    
    def __init__(self, settings_file: str = "trading_settings.json"):
        self.settings_file = settings_file
        self.default_settings = TradingSettings()
        self.user_settings: Dict[str, TradingSettings] = {}
        self.load_settings()
    
    def load_settings(self):
        """Load trading settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                
                for user_id, settings_dict in data.items():
                    self.user_settings[user_id] = TradingSettings(**settings_dict)
                
                logger.info(f"Loaded trading settings for {len(self.user_settings)} users")
            else:
                logger.info("No existing trading settings file found, using defaults")
                
        except Exception as e:
            logger.error(f"Error loading trading settings: {e}")
            self.user_settings = {}
    
    def save_settings(self):
        """Save trading settings to file"""
        try:
            data = {}
            for user_id, settings in self.user_settings.items():
                data[user_id] = asdict(settings)
            
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved trading settings for {len(self.user_settings)} users")
            
        except Exception as e:
            logger.error(f"Error saving trading settings: {e}")
    
    def get_user_settings(self, user_id: str) -> TradingSettings:
        """Get trading settings for a user"""
        if user_id not in self.user_settings:
            # Create default settings for new user
            self.user_settings[user_id] = TradingSettings()
            self.save_settings()
        
        return self.user_settings[user_id]
    
    def update_user_settings(self, user_id: str, **kwargs):
        """Update trading settings for a user"""
        settings = self.get_user_settings(user_id)
        
        # Update only provided fields
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
            else:
                logger.warning(f"Unknown setting: {key}")
        
        self.user_settings[user_id] = settings
        self.save_settings()
        
        logger.info(f"Updated trading settings for user {user_id}")
    
    def reset_user_settings(self, user_id: str):
        """Reset user settings to defaults"""
        self.user_settings[user_id] = TradingSettings()
        self.save_settings()
        logger.info(f"Reset trading settings for user {user_id}")
    
    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """Get all user settings as dictionaries"""
        return {user_id: asdict(settings) for user_id, settings in self.user_settings.items()}

# Global instance
trading_settings_manager = TradingSettingsManager()

def get_trading_settings(user_id: str) -> TradingSettings:
    """Convenience function to get user trading settings"""
    return trading_settings_manager.get_user_settings(user_id)

def update_trading_settings(user_id: str, **kwargs):
    """Convenience function to update user trading settings"""
    return trading_settings_manager.update_user_settings(user_id, **kwargs)