"""
Solana Account Timestamp Extractor
Gets accurate token creation timestamps directly from blockchain transaction history
More reliable than metadata parsing for timestamp information
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solana.rpc.commitment import Commitment

logger = logging.getLogger(__name__)

class SolanaTimestampExtractor:
    """
    Extract accurate token creation timestamps from Solana blockchain
    Uses transaction history to find account creation time
    """
    
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url
        self.client = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = AsyncClient(self.rpc_url)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.close()
    
    async def get_token_creation_timestamp(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Get token creation timestamp from blockchain transaction history
        
        Returns:
            Dict with timestamp, signature, and age information
        """
        start_time = time.time()
        
        try:
            pubkey = Pubkey.from_string(token_address)
            
            # Get all signatures for this account to find creation
            signatures_response = await self.client.get_signatures_for_address(
                pubkey,
                limit=1000,  # Get many signatures to find the earliest
                commitment=Commitment("confirmed")
            )
            
            if not signatures_response.value:
                logger.debug(f"❌ No signatures found for {token_address[:10]}...")
                return None
            
            signatures = signatures_response.value
            
            # Find the oldest signature (account creation)
            oldest_signature = None
            oldest_block_time = None
            
            for sig in reversed(signatures):  # Start from oldest
                if sig.block_time:
                    oldest_signature = str(sig.signature)  # Convert to string
                    oldest_block_time = sig.block_time
                    break
            
            if not oldest_block_time:
                logger.debug(f"❌ No block time found for {token_address[:10]}...")
                return None
            
            # Calculate current age
            current_time = time.time()
            age_seconds = current_time - oldest_block_time
            
            extraction_time = time.time() - start_time
            
            logger.info(f"✅ SOLANA TIMESTAMP: {token_address[:10]}... created {age_seconds:.1f}s ago ({extraction_time:.2f}s)")
            
            return {
                'token_address': token_address,
                'creation_timestamp': oldest_block_time,
                'creation_signature': oldest_signature,
                'age_seconds': age_seconds,
                'total_signatures': len(signatures),
                'extraction_time': extraction_time,
                'source': 'solana_blockchain',
                'confidence': 1.0  # Blockchain is authoritative
            }
            
        except Exception as e:
            extraction_time = time.time() - start_time
            logger.error(f"❌ Solana timestamp extraction failed for {token_address[:10]}...: {e} ({extraction_time:.2f}s)")
            return None
    
    async def get_multiple_timestamps(self, token_addresses: list) -> Dict[str, Dict[str, Any]]:
        """
        Get creation timestamps for multiple tokens in parallel
        More efficient for bulk operations
        """
        start_time = time.time()
        
        # Create tasks for parallel execution
        tasks = [
            self.get_token_creation_timestamp(address)
            for address in token_addresses
        ]
        
        # Execute all requests in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dictionary
        timestamp_dict = {}
        successful = 0
        
        for address, result in zip(token_addresses, results):
            if isinstance(result, dict) and result:
                timestamp_dict[address] = result
                successful += 1
            elif isinstance(result, Exception):
                logger.error(f"❌ Batch timestamp error for {address[:10]}...: {result}")
        
        total_time = time.time() - start_time
        logger.info(f"📦 Solana timestamp batch complete: {successful}/{len(token_addresses)} successful ({total_time:.2f}s)")
        
        return timestamp_dict
    
    async def is_token_fresh(self, token_address: str, max_age_seconds: int = 300) -> bool:
        """
        Quick check if token is fresh (within max_age_seconds)
        
        Args:
            token_address: Token mint address
            max_age_seconds: Maximum age in seconds (default: 5 minutes)
            
        Returns:
            True if token is fresh, False otherwise
        """
        timestamp_data = await self.get_token_creation_timestamp(token_address)
        
        if not timestamp_data:
            return False
        
        age_seconds = timestamp_data.get('age_seconds', float('inf'))
        is_fresh = age_seconds <= max_age_seconds
        
        logger.debug(f"🔍 Freshness check: {token_address[:10]}... age={age_seconds:.1f}s fresh={is_fresh}")
        
        return is_fresh

# Test functionality
async def test_solana_timestamps():
    """Test Solana timestamp extraction with recent tokens"""
    
    # Recent tokens from system logs
    test_tokens = [
        'btuF4XibuKmkv5ksmsDXnVnn8YKZ91vFxyFk7mjbonk',  # Recent Bonk.fun (should be ~14s old)
        '5dZM4Rfie33TUAkbZmWQEfosGxHqrRKA7SGJNVCabonk',  # Another recent one
        'So11111111111111111111111111111111111111112',     # Wrapped SOL (baseline - should be old)
    ]
    
    print("🧪 Testing Solana Timestamp Extraction...")
    print("=" * 50)
    
    async with SolanaTimestampExtractor() as extractor:
        for token_address in test_tokens:
            print(f"\n🔍 Testing: {token_address[:15]}...")
            
            try:
                result = await extractor.get_token_creation_timestamp(token_address)
                
                if result:
                    from datetime import datetime
                    
                    created_date = datetime.fromtimestamp(result['creation_timestamp'])
                    
                    print(f"✅ SUCCESS: Token created {created_date.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   ⏰ Age: {result['age_seconds']:.1f}s ({result['age_seconds']/60:.1f}m)")
                    print(f"   🔍 Signatures: {result['total_signatures']}")
                    print(f"   📝 Creation TX: {str(result['creation_signature'])[:20]}...")
                    print(f"   ⚡ Extraction time: {result['extraction_time']:.2f}s")
                    
                    # Test freshness check
                    is_fresh = await extractor.is_token_fresh(token_address, 300)  # 5 minutes
                    print(f"   🆕 Fresh (5min): {is_fresh}")
                    
                else:
                    print("❌ FAILED: Could not extract timestamp")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
        
        # Test batch processing
        print(f"\n📦 Testing batch processing...")
        batch_results = await extractor.get_multiple_timestamps(test_tokens[:2])
        
        print(f"Batch results: {len(batch_results)}/{2} successful")
        for address, data in batch_results.items():
            print(f"   {address[:15]}... → {data['age_seconds']:.1f}s old")

if __name__ == "__main__":
    asyncio.run(test_solana_timestamps())