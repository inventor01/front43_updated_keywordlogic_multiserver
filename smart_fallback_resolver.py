#!/usr/bin/env python3
"""
Smart Fallback Token Resolver
Intelligently processes fallback tokens with multiple strategies and cleanup
"""

import requests
import time
import logging
import psycopg2
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartFallbackResolver:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            self.database_url = 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway'
    
    def get_db_connection(self):
        return psycopg2.connect(self.database_url)
    
    def clean_test_tokens(self):
        """Remove obvious test/fake tokens from fallback processing"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Remove test tokens with obvious patterns
            cursor.execute("""
                DELETE FROM fallback_processing_coins 
                WHERE contract_address LIKE 'TEST_%' 
                OR contract_address LIKE 'FAKE%'
                OR contract_address LIKE 'RETRY%'
                OR contract_address LIKE 'RAILWAY_%'
                OR contract_address LIKE 'DEMO%'
                OR contract_address LIKE 'INVALID%'
                OR token_name LIKE '%Test%'
                OR token_name LIKE '%Fake%'
                OR token_name LIKE '%Railway%'
            """)
            
            deleted = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"🧹 Cleaned {deleted} test/fake tokens from fallback processing")
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to clean test tokens: {e}")
            return 0
    
    def process_real_tokens(self, batch_size=20):
        """Process real tokens that might have resolvable names"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get real tokens (not test tokens) that haven't been retried too many times
            cursor.execute("""
                SELECT contract_address, token_name, retry_count
                FROM fallback_processing_coins 
                WHERE processing_status = 'name_pending'
                AND retry_count < 3
                AND contract_address NOT LIKE 'TEST_%'
                AND contract_address NOT LIKE 'FAKE%'
                AND contract_address NOT LIKE 'RETRY%'
                AND contract_address NOT LIKE 'RAILWAY_%'
                AND LENGTH(contract_address) > 32
                ORDER BY created_at ASC
                LIMIT %s
            """, (batch_size,))
            
            tokens = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if not tokens:
                logger.info("No real tokens to process")
                return 0
            
            logger.info(f"Processing {len(tokens)} real tokens...")
            
            processed = 0
            for contract_address, current_name, retry_count in tokens:
                logger.info(f"Resolving: {current_name} ({contract_address[:10]}...)")
                
                # Try to resolve the name
                resolved_name = self.resolve_token_name(contract_address)
                
                if resolved_name and not resolved_name.startswith('Unnamed'):
                    # Success! Migrate to detected_tokens
                    if self.migrate_to_detected(contract_address, resolved_name):
                        logger.info(f"✅ MIGRATED: {resolved_name}")
                        processed += 1
                    else:
                        self.update_retry_count(contract_address)
                else:
                    # Update retry count
                    self.update_retry_count(contract_address)
                
                time.sleep(0.5)  # Rate limiting
            
            logger.info(f"Successfully processed {processed}/{len(tokens)} tokens")
            return processed
            
        except Exception as e:
            logger.error(f"Failed to process real tokens: {e}")
            return 0
    
    def resolve_token_name(self, contract_address):
        """Try to resolve token name using multiple methods"""
        
        # Method 1: DexScreener API
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                if pairs and len(pairs) > 0:
                    for pair in pairs:
                        base_token = pair.get('baseToken', {})
                        name = base_token.get('name')
                        
                        if name and len(name.strip()) > 0 and not name.startswith('Unnamed'):
                            return name.strip()
        except:
            pass
        
        # Method 2: Try Solscan (alternative)
        try:
            url = f"https://public-api.solscan.io/token/meta?tokenAddress={contract_address}"
            response = requests.get(url, timeout=8)
            
            if response.status_code == 200:
                data = response.json()
                name = data.get('name')
                
                if name and len(name.strip()) > 0 and not name.startswith('Unnamed'):
                    return name.strip()
        except:
            pass
        
        return None
    
    def migrate_to_detected(self, contract_address, token_name):
        """Migrate successfully resolved token to detected_tokens"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Insert into detected_tokens
            cursor.execute("""
                INSERT INTO detected_tokens 
                (address, name, symbol, platform, status, matched_keywords)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (address) DO NOTHING
            """, (contract_address, token_name, 'BONK', 'LetsBonk', 'detected', []))
            
            # Remove from fallback_processing_coins
            cursor.execute("""
                DELETE FROM fallback_processing_coins 
                WHERE contract_address = %s
            """, (contract_address,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate token: {e}")
            return False
    
    def update_retry_count(self, contract_address):
        """Update retry count for failed resolution"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE fallback_processing_coins 
                SET retry_count = COALESCE(retry_count, 0) + 1,
                    last_retry_at = CURRENT_TIMESTAMP
                WHERE contract_address = %s
            """, (contract_address,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update retry count: {e}")
    
    def cleanup_stuck_tokens(self):
        """Mark tokens as failed after too many retries"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE fallback_processing_coins 
                SET processing_status = 'resolution_failed'
                WHERE retry_count >= 5
                AND processing_status = 'name_pending'
            """)
            
            updated = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Marked {updated} tokens as resolution_failed")
            return updated
            
        except Exception as e:
            logger.error(f"Failed to cleanup stuck tokens: {e}")
            return 0

if __name__ == "__main__":
    resolver = SmartFallbackResolver()
    
    logger.info("🚀 Starting smart fallback resolution...")
    
    # Step 1: Clean test tokens
    cleaned = resolver.clean_test_tokens()
    
    # Step 2: Process real tokens
    processed = resolver.process_real_tokens(batch_size=30)
    
    # Step 3: Cleanup stuck tokens
    failed = resolver.cleanup_stuck_tokens()
    
    logger.info(f"📊 SUMMARY: Cleaned {cleaned} test tokens, processed {processed} real tokens, marked {failed} as failed")