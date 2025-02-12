import pandas as pd
import re
from utils import  get_student_usage_stats

class AronaStatistics:
    """負責讀取 `data.xlsx` 並處理 RAID/ERAID 數據"""

    def __init__(self, file_path="data.xlsx"):
        self.file_path = file_path
        self.xlsx = pd.ExcelFile(file_path)

    def get_raid_name(self, season: int):
        """根據 `data.xlsx` 找出 RAID SXX 的正確名稱"""
        for sheet in self.xlsx.sheet_names:
            df = pd.read_excel(self.xlsx, sheet_name=sheet, nrows=1)
            for column in df.columns:
                if f"S{season}" in column and "總力戰" in column:
                    return column
        print(f"⚠ 未找到 S{season} 相關的總力戰", flush=True)
        return f"S{season} 總力戰 (未知名稱)"

    def get_eraid_name(self, season: int, armor_type: str):
        """
        根據 `data.xlsx` 找出 ERAID SXX 的正確名稱，只匹配指定 `armor_type`
        """
        possible_names = []
        for sheet in self.xlsx.sheet_names:
            df = pd.read_excel(self.xlsx, sheet_name=sheet, nrows=1)
            for column in df.columns:
                if f"S{season}" in column and "大決戰" in column:
                    if armor_type in column:
                        possible_names.append(column)
                        
        # 去除重複值
        possible_names = list(dict.fromkeys(possible_names))
        
        if not possible_names:
            print(
                f"⚠ 未找到 S{season} {armor_type} 相關的 ERAID 大決戰", flush=True
            )
            return f"S{season} {armor_type} 大決戰 (未知名稱)"
        if len(possible_names) > 1:
            print(
                f"⚠ 警告: S{season} {armor_type} 匹配到多個結果, 可能有誤: {possible_names}",
                flush=True,
            )
        return possible_names[0]

    def get_summary_sheet_name(self, rank: int) -> str:
        """
        根據 rank 返回對應的 Summary 工作表名稱：
        - 1 ~ 1000："Summary - Rank 1000"
        - 1001 ~ 5000："Summary - Rank 1000 to 5000"
        - 5001 ~ 10000："Summary - Rank 5000 to 10000"
        - 10001 ~ 20000："Summary - Rank 10000 to 20000"
        """
        if 1 <= rank <= 1000:
            return "Summary - Rank 1000"
        elif 1001 <= rank <= 5000:
            return "Summary - Rank 1000 to 5000"
        elif 5001 <= rank <= 10000:
            return "Summary - Rank 5000 to 10000"
        elif 10001 <= rank <= 20000:
            return "Summary - Rank 10000 to 20000"
        else:
            raise ValueError(f"⚠ Rank {rank} 不在支援範圍內")

    def get_raid_stats(self, season: int, rank: int):
        """獲取 RAID 指定賽季的角色數據"""
        raid_name = self.get_raid_name(season)
        summary_sheet = self.get_summary_sheet_name(rank)
        df = pd.read_excel(self.xlsx, sheet_name=summary_sheet)
        if raid_name in df.columns:
            return (
                df[['stdNm', raid_name]]
                .sort_values(by=raid_name, ascending=False)
                .dropna()
                .values.tolist()
            )
        return []

    def get_eraid_stats(self, season: int, armor_type: str, rank: int):
        """獲取 ERAID 指定賽季、裝甲類型的角色數據"""
        valid_armor_types = ["LightArmor", "ElasticArmor", "HeavyArmor", "Unarmed"]
        if armor_type not in valid_armor_types:
            raise ValueError(
                f"⚠ armor_type 必須是 {valid_armor_types}, 但收到: {armor_type}"
            )

        eraid_name = self.get_eraid_name(season, armor_type)
        summary_sheet = self.get_summary_sheet_name(rank)
        df = pd.read_excel(self.xlsx, sheet_name=summary_sheet)
        if eraid_name in df.columns:
            return (
                df[['stdNm', eraid_name]]
                .sort_values(by=eraid_name, ascending=False)
                .dropna()
                .values.tolist()
            )
        return []

    
    def get_student_stats(self, student_id: str, seasons: int, armor_type: str):
        """
        獲取 student_id 在 S{seasons} {armor_type} 大決戰 的數據，並回傳格式化表格。
        """
        matching_sheets = []
        print(f"🔍 搜尋 `{student_id}` 相關的工作表...", flush=True)

        for sheet in self.xlsx.sheet_names:
            if student_id in sheet:
                matching_sheets.append(sheet)
                print(f"✅ 找到 `{student_id}` 相關的工作表: {sheet}", flush=True)

        if not matching_sheets:
            print(f"❌ 找不到 `{student_id}` 相關的工作表", flush=True)
            return None, None

        print(f"🔍 在 `{student_id}` 的工作表內，搜尋 `S{seasons}`, `{armor_type}`, `大決戰` 是否出現在內容中...", flush=True)

        for sheet in matching_sheets:
            df_full = pd.read_excel(self.xlsx, sheet_name=sheet, header=None)

            found_row = None
            end_row = None
            for index, row in df_full.iterrows():
                row_str = " ".join(row.dropna().astype(str))

                if f"S{seasons}" in row_str and armor_type in row_str and "大決戰" in row_str:
                    found_row = index
                    print(f"🎯 `{sheet}` 內部找到 `S{seasons} {armor_type} 大決戰` (位於第 {found_row+1} 行)", flush=True)
                    continue

                if found_row is not None and re.search(r"S\d+ - .* (大決戰|總力戰)", row_str):
                    end_row = index
                    print(f"⏹ 截斷 `{sheet}` 的數據 (結束於第 {end_row+1} 行)", flush=True)
                    break

            if found_row is not None:
                df_section = df_full.iloc[found_row:end_row].reset_index(drop=True) if end_row else df_full.iloc[found_row:].reset_index(drop=True)
                df_section = df_section.dropna(how="all", axis=1).dropna(how="all", axis=0).astype(str)

                title = df_section.iloc[0, 0].strip()
                title = self.translate_environment(title)
                headers = [str(x).strip() for x in df_section.iloc[1]]
                data_rows = df_section.iloc[2:].values.tolist()

                print(data_rows, flush=True)
                Two_dimensional_Arrays_data = get_student_usage_stats(data_rows)
                return sheet, title, Two_dimensional_Arrays_data

        return None, None

    def get_student_stats_raid(self, student_id: str, seasons: int):
        """
        獲取 student_id 在 S{seasons} 總力戰 的數據，並回傳格式化表格。
        """
        matching_sheets = []
        print(f"🔍 搜尋 `{student_id}` 相關的工作表...", flush=True)

        for sheet in self.xlsx.sheet_names:
            if student_id in sheet:
                matching_sheets.append(sheet)
                print(f"✅ 找到 `{student_id}` 相關的工作表: {sheet}", flush=True)

        if not matching_sheets:
            print(f"❌ 找不到 `{student_id}` 相關的工作表", flush=True)
            return None, None

        print(f"🔍 在 `{student_id}` 的工作表內，搜尋 `S{seasons}`, `總力戰` 是否出現在內容中...", flush=True)

        for sheet in matching_sheets:
            df_full = pd.read_excel(self.xlsx, sheet_name=sheet, header=None)

            found_row = None
            end_row = None
            for index, row in df_full.iterrows():
                row_str = " ".join(row.dropna().astype(str))

                if f"S{seasons}" in row_str and "總力戰" in row_str:
                    found_row = index
                    print(f"🎯 `{sheet}` 內部找到 `S{seasons} 總力戰` (位於第 {found_row+1} 行)", flush=True)
                    continue

                # **檢測 `SXX - ... 大決戰` 或 `SXX - ... 總力戰` 來截斷數據**
                if found_row is not None and re.search(r"S\d+ - .* (大決戰|總力戰)", row_str):
                    end_row = index
                    print(f"⏹ 截斷 `{sheet}` 的數據 (結束於第 {end_row+1} 行)", flush=True)
                    break

            if found_row is not None:
                df_section = df_full.iloc[found_row:end_row].reset_index(drop=True) if end_row else df_full.iloc[found_row:].reset_index(drop=True)

                # 清理 NaN 值
                df_section = df_section.dropna(how="all", axis=1).dropna(how="all", axis=0).astype(str)

                title = df_section.iloc[0, 0].strip()
                title = self.translate_environment(title)
                headers = [str(x).strip() for x in df_section.iloc[1]]
                data_rows = df_section.iloc[2:].values.tolist()

                print(data_rows, flush=True)
                Two_dimensional_Arrays_data = get_student_usage_stats(data_rows)
                print(Two_dimensional_Arrays_data, flush=True)

                return sheet, title, Two_dimensional_Arrays_data

        print(f"❌ `{student_id}` 的 S{seasons} 總力戰 沒有在內容中找到", flush=True)
        return None, None

    
    
    def get_student_usage(self, stu_name: str, rank: int) -> str:
        """
        根據學生名稱和 Rank 讀取 Excel 檔案 data.xlsx，返回該學生前 10 筆使用率統計。
        """
        try:
            sheet_name = self.get_summary_sheet_name(rank)
        except Exception as e:
            return f"❌ 錯誤: {e}"

        try:
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)
        except Exception as e:
            return f"❌ 讀取 Excel 檔案錯誤：{e}"

        # 確保欄位名稱正確
        df.columns = df.columns.str.strip()

        if 'stdNm' not in df.columns:
            return "❌ Excel 檔案格式錯誤，缺少 'stdNm' 欄位"

        # 避免 NaN 導致 contains 出錯
        df = df.dropna(subset=['stdNm'])

        # 檢查學生名稱是否存在
        student_rows = df[df['stdNm'].astype(str).str.contains(stu_name.strip(), case=False, na=False)]
        if student_rows.empty:
            return f"❌ 找不到學生 {stu_name} 的資料。"

        # 取第一筆匹配的學生資料
        student_row = student_rows.iloc[0]

        # 假設前 5 個欄位為基本資料，其餘欄位為各場使用率
        usage_cols = student_row.index[5:]
        usage_data = student_row[usage_cols]

        # 排序使用率數據（降冪），並選出前 20 筆
        usage_data = usage_data.sort_values(ascending=False).dropna()
        top10 = usage_data.head(20)

        output_lines = []
        for col, val in top10.items():
            output_lines.append(f"**{col}**: {int(val)} 場")

        return "\n".join(output_lines)
    

    def translate_environment(self, title: str) -> str:
        """
        將戰鬥環境類型從英文翻譯為中文
        """
        if not isinstance(title, str):  # 確保 title 是字串
            print(f"⚠ 警告：title 不是字串，跳過翻譯 ({title})")
            return title  # 如果不是字串，直接返回原始值

        translations = {
            "Outdoor": "野戰",
            "Street": "城鎮戰",
            "Indoor": "室內戰",
            "Unarmed": "神祕裝甲",
            "HeavyArmor": "重裝甲",
            "LightArmor": "輕裝甲",
            "ElasticArmor": "彈性裝甲",
        }

        try:
            for eng, zh in translations.items():
                title = title.replace(eng, zh)  # 替換英文為中文
            return title
        except Exception as e:
            print(f"⚠ 翻譯錯誤：{e}")
            return title  # 發生錯誤時，返回原始值


