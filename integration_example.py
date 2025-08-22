#!/usr/bin/env python3
"""
Integration Example - How to implement speed optimizations in existing system
Shows exact code changes needed for faster processing
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional

# Import the new optimization modules
from speed_optimizations import speed_extract_name, speed_validate_timestamp, get_speed_optimizer
from processing_pipeline_optimization import submit_token_for_processing

logger = logging.getLogger(__name__)

class OptimizedTokenProcessor:
    """
    Example showing how to integrate speed optimizations into existing token processing
    This replaces the current pure_name_extractor and multi_source_timestamp_validator
    """
    
    def __init__(self):
        self.processing_stats = {
            'total_processed': 0,
            'avg_processing_time': 0.0,
            'cache_hits': 0,
            'fast_extractions': 0
        }
    
    async def process_token_optimized(self, token_address: str, is_keyword_match: bool = False) -> Dict[str, Any]:
        """
        Process single token with all speed optimizations applied
        This is the main function that replaces existing slow processing
        """
        start_time = time.time()
        
        if is_keyword_match:
            # INSTANT PROCESSING for keyword matches
            logger.info(f"⚡ INSTANT PROCESSING: {token_address[:10]}... (keyword match)")
            
            # Submit to instant priority queue
            await submit_token_for_processing(token_address, is_keyword_match=True)
            
            # Get ultra-fast results
            name = await speed_extract_name(token_address)
            age_seconds, confidence = await speed_validate_timestamp(token_address)
            
            processing_time = time.time() - start_time
            
            result = {
                'address': token_address,
                'name': name,
                'age_seconds': age_seconds,
                'timestamp_confidence': confidence,
                'processing_time': processing_time,
                'method': 'instant_keyword_match',
                'priority': 'instant'
            }
            
            # Send immediate notification
            if name:
                await self._send_instant_notification(result)
                logger.info(f"✅ INSTANT SUCCESS: '{name}' in {processing_time:.3f}s")
            
            return result
        
        else:
            # NORMAL PROCESSING for regular tokens
            logger.info(f"🚀 FAST PROCESSING: {token_address[:10]}...")
            
            # Submit to high priority queue  
            await submit_token_for_processing(token_address, is_keyword_match=False)
            
            # Parallel name and timestamp extraction
            name_task = speed_extract_name(token_address)
            timestamp_task = speed_validate_timestamp(token_address)
            
            # Execute both simultaneously
            name, (age_seconds, confidence) = await asyncio.gather(
                name_task, timestamp_task, return_exceptions=True
            )
            
            # Handle any exceptions
            if isinstance(name, Exception):
                logger.warning(f"⚠️ Name extraction failed: {name}")
                name = None
            
            if isinstance(age_seconds, Exception):
                logger.warning(f"⚠️ Timestamp validation failed: {age_seconds}")
                age_seconds, confidence = 300.0, 0.5  # 5 minute fallback
            
            processing_time = time.time() - start_time
            
            result = {
                'address': token_address,
                'name': name,
                'age_seconds': age_seconds,
                'timestamp_confidence': confidence,
                'processing_time': processing_time,
                'method': 'fast_parallel',
                'priority': 'normal'
            }
            
            # Update stats
            self._update_processing_stats(processing_time)
            
            if name:
                logger.info(f"✅ FAST SUCCESS: '{name}' in {processing_time:.3f}s")
            else:
                logger.warning(f"⚠️ FAST FAILED: No name found in {processing_time:.3f}s")
            
            return result
    
    async def batch_process_tokens(self, token_addresses: list, is_urgent: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Process multiple tokens efficiently using batch optimization
        """
        if not token_addresses:
            return {}
        
        logger.info(f"📦 BATCH PROCESSING: {len(token_addresses)} tokens")
        start_time = time.time()
        
        if is_urgent:
            # Process all tokens individually in parallel for speed
            tasks = [self.process_token_optimized(addr, is_keyword_match=False) for addr in token_addresses]
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convert to dictionary
            results = {}
            for i, result in enumerate(results_list):
                if isinstance(result, dict):
                    results[token_addresses[i]] = result
                    
        else:
            # Use optimized batch processing
            optimizer = await get_speed_optimizer()
            results = await optimizer.batch_process_tokens(token_addresses)
        
        total_time = time.time() - start_time
        successful = len([r for r in results.values() if r.get('name')])
        
        logger.info(f"✅ BATCH COMPLETE: {successful}/{len(token_addresses)} in {total_time:.2f}s")
        
        return results
    
    async def _send_instant_notification(self, result: Dict[str, Any]):
        """Send immediate Discord notification for instant results"""
        # This would integrate with your existing Discord notification system
        logger.info(f"📢 INSTANT NOTIFICATION: {result['name']} (⚡{result['processing_time']:.3f}s)")
        
        # Example integration with Discord:
        # await self.discord_notifier.send_instant_notification(result)
    
    def _update_processing_stats(self, processing_time: float):
        """Update processing statistics"""
        self.processing_stats['total_processed'] += 1
        
        # Update running average
        total = self.processing_stats['total_processed']
        current_avg = self.processing_stats['avg_processing_time']
        self.processing_stats['avg_processing_time'] = ((current_avg * (total - 1)) + processing_time) / total
        
        # Track fast extractions (under 1 second)
        if processing_time < 1.0:
            self.processing_stats['fast_extractions'] += 1
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        total = self.processing_stats['total_processed']
        fast = self.processing_stats['fast_extractions']
        
        return {
            'total_processed': total,
            'average_processing_time': f"{self.processing_stats['avg_processing_time']:.3f}s",
            'fast_extraction_rate': f"{(fast/total*100):.1f}%" if total > 0 else "0%",
            'cache_hit_rate': f"{(self.processing_stats['cache_hits']/total*100):.1f}%" if total > 0 else "0%",
            'optimization_status': 'active'
        }


# Example usage showing how to replace existing code:

"""
BEFORE (in alchemy_server.py):

# Slow processing
name = await self.pure_name_processor.extract_accurate_token_name(token_address)
age_seconds, confidence = await self.timestamp_validator.validate_timestamp_multi_source(token_address)

# Process results...
if name and matched_keyword:
    # Send notification after processing completes (3-10s delay)
    await self.discord_notifier.send_notification(...)


AFTER (with optimizations):

# Fast processing
processor = OptimizedTokenProcessor()

if matched_keyword:
    # Instant processing and notification
    result = await processor.process_token_optimized(token_address, is_keyword_match=True)
    # Notification sent immediately within 0.5-1s
else:
    # Fast normal processing
    result = await processor.process_token_optimized(token_address, is_keyword_match=False)

# All data available in result dict:
name = result['name']
age_seconds = result['age_seconds']
processing_time = result['processing_time']
"""

async def integration_test():
    """Test the optimized processing system"""
    processor = OptimizedTokenProcessor()
    
    # Test instant processing (keyword match)
    test_address = "DLKHh3skdyY2Nx13sHp9kfbQySSP5uz4feT9z63Ubonk"
    
    print("Testing instant processing...")
    result = await processor.process_token_optimized(test_address, is_keyword_match=True)
    print(f"Instant result: {result}")
    
    print("\nTesting normal processing...")
    result = await processor.process_token_optimized(test_address, is_keyword_match=False)
    print(f"Normal result: {result}")
    
    print(f"\nPerformance stats: {processor.get_performance_report()}")

if __name__ == "__main__":
    asyncio.run(integration_test())