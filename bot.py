import discord
from discord.ext import commands

# 設定指令前綴，例如 "!" 或 "/"
intents = discord.Intents.default()
intents.messages = True  # 確保 Bot 能夠讀取訊息
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f'已登入：{bot.user}')

@bot.command()
async def hello(ctx):
    await ctx.send("Hello! 我是你的 Discord Bot!")

# 用你的 Bot Token 啟動 Bot

TOKEN = open("TOKEN.txt", "r").read()
bot.run(TOKEN)
