import discord
from discord.ext import commands
import json
import logging
from discord.ui import Button, View
import asyncio

logger = logging.getLogger(__name__)

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_category_name = "Tickets"
        self.mod_role_name = "Moderators"
        self.ticket_status = {}

    async def load_ticket_status(self):
        try:
            with open('ticket_status.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_ticket_status(self):
        with open('ticket_status.json', 'w') as f:
            json.dump(self.ticket_status, f, indent=4)

    async def get_ticket_category(self, guild):
        category = discord.utils.get(guild.categories, name=self.ticket_category_name)
        if category is None:
            category = await guild.create_category(self.ticket_category_name)
            logger.info(f"Guild id:{guild.id}:Created category: {self.ticket_category_name}")
        return category

    def get_mod_role(self, guild):
        role = discord.utils.get(guild.roles, name=self.mod_role_name)
        return role

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
        embed = discord.Embed(title="Ticket Closed", description=f"Ticket closed by {closer_name}", color=discord.Color.red())
        await channel.send(embed=embed)

        await channel.set_permissions(channel.guild.default_role, read_messages=False, send_messages=False)
        await channel.set_permissions(closer, read_messages=False, send_messages=False)
        await channel.set_permissions(self.bot.user, read_messages=True, send_messages=True, manage_channels=True)

        mod_role = self.get_mod_role(channel.guild)
        if mod_role:
            await channel.set_permissions(mod_role, read_messages=False, send_messages=False)

        if channel_id_str in self.ticket_status and "author" in self.ticket_status[channel_id_str]:
            creator = channel.guild.get_member(int(self.ticket_status[channel_id_str]["author"]))
            if creator:
                await channel.set_permissions(creator, read_messages=False, send_messages=False)

        await asyncio.sleep(5)

        try:
            await channel.delete()
            logger.info(f"Guild id:{guild_id}:Closed ticket channel: {channel_name}: Closed by {closer_name} with reason: {reason}")
            self.ticket_status[channel_id_str]["status"] = "closed"
            self.save_ticket_status()
        except discord.Forbidden:
            await channel.send("I do not have permission to delete this channel.")
            logger.error(f"Guild id:{guild_id}:Failed to delete channel: {channel_name}: Permission denied.")
        except discord.NotFound:
            logger.error(f"Guild id:{guild.id}:Channel not found: {channel_name}: It may have been deleted already.")

    @commands.command()
    async def ticket(self, ctx, *, reason="No reason provided"):
        guild = ctx.guild
        author = ctx.author  # Correctly get the member who invoked the command
        ticket_category = await self.get_ticket_category(guild)
        mod_role = self.get_mod_role(guild)  # Use consistent naming

        if mod_role is None:
            await ctx.send(f"No role named '{self.mod_role_name}' found. Please contact an admin.")
            logger.warning(f"Guild id:{guild.id}:No role named '{self.mod_role_name}' found.")
            return

        ticket_channel_name = f"ticket-{author.name.lower().replace(' ', '-')}-{author.discriminator}"
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
            self.ticket_status[str(ticket_channel.id)] = {
                "author": str(author.id),
                "reason": reason,
                "status": "open"
            }
            self.save_ticket_status()
        except discord.Forbidden:
            await ctx.send("I do not have permission to create a ticket channel.")
            return
        view = CloseButtonView(self)  # Pass the cog instance to the view
        embed = discord.Embed(title="Ticket Created", description=f"Your ticket has been created: {ticket_channel.mention}", color=discord.Color.green())
        embed.add_field(name="Reason", value=reason, inline=False)
        await ticket_channel.send(f"{author.mention} Welcome! {mod_role.mention}", embed=embed, view=view)  # Use .send()
        await ctx.send(f"Ticket created: {ticket_channel.mention}")

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
        mod_role = self.cog.get_mod_role(channel.guild)
        if mod_role and interaction.user in mod_role.members or channel.permissions_for(interaction.user).manage_channels:
            await self.cog.close_current_ticket(channel, interaction.user, "Closed via button")
           
        else:
            await interaction.response.send_message("You do not have permission to close this ticket.", ephemeral=True)

class CloseButtonView(View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(CloseButton(cog))