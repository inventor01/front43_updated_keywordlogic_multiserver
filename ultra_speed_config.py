"""
Ultra-speed configuration for sub-second token detection
Optimized for Railway deployment with minimal latency
"""

# Ultra-fast polling intervals (Railway optimized)
ULTRA_FAST_POLLING_INTERVAL = 0.1  # 100ms polling (10x per second)
ALCHEMY_REQUEST_INTERVAL = 0.02    # 20ms between requests (50 req/sec)
WEBSOCKET_HEARTBEAT_INTERVAL = 0.5  # 500ms WebSocket heartbeat

# Enhanced detection parameters
SIGNATURE_BATCH_SIZE = 500         # Process 500 signatures per batch
TOKEN_PROCESSING_WORKERS = 12      # 12 concurrent workers
PARALLEL_EXTRACTION_LIMIT = 16     # 16 parallel BrowserCat extractions

# Ultra-fast timestamp validation
MAX_TOKEN_AGE_SECONDS = 5          # Only process tokens ≤5 seconds old
TIMESTAMP_VALIDATION_TIMEOUT = 1   # 1 second timeout for validation
SKIP_SLOW_VALIDATIONS = True       # Skip time-consuming validations

# BrowserCat optimization for speed
BROWSERCAT_TIMEOUT = 3             # 3 second BrowserCat timeout
BROWSERCAT_SKIP_FOR_KEYWORDS = True # Skip BrowserCat for keyword matches
BROWSERCAT_PARALLEL_LIMIT = 8      # 8 parallel extractions max

# Memory optimization for speed
CACHE_TTL_SECONDS = 30             # 30 second cache TTL
MAX_SEEN_TOKENS = 5000             # Limit seen tokens cache
AGGRESSIVE_CLEANUP_INTERVAL = 10   # Cleanup every 10 seconds

# Railway-specific optimizations
USE_EDGE_LOCATIONS = True          # Use Railway's edge network
ENABLE_CONNECTION_POOLING = True   # Connection pooling for speed
PRELOAD_COMMON_QUERIES = True      # Preload frequently used queries

# Ultra-fast notification delivery
INSTANT_KEYWORD_NOTIFICATIONS = True    # Send keyword matches instantly
BATCH_URL_NOTIFICATIONS = False         # Don't batch URL notifications
DISCORD_RATE_LIMIT_BYPASS = 0.1        # 100ms between Discord messages

print("🚀 ULTRA-SPEED CONFIG LOADED: Sub-second detection enabled")
print(f"   📡 Polling: {ULTRA_FAST_POLLING_INTERVAL}s intervals")
print(f"   ⚡ Alchemy: {ALCHEMY_REQUEST_INTERVAL}s between requests")
print(f"   🔄 Workers: {TOKEN_PROCESSING_WORKERS} parallel processors")
print(f"   ⏱️ Max age: {MAX_TOKEN_AGE_SECONDS}s token window")