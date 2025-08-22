# Front 36 - Solana Token Scanner Discord Bot

## Overview
Comprehensive Solana Token Scanner Discord Bot with real-time multi-platform token detection, mobile-optimized notifications, and Railway deployment ready.

## Key Features
- **Multi-Platform Detection**: Pump.fun (🔵) and LetsBonk (🟠) token monitoring via PumpPortal WebSocket
- **Discord Bot Integration**: 35+ slash commands for comprehensive monitoring and management
- **Mobile Copy Optimization**: Contract addresses display with single backticks for easy mobile copying
- **Railway Deployment Ready**: Solved port conflicts and resource issues with optimized deployment strategy
- **Real-Time Notifications**: Platform-specific Discord notifications with keyword matching

## Mobile Copy Fix
Contract addresses now display as:
```
**Token Name** matches your keyword: `keyword`

`Contract_Address_Here`
```
This format enables easy mobile long-press copying instead of problematic triple backticks.

## Railway Deployment Solution

### Files:
- `railway_health_only.py` - Lightweight health service for Railway
- `Procfile.railway` - Railway deployment configuration
- `requirements.txt` - Optimized dependencies

### Deployment Steps:
1. Upload Front 36 package to Railway
2. Rename `Procfile.railway` to `Procfile`
3. Set environment variables:
   - `DATABASE_URL` (Railway PostgreSQL)
   - `DISCORD_TOKEN` (Discord bot token)
4. Deploy

### Crash Prevention:
- Uses Railway's auto-assigned PORT environment variable
- Lightweight health service avoids resource conflicts
- Proper component separation prevents import conflicts
- Health checks at `/health` and `/status` endpoints

## Architecture
- **Token Monitoring**: `pumpportal_server.py` or `integrated_monitoring_system.py`
- **Discord Bot**: `complete_discord_bot_with_commands.py`
- **Railway Health**: `railway_health_only.py`
- **Database**: PostgreSQL with optimized schema for multi-platform tracking

## Version History
- **Front 34**: Base system with mobile copy issues
- **Front 35**: PumpPortal integration
- **Front 36**: Mobile copy optimization + Railway deployment fixes

## Status
- ✅ Mobile copy optimization complete
- ✅ Railway deployment crashes resolved
- ✅ Discord bot with 35+ commands active
- ✅ Multi-platform token detection working
- ✅ Deployment package ready