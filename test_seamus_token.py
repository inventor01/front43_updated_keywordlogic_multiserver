#!/usr/bin/env python3
"""
Test the fixed insert_detected_token method with the Seamus token
"""

from fixed_dual_table_processor import FixedDualTableProcessor

def test_seamus_token():
    """Test inserting the Seamus token that caused the error"""
    print("🧪 Testing Seamus Token Processing")
    print("=" * 50)
    
    processor = FixedDualTableProcessor()
    
    # Test data matching the error log
    token_data = {
        'address': '9Hi9JnjmEP123456789',  # Simulated address
        'name': 'Seamus',
        'symbol': 'SEAMUS'
    }
    
    print(f"📝 Testing token: {token_data['name']}")
    print(f"   Address: {token_data['address']}")
    
    try:
        # Test the insert_detected_token method that was missing
        result = processor.insert_detected_token(
            address=token_data['address'],
            name=token_data['name'],
            symbol=token_data['symbol'],
            name_status='resolved'
        )
        
        if result:
            print(f"✅ SUCCESS: Token inserted with ID {result}")
            print("   Method insert_detected_token is working correctly")
        else:
            print("❌ FAILED: Token insertion returned None")
            
    except AttributeError as e:
        if 'insert_detected_token' in str(e):
            print("❌ CONFIRMED: insert_detected_token method is missing")
            print("   This is the source of the error")
        else:
            print(f"❌ DIFFERENT ERROR: {e}")
    except Exception as e:
        print(f"❌ OTHER ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed")

if __name__ == "__main__":
    test_seamus_token()