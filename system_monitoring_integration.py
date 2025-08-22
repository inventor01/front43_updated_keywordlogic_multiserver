"""
System Monitoring Integration - Consolidated Performance Tracking
Provides unified monitoring for all fixed systems and optimizations
"""

import logging
import time
from typing import Dict, Any, List
from dataclasses import dataclass, field
# Metaplex system removed - using DexScreener API exclusively
from age_validation_fix import smart_validator
from enhanced_extraction_integration import enhanced_integration

logger = logging.getLogger(__name__)

@dataclass
class SystemPerformanceMetrics:
    """Comprehensive system performance tracking"""
    
    # Overall performance
    total_tokens_processed: int = 0
    successful_extractions: int = 0
    notifications_sent: int = 0
    
    # Component performance
    dexscreener_api_successes: int = 0
    smart_validation_passes: int = 0
    smart_validation_blocks: int = 0
    
    # Real name extractions (excluding "Bonk.fun")
    legitimate_names_extracted: List[str] = field(default_factory=list)
    
    # Performance timings
    average_extraction_time: float = 0.0
    fastest_extraction: float = float('inf')
    
    # System health
    connection_errors_fixed: int = 0
    rate_limit_optimizations: int = 0
    
    def get_success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_tokens_processed == 0:
            return 0.0
        return (self.successful_extractions / self.total_tokens_processed) * 100
    
    def get_legitimate_name_rate(self) -> float:
        """Calculate rate of legitimate name extraction (excluding placeholders)"""
        if self.total_tokens_processed == 0:
            return 0.0
        return (len(self.legitimate_names_extracted) / self.total_tokens_processed) * 100

