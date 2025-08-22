#!/usr/bin/env python3

import sys
sys.path.append('.')

from config_manager import ConfigManager

def test_add_keyword():
    """Test the add_keyword functionality"""
    config_manager = ConfigManager()
    
    # Test adding a new keyword
    test_keyword = "frog"
    print(f"Testing add_keyword with: '{test_keyword}'")
    
    success = config_manager.add_keyword(test_keyword, user_id="TestUser")
    
    if success:
        print(f"✅ Successfully added keyword: {test_keyword}")
    else:
        print(f"❌ Failed to add keyword: {test_keyword}")
    
    return success

if __name__ == "__main__":
    test_add_keyword()