"""
Trading Engine Stub - Disabled for Pure DexScreener Deployment
"""

class TradingEngine:
    def __init__(self):
        self.enabled = False
    
    def buy_token(self, *args, **kwargs):
        return {"success": False, "error": "Trading disabled in pure deployment"}
    
    def sell_token(self, *args, **kwargs):
        return {"success": False, "error": "Trading disabled in pure deployment"}

# Default trader instance (disabled)
trader = None
