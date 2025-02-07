import aiohttp
import asyncio
import time

class AronaStatistics:
    """負責獲取和處理 Arona API 數據"""

    def __init__(self, raid_url, eraid_url, student_url, raid_info_url):
        self.raid_url = raid_url
        self.eraid_url = eraid_url
        self.student_url = student_url
        self.raid_info_url = raid_info_url
        self.student_data = None
        self.raid_info = None
        self.raid_map = {}
        self.eraid_map = {}

    async def fetch_data(self):
        """異步獲取所有學生和 RAID/ERAID 資訊"""
        self.student_data = await self.get_json(self.student_url) or {}
        self.raid_info = await self.get_json(self.raid_info_url) or {}

        # 取得 TW 服 RAID/ERAID 對應的 JP 服賽季
        self.raid_map = self.get_raid_mapping()
        self.eraid_map = self.get_eraid_mapping()

    async def get_json(self, url):
        """使用 aiohttp 進行非同步 API 請求"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        print(f"✅ 獲取成功 {url}，狀態碼: 200")
                        return await response.json()
                    else:
                        print(f"⚠ 無法獲取 {url}，狀態碼: {response.status}")
                        return None
            except Exception as e:
                print(f"⚠ API 請求失敗 {url}：{e}")
                return None
            
    def is_same_raid(self, a, b):
        """判斷兩場 RAID 是否相同"""
        return (
            a.get("RaidId") == b.get("RaidId") and
            a.get("Terrain") == b.get("Terrain") and
            all(t in b.get("ArmorTypes", []) for t in a.get("ArmorTypes", []))
        )

    def get_raid_mapping(self):
        try:
            # 取得 TW 與 JP 的 Raid 賽季資料
            tw_seasons = self.raid_info["RaidSeasons"][1]["Seasons"]
            jp_seasons = self.raid_info["RaidSeasons"][0]["Seasons"]

            # 取得 TW 服當前的 Raid 賽季
            curr_tw_raid = tw_seasons[-1]
            if float(curr_tw_raid["End"]) > time.time():
                curr_tw_raid = tw_seasons[-2]

            mapping = {}
            # 從 JP 服的資料中逆向迭代，直到遇到與 TW 當前賽季相符為止
            ref_jp = len(jp_seasons) - 1
            while ref_jp >= 0 and not self.is_same_raid(jp_seasons[ref_jp], curr_tw_raid):
                curr_jp_raid = jp_seasons[ref_jp]
                try:
                    raid_id = curr_jp_raid["RaidId"]  # 這裡就是 JP 服正確的 raid id
                    raid_name = self.raid_info["Raid"][raid_id - 1]["Name"]
                except Exception as e:
                    raid_name = "未知"
                    print(f"⚠ RAID 資訊查詢錯誤: {e}")
                terrain = curr_jp_raid["Terrain"]
                season_display = curr_jp_raid["SeasonDisplay"]
                mapping[season_display] = {
                    "id": raid_id,
                    "name": raid_name,
                    "terrain": terrain
                }
                ref_jp -= 1

            print(f"📌 修正後的 RAID Mapping: {mapping}")
            return mapping
        except Exception as e:
            print(f"⚠ 獲取 RAID Mapping 失敗: {e}")
            return {}


    def get_eraid_mapping(self):
        try:
            # 取得 TW 與 JP 的 ERAID 賽季資料
            tw_eraid_seasons = self.raid_info["RaidSeasons"][1]["EliminateSeasons"]
            jp_eraid_seasons = self.raid_info["RaidSeasons"][0]["EliminateSeasons"]

            # 取得 TW 服當前的 ERAID 賽季
            curr_tw_eraid = tw_eraid_seasons[-1]
            if float(curr_tw_eraid["End"]) > time.time():
                curr_tw_eraid = tw_eraid_seasons[-2]

            mapping = {}
            ref_jp = len(jp_eraid_seasons) - 1
            while ref_jp >= 0 and not self.is_same_raid(jp_eraid_seasons[ref_jp], curr_tw_eraid):
                curr_jp_eraid = jp_eraid_seasons[ref_jp]
                try:
                    raid_id = curr_jp_eraid["RaidId"]
                    raid_name = self.raid_info["Raid"][raid_id - 1]["Name"]
                except Exception as e:
                    raid_name = "未知"
                    print(f"⚠ ERAID 資訊查詢錯誤: {e}")
                terrain = curr_jp_eraid["Terrain"]
                season_display = curr_jp_eraid["SeasonDisplay"]
                mapping[season_display] = {
                    "id": raid_id,
                    "name": raid_name,
                    "terrain": terrain
                }
                ref_jp -= 1

            print(f"📌 修正後的 ERAID Mapping: {mapping}")
            return mapping
        except Exception as e:
            print(f"⚠ 獲取 ERAID Mapping 失敗: {e}")
            return {}
            
        
    async def fetch_raid_data(self):
        search_raid = {}
        for season, data in self.raid_map.items():
            season_id = season  
            url = self.raid_url.replace("<id>", str(season_id))
            print(f"Getting raid info for {season_id} {data['name']} {data['terrain']}")
            retrieved_info = await self.get_json(url)
            if retrieved_info is None:
                print(f"Skipping raid season {season} (raid_id: {season_id}) due to error.")
                continue
            search_raid[season] = retrieved_info
        return self.process_character_usage(search_raid)

    async def fetch_eraid_data(self):
       
        search_eraid = {}
        for season, data in self.eraid_map.items():
            # 使用 mapping 的 key 作為 season_id
            season_id = season  
            url = self.eraid_url.replace("<id>", str(season_id))
            print(f"Getting eraid info for {season_id} {data['name']} {data['terrain']}")
            retrieved_info = await self.get_json(url)
            if retrieved_info is None:
                print(f"Skipping eraid season {season} (raid_id: {season_id}) due to error.")
                continue
            search_eraid[season] = retrieved_info

        return self.process_character_usage(search_eraid)
    
    def process_character_usage(self, data):
        """處理 RAID/ERAID 角色使用統計"""
        character_usage = {}
        for battle_id, battle_data in data.items():
            char_usage_all = battle_data.get("characterUsage", {})
            for battle_type, battle_data in char_usage_all.items():
                char_usage = battle_data.get("r", {})
                for rank_range, std_dict in char_usage.items():
                    for std_id, usage_list in std_dict.items():
                        std_entry = self.student_data.get(std_id, {})
                        std_nm = std_entry.get("Name", f"未知角色 ({std_id})")
                        use_cnt = sum(usage_list)
                        if std_nm not in character_usage:
                            character_usage[std_nm] = 0
                        character_usage[std_nm] += use_cnt

        # 排序統計結果
        sorted_usage = sorted(character_usage.items(), key=lambda x: x[1], reverse=True)
        return sorted_usage
