import discord
from discord.ext import commands

# This code defines a Discord bot command that sends an embedded message with information about the bot.
class Info(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def info(self,ctx):
        
        embed=discord.Embed(title="Bot Info", description="A custom bot for handling support tickets.", color=0x00ff00)
        embed.set_author(name=ctx.author.name)
        embed.set_footer(text="Created by Vaibhavi")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Info(bot))
    print("Info cog loaded.")