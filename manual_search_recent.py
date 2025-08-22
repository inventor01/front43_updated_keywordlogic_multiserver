#!/usr/bin/env python3
"""
Manual test for search_recent functionality
Tests the database search without requiring Discord bot
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_search_recent_manual(hours=2, keyword=None):
    """Manually test the search_recent functionality"""
    
    try:
        # Connect to PostgreSQL database
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("❌ No DATABASE_URL found")
            return False
            
        logger.info(f"🔍 Testing search_recent: last {hours} hours" + (f" for keyword '{keyword}'" if keyword else ""))
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Calculate time range
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Query for tokens detected in the specified timeframe
        cursor.execute("""
            SELECT address, name, symbol, detection_timestamp, matched_keywords
            FROM detected_tokens 
            WHERE detection_timestamp >= %s
            ORDER BY detection_timestamp DESC
            LIMIT 100
        """, (cutoff_time,))
        
        recent_tokens = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not recent_tokens:
            logger.info(f"🔍 No tokens found in the last {hours} hours")
            return True
            
        logger.info(f"📊 Found {len(recent_tokens)} tokens in database")
        
        # Check each token for keyword matches
        missed_matches = []
        total_checked = 0
        
        # Get keywords (simulate from database or use test keywords)
        test_keywords = ['bonk', 'pepe', 'doge', 'plan b', 'ai', 'moon', 'safe']
        
        for token_data in recent_tokens:
            address, name, symbol, timestamp, existing_keywords = token_data
            total_checked += 1
            
            # Skip if already has keyword matches
            if existing_keywords and len(existing_keywords) > 0:
                continue
            
            # Check against keywords
            if keyword:
                search_keywords = [keyword.lower().strip()]
            else:
                search_keywords = test_keywords
            
            matched_keywords = []
            name_lower = name.lower() if name else ""
            symbol_lower = symbol.lower() if symbol else ""
            
            for kw in search_keywords:
                if kw in name_lower or kw in symbol_lower:
                    matched_keywords.append(kw)
            
            if matched_keywords:
                missed_matches.append({
                    'address': address,
                    'name': name,
                    'symbol': symbol,
                    'timestamp': timestamp,
                    'matched_keywords': matched_keywords
                })
        
        # Display results
        if missed_matches:
            logger.info(f"🚨 Found {len(missed_matches)} missed keyword matches:")
            for i, token in enumerate(missed_matches[:5], 1):
                age = datetime.now() - token['timestamp']
                age_str = f"{int(age.total_seconds()//60)}m ago" if age.total_seconds() < 3600 else f"{int(age.total_seconds()//3600)}h ago"
                logger.info(f"  {i}. {token['name']} ({token['symbol']})")
                logger.info(f"     Matched: {', '.join(token['matched_keywords'])}")
                logger.info(f"     Contract: {token['address'][:20]}...")
                logger.info(f"     Detected: {age_str}")
        else:
            logger.info(f"✅ No missed matches found - all {total_checked} tokens were properly checked")
        
        logger.info(f"📊 Search Summary:")
        logger.info(f"   • Tokens checked: {total_checked}")
        logger.info(f"   • Time range: Last {hours} hours")
        logger.info(f"   • Keywords: {len(search_keywords)} {'(specific)' if keyword else '(test keywords)'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database search error: {e}")
        return False

if __name__ == "__main__":
    """Run manual test with command line arguments"""
    
    hours = 2
    keyword = None
    
    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
        except ValueError:
            logger.error("❌ First argument must be number of hours")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        keyword = sys.argv[2]
    
    logger.info("🔍 MANUAL SEARCH_RECENT TEST")
    logger.info("=" * 50)
    
    success = test_search_recent_manual(hours, keyword)
    
    if success:
        logger.info("✅ Manual search_recent test completed")
    else:
        logger.error("❌ Manual search_recent test failed")
        sys.exit(1)