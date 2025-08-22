# Railway Deployment Guide

## Current Issue
The system was crashing on Railway due to port conflicts and resource limitations.

## Solution: Railway Single Service Architecture

### Files for Railway Deployment:
1. **`Procfile.railway`** - Railway entry point
2. **`railway_single_service.py`** - Main service orchestrator  
3. **`pumpportal_server.py`** - Token monitoring backend
4. **`complete_discord_bot_with_commands.py`** - Discord bot

### Railway Environment Variables Required:
```
DATABASE_URL=postgresql://...
DISCORD_TOKEN=your_discord_token
```

### Deployment Steps:

1. **Upload to Railway:**
   - Use the `final_working_front_8_18_25_mobile_copy_optimized.zip` package
   - Rename `Procfile.railway` to `Procfile`

2. **Set Environment Variables:**
   - Add `DATABASE_URL` (Railway PostgreSQL)
   - Add `DISCORD_TOKEN` (Discord bot token)

3. **Deploy:**
   - Railway will use `railway_single_service.py` as entry point
   - This provides health checks on port 5000
   - Background processes handle token monitoring and Discord bot

### Health Monitoring:
- `/health` - Service health check
- `/status` - Component status
- `/` - System overview

### Crash Prevention Features:
- Single port usage (5000)
- Gradual component initialization
- Proper process separation
- Railway-optimized resource usage
- Health check endpoints for Railway monitoring

### Mobile Copy Optimization:
The latest fix ensures contract addresses display as:
```
**Token Name** matches your keyword: `keyword`

`Contract_Address_Here`
```
This format enables easy mobile long-press copying.