import discord
from discord import app_commands
from discord.ext import commands
from AronaStatistics import AronaStatistics
from ImageFactory import ImageFactory
import os
import sys
import json
import asyncio
import subprocess
import AronaRankLine as arona
from utils import csv_to_json, replace_student_names
from typing import Optional


# 載入學生數據
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT1hFKXsxRA06SbB84DTe6gKcOympw3dKnDL2NMLgl7dqwnjy4SDcOBLbrRFbfkoZ_T3LUxWQo_KDeh/pub?output=csv"
students_json_path = "students.json"

# 檢查 JSON 檔案是否存在
if os.path.exists(students_json_path):
    with open(students_json_path, "r", encoding="utf-8") as file:
        all_student_data = json.load(file)
    print("✅ 成功載入 students.json")
else:
    print("⚠ 錯誤：找不到 students.json，請確認檔案是否存在！")
    all_student_data = {}  # 避免變數未定義錯誤


# 設定 Bot
intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents)

# 確保 `data.xlsx` 存在
if not os.path.exists("data.xlsx"):
    print("❌ 錯誤：找不到 `data.xlsx`，請確認檔案已生成！")
    exit(1)

id_name_mapping_path = "id_name_mapping.json"

if os.path.exists(id_name_mapping_path):
    with open(id_name_mapping_path, "r", encoding="utf-8") as file:
        id_name_mapping = json.load(file)
    print("✅ 成功載入 id_name_mapping.json")
else:
    print("⚠ 錯誤：找不到 id_name_mapping.json，請確認檔案是否存在！")
    id_name_mapping = {}

# 讀取 Excel
arona_stats = AronaStatistics("data.xlsx")

@bot.event
async def on_ready():
    print(f'✅ 已登入：{bot.user}')
    await bot.change_presence(status=discord.Status.online)
    try:
        synced = await bot.tree.sync()
        print(f"🔄 成功同步 {len(synced)} 個應用程式指令")
    except Exception as e:
        print(f"❌ 同步指令失敗: {e}")

def get_rank_range_str(rank: int) -> str:
    """
    根據 rank 回傳對應的區間文字：
      - 1 ~ 1000：返回 "排名 1~1000 內"
      - 1001 ~ 5000：返回 "排名 1001~5000 內"
      - 5001 ~ 10000：返回 "排名 5001~10000 內"
      - 10001 ~ 20000：返回 "排名 10001~20000 內"
    如果 rank 不在這些範圍內，則拋出錯誤。
    """
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

