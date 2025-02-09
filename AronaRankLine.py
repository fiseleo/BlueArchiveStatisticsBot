import requests
import json

# 要查詢的排名位置
RANKS = [1, 1000, 5000, 10000, 20000, 120000]

def get_json(url: str):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch {url} (status code: {response.status_code})")
            return None
    except Exception as e:
        print(f"Exception while fetching {url}: {e}")
        return None

def get_rank_results(data: dict) -> dict:
    b = data.get("b", {})
    results = {}
    for rank in RANKS:
        results[rank] = b.get(str(rank), "無資料")
    return results

def get_raidinfo_by_season(raid_info: dict, sensons: int, eraid: bool = False) -> dict:
    """
    從 raid_info 中取得指定賽季的資訊：
      - 若 eraid 為 False，則從 raid_info["RaidSeasons"][0]["Seasons"] 中搜尋
      - 若 eraid 為 True，則從 raid_info["RaidSeasons"][0]["EliminateSeasons"] 中搜尋
    若找不到，則回傳該陣列中的最後一筆。
    回傳的 dict 包含：
      - "SeasonDisplay"（例如 74）
      - "RaidId"（用來從 raid_info["Raid"] 中取得 Boss 名稱）
      - "Terrain"（地型）
    """
    try:
        ts = raid_info["RaidSeasons"][0]
        seasons = ts["EliminateSeasons"] if eraid else ts["Seasons"]
    except Exception as e:
        print("取得 raid_info 中的賽季資料錯誤:", e)
        return {}
    season_data = None
    for season in seasons:
        # 直接比對 sensons 與 SeasonDisplay（注意：SeasonDisplay 可能是數字或字串）
        if str(season.get("SeasonDisplay", "")).strip().lower() == str(sensons).strip().lower():
            season_data = season
            break
    if season_data is None and seasons:
        season_data = seasons[-1]
    print("[DEBUG] get_raidinfo_by_season - sensons:", sensons, "取得的賽季資料:", season_data)
    return season_data

# 修改後的 get_boss_info
def get_boss_info(raid_info: dict, raid_id: int) -> str:
    try:
        raids = raid_info.get("Raid", [])
        for r in raids:
            try:
                current_id = int(r.get("Id", 0))
            except Exception:
                continue
            if current_id == raid_id:
                return r.get("Name", "未知")
        return "未知"
    except Exception as e:
        print("取得 boss 資訊錯誤:", e)
        return "未知"