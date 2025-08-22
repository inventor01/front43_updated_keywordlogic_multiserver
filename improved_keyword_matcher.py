#!/usr/bin/env python3
"""
Improved Keyword Matcher
Fixes keyword matching bugs with flexible matching strategies
"""

import re
import psycopg2
import os
from typing import List, Tuple

class ImprovedKeywordMatcher:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            self.database_url = 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway'
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for better matching"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove common articles and prepositions
        stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = text.split()
        filtered_words = [word for word in words if word not in stop_words]
        
        # Join back and clean
        normalized = ' '.join(filtered_words)
        
        # Remove special characters except spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return normalized.strip()
    
    def flexible_keyword_match(self, token_name: str, keywords: List[str]) -> List[str]:
        """Flexible keyword matching with multiple strategies"""
        
        if not token_name or not keywords:
            return []
        
        matches = []
        token_normalized = self.normalize_text(token_name)
        token_words = set(token_normalized.split())
        
        for keyword in keywords:
            keyword_normalized = self.normalize_text(keyword)
            keyword_words = set(keyword_normalized.split())
            
            # Strategy 1: Exact normalized match
            if token_normalized == keyword_normalized:
                matches.append(keyword)
                continue
            
            # Strategy 2: One contains the other
            if token_normalized in keyword_normalized or keyword_normalized in token_normalized:
                matches.append(keyword)
                continue
            
            # Strategy 3: Word overlap (at least 50% of words match)
            if len(keyword_words) > 0:
                overlap = len(token_words.intersection(keyword_words))
                overlap_ratio = overlap / len(keyword_words)
                
                if overlap_ratio >= 0.5:  # 50% word overlap
                    matches.append(keyword)
                    continue
            
            # Strategy 4: Partial word matching (for compound words)
            for token_word in token_words:
                for keyword_word in keyword_words:
                    if len(token_word) >= 4 and len(keyword_word) >= 4:
                        if token_word in keyword_word or keyword_word in token_word:
                            matches.append(keyword)
                            break
                if keyword in matches:
                    break
        
        return list(set(matches))  # Remove duplicates
    
    def test_matching_improvements(self):
        """Test the improved matching on known cases"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Get all keywords
            cursor.execute("SELECT keyword FROM keywords")
            keywords = [row[0] for row in cursor.fetchall()]
            
            # Test cases
            test_cases = [
                "Big Leagues",
                "The Big Leagues", 
                "big leagues",
                "COIN",
                "Nuclear Waste",
                "Radioactive Material"
            ]
            
            print("🧪 TESTING IMPROVED KEYWORD MATCHING")
            print("=" * 50)
            
            for test_token in test_cases:
                matches = self.flexible_keyword_match(test_token, keywords)
                
                print(f"\nToken: '{test_token}'")
                if matches:
                    print(f"✅ Matches ({len(matches)}):")
                    for match in matches:
                        print(f"   - {match}")
                else:
                    print(f"❌ No matches")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"Testing error: {e}")
    
    def fix_big_leagues_token(self):
        """Specifically fix the Big Leagues token notification"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            token_address = '52zV3a4p44BE7PnpsvKWdGq1PjTJNTE8jDW7db7Ybonk'
            
            # Get keywords
            cursor.execute("SELECT keyword FROM keywords")
            keywords = [row[0] for row in cursor.fetchall()]
            
            # Test improved matching
            matches = self.flexible_keyword_match("Big Leagues", keywords)
            
            if matches:
                print(f"🎯 FIXING BIG LEAGUES TOKEN")
                print(f"Found matches: {matches}")
                
                # Update the token with correct keyword matches
                cursor.execute("""
                    UPDATE detected_tokens 
                    SET matched_keywords = %s, status = 'detected'
                    WHERE address = %s
                """, (matches, token_address))
                
                # Create notification record
                cursor.execute("""
                    INSERT INTO notified_tokens 
                    (token_address, token_name, notification_sent, notification_type)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (token_address) DO UPDATE SET
                    notification_sent = EXCLUDED.notification_sent,
                    notification_type = EXCLUDED.notification_type
                """, (token_address, "Big Leagues", True, "retroactive_fix"))
                
                conn.commit()
                
                print(f"✅ Fixed Big Leagues token:")
                print(f"   - Updated matched_keywords: {matches}")
                print(f"   - Changed status to 'detected'")
                print(f"   - Added notification record")
                
            else:
                print(f"❌ Still no matches found for Big Leagues")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"Fix error: {e}")

if __name__ == "__main__":
    matcher = ImprovedKeywordMatcher()
    
    # Test the improvements
    matcher.test_matching_improvements()
    
    # Fix the specific Big Leagues issue
    print(f"\n" + "="*50)
    matcher.fix_big_leagues_token()