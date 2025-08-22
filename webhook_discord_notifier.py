"""
Simple webhook Discord notifier for Railway deployment compatibility.
"""

import logging
import requests
import json
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class WebhookDiscordNotifier:
    """Simple Discord webhook notifier."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_notification(self, message: str, embed_data: Dict = None) -> bool:
        """Send notification via Discord webhook."""
        try:
            payload = {"content": message}
            
            if embed_data:
                payload["embeds"] = [embed_data]
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            return response.status_code == 204
            
        except Exception as e:
            logger.error(f"Failed to send Discord webhook: {e}")
            return False
    
    def send_token_notification(self, token_data: Dict, keyword: str = None) -> bool:
        """Send token notification with basic formatting."""
        try:
            name = token_data.get('name', 'Unknown Token')
            address = token_data.get('address', 'Unknown')
            
            message = f"🚨 **Token Alert**\n"
            message += f"**Name:** {name}\n"
            message += f"**Address:** `{address}`\n"
            
            if keyword:
                message += f"**Matched Keyword:** {keyword}\n"
            
            return self.send_notification(message)
            
        except Exception as e:
            logger.error(f"Failed to send token notification: {e}")
            return False