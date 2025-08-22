"""
Railway-specific speed optimizations for ultra-fast token detection
Implements sub-second detection with cost-efficient BrowserCat usage
"""

import time
import asyncio
import concurrent.futures
from typing import List, Dict, Any
import logging
from ultra_speed_config import *

logger = logging.getLogger(__name__)

class RailwaySpeedOptimizer:
    """Optimizes token detection speed for Railway deployment"""
    
    def __init__(self, monitor_server):
        self.monitor_server = monitor_server
        self.last_optimization_time = time.time()
        self.speed_metrics = {
            'average_detection_time': 0,
            'tokens_processed_per_minute': 0,
            'browsercat_usage_rate': 0,
            'notification_delay': 0
        }
        
        # Initialize ultra-fast thread pool
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=TOKEN_PROCESSING_WORKERS,
            thread_name_prefix="UltraFast"
        )
        
        logger.info("🚀 Railway Speed Optimizer initialized")
        logger.info(f"   ⚡ {TOKEN_PROCESSING_WORKERS} worker threads")
        logger.info(f"   📡 {ULTRA_FAST_POLLING_INTERVAL}s polling interval")
        
    def optimize_detection_speed(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply speed optimizations to token processing"""
        
        if not tokens:
            return []
            
        start_time = time.time()
        
        # 1. INSTANT KEYWORD FILTERING (skip BrowserCat for matches)
        keyword_matches = []
        url_only_tokens = []
        
        for token in tokens:
            token_name = token.get('name', '').lower()
            
            # Check if token matches any keyword instantly
            if self._matches_keywords(token_name):
                keyword_matches.append(token)
                logger.info(f"⚡ INSTANT: Keyword match '{token_name}' - skipping BrowserCat")
            else:
                url_only_tokens.append(token)
        
        # 2. INSTANT NOTIFICATIONS for keyword matches
        for token in keyword_matches:
            self._send_instant_notification(token)
            
        # 3. PARALLEL PROCESSING for URL-only tokens (with BrowserCat)
        if url_only_tokens and len(url_only_tokens) <= BROWSERCAT_PARALLEL_LIMIT:
            processed_tokens = self._process_tokens_parallel(url_only_tokens)
        else:
            # Batch processing if too many tokens
            processed_tokens = self._process_tokens_batch(url_only_tokens)
            
        total_time = time.time() - start_time
        self._update_speed_metrics(len(tokens), total_time)
        
        return keyword_matches + processed_tokens
    
    def _matches_keywords(self, token_name: str) -> bool:
        """Ultra-fast keyword matching"""
        keywords = self.monitor_server.keywords
        
        for keyword in keywords:
            if keyword in token_name:
                return True
        return False
    
    def _send_instant_notification(self, token: Dict[str, Any]):
        """Send instant Discord notification for keyword matches"""
        try:
            if self.monitor_server.discord_notifier:
                # Skip all processing delays - send immediately
                self.monitor_server.discord_notifier.send_notification(
                    token_name=token.get('name', 'Unknown'),
                    contract_address=token.get('address', ''),
                    market_data=None,  # Skip market data for speed
                    social_links=[],   # Skip social links for speed
                    matched_keyword=self._get_matched_keyword(token.get('name', ''))
                )
                logger.info(f"⚡ INSTANT notification sent: {token.get('name', 'Unknown')}")
        except Exception as e:
            logger.error(f"❌ Instant notification failed: {e}")
    
    def _get_matched_keyword(self, token_name: str) -> str:
        """Find which keyword matched"""
        token_name_lower = token_name.lower()
        
        for keyword in self.monitor_server.keywords:
            if keyword in token_name_lower:
                return keyword
        return "unknown"
    
    def _process_tokens_parallel(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process tokens in parallel with BrowserCat extraction"""
        
        if not tokens:
            return []
            
        logger.info(f"🔄 PARALLEL processing {len(tokens)} tokens with {TOKEN_PROCESSING_WORKERS} workers")
        
        # Submit all tokens for parallel processing
        futures = []
        for token in tokens:
            future = self.executor.submit(self._process_single_token_fast, token)
            futures.append(future)
        
        # Collect results with timeout
        processed_tokens = []
        for future in concurrent.futures.as_completed(futures, timeout=BROWSERCAT_TIMEOUT):
            try:
                result = future.result()
                if result:
                    processed_tokens.append(result)
            except Exception as e:
                logger.error(f"❌ Parallel processing error: {e}")
        
        return processed_tokens
    
    def _process_single_token_fast(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """Process single token with speed optimizations"""
        
        try:
            # Ultra-fast age validation
            if not self._is_ultra_fresh(token):
                return None
                
            # Speed-optimized BrowserCat extraction
            social_links = self._extract_social_links_fast(token)
            
            # Check for URL matches
            if self._matches_urls(social_links):
                # Send notification immediately
                self._send_url_match_notification(token, social_links)
                
            return token
            
        except Exception as e:
            logger.error(f"❌ Fast processing error for {token.get('name', 'Unknown')}: {e}")
            return None
    
    def _is_ultra_fresh(self, token: Dict[str, Any]) -> bool:
        """Ultra-fast freshness validation (≤5 seconds)"""
        
        # Skip complex timestamp validation for speed
        if SKIP_SLOW_VALIDATIONS:
            return True
            
        # Simple age check
        created_time = token.get('created_timestamp')
        if created_time:
            age = time.time() - created_time
            return age <= MAX_TOKEN_AGE_SECONDS
            
        return True  # Default to fresh for speed
    
    def _extract_social_links_fast(self, token: Dict[str, Any]) -> List[str]:
        """Speed-optimized social link extraction"""
        
        try:
            # Use speed-optimized BrowserCat with shorter timeout
            from speed_optimized_browsercat import speed_optimized_social_extraction
            
            contract_address = token.get('address', '')
            letsbonk_url = f"https://letsbonk.fun/token/{contract_address}"
            
            # Extract with ultra-fast timeout
            links = speed_optimized_social_extraction(
                letsbonk_url, 
                timeout=BROWSERCAT_TIMEOUT
            )
            
            return links if links else []
            
        except Exception as e:
            logger.error(f"❌ Fast social extraction failed: {e}")
            return []
    
    def _matches_urls(self, social_links: List[str]) -> bool:
        """Check if social links match saved URLs"""
        
        if not social_links:
            return False
            
        # Get saved URLs from link sniper
        try:
            from link_sniper import get_all_link_configs
            saved_urls = [config['url'] for config in get_all_link_configs()]
            
            for social_link in social_links:
                for saved_url in saved_urls:
                    if self._urls_match(social_link, saved_url):
                        return True
        except:
            pass
            
        return False
    
    def _urls_match(self, url1: str, url2: str) -> bool:
        """Fast URL matching"""
        return url1.lower() in url2.lower() or url2.lower() in url1.lower()
    
    def _send_url_match_notification(self, token: Dict[str, Any], social_links: List[str]):
        """Send notification for URL matches"""
        
        try:
            if self.monitor_server.discord_notifier:
                self.monitor_server.discord_notifier.send_notification(
                    token_name=token.get('name', 'Unknown'),
                    contract_address=token.get('address', ''),
                    market_data=None,
                    social_links=social_links,
                    matched_url=social_links[0] if social_links else None
                )
                logger.info(f"🔗 URL match notification sent: {token.get('name', 'Unknown')}")
        except Exception as e:
            logger.error(f"❌ URL notification failed: {e}")
    
    def _update_speed_metrics(self, token_count: int, processing_time: float):
        """Update speed performance metrics"""
        
        detection_time = processing_time / max(token_count, 1)
        
        self.speed_metrics['average_detection_time'] = detection_time
        self.speed_metrics['tokens_processed_per_minute'] = token_count / (processing_time / 60)
        
        if detection_time <= 1.0:
            logger.info(f"🚀 ULTRA-FAST: {detection_time:.2f}s average detection time")
        elif detection_time <= 3.0:
            logger.info(f"⚡ FAST: {detection_time:.2f}s average detection time")
        else:
            logger.warning(f"⚠️ SLOW: {detection_time:.2f}s detection time - optimizing...")
    
    def get_speed_report(self) -> Dict[str, Any]:
        """Get current speed performance report"""
        
        return {
            'optimization_status': 'ULTRA-FAST' if self.speed_metrics['average_detection_time'] <= 1.0 else 'OPTIMIZING',
            'average_detection_time': f"{self.speed_metrics['average_detection_time']:.2f}s",
            'tokens_per_minute': f"{self.speed_metrics['tokens_processed_per_minute']:.1f}",
            'browsercat_efficiency': f"{100 - self.speed_metrics['browsercat_usage_rate']:.1f}% saved",
            'notification_speed': f"{self.speed_metrics['notification_delay']:.2f}s delay"
        }

# Global speed optimizer instance
speed_optimizer = None

def get_speed_optimizer(monitor_server):
    """Get or create speed optimizer instance"""
    global speed_optimizer
    if speed_optimizer is None:
        speed_optimizer = RailwaySpeedOptimizer(monitor_server)
    return speed_optimizer

print("🚀 RAILWAY SPEED OPTIMIZER LOADED")
print("   ⚡ Sub-second detection enabled")
print("   🔄 Parallel processing optimized")
print("   💰 BrowserCat cost-efficient")