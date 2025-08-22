"""
Enhanced Extraction Integration - Replace Redundant Systems
Integrates the consolidated Metaplex system into the main extraction pipeline
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
# Metaplex system removed - using DexScreener API exclusively

logger = logging.getLogger(__name__)

class EnhancedExtractionIntegration:
    """
    Replaces redundant extraction systems with the consolidated approach
    Provides enhanced accuracy and connection management
    """
    
    def __init__(self):
        self.integration_stats = {
            'tokens_processed': 0,
            'successful_extractions': 0,
            'consolidated_successes': 0,
            'fallback_successes': 0
        }
    
    async def process_token_with_consolidated_system(self, token_address: str, existing_token_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process token using consolidated extraction system
        Replaces multiple redundant extraction attempts
        """
        self.integration_stats['tokens_processed'] += 1
        
        try:
            # Try consolidated system first
            metadata = await extract_token_metadata_consolidated(token_address)
            
            if metadata and metadata.name != "Bonk.fun":
                self.integration_stats['successful_extractions'] += 1
                self.integration_stats['consolidated_successes'] += 1
                
                # Update token data with consolidated results
                enhanced_data = {
                    **existing_token_data,
                    'name': metadata.name,
                    'confidence': metadata.confidence,
                    'extraction_source': metadata.source,
                    'timestamp': metadata.timestamp,
                    'age_seconds': metadata.age_seconds,
                    'extraction_method': 'consolidated_system'
                }
                
                logger.info(f"🎯 CONSOLIDATED SUCCESS: {token_address[:8]}... → '{metadata.name}' ({metadata.source})")
                return enhanced_data
            
            # Fallback to existing token data if consolidation fails
            existing_name = existing_token_data.get('name', '')
            if existing_name and existing_name != "Bonk.fun":
                self.integration_stats['successful_extractions'] += 1
                self.integration_stats['fallback_successes'] += 1
                
                logger.info(f"✅ FALLBACK SUCCESS: {token_address[:8]}... → '{existing_name}' (existing data)")
                return {
                    **existing_token_data,
                    'extraction_method': 'fallback_existing'
                }
            
            # No valid name found
            logger.debug(f"❌ EXTRACTION FAILED: {token_address[:8]}... (no valid name available)")
            return {
                **existing_token_data,
                'extraction_method': 'failed',
                'name': existing_token_data.get('name', 'Unknown')
            }
            
        except Exception as e:
            logger.debug(f"Enhanced extraction error for {token_address[:8]}...: {e}")
            return existing_token_data
    
    def should_use_consolidated_system(self, token_data: Dict[str, Any]) -> bool:
        """
        Determine if token should use consolidated extraction
        Prioritizes tokens that need better name resolution
        """
        current_name = token_data.get('name', '')
        
        # Use consolidated system for placeholder names or low confidence
        if current_name in ["Bonk.fun", "", "Unknown"]:
            return True
            
        # Use for LetsBonk tokens that might have better metadata
        if token_data.get('is_letsbonk_token', False):
            return True
            
        # Use for tokens with low extraction confidence
        if token_data.get('confidence', 1.0) < 0.9:
            return True
            
        return False
    
    async def enhance_token_batch(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of tokens with enhanced extraction
        Uses parallel processing for better performance
        """
        enhanced_tokens = []
        
        # Process tokens that need enhancement
        enhancement_tasks = []
        for token in tokens:
            if self.should_use_consolidated_system(token):
                task = self.process_token_with_consolidated_system(
                    token.get('address', ''), 
                    token
                )
                enhancement_tasks.append(task)
            else:
                # Token already has good data
                enhanced_tokens.append({
                    **token,
                    'extraction_method': 'existing_good'
                })
        
        # Execute enhancements in parallel
        if enhancement_tasks:
            enhanced_results = await asyncio.gather(*enhancement_tasks, return_exceptions=True)
            
            for result in enhanced_results:
                if isinstance(result, Exception):
                    logger.debug(f"Enhancement task failed: {result}")
                else:
                    enhanced_tokens.append(result)
        
        return enhanced_tokens
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get detailed integration statistics"""
        total = self.integration_stats['tokens_processed']
        success = self.integration_stats['successful_extractions']
        
        return {
            **self.integration_stats,
            'success_rate': f"{(success/total*100):.1f}%" if total > 0 else "0%",
            'consolidated_rate': f"{(self.integration_stats['consolidated_successes']/total*100):.1f}%" if total > 0 else "0%"
        }
    
    def log_integration_statistics(self):
        """Log comprehensive integration statistics"""
        stats = self.get_integration_stats()
        
        logger.info("📊 ENHANCED EXTRACTION INTEGRATION STATS:")
        logger.info(f"   🔢 Tokens processed: {stats['tokens_processed']}")
        logger.info(f"   ✅ Successful extractions: {stats['successful_extractions']} ({stats['success_rate']})")
        logger.info(f"   🎯 Consolidated successes: {stats['consolidated_successes']} ({stats['consolidated_rate']})")
        logger.info(f"   🔄 Fallback successes: {stats['fallback_successes']}")

# Global integration instance
enhanced_integration = EnhancedExtractionIntegration()

async def enhance_token_extraction(token_address: str, token_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple interface to enhanced extraction integration
    Replaces redundant extraction calls with consolidated system
    """
    return await enhanced_integration.process_token_with_consolidated_system(token_address, token_data)