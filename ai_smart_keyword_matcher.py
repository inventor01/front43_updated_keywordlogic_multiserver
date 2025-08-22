"""
AI Smart Keyword Matcher with Typo Detection and Fuzzy Matching
Prevents missed matches due to typos, variations, and spelling differences
"""

import re
import logging
from typing import List, Optional, Dict, Tuple
from fuzzywuzzy import fuzz, process
import difflib
import time

logger = logging.getLogger(__name__)

class AISmartKeywordMatcher:
    """
    Intelligent keyword matching system with typo tolerance and fuzzy matching
    Solves the "buy a busienss" vs "buy a business" problem automatically
    """
    
    def __init__(self, keywords: List[str], fuzzy_threshold: int = 85):
        self.keywords = [k.lower().strip() for k in keywords if k.strip()]
        self.fuzzy_threshold = fuzzy_threshold  # 85% similarity threshold
        self.keyword_variations = self._generate_keyword_variations()
        self.match_cache = {}  # Cache for performance
        
        logger.info(f"🧠 AI Smart Matcher initialized with {len(self.keywords)} keywords, fuzzy threshold: {fuzzy_threshold}%")
    
    def _generate_keyword_variations(self) -> Dict[str, List[str]]:
        """Generate common variations for each keyword"""
        variations = {}
        
        for keyword in self.keywords:
            keyword_vars = [keyword]  # Original keyword
            
            # Common variations
            keyword_vars.extend([
                keyword.replace(' ', ''),        # Remove spaces: "buy a business" -> "buyabusiness"
                keyword.replace(' ', '_'),       # Underscores: "buy a business" -> "buy_a_business"  
                keyword.replace(' ', '-'),       # Hyphens: "buy a business" -> "buy-a-business"
                keyword.replace('a', '@'),       # Common typo: "a" -> "@"
                keyword.replace('e', '3'),       # L33t speak variations
                keyword.replace('o', '0'),       # L33t speak variations
            ])
            
            # Remove duplicates and empty strings
            variations[keyword] = list(set([v for v in keyword_vars if v]))
            
        return variations
    
    def smart_keyword_match(self, token_name: str) -> Optional[Dict[str, any]]:
        """
        Advanced keyword matching with AI-powered typo detection
        Returns match info including confidence score and match type
        """
        if not token_name:
            return None
            
        token_name_lower = token_name.lower().strip()
        
        # Check cache first for performance
        cache_key = token_name_lower
        if cache_key in self.match_cache:
            return self.match_cache[cache_key]
        
        start_time = time.time()
        match_result = None
        
        # 1. EXACT MATCH (100% confidence)
        for keyword in self.keywords:
            if keyword == token_name_lower:
                match_result = {
                    'matched_keyword': keyword,
                    'match_type': 'exact',
                    'confidence': 100,
                    'original_token': token_name,
                    'processing_time': time.time() - start_time
                }
                break
        
        # 2. SUBSTRING MATCH (95% confidence)
        if not match_result:
            for keyword in self.keywords:
                if keyword in token_name_lower or token_name_lower in keyword:
                    match_result = {
                        'matched_keyword': keyword,
                        'match_type': 'substring',
                        'confidence': 95,
                        'original_token': token_name,
                        'processing_time': time.time() - start_time
                    }
                    break
        
        # 3. FUZZY MATCH - AI TYPO DETECTION (Dynamic confidence based on similarity)
        if not match_result:
            best_match = None
            best_score = 0
            
            for keyword in self.keywords:
                # Multiple fuzzy matching algorithms for robustness
                scores = [
                    fuzz.ratio(keyword, token_name_lower),           # Basic similarity
                    fuzz.partial_ratio(keyword, token_name_lower),   # Partial matching
                    fuzz.token_sort_ratio(keyword, token_name_lower), # Token order independent
                    fuzz.token_set_ratio(keyword, token_name_lower)   # Set-based matching
                ]
                
                # Use the highest score from all algorithms
                max_score = max(scores)
                
                if max_score >= self.fuzzy_threshold and max_score > best_score:
                    best_score = max_score
                    best_match = keyword
            
            if best_match:
                match_result = {
                    'matched_keyword': best_match,
                    'match_type': 'fuzzy_ai',
                    'confidence': best_score,
                    'original_token': token_name,
                    'processing_time': time.time() - start_time
                }
        
        # 4. VARIATION MATCH (90% confidence) 
        if not match_result:
            for keyword, variations in self.keyword_variations.items():
                for variation in variations:
                    if variation in token_name_lower or token_name_lower in variation:
                        match_result = {
                            'matched_keyword': keyword,
                            'match_type': 'variation',
                            'confidence': 90,
                            'original_token': token_name,
                            'matched_variation': variation,
                            'processing_time': time.time() - start_time
                        }
                        break
                if match_result:
                    break
        
        # 5. PHONETIC SIMILARITY (Experimental - for very close sounds)
        if not match_result:
            match_result = self._phonetic_match(token_name_lower, start_time)
        
        # Cache the result for performance
        self.match_cache[cache_key] = match_result
        
        # Log successful matches
        if match_result:
            logger.info(f"🎯 AI SMART MATCH: '{token_name}' → '{match_result['matched_keyword']}' "
                       f"({match_result['match_type']}, {match_result['confidence']}% confidence, "
                       f"{match_result['processing_time']:.3f}s)")
        
        return match_result
    
    def _phonetic_match(self, token_name: str, start_time: float) -> Optional[Dict[str, any]]:
        """Experimental phonetic matching for similar-sounding words"""
        try:
            # Simple phonetic rules for common typos
            phonetic_rules = {
                'ph': 'f',   # "phone" sounds like "fone"  
                'ck': 'k',   # "back" sounds like "bak"
                'ie': 'y',   # "tie" sounds like "ty"
                'tion': 'shun', # "action" sounds like "akshun"
            }
            
            # Apply phonetic transformations
            phonetic_token = token_name
            for pattern, replacement in phonetic_rules.items():
                phonetic_token = phonetic_token.replace(pattern, replacement)
            
            # Check if phonetic version matches any keyword
            for keyword in self.keywords:
                phonetic_keyword = keyword
                for pattern, replacement in phonetic_rules.items():
                    phonetic_keyword = phonetic_keyword.replace(pattern, replacement)
                
                if phonetic_token == phonetic_keyword:
                    return {
                        'matched_keyword': keyword,
                        'match_type': 'phonetic',
                        'confidence': 80,
                        'original_token': token_name,
                        'processing_time': time.time() - start_time
                    }
        except Exception as e:
            logger.debug(f"Phonetic matching error: {e}")
        
        return None
    
    def get_typo_suggestions(self, token_name: str, limit: int = 3) -> List[Dict[str, any]]:
        """Get suggestions for potential typo matches"""
        if not token_name:
            return []
        
        token_name_lower = token_name.lower().strip()
        suggestions = []
        
        # Get top fuzzy matches with scores
        matches = process.extract(token_name_lower, self.keywords, limit=limit, scorer=fuzz.ratio)
        
        for match_keyword, score in matches:
            if score >= 70:  # Lower threshold for suggestions
                suggestions.append({
                    'keyword': match_keyword,
                    'similarity_score': score,
                    'suggested_match': f"'{token_name}' → '{match_keyword}'"
                })
        
        return suggestions
    
    def validate_keyword_list(self) -> Dict[str, List[str]]:
        """Analyze keyword list for potential typos and duplicates"""
        issues = {
            'potential_typos': [],
            'near_duplicates': [],
            'variations': []
        }
        
        # Check each keyword against all others for similarities
        for i, keyword1 in enumerate(self.keywords):
            for j, keyword2 in enumerate(self.keywords[i+1:], i+1):
                similarity = fuzz.ratio(keyword1, keyword2)
                
                if 80 <= similarity < 95:  # Potential typos
                    issues['potential_typos'].append({
                        'keyword1': keyword1,
                        'keyword2': keyword2,
                        'similarity': similarity
                    })
                elif similarity >= 95:  # Near duplicates
                    issues['near_duplicates'].append({
                        'keyword1': keyword1,
                        'keyword2': keyword2,
                        'similarity': similarity
                    })
        
        return issues
    
    def update_keywords(self, new_keywords: List[str]):
        """Update keyword list and regenerate variations"""
        self.keywords = [k.lower().strip() for k in new_keywords if k.strip()]
        self.keyword_variations = self._generate_keyword_variations()
        self.match_cache.clear()  # Clear cache when keywords change
        
        logger.info(f"🔄 AI Smart Matcher updated with {len(self.keywords)} keywords")


