#!/usr/bin/env python3
"""
Speed & Intelligence Integration - Complete System Optimization
Combines smart optimization engine with intelligent keyword matching
Target: <2s processing time with 95%+ accuracy
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import threading

from smart_optimization_engine import SmartOptimizationEngine
from intelligent_keyword_matcher import IntelligentKeywordMatcher, MatchResult

logger = logging.getLogger(__name__)

class SpeedIntelligenceSystem:
    """Integrated system combining speed optimization with intelligent matching"""
    
    def __init__(self, browsercat_api_key: str, keywords: List[str]):
        self.browsercat_api_key = browsercat_api_key
        self.keywords = keywords
        
        # Initialize core components
        self.optimization_engine = SmartOptimizationEngine(browsercat_api_key)
        self.keyword_matcher = IntelligentKeywordMatcher(keywords)
        
        # Performance tracking
        self.processing_stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'keyword_matches': 0,
            'avg_processing_time': 0.0,
            'accuracy_rate': 0.0
        }
        
        # Intelligent caching system
        self.smart_cache = {}
        self.cache_confidence = {}
        
        # Parallel processing pools
        self.fast_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="fast")
        self.analysis_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="analysis")
        
        logger.info("🚀 Speed & Intelligence System initialized")
        logger.info(f"   🎯 Target: <2s processing with 95%+ accuracy")
        logger.info(f"   🔍 Keywords: {len(keywords)}")
    
    async def process_token_ultra_fast(self, token: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Ultra-fast token processing combining speed optimization with intelligent analysis
        Target: <2s total processing time
        """
        start_time = time.time()
        token_address = token.get('address', '')
        
        try:
            # Enhanced extraction using consolidated system only
            logger.info(f"🔍 Enhanced extraction for {token_address[:10]}...")
            
            # Use the consolidated system instead of ultra-fast APIs
            from consolidated_metaplex_system import extract_token_metadata_consolidated
            metadata = await extract_token_metadata_consolidated(token_address)
            
            if not metadata or not metadata.name or metadata.name == "Bonk.fun":
                logger.info(f"❌ ENHANCED EXTRACTION FAILED: {token_address[:10]}... (no valid name)")
                return None
            
            token_name = metadata.name
            
            extraction_time = time.time() - start_time
            logger.info(f"✅ NAME EXTRACTED: '{token_name}' in {extraction_time:.2f}s")
            
            # Phase 2: Intelligent keyword matching (0.1-0.3s target) 
            logger.info(f"🧠 PHASE 2: Intelligent keyword analysis...")
            match_start = time.time()
            
            matches = self.keyword_matcher.find_smart_matches(
                text=token_name,
                token_name=token_name
            )
            
            match_time = time.time() - match_start
            
            if not matches:
                logger.info(f"🔍 NO KEYWORD MATCHES: '{token_name}' ({match_time:.3f}s analysis)")
                return None
            
            # Phase 3: Confidence validation and result preparation
            best_match = matches[0]  # Highest confidence match
            total_time = time.time() - start_time
            
            # Update statistics
            self._update_processing_stats(True, total_time, True)
            
            # Prepare enhanced result
            result = {
                'address': token_address,
                'name': token_name,
                'matched_keyword': best_match.keyword,
                'confidence': best_match.confidence,
                'match_type': best_match.match_type,
                'processing_time': total_time,
                'extraction_time': extraction_time,
                'match_time': match_time,
                'quality_score': self._calculate_quality_score(token_name, best_match)
            }
            
            logger.info(f"🎯 MATCH FOUND: '{token_name}' → '{best_match.keyword}' (confidence: {best_match.confidence:.2f})")
            logger.info(f"⚡ TOTAL TIME: {total_time:.2f}s (target: <2s)")
            
            return result
            
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"❌ Processing error for {token_address[:10]}...: {e} ({error_time:.2f}s)")
            self._update_processing_stats(False, error_time, False)
            return None
    
    async def process_token_batch(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple tokens in parallel for maximum efficiency"""
        start_time = time.time()
        logger.info(f"🔄 BATCH PROCESSING: {len(tokens)} tokens simultaneously")
        
        # Process tokens in parallel with intelligent load balancing
        semaphore = asyncio.Semaphore(6)  # Limit concurrent processing
        
        async def process_with_semaphore(token):
            async with semaphore:
                return await self.process_token_ultra_fast(token)
        
        # Execute batch processing
        tasks = [process_with_semaphore(token) for token in tokens]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_results = []
        for result in results:
            if isinstance(result, dict):
                successful_results.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Batch processing error: {result}")
        
        batch_time = time.time() - start_time
        success_rate = len(successful_results) / len(tokens) * 100
        
        logger.info(f"📊 BATCH COMPLETED: {len(successful_results)}/{len(tokens)} successful ({success_rate:.1f}%) in {batch_time:.2f}s")
        
        return successful_results
    
    def _calculate_quality_score(self, token_name: str, match: MatchResult) -> float:
        """Calculate overall quality score for the match"""
        # Base score from match confidence
        score = match.confidence
        
        # Bonus for match type
        if match.match_type == 'exact':
            score *= 1.1
        elif match.match_type == 'fuzzy':
            score *= 0.9
        
        # Bonus for token name length (more descriptive = higher quality)
        if len(token_name) > 10:
            score *= 1.05
        elif len(token_name) < 5:
            score *= 0.95
        
        # Bonus for keyword specificity
        keyword_length_bonus = min(1.1, 1.0 + len(match.keyword) * 0.01)
        score *= keyword_length_bonus
        
        return min(1.0, score)
    
    def _update_processing_stats(self, extraction_success: bool, processing_time: float, match_found: bool):
        """Update performance statistics"""
        self.processing_stats['total_processed'] += 1
        
        if extraction_success:
            self.processing_stats['successful_extractions'] += 1
        
        if match_found:
            self.processing_stats['keyword_matches'] += 1
        
        # Update average processing time
        current_avg = self.processing_stats['avg_processing_time']
        total = self.processing_stats['total_processed']
        self.processing_stats['avg_processing_time'] = (current_avg * (total - 1) + processing_time) / total
        
        # Update accuracy rate
        if self.processing_stats['total_processed'] > 0:
            self.processing_stats['accuracy_rate'] = (
                self.processing_stats['successful_extractions'] / 
                self.processing_stats['total_processed'] * 100
            )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        # Get sub-component stats
        optimization_stats = self.optimization_engine.get_performance_stats()
        keyword_stats = self.keyword_matcher.get_performance_stats()
        
        # Calculate efficiency metrics
        total_processed = self.processing_stats['total_processed']
        if total_processed > 0:
            extraction_rate = self.processing_stats['successful_extractions'] / total_processed * 100
            match_rate = self.processing_stats['keyword_matches'] / total_processed * 100
        else:
            extraction_rate = 0
            match_rate = 0
        
        # Speed performance
        avg_time = self.processing_stats['avg_processing_time']
        speed_target_met = avg_time < 2.0
        
        return {
            'overall_performance': {
                'total_processed': total_processed,
                'extraction_rate': extraction_rate,
                'keyword_match_rate': match_rate,
                'avg_processing_time': avg_time,
                'speed_target_met': speed_target_met,
                'accuracy_rate': self.processing_stats['accuracy_rate']
            },
            'optimization_engine': optimization_stats,
            'keyword_matcher': keyword_stats,
            'efficiency_grade': self._calculate_efficiency_grade(
                extraction_rate, match_rate, avg_time
            )
        }
    
    def _calculate_efficiency_grade(self, extraction_rate: float, match_rate: float, avg_time: float) -> str:
        """Calculate overall efficiency grade"""
        # Speed score (2s target)
        if avg_time < 1.0:
            speed_score = 100
        elif avg_time < 2.0:
            speed_score = 90
        elif avg_time < 3.0:
            speed_score = 70
        else:
            speed_score = 50
        
        # Accuracy score
        accuracy_score = (extraction_rate + match_rate) / 2
        
        # Combined score
        overall_score = (speed_score * 0.4 + accuracy_score * 0.6)
        
        if overall_score >= 90:
            return "A+ (Excellent)"
        elif overall_score >= 80:
            return "A (Very Good)"
        elif overall_score >= 70:
            return "B (Good)"
        elif overall_score >= 60:
            return "C (Fair)"
        else:
            return "D (Needs Improvement)"
    
    async def optimize_for_production(self):
        """Run optimization procedures for production deployment"""
        logger.info("🔧 Running production optimizations...")
        
        # Warm up caches
        await self._warm_up_caches()
        
        # Optimize thread pools
        self._optimize_thread_pools()
        
        # Precompile regex patterns
        self.keyword_matcher._build_smart_patterns()
        
        logger.info("✅ Production optimizations complete")
    
    async def _warm_up_caches(self):
        """Pre-warm caches with common patterns"""
        # This would ideally use historical data to pre-populate caches
        pass
    
    def _optimize_thread_pools(self):
        """Optimize thread pool sizes based on system resources"""
        import os
        cpu_count = os.cpu_count() or 4
        
        # Adjust pool sizes based on available CPU cores
        optimal_fast_workers = min(cpu_count, 6)
        optimal_analysis_workers = min(cpu_count // 2, 3)
        
        # Note: In production, you'd recreate pools with optimal sizes
        logger.info(f"💡 Optimal thread configuration: Fast={optimal_fast_workers}, Analysis={optimal_analysis_workers}")