@bot.tree.command(name="raid_stats", description="取得 總力戰 角色使用統計")
async def raid_stats(interaction: discord.Interaction, season: int, rank: int):
    await interaction.response.defer()

    raid_name = arona_stats.get_raid_name(season)  # 取得 RAID SXX 的名稱
    data = arona_stats.get_raid_stats(season, rank)

    if not data:
        await interaction.followup.send(f"⚠ 無法取得 `{raid_name}` {get_rank_range_str(rank)} 的數據")
        return

    # 使用輔助函數 get_rank_range_str 來顯示 rank 區間
    embed = discord.Embed(
        title=f"📊 {raid_name} {get_rank_range_str(rank)} 角色使用率", 
        color=discord.Color.blue()
    )
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

    # 修正 Embed 標題，確保 armor_type 只顯示一次，並加入 rank 區間文字
    embed = discord.Embed(
        title=f"📊 大決戰 {eraid_name} {get_rank_range_str(rank)} 角色使用率", 
        color=discord.Color.green()
    )
    for name, count in data[:10]:
        embed.add_field(name=name, value=f"使用次數: {count}", inline=False)

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="eraid_stats_stu", description="取得特定角色的大決戰數據")
@app_commands.choices(armor_type=[
    app_commands.Choice(name="LightArmor", value="LightArmor"),
    app_commands.Choice(name="ElasticArmor", value="ElasticArmor"),
    app_commands.Choice(name="HeavyArmor", value="HeavyArmor"),
    app_commands.Choice(name="Unarmed", value="Unarmed")
])
async def statstu(interaction: discord.Interaction, stu_name: str, seasons: int, armor_type: str):
    await interaction.response.defer()

    # **查找 student_id**
    student_id = next((sid for sid, name in id_name_mapping.items() if name == stu_name), None)
    if student_id is None:
        await interaction.followup.send(f"⚠ 找不到 `{stu_name}` 的對應 ID")
        return

    # 呼叫 AronaStatistics 的方法
    sheet_name, raid_title, Two_dimensional_Arrays_data = arona_stats.get_student_stats(student_id, seasons, armor_type)
    if Two_dimensional_Arrays_data is None:
        await interaction.followup.send(f"⚠ 找不到 `{stu_name}` `S{seasons}` `{armor_type}` `大決戰` 的數據")
        return

    # 獲取學生資料
    student_info = all_student_data.get(str(student_id), None)
    if student_info is None:
        await interaction.followup.send(f"⚠ 錯誤：找不到 `{stu_name}` (`{student_id}`) 的相關資料")
        return

    # 轉換數據為圖片
    image_bytes = ImageFactory.StudentUsageImageGenerator(student_info, Two_dimensional_Arrays_data)

    # **建立 Discord Embed**
    embed = discord.Embed(
        title=f"📊 {stu_name} 的使用數據",
        description=f"查詢數據： {raid_title}\n詳情請參考下方圖片：",
        color=discord.Color.purple()
    )

    # **將圖片附加到 Embed**
    embed.set_image(url="attachment://student_usage_table.png")

    # **發送 Embed 與圖片**
    await interaction.followup.send(
        embed=embed,
        file=discord.File(image_bytes, filename="student_usage_table.png")
    )

@bot.tree.command(name="raid_stats_stu", description="取得特定角色的總力戰數據")
async def statstu(interaction: discord.Interaction, stu_name: str, seasons: int):
    await interaction.response.defer()

    # **查找 student_id**
    student_id = next((sid for sid, name in id_name_mapping.items() if name == stu_name), None)
    if student_id is None:
        await interaction.followup.send(f"⚠ 找不到 `{stu_name}` 的對應 ID")
        return

    # 呼叫 AronaStatistics 的方法
    sheet_name, raid_title, Two_dimensional_Arrays_data = arona_stats.get_student_stats_raid(student_id, seasons)
    if Two_dimensional_Arrays_data is None:
        await interaction.followup.send(f"⚠ 找不到 `{stu_name}` `S{seasons}` `總力戰` 的數據")
        return

    # 獲取學生資料
    student_info = all_student_data.get(str(student_id), None)
    if student_info is None:
        await interaction.followup.send(f"⚠ 錯誤：找不到 `{stu_name}` (`{student_id}`) 的相關資料")
        return

    # 轉換數據為圖片
    image_bytes = ImageFactory.StudentUsageImageGenerator(student_info, Two_dimensional_Arrays_data)

    # **建立 Discord Embed**
    embed = discord.Embed(
        title=f"📊 {stu_name} 的使用數據",
        description=f"查詢數據： {raid_title}\n詳情請參考下方圖片：",
        color=discord.Color.purple()
    )

    # **將圖片附加到 Embed**
    embed.set_image(url="attachment://student_usage_table.png")

    # **發送 Embed 與圖片**
    await interaction.followup.send(
        embed=embed,
        file=discord.File(image_bytes, filename="student_usage_table.png")
    )





