"""
Ultimate Timestamp Extractor - Combines Metaplex + Solana Blockchain Methods
Provides the most accurate token timestamps available by using multiple authoritative sources
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any
from metaplex_token_resolver import MetaplexTokenResolver
from solana_timestamp_extractor import SolanaTimestampExtractor

logger = logging.getLogger(__name__)

class UltimateTimestampExtractor:
    """
    Combines Metaplex metadata and Solana blockchain transaction history
    for the most accurate token timestamp extraction possible
    """
    
    def __init__(self):
        self.metaplex_resolver = None
        self.solana_extractor = None
        self.stats = {
            'total_attempts': 0,
            'metaplex_success': 0,
            'solana_success': 0,
            'combined_success': 0,
            'avg_extraction_time': 0.0
        }
        
    async def get_ultimate_timestamp(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Get the most accurate timestamp using multiple methods
        
        Strategy:
        1. Try Solana blockchain transaction history (most accurate)
        2. Try Metaplex metadata extraction (fast fallback)
        3. Combine results for maximum confidence
        """
        start_time = time.time()
        self.stats['total_attempts'] += 1
        
        result = {
            'token_address': token_address,
            'timestamp': None,
            'age_seconds': None,
            'confidence': 0.0,
            'sources': [],
            'extraction_time': 0.0
        }
        
        try:
            # METHOD 1: Solana blockchain transaction history (most reliable)
            solana_data = await self._get_solana_timestamp(token_address)
            if solana_data:
                result['timestamp'] = solana_data['creation_timestamp']
                result['age_seconds'] = solana_data['age_seconds']
                result['confidence'] = 1.0  # Blockchain is authoritative
                result['sources'].append('solana_blockchain')
                result['solana_data'] = solana_data
                self.stats['solana_success'] += 1
                
                logger.info(f"✅ BLOCKCHAIN TIMESTAMP: {token_address[:10]}... → {result['age_seconds']:.1f}s old")
            
            # METHOD 2: Metaplex metadata (faster fallback/verification)
            metaplex_data = await self._get_metaplex_timestamp(token_address)
            if metaplex_data and metaplex_data.get('creation_timestamp'):
                metaplex_ts = metaplex_data['creation_timestamp']
                metaplex_age = time.time() - metaplex_ts
                
                if not result['timestamp']:
                    # Use Metaplex as primary if Solana failed
                    result['timestamp'] = metaplex_ts
                    result['age_seconds'] = metaplex_age
                    result['confidence'] = 0.85  # Metaplex is good but not as definitive
                    
                result['sources'].append('metaplex_metadata')
                result['metaplex_data'] = metaplex_data
                self.stats['metaplex_success'] += 1
                
                # Verify agreement between methods
                if result['timestamp'] and solana_data:
                    time_diff = abs(result['timestamp'] - metaplex_ts)
                    result['timestamp_agreement'] = time_diff
                    
                    if time_diff < 60:  # Within 1 minute
                        result['confidence'] = 1.0  # High confidence with agreement
                        logger.info(f"✅ TIMESTAMP AGREEMENT: {time_diff:.1f}s difference (excellent)")
                    elif time_diff < 300:  # Within 5 minutes
                        result['confidence'] = 0.9
                        logger.info(f"👍 TIMESTAMP AGREEMENT: {time_diff:.1f}s difference (good)")
                    else:
                        logger.warning(f"⚠️ TIMESTAMP DISAGREEMENT: {time_diff:.1f}s difference")
            
            # Finalize result
            if result['timestamp']:
                result['extraction_time'] = time.time() - start_time
                self._update_avg_time(result['extraction_time'])
                
                if len(result['sources']) > 1:
                    self.stats['combined_success'] += 1
                
                logger.info(f"✅ ULTIMATE TIMESTAMP: {token_address[:10]}... → {result['age_seconds']:.1f}s old "
                          f"(confidence: {result['confidence']:.1%}, sources: {len(result['sources'])})")
                
                return result
            else:
                logger.warning(f"❌ TIMESTAMP EXTRACTION FAILED: {token_address[:10]}... (no methods succeeded)")
                return None
                
        except Exception as e:
            extraction_time = time.time() - start_time
            self._update_avg_time(extraction_time)
            logger.error(f"❌ Ultimate timestamp extraction error: {e}")
            return None
    
    async def _get_solana_timestamp(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get timestamp from Solana blockchain"""
        try:
            if not self.solana_extractor:
                self.solana_extractor = SolanaTimestampExtractor()
            
            async with self.solana_extractor:
                return await self.solana_extractor.get_token_creation_timestamp(token_address)
        except Exception as e:
            logger.debug(f"Solana timestamp failed: {e}")
            return None
    
    async def _get_metaplex_timestamp(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get timestamp from Metaplex metadata"""
        try:
            if not self.metaplex_resolver:
                self.metaplex_resolver = MetaplexTokenResolver()
            
            async with self.metaplex_resolver:
                return await self.metaplex_resolver.get_token_metadata(token_address)
        except Exception as e:
            logger.debug(f"Metaplex timestamp failed: {e}")
            return None
    
    def _update_avg_time(self, extraction_time: float):
        """Update running average extraction time"""
        total_attempts = self.stats['total_attempts']
        current_avg = self.stats['avg_extraction_time']
        self.stats['avg_extraction_time'] = ((current_avg * (total_attempts - 1)) + extraction_time) / total_attempts
    
    async def is_token_fresh(self, token_address: str, max_age_seconds: int = 300) -> bool:
        """
        Check if token is fresh using ultimate timestamp extraction
        
        Args:
            token_address: Token mint address
            max_age_seconds: Maximum age in seconds (default: 5 minutes)
        """
        timestamp_data = await self.get_ultimate_timestamp(token_address)
        
        if not timestamp_data or not timestamp_data.get('age_seconds'):
            return False
        
        is_fresh = timestamp_data['age_seconds'] <= max_age_seconds
        confidence = timestamp_data.get('confidence', 0)
        
        logger.info(f"🔍 ULTIMATE FRESHNESS: {token_address[:10]}... age={timestamp_data['age_seconds']:.1f}s "
                   f"fresh={is_fresh} confidence={confidence:.1%}")
        
        return is_fresh and confidence >= 0.8  # Require high confidence
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction performance statistics"""
        total = self.stats['total_attempts']
        if total == 0:
            return self.stats
        
        solana_rate = (self.stats['solana_success'] / total) * 100
        metaplex_rate = (self.stats['metaplex_success'] / total) * 100
        combined_rate = (self.stats['combined_success'] / total) * 100
        
        return {
            **self.stats,
            'solana_success_rate': f"{solana_rate:.1f}%",
            'metaplex_success_rate': f"{metaplex_rate:.1f}%",
            'combined_success_rate': f"{combined_rate:.1f}%"
        }
    
    def print_stats(self):
        """Print extraction statistics"""
        stats = self.get_extraction_stats()
        
        logger.info("📊 ULTIMATE TIMESTAMP EXTRACTOR STATS:")
        logger.info(f"   🔢 Total attempts: {stats['total_attempts']}")
        logger.info(f"   🔗 Solana blockchain: {stats['solana_success']} ({stats['solana_success_rate']})")
        logger.info(f"   📋 Metaplex metadata: {stats['metaplex_success']} ({stats['metaplex_success_rate']})")
        logger.info(f"   🎯 Combined methods: {stats['combined_success']} ({stats['combined_success_rate']})")
        logger.info(f"   ⏱️ Avg extraction time: {stats['avg_extraction_time']:.2f}s")

# Test the ultimate timestamp extractor
async def test_ultimate_extractor():
    """Test ultimate timestamp extraction with recent tokens"""
    
    test_tokens = [
        'xVUtGmsMCcJTHajrJ9YKxuRoiiKLeMxydHZzagZbonk',  # Very recent (16s old from logs)
        'btuF4XibuKmkv5ksmsDXnVnn8YKZ91vFxyFk7mjbonk',  # Recent (129s old from previous test)
        'So11111111111111111111111111111111111111112',   # Old token (baseline)
    ]
    
    print("🧪 Testing Ultimate Timestamp Extractor...")
    print("=" * 50)
    
    extractor = UltimateTimestampExtractor()
    
    for token_address in test_tokens:
        print(f"\n🔍 Testing: {token_address[:15]}...")
        
        try:
            result = await extractor.get_ultimate_timestamp(token_address)
            
            if result:
                from datetime import datetime
                
                created_date = datetime.fromtimestamp(result['timestamp'])
                
                print(f"✅ SUCCESS: Created {created_date.strftime('%H:%M:%S')}")
                print(f"   ⏰ Age: {result['age_seconds']:.1f}s ({result['age_seconds']/60:.1f}m)")
                print(f"   🎯 Confidence: {result['confidence']:.1%}")
                print(f"   📊 Sources: {', '.join(result['sources'])}")
                print(f"   ⚡ Extraction time: {result['extraction_time']:.2f}s")
                
                # Test freshness
                is_fresh = await extractor.is_token_fresh(token_address, 300)
                print(f"   🆕 Fresh (5min): {is_fresh}")
                
                if 'timestamp_agreement' in result:
                    print(f"   🔄 Method agreement: {result['timestamp_agreement']:.1f}s difference")
                
            else:
                print("❌ FAILED: Could not extract timestamp")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n📊 Performance Summary:")
    extractor.print_stats()

if __name__ == "__main__":
    asyncio.run(test_ultimate_extractor())