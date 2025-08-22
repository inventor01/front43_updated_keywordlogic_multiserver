# Front 42 - Essential Discord Bot Commands

## 🎯 Overview
Front 42 is a simplified version of the Solana token monitoring bot with just 5 essential Discord commands for keyword management. This streamlined version focuses on core functionality without the complexity of the full 35+ command suite.

## 📋 Available Commands

### 1. `/add <keyword>`
**Add a keyword to monitor**
- Adds a new keyword to your personal monitoring list
- Keywords are case-insensitive and normalized
- Minimum 2 characters required
- Shows total keyword count after adding

**Example:** `/add coin`

### 2. `/remove <keyword>`  
**Remove a keyword from monitoring**
- Removes a specific keyword from your list
- Stores the removed keyword for undo functionality
- Shows remaining keyword count
- Provides tip about using undo

**Example:** `/remove coin`

### 3. `/undo`
**Restore the last removed keyword**
- Restores the most recently removed keyword
- Only works for the last removal per user
- Clears undo history after use
- Shows confirmation of restoration

**Example:** `/undo`

### 4. `/list`
**List all your monitored keywords**
- Shows all keywords you're currently monitoring
- Displays creation date for each keyword
- Paginated display for large lists (10 per page)
- Shows total keyword count

**Example:** `/list`

### 5. `/clear <confirm>`
**Remove ALL your keywords (use with caution)**
- Requires exact confirmation: `yes i want to delete all`
- Removes all keywords for your account
- Cannot be undone - permanent action
- Clears undo history as well

**Example:** `/clear confirm: yes i want to delete all`

## 🔧 Features

### ✅ **Smart Keyword Matching**
- Case-insensitive matching
- Handles spacing, dashes, underscores
- Normalized comparison for consistent results

### ✅ **User-Specific Data**
- Each user has their own keyword list
- Personal undo functionality per user
- Individual keyword management

### ✅ **Safety Features**  
- Confirmation required for destructive operations
- Undo functionality for accidental removals
- Input validation and error handling

### ✅ **Railway Integration**
- Uses Railway PostgreSQL database
- Environment variable configuration
- Webhook notifications for status

## 🚀 Usage Examples

```
/add bitcoin          → Adds "bitcoin" to monitoring
/add moon shot        → Adds "moon shot" to monitoring  
/list                 → Shows all your keywords
/remove bitcoin       → Removes "bitcoin" from list
/undo                 → Restores "bitcoin" back
/clear confirm: yes i want to delete all  → Removes everything
```

## 🗃️ Database Schema

The bot uses a simple `keywords` table:
- `user_id` - Discord user ID (varchar)
- `keyword` - The keyword to monitor (varchar)  
- `created_at` - When keyword was added (timestamp)

## 💡 Benefits of Front 42

1. **Simplicity** - Only 5 commands to learn
2. **Focus** - Core keyword management without distractions
3. **Safety** - Built-in protections against accidents
4. **Performance** - Lightweight and fast
5. **Reliability** - Fewer components = fewer failure points

## 🔄 Migration from Front 41

If upgrading from the full Front 41 bot:
- All existing keywords are preserved
- Database schema remains compatible
- Token monitoring system continues unchanged
- Only Discord commands are simplified

## 🛠️ Technical Details

- **Python 3.11** runtime
- **Discord.py** for bot functionality
- **PostgreSQL** for data storage
- **Railway** for hosting
- **Environment variables** for configuration

Front 42 maintains the same robust keyword matching and database integration as Front 41, but with a cleaner, more focused command interface.