@bot.tree.command(name="raidline", description="顯示指定賽季的總力戰分數")
async def raidline(interaction: discord.Interaction, sensons: int):
    await interaction.response.defer()

    # 取得該賽季的 Raid 資料（分數資訊）
    raid_url = f"https://blue.triple-lab.com/raid/{sensons}"
    raid_data = arona.get_json(raid_url)
    if raid_data is None:
        await interaction.followup.send("無法取得總力戰資料！")
        return
    rank_results = arona.get_rank_results(raid_data)

    # 取得 raidInfo 資料（包含賽季詳細資訊與 Boss 名稱）
    raid_info_url = "https://schaledb.com/data/tw/raids.json"
    raid_info = arona.get_json(raid_info_url)
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

    # 判斷模式：若 raid_id 為 1 或 5，則為 3min 模式；否則 4min 模式
    if raid_id in [1, 5]:
        mode = "3min"
    else:
        mode = "4min"

    # 針對每個排名先判斷難度，再計算用時
    for rank in arona.RANKS:
        raw_value = rank_results[rank]
        try:
            score = int(raw_value)
            formatted_score = f"{score:,}"
        except Exception:
            formatted_score = raw_value
            continue

        # 根據 score 與模式判斷難度
        difficulty = arona.determine_difficulty(score, mode)
        print(f"[DEBUG] Rank {rank}: score = {score}, mode = {mode}, difficulty = {difficulty}")
        try:
            used_time_sec = arona.calculate_used_time(score, difficulty, raid_id)
            formatted_used_time = arona.format_time(used_time_sec)
            print(f"[DEBUG] Rank {rank}: used_time_sec = {used_time_sec}, formatted_used_time = {formatted_used_time}")
        except Exception as e:
            print(f"[DEBUG] Rank {rank}: calculate_used_time error: {e}")
            formatted_used_time = "計算錯誤"
        
        embed.add_field(
            name=f"第{rank}名",
            value=f"{formatted_score}\n({difficulty}難度) (用時 {formatted_used_time})",
            inline=False
        )

    await interaction.followup.send(embed=embed)

# 指令 /eraidline：大決戰分數
@bot.tree.command(name="eraidline", description="顯示指定賽季的大決戰分數")
async def eraidline(interaction: discord.Interaction, sensons: int):
    await interaction.response.defer()
    
    # 1. 從 blue.triple-lab 取得該賽季的 ERAID 資料
    eraid_url = f"https://blue.triple-lab.com/eraid/{sensons}"
    eraid_data = arona.get_json(eraid_url)
    if eraid_data is None:
        await interaction.followup.send("無法取得大決戰資料！")
        return
    rank_results = arona.get_rank_results(eraid_data)
    
    # 2. 從 raidInfo 取得該賽季的 ERAID 詳細資訊（包含賽季詳細資訊與 Boss 名稱）
    raid_info_url = "https://schaledb.com/data/tw/raids.json"
    raid_info = arona.get_json(raid_info_url)
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
    
    # 判斷模式：若 raid_id 為 1 或 5，則視為 3min 模式；否則 4min 模式
    mode = "3min" if raid_id in [1, 5] else "4min"
    
    # 針對每個排名，僅輸出分數與分數組合說明（不輸出用時）
    for rank in arona.RANKS:
        raw_value = rank_results[rank]
        try:
            score = int(raw_value)
            formatted_score = f"{score:,}"
        except Exception:
            formatted_score = raw_value
            continue
        
        
        #breakdown = arona.get_score_breakdown(mode, score)
        
        embed.add_field(
            name=f"第{rank}名",
            #value=f"{formatted_score}  ({breakdown}) (參考用)",
            value=f"{formatted_score}",
            inline=False
        )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="stuusage", description="取得指定學生前20筆使用率統計")
async def stuusage(interaction: discord.Interaction, stu_name: str, rank: int):
    """
    Discord 指令:
      /stuusage stu_name: "某某學生" rank: 1000
    讀取 Excel 中指定 Rank 工作表，查找該學生的前 20 項使用率數據，並回應到 Discord 頻道。
    """
    await interaction.response.defer()  # 避免超時

    # 避免阻塞主線程，使用 asyncio.to_thread()
    result = await asyncio.to_thread(arona_stats.get_student_usage, stu_name, rank)

    # 建立 Discord Embed 物件
    embed = discord.Embed(
        title=f"📊 {stu_name} 的使用率 來自 {get_rank_range_str(rank)}" ,
        color=discord.Color.blue()
    )

    # 如果找不到學生，顯示錯誤訊息
    if "❌" in result:
        embed.description = result
    else:
        embed.description = "前 20 項最高使用率："
        for line in result.split("\n"):
            embed.add_field(name="\u200B", value=line, inline=False)  # \u200B 是空白字符

    await interaction.followup.send(embed=embed)

