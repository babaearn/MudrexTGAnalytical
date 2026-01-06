# Mudrex Telegram Statistics Bot

A comprehensive Telegram bot for tracking and analyzing statistics across Mudrex's Telegram channels and groups. Built with Python and python-telegram-bot, designed for deployment on Railway with PostgreSQL.

## Features

### 📊 Signal Channel Tracking
- Real-time tracking of channel posts
- View counts, forwards, and reactions
- Subscriber count monitoring
- Historical data analysis

### 🤖 Bot Engagement Analytics
- Track queries to @Mudrextest_bot
- User leaderboards
- Most requested crypto symbols
- Topic-wise engagement metrics

### 📈 Daily Trends
- 7-day activity graphs
- Daily snapshots for historical analysis
- Member join/leave tracking

### 🔧 Admin Tools
- Full database backup export (CSV)
- Comprehensive text reports
- Bot health monitoring
- Manual sync triggers

## Architecture

### Tech Stack
- **Python 3.11+**
- **python-telegram-bot 20.7** - Telegram bot framework
- **SQLAlchemy 2.0** - ORM and database management
- **PostgreSQL** - Primary database
- **APScheduler** - Periodic task scheduling
- **Pandas** - Data export and analysis

### Project Structure
```
mudrex-stats-bot/
├── bot/
│   ├── main.py              # Entry point
│   ├── config.py            # Environment configuration
│   ├── handlers/
│   │   ├── commands.py      # User command handlers
│   │   ├── listeners.py     # Message/event listeners
│   │   └── admin.py         # Admin commands
│   ├── services/
│   │   ├── channel_stats.py # Channel statistics
│   │   ├── topic_stats.py   # Topic statistics
│   │   ├── bot_usage.py     # Bot usage analytics
│   │   └── export.py        # Backup/export
│   ├── database/
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── connection.py    # DB connection
│   │   └── queries.py       # Database queries
│   ├── utils/
│   │   ├── formatters.py    # Output formatting
│   │   ├── parsers.py       # Input parsing
│   │   └── validators.py    # Permission checks
│   └── schedulers/
│       └── tasks.py         # Periodic tasks
├── requirements.txt
├── Procfile                 # Railway deployment
├── railway.toml            # Railway config
└── README.md
```

## Database Schema

### Tables

**channel_posts** - Signal channel post tracking
- Views, forwards, reactions
- Content preview
- Timestamp tracking

**topic_messages** - Group topic messages
- User information
- Message types (user_query, bot_response, general)
- Content preview

**bot_usage** - Bot query tracking
- User details
- Requested symbols
- Query timestamps

**member_events** - Join/leave tracking
- Event type (joined/left)
- User information
- Timestamps

**daily_snapshots** - Daily aggregated statistics
- Per-channel and per-topic metrics
- Trend analysis data

**channel_subscribers** - Subscriber count history
- Historical subscriber tracking

## Commands

### Signal Channel Commands
- `/in` - All-time channel stats
- `/in jan` - January stats
- `/in dec` - December stats
- `/intotal` - Complete historical summary

### Topic Commands (Dynamic & Expandable)
- `/topics` - List all configured topics
- `/topic1` - Topic 1 all-time stats
- `/topic1 jan` - Topic 1 January stats
- `/t1` - Short alias for /topic1
- `/topic2`, `/t2`, etc. - Additional topics as configured

### Analytics Commands
- `/topusers` - Top bot users (all topics)
- `/topusers topic1` - Top users in specific topic
- `/topusers jan` - Top users for January
- `/topcrypto` - Most requested symbols
- `/topcrypto topic1` - Top symbols in topic
- `/topcrypto jan` - Top symbols for month

### Admin Commands
- `/status` - Bot health and database stats
- `/backup` - Export database as CSV files
- `/sync` - Force historical data sync
- `/report` - Generate comprehensive text report

## Setup Instructions

### 1. Prerequisites
- Python 3.11 or higher
- PostgreSQL database
- Telegram Bot Token (from @BotFather)
- Admin access to target channels/groups

### 2. Local Development

#### Clone and Install
```bash
git clone <repository-url>
cd MudrexTGAnalytical
pip install -r requirements.txt
```

#### Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
```env
BOT_TOKEN=your_bot_token
TRACKED_BOT_USERNAME=Mudrextest_bot
ADMIN_IDS=123456789,987654321
INSIGHTS_CHANNEL_ID=-1002163454656
OFFICIAL_GROUP_ID=-1001868775086
TOPICS={"1":{"id":89270,"name":"Market Intelligence"}}
DATABASE_URL=postgresql://...
```

#### Run Locally
```bash
python -m bot.main
```

### 3. Railway Deployment

#### Step 1: Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Create new project
3. Add PostgreSQL plugin

#### Step 2: Configure Environment Variables
Add all required environment variables in Railway dashboard:
- `BOT_TOKEN`
- `TRACKED_BOT_USERNAME`
- `ADMIN_IDS`
- `INSIGHTS_CHANNEL_ID`
- `OFFICIAL_GROUP_ID`
- `TOPICS`

Note: `DATABASE_URL` is automatically set by Railway's PostgreSQL plugin.

#### Step 3: Deploy
```bash
# Connect to Railway
railway login

# Link to your project
railway link

# Deploy
railway up
```

Or push to GitHub and connect Railway to your repository for automatic deployments.

### 4. Bot Configuration

#### Add Bot to Channel
1. Go to your signal channel
2. Add the bot as an administrator
3. Grant "Post Messages" permission (to read posts)

#### Add Bot to Group
1. Go to your group
2. Add the bot as an administrator
3. Enable these permissions:
   - Read messages
   - Read message history
   - Manage topics (if using topics)

