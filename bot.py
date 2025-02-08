import discord
from discord import app_commands
from discord.ext import commands
from AronaStatistics import AronaStatistics
import os
import sys
import asyncio
import pandas as pd
from tabulate import tabulate

# 設定 Bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 確保 `data.xlsx` 存在
if not os.path.exists("data.xlsx"):
    print("❌ 錯誤：找不到 `data.xlsx`，請確認檔案已生成！")
    exit(1)

# 讀取 Excel
arona_stats = AronaStatistics("data.xlsx")

@bot.event
async def on_ready():
    print(f'✅ 已登入：{bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"🔄 成功同步 {len(synced)} 個應用程式指令")
    except Exception as e:
        print(f"❌ 同步指令失敗: {e}")

@bot.tree.command(name="raid_stats", description="取得 總力戰 角色使用統計")
async def raid_stats(interaction: discord.Interaction, season: int, rank: int):
    await interaction.response.defer()

    raid_name = arona_stats.get_raid_name(season)  # 取得 RAID SXX 的名稱
    data = arona_stats.get_raid_stats(season, rank)

    if not data:
        await interaction.followup.send(f"⚠ 無法取得 `{raid_name}` 排名 `{rank}` 的數據")
        return

    embed = discord.Embed(title=f"📊 {raid_name} 排名 {rank} 角色使用率", color=discord.Color.blue())
    for name, count in data[:10]:
        embed.add_field(name=name, value=f"使用次數: `{count}`", inline=False)

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="eraid_stats", description="取得 大決戰 角色使用統計")
@app_commands.choices(armor_type=[
    app_commands.Choice(name="LightArmor", value="LightArmor"),
    app_commands.Choice(name="ElasticArmor", value="ElasticArmor"),
    app_commands.Choice(name="HeavyArmor", value="HeavyArmor"),
    app_commands.Choice(name="Unarmed", value="Unarmed")
])
async def eraid_stats(interaction: discord.Interaction, season: int, armor_type: str, rank: int):
    await interaction.response.defer()

    eraid_name = arona_stats.get_eraid_name(season, armor_type)  # 取得 ERAID SXX 的名稱

    try:
        data = arona_stats.get_eraid_stats(season, armor_type, rank)
    except ValueError as e:
        await interaction.followup.send(str(e))
        return

    if not data:
        await interaction.followup.send(f"⚠ 該季 {season} {armor_type} 類型的角色數據不存在！")
        return

    # **修正 Embed 標題，確保 armor_type 只顯示一次**
    embed = discord.Embed(title=f"📊 大決戰 {eraid_name}  排名 {rank} 角色使用率", color=discord.Color.green())

    for name, count in data[:10]:
        embed.add_field(name=name, value=f"使用次數: {count}", inline=False)

    await interaction.followup.send(embed=embed)



@bot.tree.command(name="statstu", description="取得特定角色的大決戰數據")
@app_commands.choices(armor_type=[
    app_commands.Choice(name="LightArmor", value="LightArmor"),
    app_commands.Choice(name="ElasticArmor", value="ElasticArmor"),
    app_commands.Choice(name="HeavyArmor", value="HeavyArmor"),
    app_commands.Choice(name="Unarmed", value="Unarmed")
])
async def statstu(interaction: discord.Interaction, stu_name: str, seasons: int, armor_type: str):
    await interaction.response.defer()

    arona_stats = AronaStatistics("data.xlsx")  
    sheet_name, stats_text = arona_stats.get_student_stats(stu_name, seasons, armor_type)

    if stats_text is None:
        await interaction.followup.send(f"⚠ 找不到 `{stu_name}` `S{seasons}` `{armor_type}` `大決戰` 的數據")
        return

    # **不要用 Embed，直接發送文字**
    await interaction.followup.send(f"📊 **{stu_name} - {sheet_name} 的使用數據**\n\n{stats_text}")

@bot.tree.command(name="restart", description="🔄 重新啟動 Bot (限管理員)")
@app_commands.checks.has_permissions(administrator=True)
async def restart(interaction: discord.Interaction):
    """重新啟動 Bot"""
    await interaction.response.send_message("🔄 Bot 正在重啟...", ephemeral=True)
    # 給 Discord 一點時間發送訊息
    await asyncio.sleep(2)

    # 重新啟動 Python 程式
    python = sys.executable
    os.execl(python, python, *sys.argv)


# 讀取 Bot Token
try:
    with open("TOKEN.txt", "r") as token_file:
        TOKEN = token_file.read().strip()
except FileNotFoundError:
    print("❌ 錯誤：找不到 `TOKEN.txt`，請確認 Token 文件存在！")
    exit(1)

async def main():
    async with bot:
        await bot.start(TOKEN)

import asyncio
asyncio.run(main())
