"""
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
