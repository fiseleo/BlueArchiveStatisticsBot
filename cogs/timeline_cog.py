# cogs/timeline_cog.py
import discord
from discord.ext import commands
from discord import app_commands
import AronaRankLine as arona

class TimelineCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="raidline", description="顯示指定賽季的總力戰分數線")
    async def raidline(self, interaction: discord.Interaction, sensons: int):
        await interaction.response.defer()

        raid_data = arona.get_json(f"https://blue.triple-lab.com/raid/{sensons}")
        if raid_data is None:
            await interaction.followup.send("無法取得總力戰資料！")
            return
        rank_results = arona.get_rank_results(raid_data)

        raid_info = arona.get_json("https://schaledb.com/data/tw/raids.json")
        if raid_info is None:
            await interaction.followup.send("無法取得 raidInfo 資料！")
            return
            
        season_data = arona.get_raidinfo_by_season(raid_info, sensons, eraid=False)
        if not season_data:
            await interaction.followup.send("無法取得對應的總力戰賽季資訊！")
            return

        terrain = season_data.get("Terrain", "未知地型")
        raid_id = season_data.get("RaidId", 0)
        boss_name = arona.get_boss_info(raid_info, raid_id)
        
        header = f"S{sensons} - {terrain} {boss_name} 的總力戰分數"
        embed = discord.Embed(title=header, color=discord.Color.blue())
        mode = "3min" if raid_id in [1, 5] else "4min"

        for rank in arona.RANKS:
            score = rank_results.get(rank)
            if score == "無資料" or not str(score).isdigit():
                embed.add_field(name=f"第{rank}名", value=str(score), inline=False)
                continue
            
            score = int(score)
            difficulty = arona.determine_difficulty(score, mode)
            try:
                used_time_sec = arona.calculate_used_time(score, difficulty, raid_id)
                formatted_time = arona.format_time(used_time_sec)
                value = f"{score:,}\n({difficulty}難度) (用時 {formatted_time})"
            except Exception:
                value = f"{score:,}\n({difficulty}難度) (用時 計算錯誤)"
            
            embed.add_field(name=f"第{rank}名", value=value, inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="eraidline", description="顯示指定賽季的大決戰分數線")
    async def eraidline(self, interaction: discord.Interaction, sensons: int):
        await interaction.response.defer()
        
        eraid_data = arona.get_json(f"https://blue.triple-lab.com/eraid/{sensons}")
        if eraid_data is None:
            await interaction.followup.send("無法取得大決戰資料！")
            return
        rank_results = arona.get_rank_results(eraid_data)
        
        raid_info = arona.get_json("https://schaledb.com/data/tw/raids.json")
        if raid_info is None:
            await interaction.followup.send("無法取得 raidInfo 資料！")
            return
            
        season_data = arona.get_raidinfo_by_season(raid_info, sensons, eraid=True)
        if not season_data:
            await interaction.followup.send("無法取得對應的大決戰賽季資訊！")
            return

        terrain = season_data.get("Terrain", "未知地型")
        raid_id = season_data.get("RaidId", 0)
        boss_name = arona.get_boss_info(raid_info, raid_id)
        
        header = f"S{sensons} - {terrain} {boss_name} 的大決戰分數"
        embed = discord.Embed(title=header, color=discord.Color.green())
        
        for rank in arona.RANKS:
            score = rank_results.get(rank, "無資料")
            formatted_score = f"{int(score):,}" if str(score).isdigit() else score
            embed.add_field(name=f"第{rank}名", value=formatted_score, inline=False)
    
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(TimelineCog(bot))