# cogs/student_cog.py
import discord
from discord.ext import commands
from discord import app_commands
from AronaStatistics import AronaStatistics
from ImageFactory import ImageFactory

class StudentCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.arona_stats = AronaStatistics("data.xlsx")
        # 從 bot 物件獲取共用資料
        self.id_name_mapping = bot.id_name_mapping
        self.all_student_data = bot.all_student_data

    @app_commands.command(name="eraid_stats_stu", description="取得特定角色的大決戰數據")
    @app_commands.choices(armor_type=[
        app_commands.Choice(name="LightArmor", value="LightArmor"),
        app_commands.Choice(name="ElasticArmor", value="ElasticArmor"),
        app_commands.Choice(name="HeavyArmor", value="HeavyArmor"),
        app_commands.Choice(name="Unarmed", value="Unarmed")
    ])
    async def eraid_stats_stu(self, interaction: discord.Interaction, stu_name: str, seasons: int, armor_type: str):
        await interaction.response.defer()

        student_id = next((sid for sid, name in self.id_name_mapping.items() if name == stu_name), None)
        if student_id is None:
            await interaction.followup.send(f"⚠ 找不到 `{stu_name}` 的對應 ID")
            return

        _sheet_name, raid_title, two_dim_data = self.arona_stats.get_student_stats(student_id, seasons, armor_type)
        if two_dim_data is None:
            await interaction.followup.send(f"⚠ 找不到 `{stu_name}` S{seasons} {armor_type} 大決戰的數據")
            return

        student_info = self.all_student_data.get(str(student_id))
        if student_info is None:
            await interaction.followup.send(f"⚠ 錯誤：找不到 `{stu_name}` (`{student_id}`) 的相關資料")
            return

        image_bytes = ImageFactory.StudentUsageImageGenerator(student_info, two_dim_data)
        file = discord.File(image_bytes, filename="student_usage.png")
        embed = discord.Embed(
            title=f"📊 {stu_name} 的大決戰使用數據",
            description=f"查詢數據： **{raid_title}**\n詳情請參考下方圖片：",
            color=discord.Color.purple()
        )
        embed.set_image(url="attachment://student_usage.png")
        await interaction.followup.send(embed=embed, file=file)

    @app_commands.command(name="raid_stats_stu", description="取得特定角色的總力戰數據")
    async def raid_stats_stu(self, interaction: discord.Interaction, stu_name: str, seasons: int):
        await interaction.response.defer()

        student_id = next((sid for sid, name in self.id_name_mapping.items() if name == stu_name), None)
        if student_id is None:
            await interaction.followup.send(f"⚠ 找不到 `{stu_name}` 的對應 ID")
            return

        _sheet_name, raid_title, two_dim_data = self.arona_stats.get_student_stats_raid(student_id, seasons)
        if two_dim_data is None:
            await interaction.followup.send(f"⚠ 找不到 `{stu_name}` S{seasons} 總力戰的數據")
            return

        student_info = self.all_student_data.get(str(student_id))
        if student_info is None:
            await interaction.followup.send(f"⚠ 錯誤：找不到 `{stu_name}` (`{student_id}`) 的相關資料")
            return

        image_bytes = ImageFactory.StudentUsageImageGenerator(student_info, two_dim_data)
        file = discord.File(image_bytes, filename="student_usage.png")
        embed = discord.Embed(
            title=f"📊 {stu_name} 的總力戰使用數據",
            description=f"查詢數據： **{raid_title}**\n詳情請參考下方圖片：",
            color=discord.Color.dark_blue()
        )
        embed.set_image(url="attachment://student_usage.png")
        await interaction.followup.send(embed=embed, file=file)

async def setup(bot: commands.Bot):
    await bot.add_cog(StudentCog(bot))