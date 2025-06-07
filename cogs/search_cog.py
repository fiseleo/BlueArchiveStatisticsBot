# cogs/search_cog.py
from pathlib import Path
import discord
from discord.ext import commands
from discord import app_commands
import json
import asyncio
from typing import Optional
import AronaRankLine as arona
import utils


JSON_DIR = Path(__file__).parent.parent / "Json"
TL_JSON = JSON_DIR / "TL.json"
CACHED_JSON = JSON_DIR / "cache.json"
class PaginationView(discord.ui.View):
    """用於搜尋結果的分頁視圖"""
    def __init__(self, results: list, page_size: int = 5):
        super().__init__(timeout=180)
        self.results = results
        self.page_size = page_size
        self.current_page = 0
        self.max_page = (len(results) - 1) // page_size if results else 0
        self.message: Optional[discord.Message] = None

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(title="影片搜尋結果", color=discord.Color.blue())
        start_index = self.current_page * self.page_size
        end_index = start_index + self.page_size
        page_data = self.results[start_index:end_index]

        if not page_data:
            embed.description = "此頁面沒有結果。"
            return embed
        
        for idx, item in enumerate(page_data, start=start_index + 1):
            field_value = (
                f"**分數**：{item['score']:,}\n"
                f"**用時**：{item['used_time_str']}\n"
                f"**學生**：{'、'.join(item['students'])}\n"
                f"**URL**：{item['url']}"
            )
            embed.add_field(name=f"結果 #{idx}", value=field_value, inline=False)

        embed.set_footer(text=f"頁數：{self.current_page + 1} / {self.max_page + 1}")
        return embed

    @discord.ui.button(label="上一頁", style=discord.ButtonStyle.secondary, emoji="⬅️")
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="下一頁", style=discord.ButtonStyle.secondary, emoji="➡️")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.max_page:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.errors.NotFound:
                pass # 訊息可能已被刪除

class SearchCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="search_video", description="依據條件搜尋總力戰影片資料")
    @app_commands.choices(battle_field=[
        app_commands.Choice(name="室內戰", value="室內戰"),
        app_commands.Choice(name="野戰", value="野戰"),
        app_commands.Choice(name="城鎮戰", value="城鎮戰")
    ], boss_name=[
        app_commands.Choice(name="薇娜", value="薇娜"),
        app_commands.Choice(name="赫賽德", value="赫賽德"),
        app_commands.Choice(name="白&黑", value="白&黑"),
        app_commands.Choice(name="耶羅尼姆斯", value="耶羅尼姆斯"),
        app_commands.Choice(name="KAITEN FX Mk.0", value="KAITEN FX Mk.0"),
        app_commands.Choice(name="佩洛洛吉拉", value="佩洛洛吉拉"),
        app_commands.Choice(name="霍德", value="霍德"),
        app_commands.Choice(name="高茲", value="高茲"),
        app_commands.Choice(name="葛利果", value="葛利果"),
        app_commands.Choice(name="氣墊船", value="氣墊船"),
        app_commands.Choice(name="黑影", value="黑影"),
        app_commands.Choice(name="Geburah", value="Geburah")
    ], difficulty=[
        app_commands.Choice(name="INSANE", value="INSANE"),
        app_commands.Choice(name="TORMENT", value="TORMENT"),
        app_commands.Choice(name="LUNATIC", value="LUNATIC")
    ], armor_type=[
        app_commands.Choice(name="輕裝備", value="輕裝備"),
        app_commands.Choice(name="彈力裝甲", value="彈力裝甲"),
        app_commands.Choice(name="重裝甲", value="重裝甲"),
        app_commands.Choice(name="特殊裝甲", value="特殊裝甲")
    ], considerhelper=[
        app_commands.Choice(name="是", value="true"),
        app_commands.Choice(name="否", value="false")
    ], bilibilidisplay=[
        app_commands.Choice(name="是", value="true"),
        app_commands.Choice(name="否", value="false")
    ])
    @app_commands.describe(
        include_students="包含學生 (可選，用逗號分隔)",
        exclude_students="排除學生 (可選，用逗號分隔)"
    )
    async def search_video(
        self, interaction: discord.Interaction,
        battle_field: str, boss_name: str, difficulty: str, armor_type: str,
        considerhelper: str, bilibilidisplay: str,
        include_students: str = None, exclude_students: str = None
    ):
        await interaction.response.defer()

        consider_helper_bool = considerhelper.lower() == "true"
        bilibili_display_bool = bilibilidisplay.lower() == "true"

        try:
            await asyncio.to_thread(utils.get_data, armor_type, battle_field, boss_name, difficulty, consider_helper_bool, bilibili_display_bool, exclude_students, include_students)
            await asyncio.to_thread(utils.replace_student_names, CACHED_JSON, TL_JSON)
        except Exception as e:
            await interaction.followup.send(f"從後端 API 獲取資料時發生錯誤: {e}", ephemeral=True)
            return

        try:
            with open(TL_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            await interaction.followup.send(f"讀取處理後的資料失敗: {e}", ephemeral=True)
            return

        boss_raid_id_map = { "薇娜": 1, "赫賽德": 2, "白&黑": 3, "耶羅尼姆斯": 4, "KAITEN FX Mk.0": 5, "佩洛洛吉拉": 6, "霍德": 7, "高茲": 8, "葛利果": 9, "氣墊船": 10, "黑影": 11, "Geburah": 12 }
        raid_id = boss_raid_id_map.get(boss_name, 0)
        mode = "3min" if boss_name in ["薇娜", "KAITEN FX Mk.0"] else "4min"
        
        include_list = [s.strip() for s in include_students.split(',') if s.strip()] if include_students else []
        exclude_list = [s.strip() for s in exclude_students.split(',') if s.strip()] if exclude_students else []
        
        results = []
        for rec in data:
            if not (rec.get("battle_field") == battle_field and rec.get("boss_name") == boss_name and rec.get("armor") == armor_type):
                continue
            try:
                score = int(rec.get("score", 0))
                if arona.determine_difficulty(score, mode) != difficulty:
                    continue
            except (ValueError, TypeError):
                continue
            
            students = rec.get("students", [])
            if (include_list and not all(inc in students for inc in include_list)) or \
               (exclude_list and any(exc in students for exc in exclude_list)):
                continue

            used_time_str = arona.format_time(arona.calculate_used_time(score, difficulty, raid_id)) if raid_id != 0 else "無法計算"
            results.append({"score": score, "used_time_str": used_time_str, "students": students, "url": rec.get("url")})

        if not results:
            embed = discord.Embed(title="搜尋結果", description="沒有找到符合條件的結果。", color=discord.Color.red())
            await interaction.followup.send(embed=embed)
            return
        
        results.sort(key=lambda x: x["score"], reverse=True)
        view = PaginationView(results, page_size=5)
        embed = view.create_embed()
        message = await interaction.followup.send(embed=embed, view=view)
        view.message = message

async def setup(bot: commands.Bot):
    await bot.add_cog(SearchCog(bot))