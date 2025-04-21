📘 learn.md Summary
🔧 Tech & Concepts Used
discord.py: Python library to interact with the Discord API.

discord.ext.commands: Extension module used for creating bot commands via decorators.

Cogs: Used to modularize bot commands and logic into separate Python files for better organization.

Async/Await: Handles asynchronous operations like API calls and I/O tasks, keeping the bot responsive.

⚙️ Command Explanation
@commands.command(): Registers a function as a bot command.

ctx: Context of the command (user, guild, channel info).

*, reason="...": Allows passing a multi-word string as an argument (e.g., a ticket reason).

Embeds: Used to format Discord messages neatly.

🛠️ Features Implemented
✅ Core Ticketing
Ticket creation with severity levels (low, medium, high).

Auto-routing tickets to the appropriate mod role based on severity.

Ticket reason handling and channel creation.

🔒 Permissions & Access
Role-based access for viewing/responding to tickets.

Mod-only commands for closing, resolving, and viewing ticket logs.

🛡️ Security & Moderation
Rate-limiting to prevent spam.

Webhook alerts for moderators when new tickets are created.

Auto-close tickets after a period of inactivity.

📊 Statistics & Tracking
Stats command: Shows how many tickets are open/closed.

Leaderboard: Ranks top 3 users who resolved the most tickets.

Local JSON and/or DB logging of ticket statuses and updates.

📆 Development Timeline
13/04/2025
Local ticket status via JSON.

Channel close functionality.

Logging ticket info.

Ticket priority and routing logic added.

17/04/2025
Built full-stack ticket open/close workflow with DB sync.

Implemented rate-limiting.

Added mod alerts and resolve feature.

Ticket stats tracking.

21/04/2025
Leaderboard for top resolvers.

Auto-closing idle tickets.





