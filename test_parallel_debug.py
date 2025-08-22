#!/usr/bin/env python3
"""
Test script to debug current parallel processing issues
"""

import asyncio
import logging
from parallel_processing_debug import debug_parallel_processing, get_debug_processor

# Set up logging to see debug output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_current_parallel_issues():
    """Test and debug current parallel processing implementation"""
    
    # Test with a recent token address from logs
    test_addresses = [
        "U9idm6rscFZpCLLg1uMAPSx6GyoVyxLRRmofu3Qbonk",  # From recent logs
        "LPg41Rdua4xGV8XsQHDNBH1k42dqVqyotJbPb64Zmbonk",  # From recent logs
        "8gXHqRj1qnZ3gCH7M9K8R3Y2eKcB6VkPdFsGpWN5cbonk"   # Made up for testing
    ]
    
    logger.info("🔍 Starting parallel processing debug test...")
    
    processor = await get_debug_processor()
    
    # Test single token parallel processing
    logger.info("\n=== SINGLE TOKEN PARALLEL TEST ===")
    for address in test_addresses[:2]:  # Test first 2
        logger.info(f"\n🧪 Testing parallel processing for {address[:10]}...")
        result = await debug_parallel_processing(address)
        
        print(f"\n📊 RESULTS for {address[:10]}:")
        print(f"   Processing Time: {result.get('processing_time', 0):.3f}s")
        print(f"   Successful Sources: {result.get('successful_sources', 0)}")
        print(f"   Failed Sources: {result.get('failed_sources', 0)}")
        best_result = result.get('best_result')
        best_name = best_result.get('name', 'None') if best_result else 'None'
        print(f"   Best Result: {best_name}")
        print(f"   Efficiency: {result.get('parallel_efficiency', 'Unknown')}")
        
        if result.get('failures'):
            print(f"   Failures:")
            for source, failure in result.get('failures', {}).items():
                print(f"     - {source}: {failure.get('error', 'Unknown error')[:100]}")
    
    # Test batch parallel processing
    logger.info("\n=== BATCH PARALLEL TEST ===")
    batch_results = await processor.batch_debug_tokens(test_addresses)
    
    print(f"\n📦 BATCH RESULTS:")
    successful_batch = 0
    for address, result in batch_results.items():
        best_result = result.get('best_result', {})
        if best_result.get('success'):
            successful_batch += 1
            print(f"   ✅ {address[:10]}: '{best_result.get('name')}' ({result.get('processing_time', 0):.3f}s)")
        else:
            print(f"   ❌ {address[:10]}: Failed - {result.get('error', 'Unknown error')[:50]}")
    
    print(f"\n📊 BATCH SUMMARY: {successful_batch}/{len(test_addresses)} successful")
    
    # Get comprehensive statistics
    stats = processor.get_parallel_statistics()
    print(f"\n📈 PARALLEL PROCESSING STATISTICS:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    await processor.cleanup()
    logger.info("🏁 Parallel processing debug test complete")

async def compare_with_current_system():
    """Compare debugged system with current implementation"""
    logger.info("\n=== COMPARISON WITH CURRENT SYSTEM ===")
    
    # Import current system
    try:
        from pure_name_extractor import PureTokenNameExtractor
        current_processor = PureTokenNameExtractor()
        
        test_address = "U9idm6rscFZpCLLg1uMAPSx6GyoVyxLRRmofu3Qbonk"
        
        # Test current system
        logger.info(f"🔄 Testing CURRENT system for {test_address[:10]}...")
        current_start = asyncio.get_event_loop().time()
        current_result = await current_processor.extract_accurate_token_name(test_address)
        current_time = asyncio.get_event_loop().time() - current_start
        
        # Test debugged system
        logger.info(f"🔄 Testing DEBUGGED system for {test_address[:10]}...")
        debug_result = await debug_parallel_processing(test_address)
        debug_time = debug_result.get('processing_time', 0)
        debug_name = debug_result.get('best_result', {}).get('name')
        
        print(f"\n📊 PERFORMANCE COMPARISON:")
        print(f"   Current System:")
        print(f"     - Result: '{current_result}'")
        print(f"     - Time: {current_time:.3f}s")
        print(f"   Debugged System:")
        print(f"     - Result: '{debug_name}'")
        print(f"     - Time: {debug_time:.3f}s")
        print(f"     - Sources: {debug_result.get('successful_sources', 0)}/{debug_result.get('successful_sources', 0) + debug_result.get('failed_sources', 0)}")
        
        if debug_time < current_time:
            improvement = ((current_time - debug_time) / current_time) * 100
            print(f"   🚀 IMPROVEMENT: {improvement:.1f}% faster")
        else:
            print(f"   ⚠️ DEBUG SYSTEM SLOWER: Need optimization")
            
    except Exception as e:
        logger.error(f"❌ Comparison failed: {e}")

if __name__ == "__main__":
    async def main():
        await test_current_parallel_issues()
        await compare_with_current_system()
    
    asyncio.run(main())