class SmartMatchingIntegration:
    """Integration wrapper for the existing system"""
    
    def __init__(self, keywords: List[str]):
        self.smart_matcher = AISmartKeywordMatcher(keywords, fuzzy_threshold=85)
        
    def enhanced_keyword_check(self, token_name: str, token_symbol: str = "") -> Optional[str]:
        """Enhanced keyword checking with AI smart matching"""
        
        # Check token name first
        name_match = self.smart_matcher.smart_keyword_match(token_name)
        if name_match and name_match['confidence'] >= 85:
            return name_match['matched_keyword']
        
        # Check token symbol if provided
        if token_symbol:
            symbol_match = self.smart_matcher.smart_keyword_match(token_symbol)
            if symbol_match and symbol_match['confidence'] >= 85:
                return symbol_match['matched_keyword']
        
        # Return lower confidence matches if they're still reasonable
        if name_match and name_match['confidence'] >= 75:
            logger.info(f"⚠️ Lower confidence match: {name_match['confidence']}% - Consider review")
            return name_match['matched_keyword']
        
        return None


# Test the system with the specific "buy a business" vs "buy a busienss" case
if __name__ == "__main__":
    # Test case
    test_keywords = ['buy a busienss', 'business', 'crypto', 'token']
    matcher = AISmartKeywordMatcher(test_keywords)
    
    # Test the problematic case
    test_token = "buy a business"
    result = matcher.smart_keyword_match(test_token)
    
    print(f"Testing: '{test_token}'")
    if result:
        print(f"✅ MATCH FOUND:")
        print(f"   Keyword: {result['matched_keyword']}")
        print(f"   Type: {result['match_type']}")
        print(f"   Confidence: {result['confidence']}%")
        print(f"   Time: {result['processing_time']:.3f}s")
    else:
        print("❌ No match found")
        
        # Get suggestions
        suggestions = matcher.get_typo_suggestions(test_token)
        if suggestions:
            print("💡 Suggestions:")
            for suggestion in suggestions:
                print(f"   {suggestion['suggested_match']} ({suggestion['similarity_score']}%)")