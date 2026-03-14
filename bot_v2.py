import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import nacl


# load token from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# create bot
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
async def join(ctx):
    """Join the voice channel of the command author"""

    if ctx.author.voice is None:
        await ctx.send("You are not in a voice channel.")
        return

    channel = ctx.author.voice.channel

    # already connected?
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.move_to(channel)
        await ctx.send(f"Moved to {channel}")
        return

    vc = await channel.connect()

    await ctx.send(f"Connected to {channel}")

    print("Voice client:", vc)
    print("Connected:", vc.is_connected())


@bot.command()
async def leave(ctx):
    """Leave voice channel"""

    vc = ctx.guild.voice_client

    if vc is None:
        await ctx.send("Not connected to voice.")
        return

    await vc.disconnect()

    await ctx.send("Disconnected.")


@bot.command()
async def status(ctx):
    """Check voice connection"""

    vc = ctx.guild.voice_client

    if vc is None:
        await ctx.send("No voice client connected.")
        return

    await ctx.send(
        f"Connected: {vc.is_connected()} | Channel: {vc.channel}"
    )


bot.run(TOKEN)