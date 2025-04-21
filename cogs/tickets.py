import discord
from discord.ext import commands
import json
import logging
from discord.ui import Button, View
import asyncio
import requests
logger = logging.getLogger(__name__)
from discord.ext import commands, tasks
import time
from collections import defaultdict
class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_category_name = "Tickets"
        # self.mod_role_name = "Moderators"
        self.role_mapping = {
                "low": "Moderators-Tier1",
                "medium": "Moderators-Tier2",
                "high": "Moderators-Tier3",
            }

        self.ticket_status = {}
     # Rate limiting configuration
        self.user_ticket_timestamps = defaultdict(list)  # Store timestamps of ticket creation by user
        self.cooldown_period = 300  # 5 minutes (300 seconds) between tickets
        self.max_tickets_per_day = 5  # Maximum tickets per user per day
        self.day_in_seconds = 86400  # 24 hours in seconds

        # Auto-close configuration
        self.ticket_last_activity = {}  # Track last activity time for each ticket
        self.idle_threshold = 24 * 60 * 60  # 24 hours in seconds (adjust as needed)
        self.check_idle_tickets.start()  # Start the background task

    async def load_ticket_status(self):
        try:
            with open('ticket_status.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    async def update_ticket_activity(self, channel_id):
    # Update the last activity timestamp for a ticket
        channel_id_str = str(channel_id)
        if channel_id_str in self.ticket_status and self.ticket_status[channel_id_str]["status"] == "open":
            self.ticket_last_activity[channel_id_str] = time.time()
        
    @tasks.loop(hours=1)  # Check once per hour
    async def check_idle_tickets(self):
        """Background task to check for and close idle tickets"""
        try:
            current_time = time.time()
            channels_to_close = []
            
            # Find idle tickets
            for channel_id_str, ticket_data in self.ticket_status.items():
                if ticket_data["status"] == "open":
                    last_activity = self.ticket_last_activity.get(channel_id_str, 0)
                    if current_time - last_activity > self.idle_threshold:
                        channels_to_close.append(channel_id_str)
            
            # Close idle tickets
            for channel_id_str in channels_to_close:
                try:
                    # Check if guild_id exists in ticket data, otherwise try to find the channel directly
                    guild = None
                    if "guild_id" in self.ticket_status[channel_id_str]:
                        guild_id = self.ticket_status[channel_id_str]["guild_id"]
                        guild = self.bot.get_guild(int(guild_id))
                    
                    # If guild not found via guild_id, search through all guilds
                    if not guild:
                        for g in self.bot.guilds:
                            channel = g.get_channel(int(channel_id_str))
                            if channel:
                                guild = g
                                break
                    
                    if guild:
                        channel = guild.get_channel(int(channel_id_str))
                        if channel:
                            # Send notification before closing
                            idle_hours = int(self.idle_threshold / 3600)
                            embed = discord.Embed(
                                title="Ticket Auto-Closed",
                                description=f"This ticket has been inactive for {idle_hours} hours and is being automatically closed.",
                                color=discord.Color.orange()
                            )
                            await channel.send(embed=embed)
                            
                            # Close the ticket
                            await self.close_current_ticket(channel, self.bot.user, f"Auto-closed after {idle_hours} hours of inactivity")
                            
                            # Update ticket data with guild_id if it was missing
                            if "guild_id" not in self.ticket_status[channel_id_str]:
                                self.ticket_status[channel_id_str]["guild_id"] = str(guild.id)
                                self.save_ticket_status()
                    else:
                        # If the channel doesn't exist anymore, mark it as closed
                        print(f"Channel {channel_id_str} not found, marking as closed in status")
                        self.ticket_status[channel_id_str]["status"] = "closed"
                        self.save_ticket_status()
                        
                except Exception as e:
                    print(f"Error auto-closing ticket {channel_id_str}: {str(e)}")
                    
        except Exception as e:
            print(f"Error in check_idle_tickets task: {str(e)}")
    @check_idle_tickets.before_loop
    async def before_check_idle_tickets(self):
        """Wait until the bot is ready before starting the task"""
        await self.bot.wait_until_ready()

    def save_ticket_status(self):
        with open('ticket_status.json', 'w') as f:
            json.dump(self.ticket_status, f, indent=4)
    @commands.Cog.listener()
    async def on_message(self, message):
        """Track activity when a message is sent in a ticket channel"""
        if message.guild and message.channel.category and message.channel.category.name == self.ticket_category_name:
            if message.channel.name.startswith("ticket-"):
                await self.update_ticket_activity(message.channel.id)

   
    def check_rate_limit(self, user_id):
        """Check if a user has hit the rate limit for creating tickets"""
        current_time = time.time()
        user_id_str = str(user_id)
        
        # Remove timestamps older than 24 hours
        self.user_ticket_timestamps[user_id_str] = [
            timestamp for timestamp in self.user_ticket_timestamps[user_id_str]
            if current_time - timestamp < self.day_in_seconds
        ]
        
        # Check if user has created too many tickets in the past 24 hours
        if len(self.user_ticket_timestamps[user_id_str]) >= self.max_tickets_per_day:
            return False, f"You've reached the maximum limit of {self.max_tickets_per_day} tickets per day. Please try again tomorrow."
        
        # Check if user is trying to create tickets too quickly
        if self.user_ticket_timestamps[user_id_str] and (current_time - self.user_ticket_timestamps[user_id_str][-1] < self.cooldown_period):
            remaining_time = int(self.cooldown_period - (current_time - self.user_ticket_timestamps[user_id_str][-1]))
            minutes = remaining_time // 60
            seconds = remaining_time % 60
            return False, f"Please wait {minutes} minutes and {seconds} seconds before creating another ticket."
            
        return True, ""

    def add_ticket_timestamp(self, user_id):
        """Record that a user has created a ticket"""
        self.user_ticket_timestamps[str(user_id)].append(time.time())


    async def get_ticket_category(self, guild):
        category = discord.utils.get(guild.categories, name=self.ticket_category_name)
        if category is None:
            category = await guild.create_category(self.ticket_category_name)
            logger.info(f"Guild id:{guild.id}:Created category: {self.ticket_category_name}")
        return category

    def get_mod_role(self, guild,severity):
        role_name=self.role_mapping.get(severity)
        return discord.utils.get(guild.roles, name=role_name)

    async def close_current_ticket(self, channel, closer, reason="closed"):
        guild_id = channel.guild.id
        channel_name = channel.name
        closer_name = f'{closer.name}#{closer.discriminator}'
        channel_id_str = str(channel.id)

        if not (channel.category and channel.category.name == self.ticket_category_name and channel_name.startswith("ticket-")):
            await channel.send("This is not a valid ticket channel.")
            return
        if channel_id_str not in self.ticket_status or self.ticket_status[channel_id_str]["status"] != "open":
            await channel.send("This ticket is already closed.")
            return
        
        api_ticket_id = self.ticket_status[channel_id_str].get("api_ticket_id")
        embed = discord.Embed(title="Ticket Closed", description=f"Ticket closed by {closer_name}", color=discord.Color.red())
        await channel.send(embed=embed)

         # Set permissions
        await channel.set_permissions(channel.guild.default_role, read_messages=False, send_messages=False)
        await channel.set_permissions(closer, read_messages=False, send_messages=False)
        await channel.set_permissions(self.bot.user, read_messages=True, send_messages=True, manage_channels=True)

        severity = self.ticket_status.get(str(channel.id), {}).get("severity", "low")  # default to 'low' if not found
        mod_role = self.get_mod_role(channel.guild, severity)

        if mod_role:
            await channel.set_permissions(mod_role, read_messages=False, send_messages=False)

        if channel_id_str in self.ticket_status and "author" in self.ticket_status[channel_id_str]:
            creator = channel.guild.get_member(int(self.ticket_status[channel_id_str]["author"]))
            if creator:
                await channel.set_permissions(creator, read_messages=False, send_messages=False)

        await asyncio.sleep(5)

        update_ticket_status(channel.id, "closed")
        await mark_ticket_resolved(self, channel,closer)

        # Then delete the channel
        try:
            await channel.delete()
            logger.info(f"Guild id:{guild_id}:Closed ticket channel: {channel_name}: Closed by {closer_name} with reason: {reason}")
            self.ticket_status[channel_id_str]["status"] = "closed"
            self.save_ticket_status()
        except discord.Forbidden:
            await channel.send("I do not have permission to delete this channel.")
            logger.error(f"Guild id:{guild_id}:Failed to delete channel: {channel_name}: Permission denied.")
        except discord.NotFound:
            logger.error(f"Guild id:{guild_id}:Channel not found: {channel_name}: It may have been deleted already.")
    # Add to the Ticket cog class
    async def setup_webhook_channel(self, guild):
        """Create or configure the webhook alert channel"""
        channel_name = "mod-alerts"
        
        # Channel permission overwrites
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=False,
                send_messages=False
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True,
                manage_webhooks=True
            )
        }
        
        # Add permissions for all mod roles
        for role_name in self.role_mapping.values():
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=False,
                    manage_messages=False
                )
        
        try:
            alert_channel = discord.utils.get(guild.text_channels, name=channel_name)
            if not alert_channel:
                alert_channel = await guild.create_text_channel(
                    name=channel_name,
                    overwrites=overwrites,
                    reason="Ticket alert channel creation"
                )
            else:
                # Update existing channel permissions
                for target, perm in overwrites.items():
                    await alert_channel.set_permissions(target, overwrite=perm)
            
            return alert_channel
        except discord.Forbidden:
            logger.error(f"Missing permissions to manage channels in {guild.name}")
            return None

    async def get_secure_webhook(self, guild):
        """Get or create webhook with proper permissions"""
        try:
            alert_channel = await self.setup_webhook_channel(guild)
            if not alert_channel:
                return None
            
            webhooks = await alert_channel.webhooks()
            webhook = next((wh for wh in webhooks if wh.name == "Ticket Alerts"), None)
            
            if not webhook:
                avatar = None
                if self.bot.user.avatar:
                    avatar = await self.bot.user.avatar.read()
                
                webhook = await alert_channel.create_webhook(
                    name="Ticket Alerts",
                    reason="Secure ticket notification system",
                    avatar=avatar
                )
            
            return webhook
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")
            return None

    @commands.command()
    async def ticket(self, ctx,severity: str = "low", *, reason="No reason provided"):
        guild = ctx.guild
        author = ctx.author  # Correctly get the member who invoked the command
        ticket_category = await self.get_ticket_category(guild)
        mod_role = self.get_mod_role(guild,severity)  # Use consistent naming
         # Check rate limits
        can_create, rate_limit_message = self.check_rate_limit(author.id)
        ticket_channel_name = f"ticket-{author.name.lower().replace(' ', '-')}-{author.discriminator}"
        


        if not can_create:
            await ctx.send(f"⚠️ {rate_limit_message}")
            return
        if mod_role is None:
            role_name = self.role_mapping.get(severity)
            await ctx.send(f"No role named '{role_name}' found. Please contact an admin.")
            logger.warning(f"Guild id:{guild.id}:No role named '{role_name}' found.")
            return
        if severity not in ["low", "medium", "high"]:
            await ctx.send("Invalid severity level. Please choose from 'low', 'medium', or 'high'.")
            return
        self.add_ticket_timestamp(author.id)

        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            mod_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        try:
            ticket_channel = await guild.create_text_channel(
                ticket_channel_name,
                category=ticket_category,
                overwrites=overwrites,
            )
            logger.info(f"Guild id:{guild.id}:Created ticket channel: {ticket_channel_name}: Created by {author.name}#{author.discriminator} with reason: {reason}")
            api_ticket_id = log_ticket_to_api(author.name, author.id, reason, severity, ticket_channel.id)
            self.ticket_status[str(ticket_channel.id)] = {
                "author": str(author.id),
                "reason": reason,
                "severity": severity,
                "status": "open",
                "api_ticket_id": api_ticket_id,
                "guild_id": str(guild.id)  # Add this line to track guild ID
            }
            self.save_ticket_status()
            self.ticket_last_activity[str(ticket_channel.id)] = time.time()
            # Send webhook alert
            webhook = await self.get_secure_webhook(guild)
            if webhook:
                mod_role = self.get_mod_role(guild, severity)
                embed = discord.Embed(
                    title=f"New {severity.capitalize()} Severity Ticket",
                    color=discord.Color.orange(),
                    description=f"**Reason:** {reason}"
                )
                embed.add_field(name="Creator", value=author.mention)
                embed.add_field(name="Channel", value=ticket_channel.mention)
                
                try:
                    await webhook.send(
                        content=f"{mod_role.mention if mod_role else ''} New ticket requires attention!",
                        username="Ticket Bot",
                        avatar_url=self.bot.user.display_avatar.url,
                        embed=embed,
                        allowed_mentions=discord.AllowedMentions(roles=True))
                except Exception as e:
                    logger.error(f"Failed to send webhook: {str(e)}")
                    
        except discord.Forbidden:
            await ctx.send("I do not have permission to create a ticket channel.")
            return
        view = CloseButtonView(self)  # Pass the cog instance to the view
        embed = discord.Embed(title="Ticket Created", description=f"Your ticket has been created: {ticket_channel.mention}", color=discord.Color.green())
        embed.add_field(name="Reason", value=reason, inline=False)
        await ticket_channel.send(f"{author.mention} Welcome! {mod_role.mention}", embed=embed, view=view)  # Use .send()
        await ctx.send(f"Ticket created: {ticket_channel.mention}")
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setidletime(self, ctx, hours: int):
        """Set the idle time threshold for auto-closing tickets (in hours)"""
        if hours < 1:
            await ctx.send("⚠️ Idle time must be at least 1 hour.")
            return
            
        self.idle_threshold = hours * 60 * 60  # Convert hours to seconds
        
        await ctx.send(f"✅ Tickets will now be automatically closed after {hours} hours of inactivity.")

    @commands.command()
    async def stats(self, ctx):
        """Show open/closed ticket statistics for this server"""
        guild_id = str(ctx.guild.id)
        
        open_tickets = 0
        closed_tickets = 0
        severity_counts = {"low": 0, "medium": 0, "high": 0}  # Initialize severity counter
        
        # Count tickets for current guild
        for ticket in self.ticket_status.values():
            if ticket.get("guild_id") == guild_id:
                # Update open/closed counts
                if ticket["status"] == "open":
                    open_tickets += 1
                elif ticket["status"] == "closed":
                    closed_tickets += 1
                
                # Update severity counts - ADD THIS PART
                severity = ticket.get("severity", "low")
                severity_counts[severity] += 1
        
        # Create embed
        embed = discord.Embed(
            title=f"Ticket Statistics for {ctx.guild.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="📤 Open Tickets", value=str(open_tickets), inline=True)
        embed.add_field(name="📥 Closed Tickets", value=str(closed_tickets), inline=True)
        
        # Add severity distribution field - ADD THIS SECTION
        embed.add_field(
            name="Severity Distribution",
            value=(
                f"🔵 Low: {severity_counts['low']}\n"
                f"🟡 Medium: {severity_counts['medium']}\n"
                f"🔴 High: {severity_counts['high']}"
            ),
            inline=False
        )
        leaderboard = await get_leaderboard()
        if leaderboard:
            leaderboard_text = "\n".join(
                [f"🏅 {i+1}. {mod['resolved_by_username']} — {mod['resolved_count']} tickets"
                for i, mod in enumerate(leaderboard)]
            )
            embed.add_field(name="Top Mods 👑", value=leaderboard_text, inline=False)

        embed.set_footer(text=f"Total Tickets: {open_tickets + closed_tickets}")
        
        await ctx.send(embed=embed)
     # Command to view current rate limit status
    @commands.command()
    async def ticketlimit(self, ctx):
        """Show the user their current ticket rate limit status"""
        user_id_str = str(ctx.author.id)
        current_time = time.time()
        
        # Clean up old timestamps
        self.user_ticket_timestamps[user_id_str] = [
            timestamp for timestamp in self.user_ticket_timestamps[user_id_str]
            if current_time - timestamp < self.day_in_seconds
        ]
        
        tickets_today = len(self.user_ticket_timestamps[user_id_str])
        tickets_remaining = self.max_tickets_per_day - tickets_today
        
        cooldown_expires = "now"
        if self.user_ticket_timestamps[user_id_str] and (current_time - self.user_ticket_timestamps[user_id_str][-1] < self.cooldown_period):
            remaining_time = int(self.cooldown_period - (current_time - self.user_ticket_timestamps[user_id_str][-1]))
            minutes = remaining_time // 60
            seconds = remaining_time % 60
            cooldown_expires = f"in {minutes} minutes and {seconds} seconds"
        
        embed = discord.Embed(
            title="Ticket Rate Limit Status",
            color=discord.Color.blue()
        )
        embed.add_field(name="Tickets Used Today", value=f"{tickets_today}/{self.max_tickets_per_day}", inline=False)
        embed.add_field(name="Tickets Remaining Today", value=str(tickets_remaining), inline=False)
        embed.add_field(name="Next Ticket Available", value=cooldown_expires, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    cog = Ticket(bot)
    cog.ticket_status = await cog.load_ticket_status()
    await bot.add_cog(cog)
    print("Ticket cog loaded.")

class CloseButton(Button):
    def __init__(self, cog):
        super().__init__(style=discord.ButtonStyle.danger, label="Close Ticket", emoji="🔒")
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Closing ticket...", ephemeral=True)  # Acknowledge immediately
        channel = interaction.channel
        ticket_data = self.cog.ticket_status.get(str(channel.id))
        severity = ticket_data.get("severity", "high") if ticket_data else "high"
        mod_role = self.cog.get_mod_role(channel.guild, severity)

        
        if mod_role and interaction.user in mod_role.members or channel.permissions_for(interaction.user).manage_channels:
            await self.cog.close_current_ticket(channel, interaction.user, "Closed via button")
           
        else:
            await interaction.response.send_message("You do not have permission to close this ticket.", ephemeral=True)

class CloseButtonView(View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(CloseButton(cog))



import requests

def log_ticket_to_api(user, user_id, reason, severity,ticket_channel_id):
    data = {
        "dc_user": user,
        "dc_id": user_id,
        "reason": reason,
        "severity": severity,
        "status": "open",
        "ticket_channel_id": ticket_channel_id  # Add this field
    }
    url = "http://127.0.0.1:8000/api/ticket/"
    try:
        response = requests.post(url, json=data)
        if response.status_code != 201:
            print(f"Failed to log ticket: {response.status_code} - {response.text}")
        else:
            print("Ticket successfully logged to API.")
            return response.json().get('id')
    except requests.exceptions.RequestException as e:
        print(f"Error logging ticket to API: {e}")


def update_ticket_status(ticket_channel_id, new_status='closed'):
    # Use ticket_channel_id directly as the lookup field
    url = f"http://127.0.0.1:8000/api/ticket/{ticket_channel_id}/"
    payload = {'status': new_status}
    try:
        response = requests.patch(url, json=payload)
        if response.status_code == 200:
            print(f"Ticket status updated successfully for channel ID {ticket_channel_id}")
        else:
            print(f"Failed to update ticket status: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error updating ticket status: {e}")




# Now it accepts `ctx` and `ticket_id`
async def mark_ticket_resolved(self, channel, mod):
    url = f"http://localhost:8000/api/ticket/{channel.id}/resolve/"
    
    data = {
        "mod_username": f"{mod.name}#{mod.discriminator}",
        "mod_id": mod.id
    }
    response = requests.post(url,json=data)
    if response.status_code == 200:
        await channel.send("✅ Ticket has been marked as resolved!")
    else:
        await channel.send("⚠️ Error resolving the ticket.")

async def get_leaderboard():
    try:
        response = requests.get("http://localhost:8000/api/ticket/leaderboard/")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print("Error fetching leaderboard:", e)
    return []


