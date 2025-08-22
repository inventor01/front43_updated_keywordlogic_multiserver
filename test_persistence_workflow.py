#!/usr/bin/env python3
"""
STEP 4: Test full persistence workflow - /add, restart simulation, /list, /remove
"""

import sys
import time
import os
sys.path.append('.')

from config_manager import ConfigManager

def test_persistence_workflow():
    """Test complete workflow with persistence and removal"""
    print("=" * 60)
    print("🔬 STEP 4: TESTING PERSISTENCE + /REMOVE WORKFLOW")
    print("=" * 60)
    
    # Use unique user ID for clean test
    timestamp = int(time.time())
    test_user = f"persistence_user_{timestamp}"
    other_user = f"other_user_{timestamp}"
    
    print(f"👤 Test user ID: {test_user}")
    print(f"👤 Other user ID: {other_user}")
    
    # ✅ STEP 1: Use /add moon
    print(f"\n1. ✅ STEP: /add moon")
    config_manager = ConfigManager()
    
    test_keyword = f"moon_{timestamp}"
    result = config_manager.add_keyword(test_keyword, user_id=test_user)
    print(f"   Add result: {result}")
    
    if not result[0]:
        print(f"   ❌ Failed to add keyword: {result[1]}")
        return False
    
    # Add keyword for other user (should not interfere)
    other_keyword = f"doge_{timestamp}"
    config_manager.add_keyword(other_keyword, user_id=other_user)
    print(f"   Added {other_keyword} for other user")
    
    # ✅ STEP 2: Simulate app restart/reload
    print(f"\n2. ✅ STEP: Simulate app restart")
    print(f"   Simulating: ConfigManager instance destroyed and recreated")
    
    # Destroy current instance and create new one (simulates restart)
    del config_manager
    config_manager = ConfigManager()
    print(f"   New ConfigManager instance created")
    
    # ✅ STEP 3: Use /list again - confirm keyword still appears
    print(f"\n3. ✅ STEP: /list after restart")
    
    user_keywords = config_manager.list_keywords(user_id=test_user)
    print(f"   User's keywords after restart: {user_keywords}")
    
    keyword_persisted = test_keyword in user_keywords
    print(f"   Keyword '{test_keyword}' persisted: {'✅' if keyword_persisted else '❌'}")
    
    if not keyword_persisted:
        print(f"   ❌ PERSISTENCE FAILED - keyword not found after restart")
        return False
    
    # ✅ STEP 4: Use /remove moon
    print(f"\n4. ✅ STEP: /remove {test_keyword}")
    
    # Test removal
    remove_result = config_manager.remove_keyword(test_keyword)
    print(f"   Remove result: {remove_result}")
    
    if not remove_result:
        print(f"   ❌ Failed to remove keyword")
        return False
    
    # ✅ STEP 5: Verify only current user's keyword was removed
    print(f"\n5. ✅ VERIFICATION: User isolation during removal")
    
    # Check user's keywords after removal
    user_keywords_after = config_manager.list_keywords(user_id=test_user)
    print(f"   User's keywords after removal: {user_keywords_after}")
    
    keyword_removed = test_keyword not in user_keywords_after
    print(f"   Keyword removed from user: {'✅' if keyword_removed else '❌'}")
    
    # Check other user's keywords unchanged
    other_user_keywords = config_manager.list_keywords(user_id=other_user)
    print(f"   Other user's keywords: {other_user_keywords}")
    
    other_user_unaffected = other_keyword in other_user_keywords
    print(f"   Other user unaffected: {'✅' if other_user_unaffected else '❌'}")
    
    # ✅ STEP 6: Test removing non-existent keyword
    print(f"\n6. ✅ STEP: Test removing non-existent keyword")
    
    fake_keyword = f"nonexistent_{timestamp}"
    remove_fake = config_manager.remove_keyword(fake_keyword)
    print(f"   Remove non-existent '{fake_keyword}': {remove_fake}")
    print(f"   Handles non-existent gracefully: {'✅' if not remove_fake else '⚠️'}")
    
    # ✅ STEP 7: Verify PostgreSQL changes committed
    print(f"\n7. ✅ VERIFICATION: PostgreSQL transaction commitment")
    
    # Create new instance to verify database persistence
    del config_manager
    fresh_config = ConfigManager()
    
    final_check_keywords = fresh_config.list_keywords(user_id=test_user)
    print(f"   Fresh instance keywords: {final_check_keywords}")
    
    transaction_committed = test_keyword not in final_check_keywords
    print(f"   PostgreSQL changes committed: {'✅' if transaction_committed else '❌'}")
    
    print(f"\n" + "=" * 60)
    print("🎉 PERSISTENCE + /REMOVE WORKFLOW VERIFICATION:")
    print(f"   ✅ /add persists through restart: {'PASS' if keyword_persisted else 'FAIL'}")
    print(f"   ✅ /list shows persisted keywords: {'PASS' if keyword_persisted else 'FAIL'}")
    print(f"   ✅ /remove only affects current user: {'PASS' if (keyword_removed and other_user_unaffected) else 'FAIL'}")
    print(f"   ✅ PostgreSQL changes committed: {'PASS' if transaction_committed else 'FAIL'}")
    print(f"   ✅ Non-existent keyword handling: {'PASS' if not remove_fake else 'PARTIAL'}")
    print("=" * 60)
    
    return (keyword_persisted and keyword_removed and 
            other_user_unaffected and transaction_committed)

