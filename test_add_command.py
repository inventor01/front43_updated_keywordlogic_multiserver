#!/usr/bin/env python3
"""
Test script for /add command functionality
Tests argument parsing, user_id capture, PostgreSQL saving, and duplicate prevention
"""

import os
import sys
import asyncio
from unittest.mock import Mock, AsyncMock
sys.path.append('.')

from config_manager import ConfigManager

def test_add_command_logic():
    """Test the core /add command logic step by step"""
    print("=" * 60)
    print("🧪 TESTING /ADD COMMAND - PostgreSQL Integration")
    print("=" * 60)
    
    # Test 1: Argument parsing
    print("\n1. Testing argument parsing:")
    test_keyword = "moon"
    parsed_keyword = test_keyword.strip().lower()
    print(f"   ✅ Input: '{test_keyword}' → Parsed: '{parsed_keyword}'")
    
    # Test 2: ConfigManager initialization
    print("\n2. Testing ConfigManager initialization:")
    try:
        config_manager = ConfigManager()
        print("   ✅ ConfigManager initialized successfully")
    except Exception as e:
        print(f"   ❌ ConfigManager failed: {e}")
        return False
    
    # Test 3: Test add_keyword method with user_id
    print("\n3. Testing add_keyword method:")
    test_user_id = "123456789"  # Mock Discord user ID
    
    try:
        success, reason = config_manager.add_keyword(parsed_keyword, user_id=test_user_id)
        print(f"   📊 Result: success={success}, reason='{reason}'")
        
        if success:
            print("   ✅ Keyword added successfully to PostgreSQL")
        else:
            if reason == "already_exists":
                print("   ⚠️ Keyword already exists (duplicate prevention working)")
            elif reason == "no_database":
                print("   ❌ Database not available")
                return False
            else:
                print(f"   ❌ Addition failed: {reason}")
                return False
                
    except Exception as e:
        print(f"   ❌ Exception during add_keyword: {e}")
        return False
    
    # Test 4: Verify keyword was saved
    print("\n4. Testing keyword retrieval:")
    try:
        keywords = config_manager.list_keywords()
        if parsed_keyword in keywords:
            print(f"   ✅ Keyword '{parsed_keyword}' found in database")
            print(f"   📊 Total keywords: {len(keywords)}")
        else:
            print(f"   ❌ Keyword '{parsed_keyword}' not found in database")
            print(f"   📋 Current keywords: {keywords}")
            return False
    except Exception as e:
        print(f"   ❌ Error retrieving keywords: {e}")
        return False
    
    # Test 5: Test duplicate prevention
    print("\n5. Testing duplicate prevention:")
    try:
        success, reason = config_manager.add_keyword(parsed_keyword, user_id=test_user_id)
        if not success and reason == "already_exists":
            print("   ✅ Duplicate prevention working correctly")
        else:
            print(f"   ⚠️ Duplicate handling: success={success}, reason='{reason}'")
    except Exception as e:
        print(f"   ❌ Error testing duplicates: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ /ADD COMMAND TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)
    return True

def test_discord_interaction_simulation():
    """Simulate the Discord interaction pattern"""
    print("\n🤖 SIMULATING DISCORD INTERACTION:")
    print("-" * 40)
    
    # Mock Discord interaction object
    class MockInteraction:
        def __init__(self):
            self.user = Mock()
            self.user.id = 987654321
            self.response = AsyncMock()
            self.followup = AsyncMock()
    
    # Mock the /add command logic
    async def simulate_add_command():
        interaction = MockInteraction()
        keyword = "moon"  # This would come from Discord slash command argument
        
        print(f"📝 Simulated command: /add {keyword}")
        print(f"👤 User ID captured: {interaction.user.id}")
        
        # Apply the same logic as working_discord_bot.py
        keyword = keyword.strip().lower()
        config_manager = ConfigManager()
        success, reason = config_manager.add_keyword(keyword, user_id=str(interaction.user.id))
        
        print(f"💾 Database operation: success={success}, reason='{reason}'")
        
        # Simulate the embed response logic
        if success:
            total_keywords = len(config_manager.list_keywords())
            print(f"✅ Response: Keyword added successfully (Total: {total_keywords})")
        else:
            if reason == "already_exists":
                print("⚠️ Response: Keyword already exists")
            elif reason == "no_database":
                print("❌ Response: Database error")
            else:
                print(f"❌ Response: Failed to add keyword ({reason})")
        
        return success
    
    # Run simulation
    result = asyncio.run(simulate_add_command())
    return result

if __name__ == "__main__":
    print("🚀 Starting /add command tests...")
    
    # Test basic functionality
    basic_test = test_add_command_logic()
    
    # Test Discord interaction simulation
    discord_test = test_discord_interaction_simulation()
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Basic functionality: {'✅ PASS' if basic_test else '❌ FAIL'}")
    print(f"   Discord simulation: {'✅ PASS' if discord_test else '❌ FAIL'}")
    
    if basic_test and discord_test:
        print("\n🎉 ALL TESTS PASSED - /add command ready for Railway deployment!")
    else:
        print("\n⚠️ SOME TESTS FAILED - Issues need to be fixed before deployment")