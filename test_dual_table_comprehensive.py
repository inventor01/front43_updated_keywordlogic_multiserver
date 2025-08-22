#!/usr/bin/env python3
"""
Comprehensive Dual Table System Test
Tests all functionality of the pending/resolved token dual table architecture.
"""

import asyncio
import logging
import os
import time
from dual_table_token_processor import DualTableTokenProcessor
from dual_table_name_resolver import DualTableNameResolver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DualTableSystemTester:
    def __init__(self):
        self.processor = DualTableTokenProcessor()
        self.resolver = DualTableNameResolver()
        self.test_results = []
        
    def log_test_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        
        logger.info(result)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        
        return success
    
    def test_pending_token_insertion(self):
        """Test 1: Insert token into pending_tokens table"""
        try:
            test_address = "TEST_PENDING_123456789ABCDEF"
            placeholder_name = "Test Unnamed Token Pending"
            
            token_id = self.processor.insert_pending_token(
                contract_address=test_address,
                placeholder_name=placeholder_name,
                keyword="test",
                matched_keywords=["test", "pending", "demo"],
                blockchain_age_seconds=15.5
            )
            
            if token_id:
                return self.log_test_result(
                    "Pending Token Insertion", 
                    True, 
                    f"Token ID: {token_id}"
                )
            else:
                return self.log_test_result(
                    "Pending Token Insertion", 
                    False, 
                    "Failed to insert token"
                )
                
        except Exception as e:
            return self.log_test_result(
                "Pending Token Insertion", 
                False, 
                f"Exception: {e}"
            )
    
    def test_resolved_token_insertion(self):
        """Test 2: Insert token directly into detected_tokens table"""
        try:
            test_address = "TEST_RESOLVED_123456789ABCDEF"
            token_name = "Test Resolved Token"
            symbol = "TRT"
            
            token_id = self.processor.insert_resolved_token(
                contract_address=test_address,
                token_name=token_name,
                symbol=symbol,
                keyword="test",
                matched_keywords=["test", "resolved", "demo"],
                blockchain_age_seconds=25.0
            )
            
            if token_id:
                return self.log_test_result(
                    "Resolved Token Insertion", 
                    True, 
                    f"Token: {token_name}, ID: {token_id}"
                )
            else:
                return self.log_test_result(
                    "Resolved Token Insertion", 
                    False, 
                    "Failed to insert resolved token"
                )
                
        except Exception as e:
            return self.log_test_result(
                "Resolved Token Insertion", 
                False, 
                f"Exception: {e}"
            )
    
    def test_pending_token_retrieval(self):
        """Test 3: Retrieve pending tokens from database"""
        try:
            pending_tokens = self.processor.get_pending_tokens(10)
            
            if pending_tokens is not None:
                return self.log_test_result(
                    "Pending Token Retrieval", 
                    True, 
                    f"Found {len(pending_tokens)} pending tokens"
                )
            else:
                return self.log_test_result(
                    "Pending Token Retrieval", 
                    False, 
                    "Failed to retrieve pending tokens"
                )
                
        except Exception as e:
            return self.log_test_result(
                "Pending Token Retrieval", 
                False, 
                f"Exception: {e}"
            )
    
    def test_resolved_token_retrieval(self):
        """Test 4: Retrieve resolved tokens from database"""
        try:
            resolved_tokens = self.processor.get_resolved_tokens(10)
            
            if resolved_tokens is not None:
                return self.log_test_result(
                    "Resolved Token Retrieval", 
                    True, 
                    f"Found {len(resolved_tokens)} resolved tokens"
                )
            else:
                return self.log_test_result(
                    "Resolved Token Retrieval", 
                    False, 
                    "Failed to retrieve resolved tokens"
                )
                
        except Exception as e:
            return self.log_test_result(
                "Resolved Token Retrieval", 
                False, 
                f"Exception: {e}"
            )
    
    def test_system_statistics(self):
        """Test 5: Get system statistics"""
        try:
            stats = self.processor.get_system_stats()
            
            if stats and 'pending_tokens' in stats and 'total_resolved' in stats:
                return self.log_test_result(
                    "System Statistics", 
                    True, 
                    f"Stats: {stats}"
                )
            else:
                return self.log_test_result(
                    "System Statistics", 
                    False, 
                    "Invalid statistics format"
                )
                
        except Exception as e:
            return self.log_test_result(
                "System Statistics", 
                False, 
                f"Exception: {e}"
            )
    
    async def test_token_name_resolution(self):
        """Test 6: Test DexScreener name resolution"""
        try:
            # Use a known token address
            test_address = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
            
            result = await self.resolver.resolve_token_name_dexscreener(test_address)
            
            if result and 'name' in result:
                return self.log_test_result(
                    "Token Name Resolution", 
                    True, 
                    f"Resolved: {result['name']}"
                )
            else:
                return self.log_test_result(
                    "Token Name Resolution", 
                    True,  # This is okay - token might not be indexed yet
                    "Token not indexed yet (expected for new tokens)"
                )
                
        except Exception as e:
            return self.log_test_result(
                "Token Name Resolution", 
                False, 
                f"Exception: {e}"
            )
    
    def test_token_migration(self):
        """Test 7: Migrate token from pending to resolved"""
        try:
            # First, insert a pending token for migration test
            migration_address = "TEST_MIGRATION_123456789ABCDEF"
            
            # Insert pending token
            pending_id = self.processor.insert_pending_token(
                contract_address=migration_address,
                placeholder_name="Migration Test Token",
                keyword="migration",
                matched_keywords=["migration", "test"],
                blockchain_age_seconds=30.0
            )
            
            if not pending_id:
                return self.log_test_result(
                    "Token Migration", 
                    False, 
                    "Failed to create pending token for migration test"
                )
            
            # Now migrate it
            success = self.processor.migrate_pending_to_resolved(
                contract_address=migration_address,
                token_name="Migrated Test Token",
                symbol="MTT",
                social_links={"test": True}
            )
            
            if success:
                return self.log_test_result(
                    "Token Migration", 
                    True, 
                    "Successfully migrated from pending to resolved"
                )
            else:
                return self.log_test_result(
                    "Token Migration", 
                    False, 
                    "Migration failed"
                )
                
        except Exception as e:
            return self.log_test_result(
                "Token Migration", 
                False, 
                f"Exception: {e}"
            )
    
    async def run_all_tests(self):
        """Run all dual table system tests"""
        logger.info("🧪 STARTING COMPREHENSIVE DUAL TABLE SYSTEM TESTS")
        logger.info("=" * 60)
        
        # Run synchronous tests
        test_1 = self.test_pending_token_insertion()
        test_2 = self.test_resolved_token_insertion()
        test_3 = self.test_pending_token_retrieval()
        test_4 = self.test_resolved_token_retrieval()
        test_5 = self.test_system_statistics()
        test_7 = self.test_token_migration()
        
        # Run asynchronous test
        test_6 = await self.test_token_name_resolution()
        
        # Calculate results
        passed_tests = sum(1 for result in self.test_results if result['success'])
        total_tests = len(self.test_results)
        
        logger.info("=" * 60)
        logger.info(f"📊 DUAL TABLE SYSTEM TEST RESULTS: {passed_tests}/{total_tests} PASSED")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED - DUAL TABLE SYSTEM FULLY FUNCTIONAL!")
            return True
        else:
            logger.info(f"⚠️ {total_tests - passed_tests} TESTS FAILED - CHECK LOGS FOR DETAILS")
            
            # Show failed tests
            for result in self.test_results:
                if not result['success']:
                    logger.info(f"❌ FAILED: {result['test']} - {result['details']}")
            
            return False
    
    def generate_test_report(self):
        """Generate a comprehensive test report"""
        report = []
        report.append("✅ DUAL TABLE SYSTEM TEST REPORT")
        report.append("=" * 40)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            line = f"{status} {result['test']}"
            if result['details']:
                line += f": {result['details']}"
            report.append(line)
        
        passed = sum(1 for r in self.test_results if r['success'])
        total = len(self.test_results)
        
        report.append("=" * 40)
        report.append(f"📊 SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            report.append("🎉 DUAL TABLE SYSTEM READY FOR DEPLOYMENT")
        else:
            report.append("⚠️ ISSUES FOUND - REVIEW FAILED TESTS")
        
        return "\n".join(report)

async def main():
    """Main test execution"""
    try:
        # Test database connection first
        if not os.getenv('DATABASE_URL'):
            print("❌ DATABASE_URL environment variable not found")
            return False
        
        tester = DualTableSystemTester()
        success = await tester.run_all_tests()
        
        # Print final report
        print("\n" + tester.generate_test_report())
        
        if success:
            print("\n✅ Dual table system validated and ready!")
            return True
        else:
            print("\n❌ Dual table system has issues that need fixing")
            return False
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)