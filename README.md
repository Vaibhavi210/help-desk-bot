# 🎫 Discord Ticketing Bot

A full-featured Discord bot built with `discord.py` to manage support tickets with features like severity-based routing, role permissions, auto-close, statistics, and leaderboard tracking. Perfect for moderation teams to manage support efficiently.

---

## 🚀 Features

- ✅ **Ticket Creation with Severity**
  - Supports `low`, `medium`, and `high` severity levels.
  - Routes tickets to the correct moderator role based on severity.

- 🔐 **Role-Based Access**
  - Only authorized roles can respond to or resolve tickets.

- 🔄 **Rate Limiting**
  - Prevents ticket spam by restricting command usage frequency.

- ⏲️ **Auto-Close Idle Tickets**
  - Automatically closes tickets after inactivity timeout.

- 🔔 **Webhook Alerts**
  - Notifies mods when a new ticket is created.

- 📈 **Ticket Statistics**
  - View open vs. closed ticket stats.
  - Leaderboard of top ticket resolvers.

- 🧠 **Resolve & Close Support**
  - Mark tickets as resolved with reasons.
  - Supports persistent tracking via JSON or database.

---

## Installation 📦

1. **Prerequisites**
   - Python 3.9+
   - Discord bot token
   - [External API](https://github.com/yourname/ticket-api) setup

2. **Setup**
```bash
# Clone repository
git clone https://github.com/yourname/discord-ticket-bot.git
cd discord-ticket-bot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

Edit .env:


DISCORD_TOKEN=your_bot_token_here
API_URL=http://localhost:8000/api/ticket/

# Configuration ⚙️
Discord Setup

Create roles in your server:

Moderators-Tier1 (Low severity)

Moderators-Tier2 (Medium)

Moderators-Tier3 (High)

Enable bot permissions:

Manage Channels

Manage Roles

Manage Webhooks

View Audit Log

Customization

python
# In ticket_cog.py
self.role_mapping = {
    "low": "Moderators-Tier1",
    "medium": "Moderators-Tier2", 
    "high": "Moderators-Tier3"
        }

self.cooldown_period = 300  # 5 minutes between tickets
self.max_tickets_per_day = 5
self.idle_threshold = 24 * 60 * 60  # Auto-close after 24h

## Usage 🛠️
# User Commands
bash
!ticket [low|medium|high] <reason>  # Create new ticket
!ticketlimit                        # Check rate limits
Moderator Commands
bash
!close                              # Close current ticket
!stats                              # Server statistics
!setidletime <hours>               # Set auto-close threshold (Admins)
Ticket Interface
Dedicated private channel per ticket

Automatic role-based access

🔒 Close button in every ticket

Webhook alerts to mod channel


Required Resources:

Persistent storage (for ticket_status.json)

External API hosting

Webhook endpoint (for alerts)