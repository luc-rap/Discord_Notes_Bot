import discord
from dotenv import load_dotenv
import os
from discord.ext import commands
import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

load_dotenv()
RECORDINGS_DIR = "recordings"   
os.makedirs(RECORDINGS_DIR, exist_ok=True)

connections = {}

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

async def finished_callback(sink: discord.sinks.WaveSink, ctx: commands.Context):
    """Called automatically when stop_recording() is called."""
    await sink.vc.disconnect()

    # sink.audio_data is a dict of {user_id: AudioData}
    for user_id, audio in sink.audio_data.items():
        filename = f"{RECORDINGS_DIR}/{user_id}.wav"
        with open(filename, "wb") as f:
            f.write(audio.file.read())
        print(f"Saved {filename}")

    await ctx.send(f"Saved {len(sink.audio_data)} audio track(s).")

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')   
     
#@bot.event
#async def on_message(message):
#    if message.author == bot.user:
#        return
#    if message.content.startswith('!hello'):
#        await message.channel.send('Hello!')    
        
#@bot.command()
#async def join(ctx):
#   if ctx.author.voice:
#        channel = ctx.author.voice.channel
#        await channel.connect()
#    else:
#        await ctx.send("You are not connected to a voice channel.")
        
@bot.command()
async def leave(ctx):
    await ctx.guild.voice_client.disconnect()
    
@bot.command()
async def record(ctx):
    if not ctx.author.voice:
        await ctx.send("You are not connected to a voice channel.")
        return
    print(f"Connecting to {ctx.author.voice.channel}")
    vc = await ctx.author.voice.channel.connect()
    connections[ctx.guild.id] = vc
    print(f"Connected: {vc}")
    vc.start_recording(
        discord.sinks.WaveSink(),
        finished_callback, 
        ctx
    )
    print("Recording started")
    await ctx.send("Recording started! Type `!stop` to stop.")
    
@bot.command()
async def stop(ctx: commands.Context):
    if ctx.guild.id not in connections:
        await ctx.send("Not recording.")
        return

    vc = connections.pop(ctx.guild.id)
    vc.stop_recording()  # triggers finished_callback automatically
    await ctx.send("Stopping recording")
        
bot.run(os.getenv('DISCORD_TOKEN'))


'''
ctx.guild        # the server
ctx.guild.id     # the server's unique ID

ctx.author       # the user who typed the command
ctx.author.name  # their username
ctx.author.voice # their current voice state (which channel they're in)

ctx.channel      # the text channel where the command was typed
ctx.send("hi")   # sends a message back to that channel
'''
