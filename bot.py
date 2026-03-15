import discord
from dotenv import load_dotenv
import os
from discord.ext import commands
# import asyncio


load_dotenv()
RECORDINGS_DIR = "recordings"   
os.makedirs(RECORDINGS_DIR, exist_ok=True)

connections = {}

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def finished_callback(sink: discord.sinks.WaveSink, ctx: commands.Context):
    """Called automatically when stop_recording() is called."""

    # sink.audio_data is a dict of {user_id: AudioData}
    for user_id, audio in sink.audio_data.items():
        filename = f"{RECORDINGS_DIR}/{user_id}.mp3"
        with open(filename, "wb") as f:
            f.write(audio.file.read())
        print(f"Saved {filename}")
        
    # await sink.vc.disconnect()

    await ctx.send(f"Saved {len(sink.audio_data)} audio track(s).")

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')   
     
 
@bot.command()
async def record(ctx):
    if not ctx.author.voice:
        await ctx.send("You are not connected to a voice channel.")
        return
    
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect()
        
    print(f"Connecting to {ctx.author.voice.channel}")
    vc = await ctx.author.voice.channel.connect()
    print(f"Is connected: {vc.is_connected()}")

    connections[ctx.guild.id] = vc
    print(f"Connected: {vc}")
    vc.start_recording(
        discord.sinks.MP3Sink(),
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
    print(f"Stopping recording for {vc}")
    vc.stop_recording()  # triggers finished_callback automatically
    # await asyncio.sleep(5)
    await ctx.send("Stopping recording")
    
@bot.command()
async def status(ctx: commands.Context):
    vc = ctx.guild.voice_client
    if vc is None:
        await ctx.send("No voice client")
    else:
        await ctx.send(f"Voice client exists — connected: {vc.is_connected()}, channel: {vc.channel}")
        
@bot.command()
async def disconnect(ctx: commands.Context):
    vc = ctx.guild.voice_client
    if vc:
        await vc.disconnect(force=True)
        await ctx.send("Disconnected.")
    else:
        await ctx.send("No voice client.")
        
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
#TODO:
# - test multiple users in the same channel
# - test users leaving/joining channels while recording
# - test disconnecting the bot while recording(check edge cases like this)
# - test recording for a long time (does it save properly? any memory issues?)