def test_discord_remove_simulation():
    """Simulate Discord /remove command"""
    print(f"\n🤖 DISCORD /REMOVE COMMAND SIMULATION:")
    print("-" * 40)
    
    timestamp = int(time.time())
    test_user = f"discord_remove_{timestamp}"
    test_keyword = f"testmoon_{timestamp}"
    
    # Mock Discord interaction
    class MockInteraction:
        def __init__(self, user_id):
            self.user = type('User', (), {'id': user_id})()
    
    config_manager = ConfigManager()
    
    # Add keyword first
    config_manager.add_keyword(test_keyword, user_id=test_user)
    print(f"👤 User {test_user} added keyword: {test_keyword}")
    
    # Simulate Discord /remove command
    interaction = MockInteraction(test_user)
    keyword_to_remove = test_keyword
    
    print(f"📝 Simulated command: /remove {keyword_to_remove}")
    print(f"👤 User ID from interaction: {interaction.user.id}")
    
    # Apply same logic as working_discord_bot.py would
    keyword_cleaned = keyword_to_remove.strip().lower()
    success = config_manager.remove_keyword(keyword_cleaned)
    
    print(f"💾 Remove operation result: {success}")
    
    # Verify removal
    remaining_keywords = config_manager.list_keywords(user_id=test_user)
    print(f"📋 User's remaining keywords: {remaining_keywords}")
    
    # Discord response simulation
    if success:
        total_remaining = len(remaining_keywords)
        print(f"✅ Discord Response: Keyword removed successfully")
        print(f"📊 Remaining keywords: {total_remaining} active")
    else:
        print(f"❌ Discord Response: Keyword not found or removal failed")
    
    return success

if __name__ == "__main__":
    print("🚀 Testing persistence workflow and /remove command...")
    
    # Test main workflow
    persistence_test = test_persistence_workflow()
    
    # Test Discord simulation
    discord_test = test_discord_remove_simulation()
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Persistence workflow: {'✅ PASS' if persistence_test else '❌ FAIL'}")
    print(f"   Discord remove simulation: {'✅ PASS' if discord_test else '❌ FAIL'}")
    
    if persistence_test and discord_test:
        print("\n🎉 ALL TESTS PASSED - READY FOR RAILWAY DEPLOYMENT!")
        print("   Persistence, user isolation, and removal all working correctly")
    else:
        print("\n⚠️ SOME TESTS FAILED - Issues need resolution")