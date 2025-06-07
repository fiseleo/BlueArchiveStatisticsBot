import requests

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



def calculate_used_time(score, difficulty, raid_id):
    """
    根據分數、難度與 raid_id 計算用時（單位：秒）
    用時 = 3600 - ((score - (基本HP分數 + 基本難度分數)) / 分數倍率)
    """
    multiplier = get_score_multiplier(difficulty)
    base_hp = get_base_hp_score(difficulty, raid_id)
    base_difficulty = get_base_difficulty_score(difficulty)
    target_time_score = score - (base_hp + base_difficulty)
    # Debug 輸出各參數
    print(f"[DEBUG] calculate_used_time - score: {score}, difficulty: {difficulty}, raid_id: {raid_id}")
    print(f"[DEBUG] multiplier: {multiplier}, base_hp: {base_hp}, base_difficulty: {base_difficulty}")
    print(f"[DEBUG] target_time_score: {target_time_score}")
    
    if target_time_score < 0:
        raise ValueError("輸入的分數太低，計算後的目標時間分數為負值。")
    remaining_time = target_time_score / multiplier
    used_time = 3600 - remaining_time
    print(f"[DEBUG] remaining_time: {remaining_time}, used_time: {used_time}")
    return used_time

def format_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)  # 將秒數取整
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    return f"{minutes:02d}:{secs:02d}.{milliseconds:03d}"

def get_score_multiplier(difficulty):
    """根據難度取得分數倍率"""
    multipliers = {
        'NORMAL': 120,
        'HARD': 240,
        'VERYHARD': 480,
        'HARDCORE': 960,
        'EXTREME': 1440,
        'INSANE': 1920,
        'TORMENT': 2400,
        'LUNATIC': 2880,
    }
    return multipliers.get(difficulty.upper(), 0)

def get_base_hp_score(difficulty, raid_id):
    """
    根據難度以及 raid_id 取得基本 HP 分數。
    若 raid_id 為 1 或 5，使用一組數值，否則使用另一組數值。
    """
    difficulty = difficulty.upper()
    if raid_id in [1, 5]:
        mapping = {
            'NORMAL': 229000,
            'HARD': 458000,
            'VERYHARD': 916000,
            'HARDCORE': 1832000,
            'EXTREME': 5392000,
            'INSANE': 12449600,
            'TORMENT': 18876000,
            'LUNATIC': 25683000, # unknown
        }
    else:
        mapping = {
            'NORMAL': 277000,
            'HARD': 554000,
            'VERYHARD': 1108000,
            'HARDCORE': 2216000,
            'EXTREME': 6160000,
            'INSANE': 14216000,
            'TORMENT': 19508000,
            'LUNATIC': 26315000,
        }
    return mapping.get(difficulty, 0)

def get_base_difficulty_score(difficulty):
    """根據難度取得基本難度分數"""
    difficulty = difficulty.upper()
    mapping = {
        'NORMAL': 250000,
        'HARD': 500000,
        'VERYHARD': 1000000,
        'HARDCORE': 2000000,
        'EXTREME': 4000000,
        'INSANE': 6800000,
        'TORMENT': 12200000,
        'LUNATIC': 17710000,
    }
    return mapping.get(difficulty, 0)

def determine_difficulty(score: int, mode: str) -> str:
    """
    根據分數與模式（"4min" 或 "3min"）判斷難度
    """
    if mode == "4min":
        if score >= 44025000:
            return "LUNATIC"
        elif score >= 31708000:
            return "TORMENT"
        elif score >= 21016000:
            return "INSANE"
        elif score >= 10160000:
            return "EXTREME"
        elif score >= 4216000:
            return "HARDCORE"
        elif score >= 2108000:
            return "VERYHARD"
        elif score >= 1054000:
            return "HARD"
        elif score >= 527000:
            return "NORMAL"
        else:
            return "???"
    elif mode == "3min":
        if score >= 40000000:
            return "LUNATIC"
        elif score >= 31076000:
            return "TORMENT"
        elif score >= 19249600:
            return "INSANE"
        elif score >= 9392000:
            return "EXTREME"
        elif score >= 3832000:
            return "HARDCORE"
        elif score >= 1916000:
            return "VERYHARD"
        elif score >= 958000:
            return "HARD"
        elif score >= 479000:
            return "NORMAL"
        else:
            return "???"
    else:
        return "???"
