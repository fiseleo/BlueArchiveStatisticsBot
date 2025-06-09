from pathlib import Path
import sys
import discord
from discord.ext import commands, tasks  
from discord import app_commands
import sqlite3
import AronaRankLine as arona


DB_Path = Path(__file__).parent.parent / "db"
LINUX_DB = DB_Path / "Linux" / "RaidDatabase.db"
WINDOWS_DB = DB_Path / "Windows" / "RaidDatabase.db"

DB_FILE = LINUX_DB if sys.platform.startswith("linux") else WINDOWS_DB

# Loading PNG (Boss Icons)
PNG_PATH = Path(__file__).parent.parent / "PNG"
RAID_PATH = PNG_PATH / "Raid"


TIER_MAPPING = {
    1: "<:tier_platinum:1380951310643363870>",
    10001: "<:tier_gold:1380951416419651624>",
    50001: "<:tier_silver:1380951575601610762>",
}


BOSS_ICON_MAPPING = {
    "Binah": RAID_PATH / "Binah.png",
    "Chesed": RAID_PATH / "Chesed.png",
    "EN0005": RAID_PATH / "EN0005.png",
    "EN0010": RAID_PATH / "EN0010.png", # Placeholder for 'Rot'
    "Goz": RAID_PATH / "GOZ.png",
    "Hieronymus": RAID_PATH / "Hieronymus.png",
    "HOD": RAID_PATH / "HOD.png",
    "Kaiten": RAID_PATH / "KaitenFxMk0.png",
    "KaitenFxMk0": RAID_PATH / "KaitenFxMk0.png",
    "Perorozilla": RAID_PATH / "Perorozilla.png",
    "ShiroKuro": RAID_PATH / "ShiroKuro.png",
    "HoverCraft": RAID_PATH / "Wakamo.png",
    "EN0006": RAID_PATH / "EN0006.png"
}

BOSS_RAID_ID = { "薇娜": 1, "赫賽德": 2, "白&黑": 3, "耶羅尼姆斯": 4, "KAITEN FX Mk.0": 5, "佩洛洛吉拉": 6, "霍德": 7, "高茲": 8, "葛利果": 9, "氣墊船": 10, "黑影": 11, "Geburah": 12 }
BOSS_NAME_MAP = {
    "Binah"  : "薇娜",
    "Chesed" : "赫賽德",
    "EN0005" : "葛利果",
    "EN0010"  : "Geburah",
    "Goz"    : "高茲",
    "Hieronymus" : "耶羅尼姆斯",
    "HOD"    : "霍德",
    "KaitenFxMk0" : "KAITEN FX Mk.0",
    "Perorozilla" : "佩洛洛吉拉",
    "ShiroKuro" : "白&黑",
    "HoverCraft" : "氣墊船",
    "EN0006" : "黑影"
}

STUDENT_IMAGE_PATH = Path(__file__).parent.parent / "studentsimage"




