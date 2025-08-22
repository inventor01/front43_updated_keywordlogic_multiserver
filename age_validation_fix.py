"""
Age Validation Fix - Smart Freshness Detection
Fixes overly strict age validation that blocks legitimate fresh tokens
"""

import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SmartAgeValidator:
    """
    Intelligent age validation that doesn't block legitimate fresh tokens
    Replaces the overly strict "NUCLEAR BLOCK" system
    """
    
    def __init__(self):
        self.validation_stats = {
            'total_validations': 0,
            'passed_validations': 0,
            'blocked_old_tokens': 0,
            'allowed_fresh_tokens': 0
        }
    
    def validate_token_freshness(self, token_name: str, age_seconds: float, confidence: float, sources: int) -> Dict[str, Any]:
        """
        Smart freshness validation with reasonable thresholds
        Returns validation result with detailed reasoning
        """
        self.validation_stats['total_validations'] += 1
        
        # Skip validation for obvious placeholder names
        if token_name in ["Bonk.fun", "", "Unknown"]:
            return {
                'valid': False,
                'reason': 'placeholder_name',
                'action': 'reject',
                'message': f"Rejected placeholder name: {token_name}"
            }
        
        # Allow very fresh tokens (under 2 minutes) regardless of other factors
        if age_seconds <= 120:
            self.validation_stats['allowed_fresh_tokens'] += 1
            self.validation_stats['passed_validations'] += 1
            return {
                'valid': True,
                'reason': 'very_fresh',
                'action': 'allow',
                'message': f"✅ FRESH TOKEN: {token_name} ({age_seconds:.1f}s old)"
            }
        
        # Allow tokens under 5 minutes with high confidence
        if age_seconds <= 300 and confidence >= 0.8:
            self.validation_stats['allowed_fresh_tokens'] += 1
            self.validation_stats['passed_validations'] += 1
            return {
                'valid': True,
                'reason': 'fresh_high_confidence',
                'action': 'allow',
                'message': f"✅ CONFIDENT FRESH: {token_name} ({age_seconds:.1f}s, {confidence:.0%} confidence)"
            }
        
        # Allow tokens under 10 minutes with multiple sources
        if age_seconds <= 600 and sources >= 2:
            self.validation_stats['allowed_fresh_tokens'] += 1
            self.validation_stats['passed_validations'] += 1
            return {
                'valid': True,
                'reason': 'fresh_multiple_sources',
                'action': 'allow',
                'message': f"✅ MULTI-SOURCE FRESH: {token_name} ({age_seconds:.1f}s, {sources} sources)"
            }
        
        # Block genuinely old tokens (over 20 minutes)
        if age_seconds > 1200:  # 20 minutes
            self.validation_stats['blocked_old_tokens'] += 1
            return {
                'valid': False,
                'reason': 'genuinely_old',
                'action': 'block_old',
                'message': f"⏰ OLD TOKEN: {token_name} ({age_seconds/60:.1f}min old) - too old for notifications"
            }
        
        # For tokens 10-20 minutes old, use progressive validation
        # Allow if we have good metadata extraction
        if confidence >= 0.7 or sources >= 1:
            self.validation_stats['passed_validations'] += 1
            return {
                'valid': True,
                'reason': 'progressive_validation',
                'action': 'allow_progressive',
                'message': f"✅ PROGRESSIVE ALLOW: {token_name} ({age_seconds/60:.1f}min, acceptable metadata)"
            }
        
        # Default block for unclear cases
        return {
            'valid': False,
            'reason': 'insufficient_confidence',
            'action': 'block_unclear',
            'message': f"🔍 UNCLEAR TOKEN: {token_name} (age: {age_seconds:.1f}s, confidence: {confidence:.0%}) - needs better data"
        }
    
    def should_allow_notification(self, token_name: str, age_seconds: float, confidence: float = 0.8, sources: int = 1) -> bool:
        """
        Simple boolean check for notification eligibility
        Replaces the harsh "NUCLEAR BLOCK" logic
        """
        result = self.validate_token_freshness(token_name, age_seconds, confidence, sources)
        
        if result['valid']:
            logger.info(result['message'])
        else:
            logger.debug(result['message'])
            
        return result['valid']
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation performance statistics"""
        total = self.validation_stats['total_validations']
        passed = self.validation_stats['passed_validations']
        
        return {
            **self.validation_stats,
            'pass_rate': f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            'block_rate': f"{((total-passed)/total*100):.1f}%" if total > 0 else "0%"
        }

# Global validator instance
smart_validator = SmartAgeValidator()

def validate_token_age_smart(token_name: str, age_seconds: float, confidence: float = 0.8, sources: int = 1) -> bool:
    """
    Simple interface to smart age validation
    Replaces overly strict validation logic
    """
    return smart_validator.should_allow_notification(token_name, age_seconds, confidence, sources)