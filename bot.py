import discord
from dotenv import load_dotenv
import os
from discord.ext.commands import Bot
from discord.ext import commands
load_dotenv()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')   
     
#@bot.event
#async def on_message(message):
#    if message.author == bot.user:
#        return
#    if message.content.startswith('!hello'):
#        await message.channel.send('Hello!')    
        
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("You are not connected to a voice channel.")
        
@bot.command()
async def leave(ctx):
    await ctx.guild.voice_client.disconnect()
        
bot.run(os.getenv('DISCORD_TOKEN'))

