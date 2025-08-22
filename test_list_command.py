#!/usr/bin/env python3
"""
Test script for /list command - verify user-specific keyword filtering
"""

import sys
sys.path.append('.')

from config_manager import ConfigManager

def test_list_command_user_filtering():
    """Test that /list command shows only current user's keywords"""
    print("=" * 60)
    print("🧪 STEP 3: TESTING /LIST COMMAND - User Filtering")
    print("=" * 60)
    
    config_manager = ConfigManager()
    
    # First, add some test keywords with different user IDs
    print("\n1. Adding test keywords with different user IDs:")
    
    # User 1 keywords
    user1_id = "user123"
    user1_keywords = ["moon", "elon", "bwerk"]
    
    # User 2 keywords  
    user2_id = "user456"
    user2_keywords = ["doge", "shiba", "pepe"]
    
    for keyword in user1_keywords:
        result = config_manager.add_keyword(keyword, user_id=user1_id)
        print(f"   User1: {keyword} → {result}")
    
    for keyword in user2_keywords:
        result = config_manager.add_keyword(keyword, user_id=user2_id)
        print(f"   User2: {keyword} → {result}")
    
    # Test current list_keywords method (shows ALL keywords)
    print("\n2. Current list_keywords() method (shows ALL):")
    all_keywords = config_manager.list_keywords()
    print(f"   Returns: {all_keywords}")
    print(f"   Count: {len(all_keywords)}")
    
    # Check if method supports user_id filtering
    print("\n3. Testing user-specific filtering:")
    
    # Check if list_keywords accepts user_id parameter
    try:
        user1_only = config_manager.list_keywords(user_id=user1_id)
        print(f"   ✅ User1 keywords: {user1_only}")
        if set(user1_only) == set(user1_keywords):
            print("   ✅ User filtering works correctly")
        else:
            print(f"   ❌ Expected {user1_keywords}, got {user1_only}")
    except TypeError:
        print("   ❌ list_keywords() doesn't accept user_id parameter")
        print("   🔧 Need to add user_id filtering to list_keywords method")
        return False
    
    return True

def test_discord_list_command_simulation():
    """Simulate Discord /list command call"""
    print("\n🤖 SIMULATING DISCORD /LIST COMMAND:")
    print("-" * 40)
    
    # Mock Discord interaction
    class MockInteraction:
        def __init__(self, user_id):
            self.user = type('User', (), {'id': user_id})()
    
    # Test with specific user
    interaction = MockInteraction(user_id=123456789)
    print(f"👤 User ID: {interaction.user.id}")
    
    config_manager = ConfigManager()
    
    # This is what the Discord bot should do:
    try:
        # Should get only THIS user's keywords
        user_keywords = config_manager.list_keywords(user_id=str(interaction.user.id))
        print(f"📋 User's keywords: {user_keywords}")
        
        # Format like Discord embed should show
        if user_keywords:
            keyword_text = "\n".join([f"• {kw}" for kw in user_keywords])
            print(f"\n📝 Expected Discord output:")
            print(f"📋 Your keywords:")
            print(keyword_text)
        else:
            print("\n📝 Expected Discord output:")
            print("📝 No monitoring configured")
            print("No keywords are currently being monitored.")
        
        return True
        
    except TypeError:
        print("❌ list_keywords() method needs user_id parameter")
        return False

if __name__ == "__main__":
    print("🚀 Testing /list command user filtering...")
    
    test1 = test_list_command_user_filtering()
    test2 = test_discord_list_command_simulation()
    
    print(f"\n📊 RESULTS:")
    print(f"   User filtering test: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"   Discord simulation: {'✅ PASS' if test2 else '❌ FAIL'}")
    
    if not (test1 and test2):
        print("\n🔧 FIXES NEEDED:")
        print("   1. Add user_id parameter to list_keywords() method")
        print("   2. Update Discord bot to pass user_id to list_keywords()")
        print("   3. Ensure SQL query filters by user_id")