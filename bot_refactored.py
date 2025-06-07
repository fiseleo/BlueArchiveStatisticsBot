# bot_refactored.py
from pathlib import Path
import discord
from discord.ext import commands
import os
import json
import asyncio

# --- 設定檔載入 ---
def load_config():
    """載入設定檔"""
    config = {}
    try:
        with open("TOKEN.txt", "r") as token_file:
            config['TOKEN'] = token_file.read().strip()
        with open("OWNER_ID.txt", "r") as owner_file:
            config['OWNER_ID'] = int(owner_file.read().strip())
    except FileNotFoundError as e:
        print(f"❌ 錯誤：找不到設定檔 {e.filename}，請確認文件存在！")
        exit(1)
    except (ValueError, TypeError):
        print("❌ 錯誤：OWNER_ID.txt 的內容格式不正確。")
        exit(1)
    return config

# --- 資料檔載入 ---
def load_data_files():

    data = {}
    JSON_DIR = Path(__file__).parent / "Json"
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    STUDENTS_JSON = JSON_DIR / "students.json"
    ID_NAME_MAPPING_JSON = JSON_DIR / "id_name_mapping.json"
    files_to_load = {
        STUDENTS_JSON : "all_student_data",
        ID_NAME_MAPPING_JSON : "id_name_mapping"
    }
    for file_path, data_key in files_to_load.items():
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                data[data_key] = json.load(file)
            print(f"✅ 成功載入 {file_path}")
        else:
            print(f"⚠ 警告：找不到 {file_path}，部分功能可能無法運作。")
            data[data_key] = {}
    return data

async def main():
    config = load_config()
    data_files = load_data_files()

    if not os.path.exists("data.xlsx"):
        print("❌ 錯誤：找不到 `data.xlsx`，請確認檔案已生成！")
        exit(1)

    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix="!", intents=intents)

    bot.owner_id = config['OWNER_ID']
    bot.all_student_data = data_files.get('all_student_data', {})
    bot.id_name_mapping = data_files.get('id_name_mapping', {})

    cogs_dir = "cogs"
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            try:
                await bot.load_extension(f"{cogs_dir}.{filename[:-3]}")
                print(f"🔩 已載入 Cog: {filename}")
            except Exception as e:
                print(f"❌ 載入 Cog {filename} 失敗: {e.__class__.__name__} - {e}")

    @bot.event
    async def on_ready():
        print(f'✅ 已登入：{bot.user}')
        await bot.change_presence(status=discord.Status.online)
        try:
            synced = await bot.tree.sync()
            print(f"🔄 成功同步 {len(synced)} 個應用程式指令")
        except Exception as e:
            print(f"❌ 同步指令失敗: {e}")

    # --- 啟動 Bot ---
    async with bot:
        await bot.start(config['TOKEN'])

if __name__ == "__main__":
    asyncio.run(main())