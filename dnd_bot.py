import asyncio

import discord
from dotenv import load_dotenv
import os
import json
import time
from discord.ext import commands
# import asyncio


load_dotenv()
RECORDINGS_DIR = "recordings"   
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# Store when recording started per guild so we can apply session-relative offsets in transcription.
recording_start = {}
connections = {}

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def finished_callback(sink: discord.sinks.WaveSink, ctx: commands.Context):
    """Called automatically when stop_recording() is called."""

    # session-relative start timestamp (Unix seconds since epoch)
    session_start = recording_start.get(ctx.guild.id, time.time())
    record_stop = time.time()

    # sink.audio_data is a dict of {user_id: AudioData}
    for user_id, audio in sink.audio_data.items():
        print(f"Processing audio for user {user_id} with attributes: {dir(audio)}")
        filename = f"{RECORDINGS_DIR}/{user_id}.wav"
        with open(filename, "wb") as f:
            f.write(audio.file.read())
        print(f"Saved {filename}")

    # Save offset metadata for transcript alignment
    meta_path = os.path.join(RECORDINGS_DIR, "recording_metadata.json")        
    metadata = {
        "session_start": session_start,
        "record_stop": record_stop,
        "users": {str(uid): {"saved_at": record_stop} for uid in sink.audio_data.keys()},
    }
    with open(meta_path, "w", encoding="utf-8") as meta_file:
        json.dump(metadata, meta_file, indent=2)

    # await sink.vc.disconnect()
    
    for user_id, audio in sink.audio_data.items():
        print(f"User {user_id} audio attributes: {dir(audio)}")

    await ctx.send(f"Saved {len(sink.audio_data)} audio track(s).")

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')   
     
 
@bot.command()
async def record(ctx):
    if not ctx.author.voice:
        await ctx.send("You are not connected to a voice channel.")
        return
    
    if ctx.guild.id in connections:
        await ctx.send("Already recording. Use !stop first.")
        return
    
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect()
        
    print(f"Connecting to {ctx.author.voice.channel}")
    vc = await ctx.author.voice.channel.connect()
    print(f"Is connected: {vc.is_connected()}")

    connections[ctx.guild.id] = (vc, sink := discord.sinks.WaveSink())
    recording_start[ctx.guild.id] = time.time()
    print(f"Connected: {vc}")
    vc.start_recording(
        sink,
        finished_callback
    )
    print("Recording started")
    await ctx.send("Recording started! Type `!stop` to stop.")
    
@bot.command()
async def stop(ctx: commands.Context):
    if ctx.guild.id not in connections:
        await ctx.send("Not recording.")
        return

    vc, sink = connections.pop(ctx.guild.id)
    #print([a for a in dir(vc) if not a.startswith("_")])
    print(f"Stopping recording for {vc}")
    vc.stop_recording()  # triggers finished_callback automatically
    # await asyncio.sleep(5)
    await ctx.send("Stopping recording")
    
@bot.command()
async def check(ctx):
    if ctx.guild.id not in connections:
        await ctx.send("Not recording")
        return
    vc, sink = connections[ctx.guild.id]
    print(f"audio_data: {sink.audio_data}")
    print(f"is_recording: {vc.is_recording()}")
    await ctx.send(f"audio_data keys: {list(sink.audio_data.keys())}")
        
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