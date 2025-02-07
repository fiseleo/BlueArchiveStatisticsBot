import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from AronaStatistics import AronaStatistics

# 設定 API URL
RAID_URL = "https://media.arona.ai/data/v3/raid/<id>/total"
ERAID_URL = "https://media.arona.ai/data/v3/eraid/<id>/total"
STUDENT_URL = "https://schaledb.com/data/tw/students.json"
RAID_INFO_URL = "https://schaledb.com/data/tw/raids.json"

# 初始化統計物件
arona_stats = AronaStatistics(RAID_URL, ERAID_URL, STUDENT_URL, RAID_INFO_URL)

# 設定 Bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ 已登入：{bot.user}')
    await arona_stats.fetch_data()  # 讓 bot 在啟動時先取得基礎數據
    try:
        synced = await bot.tree.sync()
        print(f"🔄 成功同步 {len(synced)} 個應用程式指令")
    except Exception as e:
        print(f"❌ 同步指令失敗: {e}")

@bot.tree.command(name="raid_stats", description="取得目前 Raid 角色使用統計")
async def raid_stats(interaction: discord.Interaction):
    await interaction.response.defer()
    sorted_usage = await arona_stats.fetch_raid_data()

    embed = discord.Embed(title="📊 目前 RAID 角色使用率", color=discord.Color.blue())
    for name, count in sorted_usage[:10]:
        embed.add_field(name=name, value=f"使用次數: {count}", inline=False)

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="eraid_stats", description="取得 ERAID 角色使用統計")
async def eraid_stats(interaction: discord.Interaction):
    """顯示目前 ERAID 角色使用統計"""
    await interaction.response.defer()
    sorted_usage = await arona_stats.fetch_eraid_data()

    # 建立 Embed 訊息
    embed = discord.Embed(title="📊 目前 ERAID 角色使用率", color=discord.Color.green())
    for name, count in sorted_usage[:10]:  # 只顯示前 10 名
        embed.add_field(name=name, value=f"使用次數: {count}", inline=False)

    await interaction.followup.send(embed=embed)

# 讀取 Bot Token
TOKEN = open("TOKEN.txt", "r").read().strip()

async def main():
    async with bot:
        await bot.start(TOKEN)

asyncio.run(main())
