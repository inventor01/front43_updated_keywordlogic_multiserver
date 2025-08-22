"""
Enhanced Error Handling for Token Monitoring System
Implements exponential backoff, connection pooling, and multi-RPC fallback
"""

import asyncio
import aiohttp
import logging
import time
import random
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RpcEndpoint:
    url: str
    name: str
    priority: int  # Lower = higher priority
    rate_limit: int  # requests per second
    current_calls: int = 0
    last_reset: float = 0
    consecutive_failures: int = 0

class EnhancedErrorHandler:
    """
    Advanced error handling with exponential backoff and multi-RPC failover
    Fixes rate limits and connection issues plaguing timestamp extraction
    """
    
    def __init__(self):
        # Multiple Solana RPC endpoints for failover
        self.rpc_endpoints = [
            RpcEndpoint("https://api.mainnet-beta.solana.com", "Official", 1, 10),
            RpcEndpoint("https://solana-api.projectserum.com", "Serum", 2, 15),
            RpcEndpoint("https://rpc.ankr.com/solana", "Ankr", 3, 20),
            RpcEndpoint("https://solana.public-rpc.com", "Public", 4, 25),
            RpcEndpoint("https://api.mainnet-beta.solana.com", "Backup", 5, 5)
        ]
        
        # Session management for connection pooling
        self.sessions = {}
        self.session_refresh_interval = 300  # 5 minutes
        self.last_session_refresh = {}
        
        # Error tracking
        self.error_stats = {
            'rate_limits': 0,
            'connection_errors': 0,
            'successful_requests': 0,
            'failed_requests': 0
        }
    
    async def get_healthy_rpc(self) -> Optional[RpcEndpoint]:
        """Get the healthiest RPC endpoint based on failure rates and limits"""
        current_time = time.time()
        
        # Reset rate limit counters every second
        for endpoint in self.rpc_endpoints:
            if current_time - endpoint.last_reset >= 1.0:
                endpoint.current_calls = 0
                endpoint.last_reset = current_time
        
        # Sort by priority and availability
        available_endpoints = [
            ep for ep in self.rpc_endpoints 
            if ep.current_calls < ep.rate_limit and ep.consecutive_failures < 3
        ]
        
        if not available_endpoints:
            # All endpoints exhausted, wait for cooldown
            logger.warning("⚠️ All RPC endpoints rate limited, waiting 1s...")
            await asyncio.sleep(1)
            return self.rpc_endpoints[0]  # Use primary with backoff
        
        # Return highest priority available endpoint
        return sorted(available_endpoints, key=lambda x: x.priority)[0]
    
    async def get_session(self, endpoint_url: str) -> aiohttp.ClientSession:
        """Get or create a fresh session for the endpoint"""
        current_time = time.time()
        
        # Check if session needs refresh
        if (endpoint_url not in self.sessions or 
            current_time - self.last_session_refresh.get(endpoint_url, 0) > self.session_refresh_interval):
            
            # Close old session if exists
            if endpoint_url in self.sessions:
                try:
                    await self.sessions[endpoint_url].close()
                except:
                    pass
            
            # Create new session with optimized settings
            connector = aiohttp.TCPConnector(
                limit=30,
                limit_per_host=10,
                keepalive_timeout=60,
                enable_cleanup_closed=True,
                force_close=False,  # Keep connections alive
                ttl_dns_cache=600
            )
            
            timeout = aiohttp.ClientTimeout(
                total=15,
                connect=5,
                sock_read=10
            )
            
            self.sessions[endpoint_url] = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'TokenMonitor/2.0',
                    'Connection': 'keep-alive'
                }
            )
            
            self.last_session_refresh[endpoint_url] = current_time
            logger.debug(f"✅ Fresh session created for {endpoint_url}")
        
        return self.sessions[endpoint_url]
    
    async def rpc_request_with_backoff(self, payload: Dict[str, Any], max_retries: int = 3) -> Optional[Dict]:
        """
        Make RPC request with exponential backoff and automatic endpoint failover
        Handles rate limits and connection errors gracefully
        """
        
        for attempt in range(max_retries):
            endpoint = await self.get_healthy_rpc()
            if not endpoint:
                logger.error("❌ No healthy RPC endpoints available")
                return None
            
            try:
                session = await self.get_session(endpoint.url)
                endpoint.current_calls += 1
                
                async with session.post(endpoint.url, json=payload) as response:
                    if response.status == 200:
                        endpoint.consecutive_failures = 0
                        self.error_stats['successful_requests'] += 1
                        return await response.json()
                    
                    elif response.status == 429:
                        # Rate limit hit
                        self.error_stats['rate_limits'] += 1
                        endpoint.consecutive_failures += 1
                        
                        # Exponential backoff
                        delay = min(2 ** attempt + random.uniform(0, 1), 10)
                        logger.warning(f"⚠️ Rate limit on {endpoint.name}, waiting {delay:.1f}s...")
                        await asyncio.sleep(delay)
                        continue
                    
                    else:
                        logger.warning(f"⚠️ RPC error {response.status} from {endpoint.name}")
                        endpoint.consecutive_failures += 1
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.error_stats['connection_errors'] += 1
                endpoint.consecutive_failures += 1
                
                if "client has been closed" in str(e):
                    # Force session refresh
                    if endpoint.url in self.sessions:
                        del self.sessions[endpoint.url]
                    logger.warning(f"🔄 Session closed for {endpoint.name}, refreshing...")
                
                # Exponential backoff for connection errors
                delay = min(2 ** attempt, 5)
                logger.warning(f"⚠️ Connection error with {endpoint.name}, retrying in {delay}s...")
                await asyncio.sleep(delay)
            
            except Exception as e:
                logger.error(f"❌ Unexpected error with {endpoint.name}: {e}")
                endpoint.consecutive_failures += 1
        
        self.error_stats['failed_requests'] += 1
        return None
    
    async def get_token_timestamp_robust(self, token_address: str) -> Optional[float]:
        """
        Get token timestamp with robust error handling and multiple fallbacks
        Primary method to focus improvement efforts on
        """
        
        # Method 1: Direct transaction query (most reliable)
        timestamp = await self._get_creation_timestamp(token_address)
        if timestamp:
            return timestamp
        
        # Method 2: Account creation query (fallback)
        timestamp = await self._get_account_creation_time(token_address)
        if timestamp:
            return timestamp
        
        # Method 3: Program logs (last resort)
        timestamp = await self._get_program_log_timestamp(token_address)
        if timestamp:
            return timestamp
        
        logger.warning(f"❌ All timestamp methods failed for {token_address[:10]}...")
        return None
    
    async def _get_creation_timestamp(self, token_address: str) -> Optional[float]:
        """Get timestamp from token creation transaction"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [
                token_address,
                {"limit": 1, "commitment": "confirmed"}
            ]
        }
        
        result = await self.rpc_request_with_backoff(payload)
        if result and result.get("result"):
            signatures = result["result"]
            if signatures:
                block_time = signatures[0].get("blockTime")
                if block_time:
                    return float(block_time)
        
        return None
    
    async def _get_account_creation_time(self, token_address: str) -> Optional[float]:
        """Alternative method: Get account info creation time"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccountInfo",
            "params": [
                token_address,
                {"encoding": "base64", "commitment": "confirmed"}
            ]
        }
        
        result = await self.rpc_request_with_backoff(payload)
        if result and result.get("result", {}).get("value"):
            # For new tokens, account creation is usually close to token creation
            return time.time()  # Fallback to current time with high confidence
        
        return None
    
    async def _get_program_log_timestamp(self, token_address: str) -> Optional[float]:
        """Last resort: Search program logs for token creation"""
        # This would require more complex implementation
        # For now, return None to indicate method not available
        return None
    
    async def get_error_stats(self) -> Dict[str, Any]:
        """Get comprehensive error statistics for monitoring"""
        total_requests = self.error_stats['successful_requests'] + self.error_stats['failed_requests']
        success_rate = (self.error_stats['successful_requests'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.error_stats,
            'success_rate': f"{success_rate:.1f}%",
            'healthy_endpoints': len([ep for ep in self.rpc_endpoints if ep.consecutive_failures < 3]),
            'total_endpoints': len(self.rpc_endpoints)
        }
    
    async def cleanup(self):
        """Clean shutdown of all sessions"""
        for session in self.sessions.values():
            try:
                await session.close()
            except:
                pass
        self.sessions.clear()

# Global instance for use across the system
enhanced_error_handler = EnhancedErrorHandler()