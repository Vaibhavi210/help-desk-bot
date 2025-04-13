discord package is used as a tool to interact with the discord api
discord.ext is a extension for command that is used for creating command using commands decorator
cogs are used a module for oragnizing the commands into groups 
loadind the cog extension should be asynchronous
asyn tells that this function is asynchronous ans await tells that this line requires time so continue with your other tasks to compiler
@commands.command(): This decorator registers the following function (newticket) as a bot command that users can trigger with the prefix (e.g., !newticket).
ctx: This is the command context object. It contains information about where and by whom the command was invoked (guild, channel, author, etc.).
*, reason="No reason provided.": This allows users to provide a reason after the command name. The * makes sure that any subsequent words are treated as part of the reason argument. It also provides a default value if no reason is given.
Embeds are a nice way to format messages on Discord.

13/4/25
added how to add ticket status locally in a json file
added how to close the channel
how to log the ticket information