#### Get Chat IDs
If you need to find chat/topic IDs:
```python
# Use the bot's built-in ID getter
# Forward a message from the channel/topic to @userinfobot
```

## Configuration Guide

### Adding New Topics
To track additional topics, update the `TOPICS` environment variable:

```json
{
  "1": {"id": 89270, "name": "Market Intelligence"},
  "2": {"id": 12345, "name": "General Discussion"},
  "3": {"id": 67890, "name": "Support"}
}
```

The bot will automatically:
- Create `/topic2`, `/topic3`, etc. commands
- Create short aliases `/t2`, `/t3`, etc.
- Track bot engagement per topic
- Generate separate statistics

### Adding Admin Users
Add user IDs to `ADMIN_IDS` (comma-separated):
```env
ADMIN_IDS=123456789,987654321,456789123
```

To get your user ID, message @userinfobot on Telegram.

### Adjusting Sync Intervals
```env
UPDATE_VIEWS_INTERVAL_MINUTES=60  # Update view counts every hour
DAILY_SNAPSHOT_HOUR=0             # Daily snapshot at midnight IST
```

## How It Works

### Real-Time Tracking
The bot listens to:
1. **Channel Posts** - Automatically tracked when posted
2. **Topic Messages** - All messages in configured topics
3. **Bot Responses** - Detects when @Mudrextest_bot replies to users
4. **Member Events** - Join/leave events in the group

### Bot Query Detection
When a user queries the tracked bot:
1. User sends a message like `/BTCUSDT` in a topic
2. @Mudrextest_bot replies with chart/data
3. Stats bot detects the reply
4. Extracts the original query and symbol
5. Stores in `bot_usage` table with user info

### Symbol Extraction
The bot automatically extracts crypto symbols from queries:
- `/BTCUSDT` → BTCUSDT
- `/btc` → BTCUSDT (automatically adds USDT)
- `/ETH` → ETHUSDT
- `Check /SOLUSDT chart` → SOLUSDT

### Periodic Tasks
1. **Hourly**: Update view counts for recent channel posts
2. **Daily (Midnight IST)**: Create daily snapshots for trends
3. **Weekly (Sunday 2 AM IST)**: Cleanup old data (optional)

## Data Export

### Backup Format
The `/backup` command exports all tables as CSV files:
- `channel_posts_YYYYMMDD_HHMMSS.csv`
- `topic_messages_YYYYMMDD_HHMMSS.csv`
- `bot_usage_YYYYMMDD_HHMMSS.csv`
- `member_events_YYYYMMDD_HHMMSS.csv`
- `daily_snapshots_YYYYMMDD_HHMMSS.csv`
- `channel_subscribers_YYYYMMDD_HHMMSS.csv`

### Report Format
The `/report` command generates a comprehensive text report with:
- Channel statistics (all-time)
- Per-topic statistics
- Top users across all topics
- Top symbols across all topics
- Formatted for easy reading and sharing

## Troubleshooting

### Bot Not Responding
1. Check bot is running: `/status` command
2. Verify bot token is correct
3. Check Railway logs for errors
4. Ensure database connection is working

### Missing Statistics
1. Verify bot has admin access to channel/group
2. Check topic IDs are correct
3. Run `/sync` to trigger manual sync
4. Check Railway logs for permission errors

### Database Connection Issues
1. Verify `DATABASE_URL` environment variable
2. Check PostgreSQL plugin is running
3. Test connection with `/status` command
4. Check Railway PostgreSQL logs

### Bot Not Detecting Queries
1. Verify `TRACKED_BOT_USERNAME` is correct
2. Ensure bot can read message history
3. Check if tracked bot is replying to user messages
4. Verify topic IDs are in the configured list

## Security Considerations

### Admin-Only Access
All commands are restricted to users in `ADMIN_IDS` to prevent:
- Unauthorized data access
- Spam from public users
- Database export by non-admins

### Environment Variables
Never commit `.env` files or tokens to version control:
```bash
# .gitignore should include:
.env
*.env
.env.local
```

### Database Security
- Use Railway's managed PostgreSQL (automatic backups)
- DATABASE_URL contains credentials - keep secret
- Regular backups via `/backup` command

## Monitoring and Maintenance

### Health Checks
Use `/status` command regularly to monitor:
- Bot uptime
- Database connection
- Last sync time
- Record counts

### Regular Backups
Schedule regular backups:
1. Use `/backup` command weekly
2. Download and store CSV files securely
3. Verify backup completeness

### Log Monitoring
Check Railway logs for:
- Error messages
- API rate limits
- Database connection issues
- Permission errors

## Performance Optimization

### Rate Limiting
The bot includes automatic rate limiting:
- 0.5s delay between API calls during sync
- Configurable via `RATE_LIMIT_DELAY`

### Database Indexing
All tables include indexes on:
- Frequently queried columns
- Date/timestamp columns for range queries
- Foreign key relationships

### Query Optimization
- Uses SQLAlchemy with async support
- Connection pooling for efficiency
- Prepared statements prevent SQL injection

## Future Enhancements

Potential features to add:
- [ ] PDF report generation
- [ ] Scheduled report delivery
- [ ] Webhook support for real-time updates
- [ ] Analytics dashboard (web interface)
- [ ] Multi-language support
- [ ] Custom date range queries
- [ ] Export to Google Sheets
- [ ] Sentiment analysis on messages

## Contributing

To contribute to this project:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is proprietary software for Mudrex internal use.

## Support

For issues or questions:
1. Check this README first
2. Review Railway logs
3. Test with `/status` command
4. Contact the development team

## Changelog

### v1.0.0 (2024-01-XX)
- Initial release
- Signal channel tracking
- Topic message tracking
- Bot usage analytics
- Admin commands
- Railway deployment support
