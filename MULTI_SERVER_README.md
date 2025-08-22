# Front 43_updated_keywordlogic - Multi-Server Discord Bot

## 🚀 Enhanced Features

This version provides **per-server keyword management** where each Discord server has its own unique keywords database and webhook configuration.

### Key Improvements:
- ✅ **Server-Specific Keywords**: Each server maintains its own keyword list
- ✅ **Enhanced Bidirectional Matching**: Fixes "blue collar" vs "blue collar boys" issue
- ✅ **Per-Server Webhooks**: Each server can configure its own notification channel
- ✅ **Complete Isolation**: Server A keywords don't affect Server B notifications
- ✅ **Admin Controls**: Only server admins can configure webhooks

## 📊 Database Schema

### Server-Specific Tables:
1. **server_keywords**: Keywords per server and user
2. **server_webhooks**: Webhook URLs per server
3. **server_notifications**: Notification history per server

## 🎯 Commands (6 Essential)

| Command | Description | Admin Only |
|---------|-------------|------------|
| `/add <keyword>` | Add keyword to this server | No |
| `/remove <keyword>` | Remove keyword from this server | No |
| `/list` | Show keywords for this server | No |
| `/clear <confirm>` | Clear all keywords in this server | No |
| `/undo` | Undo last action in this server | No |
| `/webhook <url>` | Configure webhook for this server | Yes |

## 🔧 Setup Process

### For Each New Server:

1. **Add Bot to Server**
   - Use OAuth2 URL with proper permissions
   - Bot will appear in member list

2. **Configure Webhook** (Admin Required)
   ```
   /webhook webhook_url: https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
   ```

3. **Add Keywords** (Any User)
   ```
   /add keyword: blue collar
   /add keyword: grok
   /add keyword: ai agent
   ```

4. **Test Setup**
   ```
   /list
   ```

## 🔄 How It Works

### Keyword Isolation:
- **Server A** has keywords: `["ai", "grok", "blue collar"]`
- **Server B** has keywords: `["meme", "doge", "pepe"]`
- **Result**: Token matching "ai" only notifies Server A

### Webhook Routing:
- **Server A** webhook: `https://discord.com/api/webhooks/123.../ABC`
- **Server B** webhook: `https://discord.com/api/webhooks/456.../DEF`
- **Result**: Each server gets notifications in its own channel

### Enhanced Matching Algorithm:
```python
# These now match correctly:
"blue collar" matches "blue collar boys" ✅
"ai agent" matches "ai agent coin" ✅
"grok" matches "grok ai token" ✅
```

## 🚨 Migration from Single-Server

If migrating from the original Front 43_updated_keywordlogic:

1. **Backup existing keywords**
2. **Run new server_specific_bot.py**
3. **Configure webhooks per server**
4. **Re-add keywords using `/add` commands**

## 🛠️ Technical Implementation

### Database Connection:
- Uses environment `DATABASE_URL` or fallback to Railway
- Auto-creates server-specific tables on startup

### Server Context:
- All operations include `server_id` parameter
- Undo history uses `{server_id}_{user_id}` keys
- Webhook cache maintains per-server mappings

### Security:
- Only server administrators can configure webhooks
- Users can only manage their own keywords
- Server isolation prevents cross-contamination

## 🎉 Benefits

1. **True Multi-Server Support**: Each server operates independently
2. **Enhanced Matching**: Solves bidirectional keyword issues
3. **Scalable Architecture**: Supports unlimited servers
4. **Admin Controls**: Server-level webhook management
5. **User Experience**: Consistent commands across all servers
6. **Data Integrity**: Complete separation of server data

This multi-server version provides the foundation for enterprise-scale Discord bot deployment with proper data isolation and enhanced matching capabilities.