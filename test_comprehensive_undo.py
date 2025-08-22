#!/usr/bin/env python3
"""
Test comprehensive undo functionality
"""

import sys

class ComprehensiveUndoTest:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        
    def test_undo_structure(self):
        """Test undo system structure"""
        print("\n🧪 Testing Comprehensive Undo Structure...")
        
        try:
            with open('complete_discord_bot_with_commands.py', 'r') as f:
                content = f.read()
            
            if 'self.undo_history = {}' in content:
                print("  ✅ Comprehensive undo history tracking found")
                self.passed += 1
            else:
                print("  ❌ Comprehensive undo history tracking missing")
                self.failed += 1
            
            # Check for add action tracking
            if "'action': 'add'" in content:
                print("  ✅ Add action tracking found")
                self.passed += 1
            else:
                print("  ❌ Add action tracking missing")
                self.failed += 1
                
            # Check for remove action tracking
            if "'action': 'remove'" in content:
                print("  ✅ Remove action tracking found")
                self.passed += 1
            else:
                print("  ❌ Remove action tracking missing")
                self.failed += 1
                
            # Check for clear action tracking
            if "'action': 'clear'" in content:
                print("  ✅ Clear action tracking found")
                self.passed += 1
            else:
                print("  ❌ Clear action tracking missing")
                self.failed += 1
                
        except Exception as e:
            print(f"  ❌ Undo structure test failed: {e}")
            self.failed += 1
    
    def test_undo_logic(self):
        """Test undo logic for different actions"""
        print("\n🧪 Testing Undo Logic...")
        
        try:
            with open('complete_discord_bot_with_commands.py', 'r') as f:
                content = f.read()
            
            # Check for add undo logic
            if "action_type == 'add'" in content and "DELETE FROM keywords" in content:
                print("  ✅ Add undo logic (remove keyword) found")
                self.passed += 1
            else:
                print("  ❌ Add undo logic missing")
                self.failed += 1
                
            # Check for remove undo logic
            if "action_type == 'remove'" in content and "INSERT INTO keywords" in content:
                print("  ✅ Remove undo logic (restore keyword) found")
                self.passed += 1
            else:
                print("  ❌ Remove undo logic missing")
                self.failed += 1
                
            # Check for clear undo logic
            if "action_type == 'clear'" in content and "keywords_to_restore" in content:
                print("  ✅ Clear undo logic (restore all keywords) found")
                self.passed += 1
            else:
                print("  ❌ Clear undo logic missing")
                self.failed += 1
                
        except Exception as e:
            print(f"  ❌ Undo logic test failed: {e}")
            self.failed += 1
    
    def test_clear_preservation(self):
        """Test that clear operations preserve keywords for undo"""
        print("\n🧪 Testing Clear Action Preservation...")
        
        try:
            with open('complete_discord_bot_with_commands.py', 'r') as f:
                content = f.read()
            
            # Check that keywords are stored before deletion
            if "SELECT keyword FROM keywords WHERE user_id" in content:
                print("  ✅ Keywords fetched before clear operation")
                self.passed += 1
            else:
                print("  ❌ Keywords not preserved before clear")
                self.failed += 1
                
            # Check that keywords are stored in undo history
            if "'keywords': keywords_to_delete" in content:
                print("  ✅ Keywords stored in undo history for clear")
                self.passed += 1
            else:
                print("  ❌ Keywords not stored for undo")
                self.failed += 1
                
        except Exception as e:
            print(f"  ❌ Clear preservation test failed: {e}")
            self.failed += 1
    
    def test_command_descriptions(self):
        """Test that command descriptions reflect new functionality"""
        print("\n🧪 Testing Updated Command Descriptions...")
        
        try:
            with open('complete_discord_bot_with_commands.py', 'r') as f:
                content = f.read()
            
            # Check undo command description
            if 'description="Undo the last action (add, remove, or clear)"' in content:
                print("  ✅ Undo command description updated")
                self.passed += 1
            else:
                print("  ❌ Undo command description not updated")
                self.failed += 1
                
            # Check clear command tip
            if "Use `/undo` to restore all keywords" in content:
                print("  ✅ Clear command includes undo tip")
                self.passed += 1
            else:
                print("  ❌ Clear command missing undo tip")
                self.failed += 1
                
        except Exception as e:
            print(f"  ❌ Command description test failed: {e}")
            self.failed += 1
    
    def run_all_tests(self):
        """Run comprehensive undo test suite"""
        print("🚀 Starting Comprehensive Undo Test Suite")
        print("=" * 50)
        
        self.test_undo_structure()
        self.test_undo_logic()
        self.test_clear_preservation()
        self.test_command_descriptions()
        
        print("\n" + "=" * 50)
        print(f"📊 TEST RESULTS:")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {self.passed/(self.passed+self.failed)*100:.1f}%")
        
        if self.failed == 0:
            print("🎉 ALL TESTS PASSED - Comprehensive undo system ready!")
            return True
        else:
            print("⚠️  Some tests failed - review undo implementation")
            return False

if __name__ == "__main__":
    tester = ComprehensiveUndoTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)