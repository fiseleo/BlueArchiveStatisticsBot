# cogs/stats_cog.py
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from AronaStatistics import AronaStatistics

class StatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.arona_stats = AronaStatistics("data.xlsx")

    @staticmethod
    def get_rank_range_str(rank: int) -> str:
        """根據 rank 回傳對應的區間文字"""
        if 1 <= rank <= 1000:
            return "排名 1~1000 內"
        elif 1001 <= rank <= 5000:
            return "排名 1001~5000 內"
        elif 5001 <= rank <= 10000:
            return "排名 5001~10000 內"
        elif 10001 <= rank <= 20000:
            return "排名 10001~20000 內"
        else:
            raise ValueError(f"⚠ Rank {rank} 不在支援的範圍內")

    @app_commands.command(name="raid_stats", description="取得 總力戰 角色使用統計")
    async def raid_stats(self, interaction: discord.Interaction, season: int, rank: int):
        await interaction.response.defer()
        try:
            rank_str = self.get_rank_range_str(rank)
        except ValueError as e:
            await interaction.followup.send(str(e))
            return

        raid_name = self.arona_stats.get_raid_name(season)
        data = self.arona_stats.get_raid_stats(season, rank)

        if not data:
            await interaction.followup.send(f"⚠ 無法取得 `{raid_name}` {rank_str} 的數據")
            return

        embed = discord.Embed(
            title=f"📊 {raid_name} {rank_str} 角色使用率",
            color=discord.Color.blue()
        )
        for name, count in data[:10]:
            embed.add_field(name=name, value=f"使用次數: `{count}`", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="eraid_stats", description="取得 大決戰 角色使用統計")
    @app_commands.choices(armor_type=[
        app_commands.Choice(name="LightArmor", value="LightArmor"),
        app_commands.Choice(name="ElasticArmor", value="ElasticArmor"),
        app_commands.Choice(name="HeavyArmor", value="HeavyArmor"),
        app_commands.Choice(name="Unarmed", value="Unarmed")
    ])
    async def eraid_stats(self, interaction: discord.Interaction, season: int, armor_type: str, rank: int):
        await interaction.response.defer()
        try:
            rank_str = self.get_rank_range_str(rank)
        except ValueError as e:
            await interaction.followup.send(str(e))
            return

        eraid_name = self.arona_stats.get_eraid_name(season, armor_type)
        try:
            data = self.arona_stats.get_eraid_stats(season, armor_type, rank)
        except ValueError as e:
            await interaction.followup.send(str(e))
            return

        if not data:
            await interaction.followup.send(f"⚠ 該季 S{season} {armor_type} 類型的角色數據不存在！")
            return

        embed = discord.Embed(
            title=f"📊 大決戰 {eraid_name} {rank_str} 角色使用率",
            color=discord.Color.green()
        )
        for name, count in data[:10]:
            embed.add_field(name=name, value=f"使用次數: {count}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="stuusage", description="取得指定學生前20筆使用率統計")
    async def stuusage(self, interaction: discord.Interaction, stu_name: str, rank: int):
        await interaction.response.defer()
        try:
            rank_str = self.get_rank_range_str(rank)
        except ValueError as e:
            await interaction.followup.send(str(e), ephemeral=True)
            return
            
        result = await asyncio.to_thread(self.arona_stats.get_student_usage, stu_name, rank)

        embed = discord.Embed(
            title=f"📊 {stu_name} 的使用率 (來自 {rank_str})",
            color=discord.Color.blue()
        )
        if "❌" in result:
            embed.description = result
        else:
            description_text = "前 20 項最高使用率：\n"
            # 將結果格式化為更易讀的列表
            formatted_lines = [f"• {line}" for line in result.strip().split('\n') if line]
            description_text += "\n".join(formatted_lines)
            embed.description = description_text
            
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))