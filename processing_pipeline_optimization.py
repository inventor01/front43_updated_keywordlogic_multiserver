#!/usr/bin/env python3
"""
Processing Pipeline Optimization
Implements intelligent token processing pipeline with maximum speed and accuracy
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ProcessingPriority(Enum):
    """Token processing priority levels"""
    INSTANT = "instant"      # Keyword matches - process immediately  
    HIGH = "high"           # Recently detected - process within 5s
    NORMAL = "normal"       # Standard tokens - process within 30s
    LOW = "low"            # Old tokens - batch process

@dataclass
class TokenProcessingTask:
    """Container for token processing tasks"""
    address: str
    priority: ProcessingPriority
    submitted_at: float
    attempts: int = 0
    last_attempt: float = 0.0
    metadata: Dict[str, Any] = None

class OptimizedProcessingPipeline:
    """
    Intelligent processing pipeline with priority queues and smart batching
    Optimizes for both speed and accuracy based on token characteristics
    """
    
    def __init__(self):
        # Priority queues for different processing speeds
        self.instant_queue = asyncio.Queue(maxsize=50)
        self.high_priority_queue = asyncio.Queue(maxsize=200)
        self.normal_queue = asyncio.Queue(maxsize=1000)
        self.batch_queue = asyncio.Queue(maxsize=5000)
        
        # Processing workers
        self.instant_workers = []
        self.batch_workers = []
        self.running = False
        
        # Performance tracking
        self.processing_stats = {
            'instant_processed': 0,
            'high_processed': 0,
            'normal_processed': 0,
            'batch_processed': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0
        }
        
        # Smart batching configuration
        self.batch_size = 20
        self.batch_timeout = 5.0  # Process batch every 5 seconds
        self.max_concurrent_batches = 3
        
    async def start_processing_workers(self):
        """Start all processing workers"""
        self.running = True
        
        # Instant processing workers (1-2 workers for immediate response)
        for i in range(2):
            worker = asyncio.create_task(self._instant_processing_worker(f"instant-{i}"))
            self.instant_workers.append(worker)
        
        # High priority workers (3-4 workers for fast processing)
        for i in range(3):
            worker = asyncio.create_task(self._high_priority_worker(f"high-{i}"))
            self.instant_workers.append(worker)
        
        # Batch processing workers (2-3 workers for efficiency)
        for i in range(2):
            worker = asyncio.create_task(self._batch_processing_worker(f"batch-{i}"))
            self.batch_workers.append(worker)
        
        logger.info("🚀 PIPELINE: All processing workers started")
        
    async def submit_token(self, token_address: str, priority: ProcessingPriority = ProcessingPriority.NORMAL, metadata: Dict[str, Any] = None) -> bool:
        """Submit token for processing with specified priority"""
        
        task = TokenProcessingTask(
            address=token_address,
            priority=priority,
            submitted_at=time.time(),
            metadata=metadata or {}
        )
        
        try:
            if priority == ProcessingPriority.INSTANT:
                await self.instant_queue.put(task)
                logger.info(f"⚡ INSTANT QUEUE: {token_address[:10]}... (keyword match)")
                
            elif priority == ProcessingPriority.HIGH:
                await self.high_priority_queue.put(task)
                logger.info(f"🚀 HIGH PRIORITY: {token_address[:10]}... (recent token)")
                
            elif priority == ProcessingPriority.NORMAL:
                await self.normal_queue.put(task)
                logger.debug(f"📝 NORMAL QUEUE: {token_address[:10]}...")
                
            else:  # LOW priority
                await self.batch_queue.put(task)
                logger.debug(f"📦 BATCH QUEUE: {token_address[:10]}...")
            
            return True
            
        except asyncio.QueueFull:
            logger.warning(f"⚠️ QUEUE FULL: Dropping {token_address[:10]}... (priority: {priority.value})")
            return False
    
    async def _instant_processing_worker(self, worker_name: str):
        """Worker for instant processing of keyword matches"""
        from speed_optimizations import get_speed_optimizer
        
        logger.info(f"⚡ WORKER START: {worker_name} (instant processing)")
        
        while self.running:
            try:
                # Get task with timeout
                task = await asyncio.wait_for(self.instant_queue.get(), timeout=1.0)
                
                start_time = time.time()
                logger.info(f"⚡ {worker_name}: Processing {task.address[:10]}... (INSTANT)")
                
                # Ultra-fast processing for keyword matches
                optimizer = await get_speed_optimizer()
                
                # Parallel name and timestamp extraction
                name_task = optimizer.ultra_fast_name_extraction(task.address)
                timestamp_task = optimizer.lightning_timestamp_validation(task.address)
                
                name, (age_seconds, confidence) = await asyncio.gather(
                    name_task, timestamp_task, return_exceptions=True
                )
                
                processing_time = time.time() - start_time
                
                if name and not isinstance(name, Exception):
                    # Success - send immediate notification
                    result = {
                        'address': task.address,
                        'name': name,
                        'age_seconds': age_seconds if not isinstance(age_seconds, Exception) else 60.0,
                        'confidence': confidence if not isinstance(confidence, Exception) else 0.8,
                        'processing_time': processing_time,
                        'priority': task.priority.value,
                        'worker': worker_name
                    }
                    
                    # Trigger immediate notification
                    await self._send_instant_notification(result)
                    
                    self.processing_stats['instant_processed'] += 1
                    logger.info(f"✅ {worker_name}: INSTANT SUCCESS '{name}' ({processing_time:.3f}s)")
                    
                else:
                    # Failed instant processing - demote to high priority for retry
                    task.priority = ProcessingPriority.HIGH
                    task.attempts += 1
                    await self.high_priority_queue.put(task)
                    logger.warning(f"⚠️ {worker_name}: INSTANT FAILED, demoting to HIGH priority")
                
                self.instant_queue.task_done()
                
            except asyncio.TimeoutError:
                # No tasks - continue waiting
                continue
            except Exception as e:
                logger.error(f"❌ {worker_name}: Worker error - {e}")
                continue
    
    async def _high_priority_worker(self, worker_name: str):
        """Worker for high-priority processing"""
        from speed_optimizations import get_speed_optimizer
        
        logger.info(f"🚀 WORKER START: {worker_name} (high priority)")
        
        while self.running:
            try:
                # Get task with timeout
                task = await asyncio.wait_for(self.high_priority_queue.get(), timeout=2.0)
                
                start_time = time.time()
                logger.info(f"🚀 {worker_name}: Processing {task.address[:10]}... (HIGH)")
                
                optimizer = await get_speed_optimizer()
                result = await optimizer._process_single_token_optimized(task.address)
                
                processing_time = time.time() - start_time
                
                if result.get('name'):
                    result.update({
                        'processing_time': processing_time,
                        'priority': task.priority.value,
                        'worker': worker_name,
                        'attempts': task.attempts
                    })
                    
                    # Send notification for successful high-priority processing
                    await self._process_high_priority_result(result)
                    
                    self.processing_stats['high_processed'] += 1
                    logger.info(f"✅ {worker_name}: HIGH SUCCESS '{result['name']}' ({processing_time:.3f}s)")
                    
                else:
                    # Failed high priority - demote to batch processing
                    task.priority = ProcessingPriority.LOW
                    task.attempts += 1
                    if task.attempts < 3:  # Limit retries
                        await self.batch_queue.put(task)
                        logger.warning(f"⚠️ {worker_name}: HIGH FAILED, demoting to BATCH")
                
                self.high_priority_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ {worker_name}: Worker error - {e}")
                continue
    
    async def _batch_processing_worker(self, worker_name: str):
        """Worker for batch processing of multiple tokens"""
        from speed_optimizations import get_speed_optimizer
        
        logger.info(f"📦 WORKER START: {worker_name} (batch processing)")
        
        while self.running:
            try:
                # Collect batch of tokens
                batch_tokens = []
                batch_start = time.time()
                
                # Collect tokens for batch (with timeout)
                while len(batch_tokens) < self.batch_size and (time.time() - batch_start) < self.batch_timeout:
                    try:
                        task = await asyncio.wait_for(self.batch_queue.get(), timeout=1.0)
                        batch_tokens.append(task)
                        self.batch_queue.task_done()
                    except asyncio.TimeoutError:
                        if batch_tokens:  # Process partial batch
                            break
                        continue
                
                if not batch_tokens:
                    continue
                
                logger.info(f"📦 {worker_name}: Processing batch of {len(batch_tokens)} tokens")
                
                # Extract addresses for batch processing
                addresses = [task.address for task in batch_tokens]
                
                # Batch process all tokens
                optimizer = await get_speed_optimizer()
                results = await optimizer.batch_process_tokens(addresses)
                
                # Process results
                successful = 0
                for task in batch_tokens:
                    result = results.get(task.address)
                    if result and result.get('name'):
                        result.update({
                            'priority': task.priority.value,
                            'worker': worker_name,
                            'attempts': task.attempts
                        })
                        await self._process_batch_result(result)
                        successful += 1
                
                self.processing_stats['batch_processed'] += successful
                logger.info(f"✅ {worker_name}: BATCH COMPLETE {successful}/{len(batch_tokens)} successful")
                
            except Exception as e:
                logger.error(f"❌ {worker_name}: Batch worker error - {e}")
                continue
    
    async def _send_instant_notification(self, result: Dict[str, Any]):
        """Send immediate Discord notification for instant results"""
        # This would integrate with your Discord notification system
        logger.info(f"📢 INSTANT NOTIFICATION: {result['name']} ({result['processing_time']:.3f}s)")
        
    async def _process_high_priority_result(self, result: Dict[str, Any]):
        """Process high-priority results"""
        # This would integrate with your notification and storage systems
        logger.info(f"📢 HIGH PRIORITY RESULT: {result['name']} ({result['processing_time']:.3f}s)")
        
    async def _process_batch_result(self, result: Dict[str, Any]):
        """Process batch results"""
        # This would integrate with your storage and analysis systems
        logger.debug(f"📦 BATCH RESULT: {result['name']}")
    
    async def stop_workers(self):
        """Stop all processing workers"""
        self.running = False
        
        # Cancel all workers
        for worker in self.instant_workers + self.batch_workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.instant_workers, *self.batch_workers, return_exceptions=True)
        
        logger.info("🛑 PIPELINE: All workers stopped")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status and performance metrics"""
        return {
            'queues': {
                'instant': self.instant_queue.qsize(),
                'high_priority': self.high_priority_queue.qsize(),
                'normal': self.normal_queue.qsize(),
                'batch': self.batch_queue.qsize()
            },
            'processing_stats': self.processing_stats,
            'workers_running': self.running
        }

# Global pipeline instance
processing_pipeline = None

async def get_processing_pipeline():
    """Get initialized processing pipeline"""
    global processing_pipeline
    if processing_pipeline is None:
        processing_pipeline = OptimizedProcessingPipeline()
        await processing_pipeline.start_processing_workers()
    return processing_pipeline

async def submit_token_for_processing(token_address: str, is_keyword_match: bool = False, metadata: Dict[str, Any] = None):
    """Quick interface for submitting tokens for optimized processing"""
    pipeline = await get_processing_pipeline()
    
    priority = ProcessingPriority.INSTANT if is_keyword_match else ProcessingPriority.HIGH
    return await pipeline.submit_token(token_address, priority, metadata)