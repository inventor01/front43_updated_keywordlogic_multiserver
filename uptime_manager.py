"""
Integrated Uptime Manager - Ensures continuous operation
Works directly with the existing monitoring system
"""

import time
import logging
import threading
import gc
import psutil
import signal
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

class UptimeManager:
    def __init__(self, server_instance):
        self.server = server_instance
        self.running = True
        self.start_time = time.time()
        self.last_cleanup = time.time()
        self.error_count = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.graceful_shutdown)
        signal.signal(signal.SIGINT, self.graceful_shutdown)
        
        # Start background monitoring
        self.start_background_monitoring()
        logger.info("✅ Uptime manager initialized - targeting 100% availability")
        
    def start_background_monitoring(self):
        """Start background threads for uptime management"""
        # Memory cleanup thread (every 15 minutes)
        cleanup_thread = threading.Thread(target=self.memory_cleanup_loop, daemon=True, name="UptimeCleanup")
        cleanup_thread.start()
        
        # Health monitoring thread (every 5 minutes)  
        health_thread = threading.Thread(target=self.health_monitoring_loop, daemon=True, name="UptimeHealth")
        health_thread.start()
        
        # Resource monitoring thread (every 2 minutes)
        resource_thread = threading.Thread(target=self.resource_monitoring_loop, daemon=True, name="UptimeResources")
        resource_thread.start()
        
        logger.info("✅ Background uptime monitoring threads started")
        
    def memory_cleanup_loop(self):
        """Background memory cleanup to prevent memory leaks"""
        while self.running:
            try:
                time.sleep(900)  # 15 minutes
                self.perform_memory_cleanup()
            except Exception as e:
                logger.error(f"Memory cleanup error: {e}")
                self.error_count += 1
                time.sleep(900)
                
    def health_monitoring_loop(self):
        """Background health monitoring"""
        while self.running:
            try:
                time.sleep(300)  # 5 minutes
                self.perform_health_check()
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                self.error_count += 1
                time.sleep(300)
                
    def resource_monitoring_loop(self):
        """Background resource monitoring"""
        while self.running:
            try:
                time.sleep(120)  # 2 minutes
                self.monitor_system_resources()
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                self.error_count += 1
                time.sleep(120)
                
    def perform_memory_cleanup(self):
        """Aggressive memory cleanup to prevent bloat"""
        try:
            initial_memory = psutil.virtual_memory().percent
            
            # Clear TTL caches if they exist in the server
            if hasattr(self.server, 'seen_token_addresses') and self.server.seen_token_addresses:
                cache_size = len(self.server.seen_token_addresses)
                self.server.seen_token_addresses.clear()
                logger.info(f"🧹 Cleared token address cache ({cache_size} entries)")
                
            if hasattr(self.server, 'processed_signatures') and self.server.processed_signatures:
                cache_size = len(self.server.processed_signatures)
                self.server.processed_signatures.clear()
                logger.info(f"🧹 Cleared signature cache ({cache_size} entries)")
                
            # Force garbage collection
            collected = gc.collect()
            
            final_memory = psutil.virtual_memory().percent
            memory_freed = initial_memory - final_memory
            
            uptime_hours = (time.time() - self.start_time) / 3600
            
            logger.info(f"🧹 CLEANUP COMPLETE: {collected} objects freed, "
                       f"Memory: {final_memory:.1f}% (freed {memory_freed:.1f}%), "
                       f"Uptime: {uptime_hours:.2f}h")
            
            self.last_cleanup = time.time()
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
            self.error_count += 1
            
    def perform_health_check(self):
        """Comprehensive system health check"""
        try:
            uptime_hours = (time.time() - self.start_time) / 3600
            memory = psutil.virtual_memory()
            
            # Check if monitoring is still active
            if hasattr(self.server, 'running') and not self.server.running:
                logger.warning("⚠️ Main server reports not running - investigating")
                self.error_count += 1
                return
                
            # Check Discord bot health
            if hasattr(self.server, 'bot') and self.server.bot:
                if self.server.bot.is_closed():
                    logger.warning("⚠️ Discord bot connection lost")
                    self.error_count += 1
                else:
                    logger.debug("✅ Discord bot connection healthy")
                    
            # Log health status
            logger.info(f"💓 HEALTH CHECK: Uptime {uptime_hours:.2f}h, "
                       f"Memory {memory.percent:.1f}%, Errors: {self.error_count}")
                       
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.error_count += 1
            
    def monitor_system_resources(self):
        """Monitor CPU, memory, and disk usage"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Log resource usage periodically
            logger.debug(f"📊 RESOURCES: Memory {memory.percent:.1f}%, CPU {cpu_percent:.1f}%")
            
            # Trigger cleanup if memory is high
            if memory.percent > 80:
                logger.warning(f"⚠️ High memory usage: {memory.percent:.1f}% - triggering cleanup")
                self.perform_memory_cleanup()
                
            # Log warning if CPU is consistently high
            if cpu_percent > 85:
                logger.warning(f"⚠️ High CPU usage: {cpu_percent:.1f}%")
                
        except Exception as e:
            logger.error(f"Resource monitoring failed: {e}")
            self.error_count += 1
            
    def graceful_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"🔄 Received shutdown signal {signum} - graceful shutdown initiated")
        self.running = False
        
        # Stop server components gracefully
        if hasattr(self.server, 'running'):
            self.server.running = False
            
        # Allow time for cleanup
        time.sleep(2)
        
        logger.info("✅ Graceful shutdown completed")
        sys.exit(0)
        
    def get_uptime_statistics(self):
        """Get comprehensive uptime statistics"""
        current_time = time.time()
        uptime_seconds = current_time - self.start_time
        uptime_hours = uptime_seconds / 3600
        uptime_days = uptime_hours / 24
        
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()
        except:
            memory = None
            cpu_percent = 0
            
        # Calculate availability percentage
        availability = max(0, 100 - (self.error_count * 0.1))  # Each error reduces availability by 0.1%
        
        stats = {
            "uptime_hours": round(uptime_hours, 2),
            "uptime_days": round(uptime_days, 2),
            "uptime_seconds": int(uptime_seconds),
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "current_time": datetime.fromtimestamp(current_time).isoformat(),
            "error_count": self.error_count,
            "availability_percent": round(availability, 2),
            "memory_percent": memory.percent if memory else 0,
            "cpu_percent": cpu_percent,
            "last_cleanup": datetime.fromtimestamp(self.last_cleanup).isoformat(),
            "status": "healthy" if self.error_count < 5 else "degraded" if self.error_count < 20 else "critical"
        }
        
        return stats
        
    def log_uptime_milestone(self):
        """Log uptime milestones"""
        uptime_hours = (time.time() - self.start_time) / 3600
        
        # Log milestones
        if uptime_hours >= 24 and uptime_hours % 24 < 0.1:  # Every 24 hours
            logger.info(f"🎉 UPTIME MILESTONE: {uptime_hours:.1f} hours ({uptime_hours/24:.1f} days) - "
                       f"Errors: {self.error_count}")
        elif uptime_hours >= 1 and uptime_hours % 1 < 0.1:  # Every hour
            logger.info(f"⏰ HOURLY UPTIME: {uptime_hours:.1f}h - System running smoothly")
            
    def shutdown(self):
        """Manual shutdown"""
        self.running = False
        logger.info("🔄 Uptime manager shutting down")

# Simple wrapper for integration
def create_uptime_manager(server_instance):
    """Create and return uptime manager instance"""
    return UptimeManager(server_instance)