"""
AI Keyword Sync Integration
Automatically updates AI smart matcher when keywords change
"""

import logging
from typing import List
from ai_smart_keyword_matcher import AISmartKeywordMatcher, SmartMatchingIntegration

logger = logging.getLogger(__name__)

class AIKeywordSyncIntegration:
    """Integrates AI Smart Matcher with automatic keyword synchronization"""
    
    def __init__(self, initial_keywords: List[str], monitoring_server=None):
        self.monitoring_server = monitoring_server
        self.update_ai_matchers(initial_keywords)
        
    def update_ai_matchers(self, new_keywords: List[str]):
        """Update AI matchers with new keyword list"""
        try:
            if self.monitoring_server:
                # Update AI smart matcher
                self.monitoring_server.ai_smart_matcher = AISmartKeywordMatcher(new_keywords, fuzzy_threshold=85)
                self.monitoring_server.smart_matching_integration = SmartMatchingIntegration(new_keywords)
                
                logger.info(f"🧠 AI Smart Matcher updated with {len(new_keywords)} keywords")
                logger.info("✅ Typo detection system refreshed with latest keywords")
                
                # Update the keywords list in the monitoring server
                self.monitoring_server.keywords = new_keywords
                
                return True
        except Exception as e:
            logger.error(f"❌ Failed to update AI matchers: {e}")
            return False
        
        return False
    
    def add_keyword(self, keyword: str) -> bool:
        """Add a single keyword and update AI matchers"""
        if self.monitoring_server and keyword not in self.monitoring_server.keywords:
            updated_keywords = self.monitoring_server.keywords + [keyword]
            return self.update_ai_matchers(updated_keywords)
        return False
    
    def remove_keyword(self, keyword: str) -> bool:
        """Remove a keyword and update AI matchers"""
        if self.monitoring_server and keyword in self.monitoring_server.keywords:
            updated_keywords = [k for k in self.monitoring_server.keywords if k != keyword]
            return self.update_ai_matchers(updated_keywords)
        return False
    
    def get_typo_suggestions_for_token(self, token_name: str) -> List[dict]:
        """Get typo suggestions for a token that didn't match"""
        if self.monitoring_server and self.monitoring_server.ai_smart_matcher:
            return self.monitoring_server.ai_smart_matcher.get_typo_suggestions(token_name)
        return []
    
    def validate_keyword_list(self) -> dict:
        """Analyze current keyword list for potential issues"""
        if self.monitoring_server and self.monitoring_server.ai_smart_matcher:
            return self.monitoring_server.ai_smart_matcher.validate_keyword_list()
        return {'potential_typos': [], 'near_duplicates': [], 'variations': []}