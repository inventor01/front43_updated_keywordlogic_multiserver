"""
Universal Undo Manager for Token Monitoring System
Tracks user actions and provides undo functionality for Discord commands
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os

logger = logging.getLogger(__name__)

class UndoManager:
    def __init__(self, config_manager=None, link_sniper=None, max_history=50):
        """
        Initialize undo manager with references to system components
        
        Args:
            config_manager: ConfigManager instance for keyword operations
            link_sniper: LinkSniper instance for URL operations
            max_history: Maximum number of undo actions to track per user
        """
        self.config_manager = config_manager
        self.link_sniper = link_sniper
        self.max_history = max_history
        self.undo_file = "undo_history.json"
        self.user_history = self._load_history()
    
    def _load_history(self) -> Dict[str, List[Dict]]:
        """Load undo history from file"""
        try:
            if os.path.exists(self.undo_file):
                with open(self.undo_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load undo history: {e}")
        return {}
    
    def _save_history(self):
        """Save undo history to file"""
        try:
            with open(self.undo_file, 'w') as f:
                json.dump(self.user_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save undo history: {e}")
    
    def _cleanup_old_history(self, user_id: str):
        """Remove old history entries to maintain max_history limit"""
        if user_id in self.user_history:
            history = self.user_history[user_id]
            # Keep only the most recent entries
            self.user_history[user_id] = history[-self.max_history:]
            
            # Remove entries older than 24 hours
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.user_history[user_id] = [
                entry for entry in self.user_history[user_id]
                if datetime.fromisoformat(entry['timestamp']) > cutoff_time
            ]
    
    def record_action(self, user_id: str, action_type: str, action_data: Dict[str, Any]):
        """
        Record a user action for potential undo
        
        Args:
            user_id: Discord user ID
            action_type: Type of action (add_keyword, remove_keyword, add_url, remove_url, etc.)
            action_data: Data needed to undo the action
        """
        user_id = str(user_id)
        
        if user_id not in self.user_history:
            self.user_history[user_id] = []
        
        action_record = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'data': action_data
        }
        
        self.user_history[user_id].append(action_record)
        self._cleanup_old_history(user_id)
        self._save_history()
        
        logger.info(f"📝 Recorded undo action for user {user_id}: {action_type}")
    
    def get_last_action(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent action for a user"""
        user_id = str(user_id)
        
        if user_id not in self.user_history or not self.user_history[user_id]:
            return None
        
        return self.user_history[user_id][-1]
    
    def undo_last_action(self, user_id: str) -> Dict[str, Any]:
        """
        Undo the last action performed by a user
        
        Returns:
            Dictionary with success status and details
        """
        user_id = str(user_id)
        
        last_action = self.get_last_action(user_id)
        if not last_action:
            return {
                'success': False,
                'message': "❌ No recent actions to undo"
            }
        
        action_type = last_action['action_type']
        action_data = last_action['data']
        
        try:
            result = self._execute_undo(action_type, action_data)
            
            if result['success']:
                # Remove the undone action from history
                self.user_history[user_id].pop()
                self._save_history()
                logger.info(f"✅ Successfully undid action {action_type} for user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to undo action {action_type}: {e}")
            return {
                'success': False,
                'message': f"❌ Failed to undo action: {str(e)}"
            }
    
    def _execute_undo(self, action_type: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the undo operation based on action type"""
        
        if action_type == 'add_keywords':
            return self._undo_add_keywords(action_data)
        elif action_type == 'remove_keywords':
            return self._undo_remove_keywords(action_data)
        elif action_type == 'add_urls':
            return self._undo_add_urls(action_data)
        elif action_type == 'remove_urls':
            return self._undo_remove_urls(action_data)
        elif action_type == 'clear_keywords':
            return self._undo_clear_keywords(action_data)
        elif action_type == 'clear_all':
            return self._undo_clear_all(action_data)
        else:
            return {
                'success': False,
                'message': f"❌ Unknown action type: {action_type}"
            }
    
    def _undo_add_keywords(self, action_data: Dict) -> Dict[str, Any]:
        """Undo adding keywords"""
        added_keywords = action_data.get('added_keywords', [])
        
        if not added_keywords:
            return {'success': False, 'message': "❌ No keywords to remove"}
        
        removed_count = 0
        for keyword in added_keywords:
            if self.config_manager and hasattr(self.config_manager, 'remove_keyword') and self.config_manager.remove_keyword(keyword):
                removed_count += 1
        
        return {
            'success': True,
            'message': f"✅ **Undid Keyword Addition**\n\n🗑️ **Removed:** {removed_count} keywords\n• " + "\n• ".join(added_keywords)
        }
    
    def _undo_remove_keywords(self, action_data: Dict) -> Dict[str, Any]:
        """Undo removing keywords"""
        removed_keywords = action_data.get('removed_keywords', [])
        
        if not removed_keywords:
            return {'success': False, 'message': "❌ No keywords to restore"}
        
        added_count = 0
        for keyword in removed_keywords:
            if self.config_manager and hasattr(self.config_manager, 'add_keyword') and self.config_manager.add_keyword(keyword):
                added_count += 1
        
        return {
            'success': True,
            'message': f"✅ **Undid Keyword Removal**\n\n➕ **Restored:** {added_count} keywords\n• " + "\n• ".join(removed_keywords)
        }
    
    def _undo_add_urls(self, action_data: Dict) -> Dict[str, Any]:
        """Undo adding URLs"""
        if not self.link_sniper:
            return {'success': False, 'message': "❌ Link sniper not available"}
        
        user_id = action_data.get('user_id')
        added_urls = action_data.get('added_urls', [])
        
        if not added_urls:
            return {'success': False, 'message': "❌ No URLs to remove"}
        
        removed_count = 0
        for url in added_urls:
            if self.link_sniper.remove_link_config(user_id, url):
                removed_count += 1
        
        return {
            'success': True,
            'message': f"✅ **Undid URL Addition**\n\n🗑️ **Removed:** {removed_count} URLs\n• " + "\n• ".join([url[:50] + "..." if len(url) > 50 else url for url in added_urls])
        }
    
    def _undo_remove_urls(self, action_data: Dict) -> Dict[str, Any]:
        """Undo removing URLs"""
        if not self.link_sniper:
            return {'success': False, 'message': "❌ Link sniper not available"}
        
        user_id = action_data.get('user_id')
        removed_configs = action_data.get('removed_configs', [])
        
        if not removed_configs:
            return {'success': False, 'message': "❌ No URL configurations to restore"}
        
        added_count = 0
        for config in removed_configs:
            success = self.link_sniper.add_link_config(
                user_id=user_id,
                target_link=config['target_link'],
                max_market_cap=config.get('max_market_cap'),
                buy_amount=config.get('buy_amount', 0.01),
                notify_only=config.get('notify_only', True)
            )
            if success:
                added_count += 1
        
        urls = [config['target_link'] for config in removed_configs]
        return {
            'success': True,
            'message': f"✅ **Undid URL Removal**\n\n➕ **Restored:** {added_count} URL configurations\n• " + "\n• ".join([url[:50] + "..." if len(url) > 50 else url for url in urls])
        }
    
    def _undo_clear_keywords(self, action_data: Dict) -> Dict[str, Any]:
        """Undo clearing all keywords"""
        cleared_keywords = action_data.get('cleared_keywords', [])
        
        if not cleared_keywords:
            return {'success': False, 'message': "❌ No keywords to restore"}
        
        added_count = 0
        for keyword in cleared_keywords:
            if self.config_manager and hasattr(self.config_manager, 'add_keyword') and self.config_manager.add_keyword(keyword):
                added_count += 1
        
        return {
            'success': True,
            'message': f"✅ **Undid Clear Keywords**\n\n➕ **Restored:** {added_count} keywords\n• " + "\n• ".join(cleared_keywords)
        }
    
    def _undo_clear_all(self, action_data: Dict) -> Dict[str, Any]:
        """Undo clearing all keywords and URLs"""
        user_id = action_data.get('user_id')
        cleared_keywords = action_data.get('cleared_keywords', [])
        cleared_configs = action_data.get('cleared_configs', [])
        
        # Restore keywords
        keyword_count = 0
        for keyword in cleared_keywords:
            if self.config_manager and hasattr(self.config_manager, 'add_keyword') and self.config_manager.add_keyword(keyword):
                keyword_count += 1
        
        # Restore URLs
        url_count = 0
        if self.link_sniper:
            for config in cleared_configs:
                success = self.link_sniper.add_link_config(
                    user_id=user_id,
                    target_link=config['target_link'],
                    max_market_cap=config.get('max_market_cap'),
                    buy_amount=config.get('buy_amount', 0.01),
                    notify_only=config.get('notify_only', True)
                )
                if success:
                    url_count += 1
        
        return {
            'success': True,
            'message': f"✅ **Undid Clear All**\n\n➕ **Restored:** {keyword_count} keywords, {url_count} URLs"
        }
    
    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent action history for a user"""
        user_id = str(user_id)
        
        if user_id not in self.user_history:
            return []
        
        history = self.user_history[user_id][-limit:]
        
        # Format for display
        formatted_history = []
        for entry in history:
            formatted_entry = {
                'timestamp': entry['timestamp'],
                'action': self._format_action_description(entry['action_type'], entry['data']),
                'can_undo': True
            }
            formatted_history.append(formatted_entry)
        
        return formatted_history
    
    def _format_action_description(self, action_type: str, action_data: Dict) -> str:
        """Format action description for display"""
        if action_type == 'add_keywords':
            count = len(action_data.get('added_keywords', []))
            return f"Added {count} keyword{'s' if count != 1 else ''}"
        elif action_type == 'remove_keywords':
            count = len(action_data.get('removed_keywords', []))
            return f"Removed {count} keyword{'s' if count != 1 else ''}"
        elif action_type == 'add_urls':
            count = len(action_data.get('added_urls', []))
            return f"Added {count} URL{'s' if count != 1 else ''}"
        elif action_type == 'remove_urls':
            count = len(action_data.get('removed_configs', []))
            return f"Removed {count} URL{'s' if count != 1 else ''}"
        elif action_type == 'clear_keywords':
            count = len(action_data.get('cleared_keywords', []))
            return f"Cleared {count} keyword{'s' if count != 1 else ''}"
        elif action_type == 'clear_all':
            kw_count = len(action_data.get('cleared_keywords', []))
            url_count = len(action_data.get('cleared_configs', []))
            return f"Cleared all ({kw_count} keywords, {url_count} URLs)"
        else:
            return action_type.replace('_', ' ').title()
    
    def clear_user_history(self, user_id: str) -> bool:
        """Clear all history for a specific user"""
        try:
            user_id = str(user_id)
            if user_id in self.user_history:
                del self.user_history[user_id]
                self._save_history()
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing user history: {e}")
            return False
    
    @property
    def history_file(self) -> str:
        """Get the path to the history file"""
        return self.undo_file