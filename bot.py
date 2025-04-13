import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import logging

logger=logging.getLogger(__name__)
# Set up logging configuration
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

load_dotenv()
token=os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot=commands.Bot(command_prefix='!', intents=intents)


@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

# 🔁 Load all Cogs from a folder named "cogs"
initial_extensions = [
    "cogs.info", 
    "cogs.tickets" # This refers to cogs/info.py
    # Add other cog files here like "cogs.tickets", "cogs.admin", etc.
]

# Override the setup_hook method to load extensions asynchronously
async def load_extensions():
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            print(f'Loaded extension: {extension}')
        except commands.ExtensionAlreadyLoaded:
            print(f"Extension '{extension}' is already loaded.")
        except commands.ExtensionNotFound:
            print(f"Extension '{extension}' not found.")
        except commands.ExtensionFailed as e:
            print(f"Failed to load extension '{extension}': {e}")
        except Exception as e:
            print(f"An unexpected error occurred while loading '{extension}': {e}")

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await load_extensions()
# if __name__ == "__main__":
    

#     bot.run(token)
async def main():
    await bot.start(token)

if __name__ == '__main__':
    asyncio.run(main())