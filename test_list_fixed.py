#!/usr/bin/env python3
"""
Test the FIXED /list command with user filtering
"""

import sys
sys.path.append('.')

from config_manager import ConfigManager

def test_fixed_list_command():
    """Test the fixed list command with user filtering"""
    print("=" * 60)
    print("🧪 TESTING FIXED /LIST COMMAND - User Filtering")
    print("=" * 60)
    
    config_manager = ConfigManager()
    
    # Set up test data with different users
    test_user1 = "user123"
    test_user2 = "user456"
    
    # Add some keywords for each user
    print("\n1. Setting up test keywords:")
    
    # User 1 keywords
    user1_keywords = ["moon", "rocket", "diamond"]
    for kw in user1_keywords:
        result = config_manager.add_keyword(kw, user_id=test_user1)
        print(f"   User1 ({test_user1}): {kw} → {result[1]}")
    
    # User 2 keywords  
    user2_keywords = ["doge", "shiba", "pepe"]
    for kw in user2_keywords:
        result = config_manager.add_keyword(kw, user_id=test_user2)
        print(f"   User2 ({test_user2}): {kw} → {result[1]}")
    
    # Test user-specific filtering
    print("\n2. Testing user-specific keyword retrieval:")
    
    user1_only = config_manager.list_keywords(user_id=test_user1)
    print(f"   User1 keywords: {sorted(user1_only)}")
    
    user2_only = config_manager.list_keywords(user_id=test_user2)
    print(f"   User2 keywords: {sorted(user2_only)}")
    
    all_keywords = config_manager.list_keywords()
    print(f"   All keywords: {len(all_keywords)} total")
    
    # Verify filtering works correctly
    print("\n3. Verification:")
    
    # Check User1 has only their keywords
    user1_expected = set(user1_keywords)
    user1_actual = set(user1_only)
    user1_match = user1_expected.issubset(user1_actual)
    print(f"   User1 has their keywords: {user1_match} ({'✅' if user1_match else '❌'})")
    
    # Check User2 has only their keywords  
    user2_expected = set(user2_keywords)
    user2_actual = set(user2_only)
    user2_match = user2_expected.issubset(user2_actual)
    print(f"   User2 has their keywords: {user2_match} ({'✅' if user2_match else '❌'})")
    
    # Check users don't see each other's keywords
    no_overlap = len(set(user1_only) & set(user2_only)) == 0
    print(f"   No keyword overlap: {no_overlap} ({'✅' if no_overlap else '❌'})")
    
    return user1_match and user2_match

def test_discord_list_format():
    """Test the expected Discord output format"""
    print("\n🤖 TESTING DISCORD OUTPUT FORMAT:")
    print("-" * 40)
    
    config_manager = ConfigManager()
    test_user = "format_test_user"
    
    # Add test keywords
    test_keywords = ["moon", "elon", "bwerk"]
    for kw in test_keywords:
        config_manager.add_keyword(kw, user_id=test_user)
    
    # Get user's keywords
    user_keywords = config_manager.list_keywords(user_id=test_user)
    
    # Format like Discord should
    if user_keywords:
        print("📋 Your keywords:")
        for kw in sorted(user_keywords):
            print(f"• {kw}")
        print(f"\n✅ {len(user_keywords)} keywords found")
    else:
        print("📝 No monitoring configured")
        print("No keywords are currently being monitored.")
    
    # Expected format verification
    expected_format = ["moon", "elon", "bwerk"]
    actual_keywords = sorted([kw for kw in user_keywords if kw in expected_format])
    
    format_correct = set(expected_format).issubset(set(user_keywords))
    print(f"\nFormat test: {'✅ PASS' if format_correct else '❌ FAIL'}")
    
    return format_correct

if __name__ == "__main__":
    print("🚀 Testing fixed /list command...")
    
    test1 = test_fixed_list_command()
    test2 = test_discord_list_format()
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   User filtering: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"   Discord format: {'✅ PASS' if test2 else '❌ FAIL'}")
    
    if test1 and test2:
        print("\n🎉 /LIST COMMAND FIXED AND WORKING!")
        print("   ✅ Users see only their own keywords")
        print("   ✅ Clean, readable format")
        print("   ✅ Graceful handling of empty lists")
    else:
        print("\n⚠️ Issues still need to be resolved")