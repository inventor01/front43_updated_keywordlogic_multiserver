#!/usr/bin/env python3
"""
Front 42 - Command Test Suite
Tests the 5 essential commands: add, remove, undo, list, clear
"""

import sys

class Front42CommandTest:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        
    def test_discord_bot_structure(self):
        """Test Discord bot command structure"""
        print("\n🧪 Testing Discord Bot Command Structure...")
        
        try:
            import complete_discord_bot_with_commands
            bot_module = complete_discord_bot_with_commands
            
            # Check if bot instance exists
            if hasattr(bot_module, 'bot'):
                print("  ✅ Bot instance created successfully")
                self.passed += 1
            else:
                print("  ❌ Bot instance not found")
                self.failed += 1
            
            # Check if DatabaseManager exists
            if hasattr(bot_module, 'DatabaseManager'):
                print("  ✅ DatabaseManager class found")
                self.passed += 1
            else:
                print("  ❌ DatabaseManager class missing")
                self.failed += 1
                
            print("  ✅ Discord bot module loads successfully")
            self.passed += 1
            
        except Exception as e:
            print(f"  ❌ Discord bot module failed to load: {e}")
            self.failed += 1
    
    def test_command_definitions(self):
        """Test that all 5 commands are defined"""
        print("\n🧪 Testing Command Definitions...")
        
        try:
            with open('complete_discord_bot_with_commands.py', 'r') as f:
                content = f.read()
            
            commands = ['add', 'remove', 'undo', 'list', 'clear']
            
            for cmd in commands:
                if f'@bot.tree.command(name="{cmd}"' in content:
                    print(f"  ✅ Command '{cmd}' defined correctly")
                    self.passed += 1
                else:
                    print(f"  ❌ Command '{cmd}' not found")
                    self.failed += 1
                    
        except Exception as e:
            print(f"  ❌ Error checking command definitions: {e}")
            self.failed += 1
    
    def test_database_integration(self):
        """Test database integration"""
        print("\n🧪 Testing Database Integration...")
        
        try:
            import complete_discord_bot_with_commands
            
            # Test database manager
            db = complete_discord_bot_with_commands.DatabaseManager()
            
            if hasattr(db, 'database_url'):
                print("  ✅ Database URL configured")
                self.passed += 1
            else:
                print("  ❌ Database URL not configured")
                self.failed += 1
            
            if hasattr(db, 'get_connection'):
                print("  ✅ Database connection method exists")
                self.passed += 1
            else:
                print("  ❌ Database connection method missing")
                self.failed += 1
                
        except Exception as e:
            print(f"  ❌ Database integration test failed: {e}")
            self.failed += 1
    
    def test_undo_functionality(self):
        """Test undo functionality structure"""
        print("\n🧪 Testing Undo Functionality...")
        
        try:
            with open('complete_discord_bot_with_commands.py', 'r') as f:
                content = f.read()
            
            if 'last_removed_keyword' in content:
                print("  ✅ Undo tracking mechanism found")
                self.passed += 1
            else:
                print("  ❌ Undo tracking mechanism missing")
                self.failed += 1
            
            if 'bot.last_removed_keyword[user_id] = keyword' in content:
                print("  ✅ Undo storage logic found")
                self.passed += 1
            else:
                print("  ❌ Undo storage logic missing")
                self.failed += 1
                
        except Exception as e:
            print(f"  ❌ Undo functionality test failed: {e}")
            self.failed += 1
    
    def test_clear_confirmation(self):
        """Test clear command confirmation"""
        print("\n🧪 Testing Clear Command Confirmation...")
        
        try:
            with open('complete_discord_bot_with_commands.py', 'r') as f:
                content = f.read()
            
            if 'yes i want to delete all' in content:
                print("  ✅ Clear command confirmation phrase found")
                self.passed += 1
            else:
                print("  ❌ Clear command confirmation missing")
                self.failed += 1
            
            if 'confirm: str' in content:
                print("  ✅ Clear command requires confirmation parameter")
                self.passed += 1
            else:
                print("  ❌ Clear command confirmation parameter missing")
                self.failed += 1
                
        except Exception as e:
            print(f"  ❌ Clear confirmation test failed: {e}")
            self.failed += 1
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Front 42 Command Test Suite")
        print("=" * 50)
        
        self.test_discord_bot_structure()
        self.test_command_definitions()
        self.test_database_integration()
        self.test_undo_functionality()
        self.test_clear_confirmation()
        
        print("\n" + "=" * 50)
        print(f"📊 TEST RESULTS:")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {self.passed/(self.passed+self.failed)*100:.1f}%")
        
        if self.failed == 0:
            print("🎉 ALL TESTS PASSED - Front 42 ready for use!")
            return True
        else:
            print("⚠️  Some tests failed - review issues before deployment")
            return False

if __name__ == "__main__":
    tester = Front42CommandTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)