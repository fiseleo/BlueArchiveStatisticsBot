import pandas as pd

class AronaStatistics:
    """負責讀取 `data.xlsx` 並處理 RAID/ERAID 數據"""

    def __init__(self, file_path="data.xlsx"):
        self.file_path = file_path
        self.xlsx = pd.ExcelFile(file_path)

    def get_raid_name(self, season: int):
        """根據 `data.xlsx` 找出 RAID SXX 的正確名稱"""
        for sheet in self.xlsx.sheet_names:
            df = pd.read_excel(self.xlsx, sheet_name=sheet, nrows=1)  # 只讀取第一行，拿欄位名稱
            for column in df.columns:
                if f"S{season}" in column and "總力戰" in column:
                    return column  # 找到對應的 RAID 名稱就回傳
        print(f"⚠ 未找到 S{season} 相關的 RAID 總力戰")
        return f"S{season} 總力戰 (未知名稱)"


    def get_raid_stats(self, season: int, rank: int):
        """獲取 RAID 指定賽季的角色數據"""
        raid_name = self.get_raid_name(season)  # 確保 RAID 名稱來自 Excel 內部
        for sheet in self.xlsx.sheet_names:
            df = pd.read_excel(self.xlsx, sheet_name=sheet)
            if raid_name in df.columns:  # 確保該 RAID 季度存在
                return df[['stdNm', raid_name]].sort_values(by=raid_name, ascending=False).dropna().values.tolist()
        return []
    def get_eraid_name(self, season: int, armor_type: str):
        """根據 `data.xlsx` 找出 ERAID SXX 的正確名稱，只匹配指定 `armor_type`"""
        possible_names = []

        for sheet in self.xlsx.sheet_names:
            df = pd.read_excel(self.xlsx, sheet_name=sheet, nrows=1)  # 只讀取第一行，拿欄位名稱
            for column in df.columns:
                if f"S{season}" in column and "大決戰" in column:
                    if armor_type in column:
                        possible_names.append(column)

        if not possible_names:
            print(f"⚠ 未找到 S{season} {armor_type} 相關的 ERAID 大決戰")
            return f"S{season} {armor_type} 大決戰 (未知名稱)"

        # **確保只返回唯一的匹配**
        if len(possible_names) > 1:
            print(f"⚠ 警告: S{season} {armor_type} 匹配到多個結果, 可能有誤: {possible_names}")
        
        return possible_names[0]  # 只返回第一個匹配的名稱




    def get_eraid_stats(self, season: int, armor_type: str, rank: int):
        """獲取 ERAID 指定賽季、裝甲類型的角色數據"""

        # 限制 armor_type 只能是這四種
        valid_armor_types = ["LightArmor", "ElasticArmor", "HeavyArmor", "Unarmed"]
        if armor_type not in valid_armor_types:
            raise ValueError(f"⚠ armor_type 必須是 {valid_armor_types}, 但收到: {armor_type}")

        eraid_name = self.get_eraid_name(season, armor_type)  # 取得正確的 ERAID 名稱
        for sheet in self.xlsx.sheet_names:
            df = pd.read_excel(self.xlsx, sheet_name=sheet)
            if eraid_name in df.columns:  # 確保該 ERAID 季度存在
                return df[['stdNm', eraid_name]].sort_values(by=eraid_name, ascending=False).dropna().values.tolist()
        return []


    def get_student_stats(self, stu_name: str):
        """獲取特定角色的 RAID 和 ERAID 數據"""
        student_sheets = [s for s in self.xlsx.sheet_names if stu_name in s]
        if not student_sheets:
            return {}

        student_data = {}
        for sheet in student_sheets:
            df = pd.read_excel(self.xlsx, sheet_name=sheet)
            student_data[sheet] = df.to_dict()

        return student_data
