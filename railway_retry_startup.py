#!/usr/bin/env python3
"""
Railway Retry Service Startup - Immediate retry increment for demonstration
"""

import os
import time
import psycopg2
from urllib.parse import urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def railway_startup_retries():
    """Force some retry increments on Railway startup for immediate demonstration"""
    logger.info("🚀 Railway Retry Startup - Initializing retry demonstrations...")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.warning("⚠️ No DATABASE_URL found")
        return
    
    try:
        url = urlparse(database_url)
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            database=url.path[1:],
            user=url.username,
            password=url.password
        )
        
        cursor = conn.cursor()
        
        # Check for tokens that need retry demonstration
        cursor.execute("""
            SELECT contract_address, token_name, retry_count 
            FROM fallback_processing_coins 
            WHERE retry_count < 5
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        tokens = cursor.fetchall()
        
        if tokens:
            logger.info(f"📋 Found {len(tokens)} tokens for retry demonstration")
            
            for token in tokens:
                contract_address = token[0]
                token_name = token[1]
                current_retry = token[2] if token[2] is not None else 0
                
                # Increment retry count
                cursor.execute("""
                    UPDATE fallback_processing_coins 
                    SET retry_count = COALESCE(retry_count, 0) + 1,
                        last_retry_at = CURRENT_TIMESTAMP
                    WHERE contract_address = %s
                """, (contract_address,))
                
                if cursor.rowcount > 0:
                    logger.info(f"📈 Retry {current_retry + 1} for {token_name[:30]}...")
                
                time.sleep(0.5)
            
            conn.commit()
            logger.info("✅ Railway startup retry demonstration completed")
        
        else:
            logger.info("📭 No tokens found for retry demonstration")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Railway startup retry error: {e}")

if __name__ == "__main__":
    railway_startup_retries()