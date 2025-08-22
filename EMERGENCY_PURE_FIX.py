#!/usr/bin/env python3
"""
EMERGENCY FIX: Replace ALL Jupiter/Solana RPC components with pure DexScreener
This ensures NO Jupiter or Solana RPC retry loops appear in production logs
"""

import os
import sys

def emergency_pure_fix():
    """Replace all problematic imports with pure DexScreener components"""
    
    # Files that need to be neutralized (contain Jupiter/Solana RPC retries)
    problematic_files = [
        'dual_api_name_extractor.py',
        'enhanced_token_name_resolver.py', 
        'enhanced_name_extractor.py',
        'optimized_name_extractor.py',
        'high_success_integration.py'
    ]
    
    print("🚨 EMERGENCY PURE FIX: Neutralizing Jupiter/Solana RPC components")
    print("=" * 60)
    
    for filename in problematic_files:
        if os.path.exists(filename):
            print(f"❌ DISABLING: {filename}")
            
            # Create pure DexScreener replacement
            pure_content = f'''"""
PURE DEXSCREENER REPLACEMENT - NO Jupiter/Solana RPC
This file has been replaced to eliminate retry loops
Use dexscreener_70_percent_extractor.py instead
"""

import asyncio
import logging
from dexscreener_70_percent_extractor import extract_name_70_percent

logger = logging.getLogger(__name__)

async def extract_dual_api_name(token_address: str):
    """Pure DexScreener replacement - NO Jupiter/Solana RPC"""
    logger.info("🎯 PURE REPLACEMENT: Using DexScreener-only extraction")
    return await extract_name_70_percent(token_address)

async def resolve_token_name_with_retry(token_address: str):
    """Pure DexScreener replacement - NO Jupiter/Solana RPC"""
    logger.info("🎯 PURE REPLACEMENT: Using DexScreener-only extraction")
    return await extract_name_70_percent(token_address)

async def get_optimized_extractor():
    """Pure DexScreener replacement - NO Jupiter/Solana RPC"""
    from dexscreener_70_percent_extractor import get_dex_70_extractor
    return await get_dex_70_extractor()

async def get_high_success_extractor():
    """Pure DexScreener replacement - NO Jupiter/Solana RPC"""
    from dexscreener_70_percent_extractor import get_dex_70_extractor
    return await get_dex_70_extractor()

# Legacy compatibility functions
class DualAPINameExtractor:
    async def extract_dual_api_name(self, token_address: str):
        return await extract_name_70_percent(token_address)

class EnhancedTokenNameResolver:
    async def resolve_token_name_with_retry(self, token_address: str):
        return await extract_name_70_percent(token_address)
'''
            
            # Write pure replacement
            with open(filename, 'w') as f:
                f.write(pure_content)
            
            print(f"✅ REPLACED: {filename} -> Pure DexScreener")
    
    print("=" * 60)
    print("✅ EMERGENCY FIX COMPLETE: All Jupiter/Solana RPC components neutralized")
    print("🎯 RESULT: Only DexScreener 70% extraction will be used")
    print("❌ ELIMINATED: Jupiter retry logs")
    print("❌ ELIMINATED: Solana RPC retry logs")

if __name__ == "__main__":
    emergency_pure_fix()