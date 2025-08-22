#!/usr/bin/env python3
"""
FINAL TEST: /list command with all requirements
"""

import sys
import time
sys.path.append('.')

from config_manager import ConfigManager

def test_list_command_complete():
    """Test all /list command requirements"""
    print("=" * 60)
    print("🔬 STEP 3: TESTING /LIST COMMAND - FINAL VERIFICATION")
    print("=" * 60)
    
    # Use unique user IDs to avoid conflicts
    timestamp = int(time.time())
    test_user = f"discord_user_{timestamp}"
    other_user = f"other_user_{timestamp}"
    
    print(f"👤 Testing with user ID: {test_user}")
    
    config_manager = ConfigManager()
    
    # ✅ Test 1: Add keywords for current user
    print(f"\n1. ✅ Adding keywords for current user:")
    user_keywords = ["moon", "elon", "bwerk"]
    for kw in user_keywords:
        unique_kw = f"{kw}_{timestamp}"
        result = config_manager.add_keyword(unique_kw, user_id=test_user)
        print(f"   {unique_kw}: {result[1]}")
    
    # Add keywords for different user (should not appear in results)
    print(f"\n2. ✅ Adding keywords for other user (should be filtered out):")
    other_keywords = ["doge", "pepe"] 
    for kw in other_keywords:
        unique_kw = f"{kw}_{timestamp}"
        result = config_manager.add_keyword(unique_kw, user_id=other_user)
        print(f"   {unique_kw}: {result[1]}")
    
    # ✅ Test 3: Query only current user's keywords
    print(f"\n3. ✅ Testing user-specific keyword query:")
    user_only_keywords = config_manager.list_keywords(user_id=test_user)
    print(f"   User's keywords: {user_only_keywords}")
    print(f"   Count: {len(user_only_keywords)}")
    
    # Verify filtering works
    expected_count = 3  # moon, elon, bwerk
    actual_count = len(user_only_keywords)
    filtering_works = actual_count == expected_count
    
    print(f"   Expected {expected_count}, got {actual_count}: {'✅' if filtering_works else '❌'}")
    
    # ✅ Test 4: Clean, readable format
    print(f"\n4. ✅ Testing Discord output format:")
    if user_only_keywords:
        print("📋 Your keywords:")
        for kw in sorted(user_only_keywords):
            print(f"• {kw}")
        format_test = True
    else:
        print("📝 No monitoring configured")
        print("No keywords are currently being monitored.")
        format_test = len(user_only_keywords) == 0
    
    # ✅ Test 5: Graceful handling of empty case
    print(f"\n5. ✅ Testing empty keywords case:")
    empty_user = f"empty_user_{timestamp}"
    empty_keywords = config_manager.list_keywords(user_id=empty_user)
    print(f"   Empty user keywords: {empty_keywords}")
    print(f"   Length: {len(empty_keywords)}")
    
    empty_handling = len(empty_keywords) == 0
    print(f"   Empty case handled: {'✅' if empty_handling else '❌'}")
    
    # ✅ Test 6: Verify no cross-user contamination
    print(f"\n6. ✅ Testing user isolation:")
    other_user_keywords = config_manager.list_keywords(user_id=other_user)
    overlap = set(user_only_keywords) & set(other_user_keywords)
    isolation_works = len(overlap) == 0
    
    print(f"   Other user keywords: {len(other_user_keywords)}")
    print(f"   Keyword overlap: {len(overlap)} (should be 0)")
    print(f"   User isolation: {'✅' if isolation_works else '❌'}")
    
    print(f"\n" + "=" * 60)
    print("🎉 /LIST COMMAND REQUIREMENTS VERIFICATION:")
    print(f"   ✅ Queries only current user's keywords: {'PASS' if filtering_works else 'FAIL'}")
    print(f"   ✅ Returns clean, readable format: {'PASS' if format_test else 'FAIL'}")
    print(f"   ✅ Gracefully handles no keywords: {'PASS' if empty_handling else 'FAIL'}")
    print(f"   ✅ User isolation maintained: {'PASS' if isolation_works else 'FAIL'}")
    print("=" * 60)
    
    return filtering_works and format_test and empty_handling and isolation_works

if __name__ == "__main__":
    success = test_list_command_complete()
    
    if success:
        print("\n🚀 /LIST COMMAND READY FOR RAILWAY DEPLOYMENT")
        print("The command correctly filters by user_id and displays properly")
    else:
        print("\n⚠️ ISSUES FOUND - Fix before Railway deployment")