class GLRankLineCog(commands.Cog):
    """用於顯示總力戰與大決戰排行榜的 Cog"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_path = DB_FILE
        self.table_list = self._get_db_tables()
        self._create_warnings_table()
        self.check_rank_warnings.start()

    def cog_unload(self):
        self.check_rank_warnings.cancel()

    def _get_db_tables(self) -> list:
        if not self.db_path.exists(): return []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'S%' ORDER BY name DESC")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"SQLite 錯誤: {e}")
            return []

    def _create_warnings_table(self):
        """建立用於儲存排名提醒的資料表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS RankWarnings (
                        DiscordUserId INTEGER PRIMARY KEY,
                        AccountId INTEGER NOT NULL,
                        TargetRank INTEGER NOT NULL,
                        LatestTable TEXT NOT NULL,
                        Notified INTEGER NOT NULL DEFAULT 0
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            print(f"建立 RankWarnings 資料表時發生錯誤: {e}")

    @tasks.loop(minutes=5.0)
    async def check_rank_warnings(self):
        """背景任務：每5分鐘檢查一次排名"""
        print("[INFO] 正在執行排名提醒檢查...")
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 選取所有尚未通知的提醒
                cursor.execute("SELECT * FROM RankWarnings WHERE Notified = 0")
                warnings = cursor.fetchall()

                for warning in warnings:
                    try:
                        # 查詢該玩家的最新排名
                        rank_cursor = conn.cursor()
                        rank_cursor.execute(f'SELECT Rank FROM "{warning["LatestTable"]}" WHERE AccountId = ?', (warning["AccountId"],))
                        current_rank_row = rank_cursor.fetchone()

                        if current_rank_row and current_rank_row['Rank']:
                            current_rank = current_rank_row['Rank']
                            target_rank = warning['TargetRank']

                            # 檢查排名是否已進入100名的危險區
                            if 0 < (current_rank - target_rank) <= 100:
                                user = await self.bot.fetch_user(warning['DiscordUserId'])
                                if user:
                                    print(f"[INFO] 玩家 {user.name} ({warning['AccountId']}) 排名 {current_rank} 已接近目標 {target_rank}，準備發送提醒。")
                                    await user.send(f"**【總力戰排名提醒】**\n<@{warning['DiscordUserId']}> 您的排名 **{current_rank}** 快到目標 **{target_rank}** 了，請準備卷分！")
                                    
                                    # 更新資料庫，標記為已通知
                                    update_cursor = conn.cursor()
                                    update_cursor.execute("UPDATE RankWarnings SET Notified = 1 WHERE DiscordUserId = ?", (warning['DiscordUserId'],))
                                    conn.commit()
                    except Exception as e:
                        print(f"處理單個排名提醒時出錯 (DiscordUserId: {warning['DiscordUserId']}): {e}")

        except sqlite3.Error as e:
            print(f"檢查排名提醒時資料庫出錯: {e}")
        except Exception as e:
            print(f"執行排名提醒任務時發生未知錯誤: {e}")

    @check_rank_warnings.before_loop
    async def before_check_rank_warnings(self):
        """等待機器人準備就緒後再開始背景任務"""
        await self.bot.wait_until_ready()
            
    # --- 新增指令 ---
    @app_commands.command(name="glwarnrank", description="設定排名提醒，當您的排名接近目標時提醒您")
    @app_commands.describe(uid="您的遊戲內 UID", targetrank="您想設定的目標排名")
    async def glwarnrank(self, interaction: discord.Interaction, uid: int, targetrank: int):
        await interaction.response.defer(ephemeral=True)
        if not self.table_list:
            await interaction.followup.send("錯誤：目前沒有可用的總力戰/大決戰資料。", ephemeral=True)
            return

        latest_table = self.table_list[0]
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f'SELECT Rank FROM "{latest_table}" WHERE AccountId = ?', (uid,))
                rank_row = cursor.fetchone()

                if not rank_row:
                    await interaction.followup.send(f"在最新的總力戰 **{latest_table}** 中找不到 UID 為 `{uid}` 的玩家。", ephemeral=True)
                    return

                current_rank = rank_row[0]
                
                if current_rank > targetrank:
                    await interaction.followup.send(f"❌ **無法設定提醒**\n您目前的排名 `{current_rank}` 已經低於目標 `{targetrank}`，請重新設定。", ephemeral=True)
                elif abs(current_rank - targetrank) <= 100:
                    await interaction.followup.send(f"❌ **無法設定提醒**\n您目前的排名 `{current_rank}` 與目標 `{targetrank}` 相差不到100名，離得太近了！請重新設定。", ephemeral=True)
                else: # current_rank < targetrank and difference > 100
                    # 成功設定提醒，寫入資料庫
                    cursor.execute("""
                        INSERT OR REPLACE INTO RankWarnings (DiscordUserId, AccountId, TargetRank, LatestTable, Notified)
                        VALUES (?, ?, ?, ?, 0)
                    """, (interaction.user.id, uid, targetrank, latest_table))
                    conn.commit()
                    await interaction.followup.send(f"✅ **已開啟排名檢測**\n當您在 **{latest_table}** 的排名接近 `{targetrank}` 時，將會私訊提醒您。", ephemeral=True)

        except sqlite3.Error as e:
            await interaction.followup.send(f"處理您的請求時資料庫發生錯誤：{e}", ephemeral=True)


    @app_commands.command(name="glwarnrankclear", description="清除您設定的排名提醒")
    async def glwarnrankclear(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM RankWarnings WHERE DiscordUserId = ?", (interaction.user.id,))
                conn.commit()
                if cursor.rowcount > 0:
                    await interaction.followup.send("✅ 您設定的排名提醒已成功關閉。", ephemeral=True)
                else:
                    await interaction.followup.send("ℹ️ 您目前沒有設定任何排名提醒。", ephemeral=True)
        except sqlite3.Error as e:
            await interaction.followup.send(f"處理您的請求時資料庫發生錯誤：{e}", ephemeral=True)


    # ... (此處省略 _create_user_rank_embed 和其他指令的程式碼，它們與前一版相同) ...
    # (The rest of the cog code from the previous correct version goes here)
    async def _create_user_rank_embed(self, data: sqlite3.Row, season_display: int, display_boss_name: str, raid_id: int, is_eliminate: bool, columns: list) -> tuple[discord.Embed, discord.File | None]:
        """(輔助函式) 根據傳入的參數建立單一使用者的排名資訊 Embed"""
        raid_type_str = '大決戰' if is_eliminate else '總力戰'
        embed = discord.Embed(
            title=f"{data['Nickname']} 的 {raid_type_str} 排名",
            description=f"**賽季**: S{season_display} - {display_boss_name}",
            color=discord.Color.gold()
        )

        char_id = data['RepresentCharacterUniqueId']
        student_image_file = None
        image_path = STUDENT_IMAGE_PATH / f"{char_id}.webp"
        if image_path.exists():
            student_image_file = discord.File(image_path, filename=f"{char_id}.webp")
            embed.set_thumbnail(url=f"attachment://{char_id}.webp")
        
        field_value = f"**總分: {data['BestRankingPoint']:,}**\n"
        mode = "3min" if raid_id in [1, 5] else "4min"

        if is_eliminate:
            armor_cols = [c for c in ['LightArmor', 'HeavyArmor', 'Unarmed', 'ElasticArmor'] if c in columns]
            for armor in armor_cols:
                armor_score = data[armor]
                if not armor_score or armor_score == 0: continue
                difficulty = arona.determine_difficulty(int(armor_score), mode)
                try:
                    used_time_sec = arona.calculate_used_time(int(armor_score), difficulty, raid_id)
                    formatted_time = arona.format_time(used_time_sec)
                    field_value += f"> **{armor}**: {armor_score:,} ({difficulty} - {formatted_time})\n"
                except Exception:
                    field_value += f"> **{armor}**: {armor_score:,} ({difficulty} - 計算錯誤)\n"
        else:
            difficulty = arona.determine_difficulty(int(data['BestRankingPoint']), mode)
            try:
                used_time_sec = arona.calculate_used_time(int(data['BestRankingPoint']), difficulty, raid_id)
                formatted_time = arona.format_time(used_time_sec)
                field_value += f"難度: **{difficulty}**\n用時: **{formatted_time}**"
            except Exception:
                field_value += f"難度: **{difficulty}**\n用時: **計算錯誤**"

        embed.add_field(name=f"第 {data['Rank']} 名", value=field_value, inline=False)
        return embed, student_image_file

    @app_commands.command(name="glrainline", description="顯示台服總力/大決戰線")
    async def glrainline(self, interaction: discord.Interaction):
        if not self.table_list:
            await interaction.response.send_message("錯誤：找不到任何總力戰資料庫或資料表。", ephemeral=True)
            return
        view = GLRankLineView(self)
        await interaction.response.send_message("請選擇您想查詢的總力戰或大決戰賽季：", view=view, ephemeral=True)
    
    @app_commands.command(name="glrankuser", description="顯示玩家在總力戰或大決戰中的排名")
    async def glrankuser(self, interaction: discord.Interaction, nickname: str):
        if not self.table_list:
            await interaction.response.send_message("錯誤：找不到任何總力戰資料庫或資料表。", ephemeral=True)
            return
        view = GLRankUserView(self, nickname)
        await interaction.response.send_message(f"正在查詢玩家 **{nickname}** 的資訊，請選擇一個賽季：", view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    """用於將此 Cog 加入 Bot 的函式"""
    await bot.add_cog(GLRankLineCog(bot))
    print("GLRankLineCog has been loaded.")

class PaginatedUserView(discord.ui.View):
    def __init__(self, all_user_data: list, cog: GLRankLineCog, context: dict, timeout=180):
        super().__init__(timeout=timeout)
        self.all_user_data = all_user_data
        self.cog = cog
        self.context = context
        self.current_index = 0

        self.prev_button = discord.ui.Button(label="◀️ 上一位", style=discord.ButtonStyle.secondary)
        self.prev_button.callback = self.go_to_previous
        self.add_item(self.prev_button)

        self.next_button = discord.ui.Button(label="▶️ 下一位", style=discord.ButtonStyle.secondary)
        self.next_button.callback = self.go_to_next
        self.add_item(self.next_button)

        self._update_button_states()

    def _update_button_states(self):
        self.prev_button.disabled = self.current_index == 0
        self.next_button.disabled = self.current_index >= len(self.all_user_data) - 1

    async def update_message(self, interaction: discord.Interaction):
        self._update_button_states()
        current_data = self.all_user_data[self.current_index]
        embed, student_file = await self.cog._create_user_rank_embed(current_data, **self.context)
        embed.set_footer(text=f"玩家 {self.current_index + 1} / {len(self.all_user_data)}")
        files = [student_file] if student_file else []
        await interaction.response.edit_message(embed=embed, view=self, attachments=files)

    async def go_to_previous(self, interaction: discord.Interaction):
        self.current_index -= 1
        await self.update_message(interaction)

    async def go_to_next(self, interaction: discord.Interaction):
        self.current_index += 1
        await self.update_message(interaction)

class GLRankUserSelect(discord.ui.Select):
    def __init__(self, cog: GLRankLineCog, nickname: str):
        self.cog = cog
        self.nickname = nickname
        options = [discord.SelectOption(label=table, description=f"查詢 {nickname} 在此賽季的排名") for table in cog.table_list]
        super().__init__(placeholder="選擇一個賽季...", min_values=1, max_values=1, options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False, thinking=True)
        table_name = self.values[0]

        try:
            with sqlite3.connect(self.cog.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(f'PRAGMA table_info("{table_name}")')
                columns = [row[1] for row in cursor.fetchall()]
                is_eliminate = any(armor in columns for armor in ['LightArmor', 'HeavyArmor', 'Unarmed', 'ElasticArmor'])
                parts = table_name.split('_', 1)
                boss_name_from_table = parts[1]
                season_display = int(parts[0].replace('S', ''))
                internal_boss_key = next((key for key in BOSS_NAME_MAP.keys() if key.lower() in boss_name_from_table.lower()), None)
                display_boss_name = BOSS_NAME_MAP.get(internal_boss_key, boss_name_from_table)
                raid_id = BOSS_RAID_ID.get(display_boss_name, 0)
                
                context = {
                    "season_display": season_display, "display_boss_name": display_boss_name,
                    "raid_id": raid_id, "is_eliminate": is_eliminate, "columns": columns
                }

                query = f'SELECT * FROM "{table_name}" WHERE Nickname = ?'
                cursor.execute(query, (self.nickname,))
                all_data = cursor.fetchall()
                num_results = len(all_data)

                if num_results == 0:
                    await interaction.followup.send(f"在賽季 **{table_name}** 中找不到玩家 **{self.nickname}** 的排名資料。")
                elif num_results == 1:
                    embed, student_file = await self.cog._create_user_rank_embed(all_data[0], **context)
                    await interaction.followup.send(embed=embed, file=student_file)
                else:
                    first_embed, first_file = await self.cog._create_user_rank_embed(all_data[0], **context)
                    first_embed.set_footer(text=f"玩家 1 / {num_results}")
                    view = PaginatedUserView(all_data, self.cog, context)
                    await interaction.followup.send(
                        f"找到了 {num_results} 位名為 **{self.nickname}** 的玩家，正在顯示第 1 位:",
                        embed=first_embed, file=first_file, view=view
                    )
        except Exception as e:
            await interaction.followup.send(f"處理您的請求時發生未預期的錯誤：{e}", ephemeral=True)
            print(f"Callback 執行 '{table_name}' 時出錯: {e}")

class GLRankUserView(discord.ui.View):
    def __init__(self, cog: GLRankLineCog, nickname: str):
        super().__init__(timeout=300)
        self.add_item(GLRankUserSelect(cog, nickname))

class GLRankLineSelect(discord.ui.Select):
    def __init__(self, cog: GLRankLineCog):
        self.cog = cog
        options = [discord.SelectOption(label=table, description=f"查詢 {table} 的分數線") for table in cog.table_list]
        super().__init__(placeholder="選擇一個賽季...", min_values=1, max_values=1, options=options[:25])
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        table_name = self.values[0]
        try:
            with sqlite3.connect(self.cog.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(f'PRAGMA table_info("{table_name}")')
                columns = [row[1] for row in cursor.fetchall()]
                is_eliminate = any(armor in columns for armor in ['LightArmor', 'HeavyArmor', 'Unarmed', 'ElasticArmor'])
                
                parts = table_name.split('_', 1)
                boss_name_from_table = parts[1]
                season_display = int(parts[0].replace('S', ''))
                
                internal_boss_key = next((key for key in BOSS_NAME_MAP.keys() if key.lower() in boss_name_from_table.lower()), None)
                display_boss_name = BOSS_NAME_MAP.get(internal_boss_key, boss_name_from_table)
                raid_id = BOSS_RAID_ID.get(display_boss_name, 0)
                
                ranks_to_query = [1, 1000, 5000, 10001, 50001]
                query = f'SELECT * FROM "{table_name}" WHERE Rank IN ({",".join(map(str, ranks_to_query))})'
                cursor.execute(query)
                db_results = {row['Rank']: row for row in cursor.fetchall()}

                raid_type_str = '大決戰' if is_eliminate else '總力戰'
                embed_title = f"S{season_display} - {display_boss_name} {raid_type_str} 分數線"
                embed_color = discord.Color.red() if is_eliminate else discord.Color.blue()
                embed = discord.Embed(title=embed_title, color=embed_color)

                boss_icon_file = None
                if internal_boss_key and BOSS_ICON_MAPPING.get(internal_boss_key, "").exists():
                    boss_icon_file = discord.File(BOSS_ICON_MAPPING[internal_boss_key], filename=BOSS_ICON_MAPPING[internal_boss_key].name)
                    embed.set_thumbnail(url=f"attachment://{BOSS_ICON_MAPPING[internal_boss_key].name}")

                for rank in ranks_to_query:
                    data = db_results.get(rank)
                    if not data:
                        embed.add_field(name=f"第 {rank} 名", value="無資料", inline=False)
                        continue

                    emoji = TIER_MAPPING.get(rank, "")  # Get emoji if rank matches, else empty string
                    field_name = f"{emoji} 第 {rank} 名".strip() # .strip() removes leading space if no emoji
                    
                    field_value = f"**{data['Nickname']}**\n總分: **{data['BestRankingPoint']:,}**\n"
                    mode = "3min" if raid_id in [1, 5] else "4min"

                    if is_eliminate:
                        armor_cols = [c for c in ['LightArmor', 'HeavyArmor', 'Unarmed', 'ElasticArmor'] if c in columns]
                        for armor in armor_cols:
                            armor_score = data[armor]
                            if not armor_score or armor_score == 0: continue
                            difficulty = arona.determine_difficulty(int(armor_score), mode)
                            try:
                                used_time_sec = arona.calculate_used_time(int(armor_score), difficulty, raid_id)
                                field_value += f"> **{armor}**: {armor_score:,} ({difficulty} - {arona.format_time(used_time_sec)})\n"
                            except Exception:
                                field_value += f"> **{armor}**: {armor_score:,} ({difficulty} - 計算錯誤)\n"
                    else:
                        difficulty = arona.determine_difficulty(int(data['BestRankingPoint']), mode)
                        try:
                            used_time_sec = arona.calculate_used_time(int(data['BestRankingPoint']), difficulty, raid_id)
                            field_value += f"難度: **{difficulty}**\n用時: **{arona.format_time(used_time_sec)}**"
                        except Exception:
                             field_value += f"難度: **{difficulty}**\n用時: **計算錯誤**"
                    
                    embed.add_field(name=field_name, value=field_value, inline=False)
            
                await interaction.followup.send(embed=embed, file=boss_icon_file)
        except Exception as e:
            await interaction.followup.send(f"處理您的請求時發生未預期的錯誤：{e}")
            print(f"Callback 執行 '{table_name}' 時出錯: {e}")

class GLRankLineView(discord.ui.View):
    def __init__(self, cog: GLRankLineCog):
        super().__init__(timeout=300)
        self.add_item(GLRankLineSelect(cog))