class SystemMonitoringIntegration:
    """
    Unified monitoring for all system optimizations
    Tracks performance improvements and identifies remaining issues
    """
    
    def __init__(self):
        self.metrics = SystemPerformanceMetrics()
        self.monitoring_start_time = time.time()
        self.last_performance_log = 0
        
    def record_token_processing(self, token_name: str, extraction_time: float, extraction_method: str, success: bool):
        """Record token processing result"""
        self.metrics.total_tokens_processed += 1
        
        if success:
            self.metrics.successful_extractions += 1
            
            # Track legitimate names (not placeholders)
            if token_name not in ["Bonk.fun", "", "Unknown", None]:
                self.metrics.legitimate_names_extracted.append(token_name)
                logger.info(f"✅ LEGITIMATE NAME: '{token_name}' via {extraction_method} ({extraction_time:.2f}s)")
        
        # Update timing metrics
        if extraction_time > 0:
            total_time = self.metrics.average_extraction_time * (self.metrics.total_tokens_processed - 1)
            self.metrics.average_extraction_time = (total_time + extraction_time) / self.metrics.total_tokens_processed
            
            if extraction_time < self.metrics.fastest_extraction:
                self.metrics.fastest_extraction = extraction_time
        
        # Track method performance
        if extraction_method == 'dexscreener_api':
            self.metrics.dexscreener_api_successes += 1
    
    def record_validation_result(self, token_name: str, age_seconds: float, validation_passed: bool):
        """Record smart validation results"""
        if validation_passed:
            self.metrics.smart_validation_passes += 1
            logger.debug(f"✅ SMART VALIDATION: {token_name} passed (age: {age_seconds:.1f}s)")
        else:
            self.metrics.smart_validation_blocks += 1
            logger.debug(f"🚫 SMART VALIDATION: {token_name} blocked (age: {age_seconds:.1f}s)")
    
    def record_connection_fix(self):
        """Record when connection management fixes issues"""
        self.metrics.connection_errors_fixed += 1
    
    def record_notification_sent(self, token_name: str):
        """Record successful notification"""
        self.metrics.notifications_sent += 1
        logger.info(f"📱 NOTIFICATION SENT: {token_name}")
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        uptime_hours = (time.time() - self.monitoring_start_time) / 3600
        
        # Get component statistics
        consolidated_stats = {}
        validation_stats = {}
        integration_stats = {}
        
        try:
            dexscreener_stats = {'method': 'dexscreener_api', 'status': 'active'}
        except:
            pass
            
        try:
            validation_stats = smart_validator.get_validation_stats() if hasattr(smart_validator, 'get_validation_stats') else {}
        except:
            pass
            
        try:
            integration_stats = enhanced_integration.get_integration_stats() if hasattr(enhanced_integration, 'get_integration_stats') else {}
        except:
            pass
        
        return {
            'system_health': 'Excellent' if self.metrics.get_success_rate() > 40 else 'Good' if self.metrics.get_success_rate() > 20 else 'Needs Attention',
            'uptime_hours': round(uptime_hours, 2),
            'performance': {
                'total_processed': self.metrics.total_tokens_processed,
                'success_rate': f"{self.metrics.get_success_rate():.1f}%",
                'legitimate_names': len(self.metrics.legitimate_names_extracted),
                'legitimate_rate': f"{self.metrics.get_legitimate_name_rate():.1f}%",
                'notifications_sent': self.metrics.notifications_sent,
                'avg_extraction_time': f"{self.metrics.average_extraction_time:.2f}s",
                'fastest_extraction': f"{self.metrics.fastest_extraction:.2f}s" if self.metrics.fastest_extraction != float('inf') else "N/A"
            },
            'components': {
                'dexscreener_api': dexscreener_stats,
                'smart_validation': validation_stats,
                'enhanced_integration': integration_stats
            },
            'optimizations': {
                'connection_fixes': self.metrics.connection_errors_fixed,
                'smart_validation_passes': self.metrics.smart_validation_passes,
                'smart_validation_blocks': self.metrics.smart_validation_blocks,
                'dexscreener_successes': self.metrics.dexscreener_api_successes
            },
            'recent_legitimate_names': self.metrics.legitimate_names_extracted[-10:] if len(self.metrics.legitimate_names_extracted) > 10 else self.metrics.legitimate_names_extracted
        }
    
    def log_performance_summary(self, force: bool = False):
        """Log comprehensive performance summary"""
        current_time = time.time()
        
        # Log every 5 minutes or when forced
        if force or (current_time - self.last_performance_log) >= 300:
            status = self.get_comprehensive_status()
            
            logger.info("🎯 SYSTEM OPTIMIZATION PERFORMANCE SUMMARY:")
            logger.info(f"   📊 System Health: {status['system_health']}")
            logger.info(f"   ⏰ Uptime: {status['uptime_hours']} hours")
            logger.info(f"   🔢 Tokens Processed: {status['performance']['total_processed']}")
            logger.info(f"   ✅ Success Rate: {status['performance']['success_rate']}")
            logger.info(f"   🎯 Legitimate Names: {status['performance']['legitimate_names']} ({status['performance']['legitimate_rate']})")
            logger.info(f"   📱 Notifications: {status['performance']['notifications_sent']}")
            logger.info(f"   ⚡ Avg Speed: {status['performance']['avg_extraction_time']}")
            
            if status['recent_legitimate_names']:
                logger.info("   🏆 Recent Legitimate Names:")
                for name in status['recent_legitimate_names'][-5:]:
                    logger.info(f"      → '{name}'")
            
            logger.info(f"   🔧 Optimizations Active:")
            logger.info(f"      ✅ Smart Validation Passes: {status['optimizations']['smart_validation_passes']}")
            logger.info(f"      🚫 Smart Validation Blocks: {status['optimizations']['smart_validation_blocks']}")
            logger.info(f"      🎯 Consolidated Successes: {status['optimizations']['consolidated_successes']}")
            
            self.last_performance_log = current_time
    
    def get_system_weaknesses(self) -> List[str]:
        """Identify remaining system weaknesses"""
        weaknesses = []
        status = self.get_comprehensive_status()
        
        if self.metrics.get_success_rate() < 50:
            weaknesses.append(f"Success rate below 50% ({status['performance']['success_rate']})")
        
        if self.metrics.average_extraction_time > 10:
            weaknesses.append(f"Slow extraction time ({status['performance']['avg_extraction_time']})")
        
        if self.metrics.connection_errors_fixed > 10:
            weaknesses.append("High connection error rate")
        
        if len(self.metrics.legitimate_names_extracted) < self.metrics.total_tokens_processed * 0.3:
            weaknesses.append("Low legitimate name extraction rate")
        
        return weaknesses

# Global monitoring instance
system_monitor = SystemMonitoringIntegration()

def record_extraction_success(token_name: str, extraction_time: float, method: str):
    """Simple interface to record successful extraction"""
    system_monitor.record_token_processing(token_name, extraction_time, method, True)

def record_validation_result(token_name: str, age: float, passed: bool):
    """Simple interface to record validation result"""
    system_monitor.record_validation_result(token_name, age, passed)

def log_system_performance():
    """Simple interface to log system performance"""
    system_monitor.log_performance_summary()

def get_system_status() -> Dict[str, Any]:
    """Simple interface to get system status"""
    return system_monitor.get_comprehensive_status()