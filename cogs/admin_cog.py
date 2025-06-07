# cogs/admin_cog.py

import discord
from discord.ext import commands
from discord import app_commands
import os
import sys
import asyncio
import subprocess


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def restart_bot(self):
        """輔助函式，使用 execv 重新啟動 Bot"""
        python = sys.executable
        os.execl(python, python, *sys.argv)

    @app_commands.command(name="restart", description="🔄 重新啟動 Bot (限管理員)")
    @app_commands.checks.has_permissions(administrator=True)
    async def restart(self, interaction: discord.Interaction):
        """重新啟動 Bot"""
        await interaction.response.send_message("🔄 Bot 正在重啟...", ephemeral=True)
        await asyncio.sleep(2)
        self.restart_bot()

    async def _execute_script(self, interaction: discord.Interaction, script_name: str):
        """
        執行外部 Python 腳本的通用函式。
        - script_name: 要執行的腳本檔案名稱 (例如: "arona_ai_helper.py")
        """
        if interaction.user.id != self.bot.owner_id:
            await interaction.followup.send("⚠ 你沒有權限執行此命令！", ephemeral=True)
            return

        script_path = os.path.join(os.getcwd(), script_name)
        if not os.path.exists(script_path):
            await interaction.followup.send(f"❌ 找不到 `{script_name}`，請確認檔案是否存在。", ephemeral=True)
            return

        try:
            # 使用 sys.executable 確保跨平台相容性 (Windows/Linux)
            # 這會使用當前執行 Bot 的 Python 解譯器來跑腳本
            python_executable = sys.executable
            
            process = subprocess.Popen(
                [python_executable, script_path], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                encoding='utf-8'
            )
            
            # 等待腳本執行完成並取得輸出
            stdout, stderr = process.communicate()
            output = (stdout + "\n" + stderr).strip()

            if not output:
                output = "✅ 腳本執行成功，但沒有輸出。"

            # 限制輸出長度以避免超過 Discord 字元限制
            if len(output) > 1900:
                output = output[:1900] + "\n...(輸出過長，已截斷)"

            embed = discord.Embed(
                title=f"🖥 執行 `{script_name}` 結果", 
                description=f"```\n{output}\n```", 
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # 腳本執行完畢後，通知並重啟 Bot
            await interaction.followup.send(f"🔄 **`{script_name}` 執行完畢，正在重新啟動 Bot...**", ephemeral=True)
            self.restart_bot()

        except Exception as e:
            await interaction.followup.send(f"❌ 執行 `{script_name}` 失敗：{e}", ephemeral=True)


    @app_commands.command(name="exec_helper", description="執行 Arona AI Helper（只有作者能用）")
    async def exec_helper(self, interaction: discord.Interaction):
        """執行 arona_ai_helper.py 腳本"""
        await interaction.response.defer(ephemeral=True)
        await self._execute_script(interaction, "arona_ai_helper.py")


    @app_commands.command(name="exec_schaledb_download", description="執行下載 SchaleDB 資料腳本（只有作者能用）")
    async def exec_schaledb_download(self, interaction: discord.Interaction):
        """執行 DownloadSchaleDBData.py 腳本"""
        await interaction.response.defer(ephemeral=True)
        await self._execute_script(interaction, "DownloadSchaleDBData.py")


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