class PaginationView(discord.ui.View):
    def __init__(self, results: list, page_size: int = 5):
        super().__init__(timeout=180)  # 互動視窗 3 分鐘後逾時
        self.results = results
        self.page_size = page_size
        self.current_page = 0
        # 計算總頁數
        self.max_page = (len(results) - 1) // page_size if results else 0
        
        # 等待逾時後要更新訊息用
        self.message: Optional[discord.Message] = None

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(title="搜尋結果", color=discord.Color.blue())
        start_index = self.current_page * self.page_size
        end_index = start_index + self.page_size
        page_data = self.results[start_index:end_index]

        if not page_data:
            embed.description = "沒有找到符合條件的結果。"
            return embed
        
        for idx, item in enumerate(page_data, start=start_index + 1):
            field_value = (
                f"分數：{item['score']}\n"
                f"用時：{item['used_time_str']}\n"
                f"學生：{'、'.join(item['students'])}\n"
                f"URL：{item['URL']}"
            )
            embed.add_field(name=f"結果 {idx}", value=field_value, inline=False)

        embed.set_footer(text=f"頁數：{self.current_page + 1} / {self.max_page + 1}")
        return embed

    @discord.ui.button(label="上一頁", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="下一頁", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.max_page:
            self.current_page += 1
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def on_timeout(self):
        """
        當 View 逾時（timeout=180 秒後）自動被呼叫。
        在這裡清除或禁用按鈕，並更新訊息。
        """
        # 清除所有按鈕
        self.clear_items()
        
        # 如果要只是禁用按鈕（而非刪除），可以用：
        # for child in self.children:
        #     child.disabled = True

        # 如果之前有記錄 message，就可以直接編輯
        if self.message:
            await self.message.edit(view=self)
@bot.tree.command(name="search-video", description="依據條件搜尋影片資料")
@app_commands.choices(battle_field=[
    app_commands.Choice(name="室內戰", value="室內戰"),
    app_commands.Choice(name="野戰", value="野戰"),
    app_commands.Choice(name="城鎮戰", value="城鎮戰")
])
@app_commands.choices(boss_name=[
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
])
@app_commands.choices(difficulty=[
    app_commands.Choice(name="INSANE", value="INSANE"),
    app_commands.Choice(name="TORMENT", value="TORMENT"),
    app_commands.Choice(name="LUNATIC", value="LUNATIC")
])
@app_commands.choices(armor_type=[
    app_commands.Choice(name="輕裝備", value="輕裝備"),
    app_commands.Choice(name="彈力裝甲", value="彈力裝甲"),
    app_commands.Choice(name="重裝甲", value="重裝甲"),
    app_commands.Choice(name="特殊裝甲", value="特殊裝甲")
])
@app_commands.describe(
    include_students="包含學生 (可選，逗號分隔)",
    exclude_students="排除學生 (可選，逗號分隔)"
)
async def search_video(
    interaction: discord.Interaction,
    battle_field: str,
    boss_name: str,
    difficulty: str,
    armor_type: str,
    include_students: str = None,
    exclude_students: str = None
):
    await interaction.response.defer()
    
    # Debug：印出收到的參數
    print(f"DEBUG: search_video 收到參數：battle_field={battle_field}, boss_name={boss_name}, difficulty={difficulty}, armor_type={armor_type}")
    if include_students:
        print(f"DEBUG: include_students={include_students}")
    if exclude_students:
        print(f"DEBUG: exclude_students={exclude_students}")
    
    # 將阻塞的 CSV 轉換與名稱替換放到非同步線程執行
    await asyncio.to_thread(csv_to_json, url, "output.json")
    await asyncio.to_thread(replace_student_names, "output.json", "TL.json")
    
    # 讀取最終 JSON 檔
    try:
        with open("TL.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        await interaction.followup.send(f"讀取資料失敗: {e}", ephemeral=True)
        return
    
    boss_raid_id_map = {
        "薇娜": 1,
        "赫賽德": 2,
        "白&黑": 3,
        "耶羅尼姆斯": 4,
        "KAITEN FX Mk.0": 5,
        "佩洛洛吉拉": 6,
        "霍德": 7,
        "高茲": 8,
        "葛利果": 9,
        "氣墊船": 10,
        "黑影": 11,
        "Geburah": 12
    }
    # 若找不到，預設 0
    raid_id = boss_raid_id_map.get(boss_name, 0)
    
    # 轉換 include_students 與 exclude_students 為清單
    include_list = [s.strip() for s in include_students.split(",") if s.strip()] if include_students else []
    exclude_list = [s.strip() for s in exclude_students.split(",") if s.strip()] if exclude_students else []
    
    # 根據 boss_name 判斷使用模式：若為 薇娜 或 KAITEN FX Mk.0 則為 3min 模式，其他為 4min
    mode = "3min" if boss_name in ["薇娜", "KAITEN FX Mk.0"] else "4min"
    print(f"DEBUG: 使用模式設定為：{mode}")
    
    results = []
    for rec in data:
        # 比對 battle_field, boss_name, armor_type 必須完全相符
        if rec.get("battle-field") != battle_field:
            continue
        if rec.get("boss-name") != boss_name:
            continue
        if rec.get("armor") != armor_type:
            continue

        # 判斷難度
        score = rec.get("score", 0)
        rec_diff = arona.determine_difficulty(score, mode)
        print(f"DEBUG: record id={rec.get('id')} score={score} 判定難度={rec_diff}")
        if rec_diff != difficulty:
            continue

        # 取得學生欄位
        students = []
        for i in range(1, 61):
            student = rec.get(f"student{i}")
            if student is None:
                break
            students.append(student)

        # 檢查 include_students 與 exclude_students 條件
        if include_list and not all(include in students for include in include_list):
            continue
        if exclude_list and any(exclude in students for exclude in exclude_list):
            continue

        try:
            used_time_sec = arona.calculate_used_time(score, difficulty, raid_id)
            # 假設有一個 format_time 函式可以把秒數轉成 mm:ss
            used_time_str = arona.format_time(used_time_sec)
        except Exception as e:
            used_time_str = "計算失敗"

        results.append({
            "score": score,
            "used_time_str": used_time_str,  # 把用時字串一起存
            "students": students,
            "URL": rec.get("URL")
        })

        
    if not results:
        embed = discord.Embed(title="搜尋結果", description="沒有找到符合條件的結果。", color=discord.Color.blue())
        await interaction.followup.send(embed=embed)
        return  
      
    results.sort(key=lambda x: x["score"], reverse=True)  # 依分數排序  
    # 建立 Discord Embed 回覆
    view = PaginationView(results, page_size=5)
    embed = view.create_embed()  # 產生第一頁的 Embed
    message = await interaction.followup.send(embed=embed, view=view) # 顯示 Embed 與 View

    view.message = message  # 記錄 message，以便更新

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

@bot.tree.command(name="exec", description="執行 Arona AI Helper（只有作者能用）")
async def exec_script(interaction: discord.Interaction):
    """執行本地 `arona_ai_helper.py`，並在結束後重啟 Bot"""
    await interaction.response.defer(ephemeral=True)  # 🔹 **輸出只有發送者可見**

    # **權限檢查：只有 Bot 擁有者能執行**
    if interaction.user.id != OWNER_ID:
        await interaction.followup.send("⚠ 你沒有權限執行此命令！")
        return

    # **指定 `arona_ai_helper.py` 路徑**
    script_path = os.path.join(os.getcwd(), "arona_ai_helper.py")
    if not os.path.exists(script_path):
        await interaction.followup.send("❌ 找不到 `arona_ai_helper.py`，請確認檔案是否存在。")
        return

    try:
        # **使用 subprocess.Popen 來執行腳本，沒有超時限制**
        process = subprocess.Popen(["python", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # **等待腳本執行結束**
        stdout, stderr = process.communicate()

        # **合併標準輸出與錯誤輸出**
        output = (stdout + "\n" + stderr).strip()

        if not output:
            output = "✅ 腳本執行成功，但沒有輸出。"

        # **限制輸出長度（避免過長）**
        if len(output) > 1900:
            output = output[:1900] + "\n...(輸出過長，已截斷)"

        # **回傳執行結果**
        embed = discord.Embed(title=f"🖥 執行 `arona_ai_helper.py` 結果", description=f"```\n{output}\n```", color=discord.Color.blue())
        await interaction.followup.send(embed=embed)

        # **通知使用者 bot 即將重啟**
        await interaction.followup.send("🔄 **Arona AI Helper 執行完畢，正在重新啟動 Bot...**")

        # **重啟 bot**
        restart_bot()

    except Exception as e:
        await interaction.followup.send(f"❌ 腳本執行失敗：{e}")

@bot.tree.command(name="exec-download-schaledb-data", description="執行下載 SchaleDB 資料腳本（只有作者能用）")
async def exec_script(interaction: discord.Interaction):
    """執行本地 `arona_ai_helper.py`，並在結束後重啟 Bot"""
    await interaction.response.defer(ephemeral=True)  # 🔹 **輸出只有發送者可見**

    # **權限檢查：只有 Bot 擁有者能執行**
    if interaction.user.id != OWNER_ID:
        await interaction.followup.send("⚠ 你沒有權限執行此命令！")
        return

    # **指定 `DownloadSchaleDBData.py` 路徑**
    script_path = os.path.join(os.getcwd(), "DownloadSchaleDBData.py")
    if not os.path.exists(script_path):
        await interaction.followup.send("❌ 找不到 `DownloadSchaleDBData.py`，請確認檔案是否存在。")
        return

    try:
        # **使用 subprocess.Popen 來執行腳本，沒有超時限制**
        process = subprocess.Popen(["python", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # **等待腳本執行結束**
        stdout, stderr = process.communicate()

        # **合併標準輸出與錯誤輸出**
        output = (stdout + "\n" + stderr).strip()

        if not output:
            output = "✅ 腳本執行成功，但沒有輸出。"

        # **限制輸出長度（避免過長）**
        if len(output) > 1900:
            output = output[:1900] + "\n...(輸出過長，已截斷)"

        # **回傳執行結果**
        embed = discord.Embed(title=f"🖥 執行 `DownloadSchaleDBData.py` 結果", description=f"```\n{output}\n```", color=discord.Color.blue())
        await interaction.followup.send(embed=embed)

        # **通知使用者 bot 即將重啟**
        await interaction.followup.send("🔄 **Arona AI Helper 執行完畢，正在重新啟動 Bot...**")

        # **重啟 bot**
        restart_bot()

    except Exception as e:
        await interaction.followup.send(f"❌ 腳本執行失敗：{e}")
def restart_bot():
    """使用 `execv` 重新啟動 Bot"""
    python = sys.executable
    os.execl(python, python, *sys.argv)  # 🚀 **直接重新啟動當前腳本**

# 讀取 Bot Token
try:
    with open("TOKEN.txt", "r") as token_file:
        TOKEN = token_file.read().strip()
except FileNotFoundError:
    print("❌ 錯誤：找不到 `TOKEN.txt`，請確認 Token 文件存在！")
    exit(1)
try:
    with open("OWNER_ID.txt", "r") as owner_file:
        OWNER_ID = int(owner_file.read().strip())
except FileNotFoundError:
    print("❌ 錯誤：找不到 `OWNER_ID.txt`，請確認擁有者 ID 文件存在！")
    exit(1)

async def main():
    async with bot:
        await bot.start(TOKEN)

import asyncio
asyncio.run(main())
