
import pandas as pd
import asyncio
import AronaRankLine as determine_difficulty
import json
import requests
def get_student_usage_stats(usage_data: list) -> list:
    """
    接收學生使用狀況資料的二維陣列，每個內部陣列包含完整列資料：
      [排名, 借用, 三星以下, 四星, 五星無武, 專一, 專二, 專三, 共計]
    轉換後僅回傳使用狀況數據（二維陣列），捨棄第一個及最後一個欄位。
    
    例如：
      輸入：
        [
          ['1000以下', '0', '0', '0', '0', '0', '1', '999', '1000'],
          ['5000以下', '27', '0', '0', '0', '0', '22', '4958', '5007'],
          ['10000以下', '79', '0', '0', '0', '0', '173', '9797', '10049'],
          ['20000以下', '4175', '0', '0', '0', '3', '1187', '18767', '24132']
        ]
      輸出：
        [
          [0, 0, 0, 0, 0, 1, 999],
          [27, 0, 0, 0, 0, 22, 4958],
          [0, 0, 0, 0, 0, 173, 9797],
          [4175, 0, 0, 0, 3, 1187, 18767]
        ]
    注意：當該列的排名為 "10000以下" 時，將強制把「借用」數據設為 0。
    """
    if not isinstance(usage_data, list):
        print("資料錯誤：輸入應為二維陣列", flush=True)
        return None

    processed = []
    for idx, row in enumerate(usage_data):
        # 確認每列至少有 3 個元素（排名、至少一筆數據、共計）
        if not isinstance(row, list) or len(row) < 3:
            print(f"資料錯誤：第 {idx+1} 個內部陣列格式不正確", flush=True)
            return None

        # 取出中間欄位：捨棄第一欄（排名）與最後一欄（共計）
        usage_row = row[1:-1]

        # 嘗試將每個元素轉換成 int 型態
        try:
            usage_row_int = [int(x) for x in usage_row]
        except Exception as e:
            print(f"資料轉換錯誤：第 {idx+1} 個內部陣列無法轉換為整數: {e}", flush=True)
            return None

        processed.append(usage_row_int)

    print("轉換後的學生使用狀況資料：", flush=True)
    for row in processed:
        print(row, flush=True)
    return processed


jp_url = 'https://schaledb.com/data/jp/students.json'
tw_url = 'https://schaledb.com/data/tw/students.json'

def replace_student_names(input_json: str, output_json: str):
    """
    讀取轉換後的 JSON，進行學生名稱替換（依據學生對照表）以及
    armor、boss-name、battle-field 欄位的翻譯，再輸出最終 JSON 檔
    """
    # 1) 取得學生對照資料，建立中文->日文以及日文->中文對照表
    try:
        jp_response = requests.get(jp_url)
        tw_response = requests.get(tw_url)
        jp_students = jp_response.json()
        tw_students = tw_response.json()
    except Exception as e:
        print(f"下載學生資料失敗: {e}")
        return

    # 建立「中文名稱 -> 日文名稱」的字典（完整字串包含括號）
    cn_to_jp_mapping = {}
    for student_id in tw_students:
        tw_student = tw_students.get(student_id)
        jp_student = jp_students.get(student_id)
        if tw_student and jp_student:
            tw_name = tw_student.get("Name")  # 例如 "沙耶(私服)"
            jp_name = jp_student.get("Name")  # 例如 "サヤ（私服）"
            if tw_name and jp_name:
                cn_to_jp_mapping[tw_name] = jp_name
    # 建立反向字典「日文名稱 -> 中文名稱」
    jp_to_cn_mapping = {jp: cn for cn, jp in cn_to_jp_mapping.items()}

    # 2) 定義額外欄位的翻譯對照表
    boss_name_mapping = {
        "ビナー": "薇娜",
        "ケセド": "赫賽德",
        "シロ&クロ": "白&黑",
        "ヒエロニムス": "耶羅尼姆斯",
        "KAITEN FX Mk.0": "KAITEN FX Mk.0",
        "ペロロジラ": "佩洛洛吉拉",
        "ホド": "霍德",
        "ゴズ": "高茲",
        "グレゴリオ": "葛利果",
        "ホバークラフト": "氣墊船",
        "クロカゲ": "黑影",
        "ゲブラ": "Geburah",
        "コクマー": "Chokmah"
    }
    armor_mapping = {
        "弾力装甲": "彈力裝甲",
        "特殊装甲": "特殊裝甲",
        "重装甲": "重裝甲",
        "軽装備": "輕裝備"
    }
    battle_field_mapping = {
        "市街地": "城鎮戰",
        "屋外": "野戰",
        "屋内": "室內戰"
    }

    # 3) 讀取 JSON 檔（假設其結構為 data.json 的格式：列表，每筆紀錄包含 "students" 列表）
    with open(input_json, "r", encoding="utf-8") as f:
        records = json.load(f)

    # 4) 替換學生名稱：針對 rec["students"] 中每個名稱，若在對照表中則替換為中文名稱
    for rec in records:
        if "students" in rec and isinstance(rec["students"], list):
            rec["students"] = [jp_to_cn_mapping.get(name, name) for name in rec["students"]]

    # 5) 替換其他欄位：armor, boss-name, battle-field
    for rec in records:
        if "armor" in rec and rec["armor"] is not None:
            original = rec["armor"]
            if original in armor_mapping:
                rec["armor"] = armor_mapping[original]
        if "boss-name" in rec and rec["boss-name"] is not None:
            original = rec["boss-name"]
            if original in boss_name_mapping:
                rec["boss-name"] = boss_name_mapping[original]
        if "battle-field" in rec and rec["battle-field"] is not None:
            original = rec["battle-field"]
            if original in battle_field_mapping:
                rec["battle-field"] = battle_field_mapping[original]

    # 6) 輸出最終 JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4, ensure_ascii=False)

    print(f"✅ 學生及其他欄位翻譯完成，輸出：{output_json}")




def get_data(armor_type: str, battle_field: str, boss_name: str,
                     difficulty: str, considerHelper_bool: bool, bilibiliDisplay_bool: bool,exclude_students: str, include_students: str):
    url = "https://kina-ko-m-ochi.com/data_to_change/get_data.php"
    
    # 建立中→日翻譯對照表
    armor_translation = {
        "輕裝備": "軽装備",
        "彈力裝甲": "弾力装甲",
        "重裝甲": "重装甲",
        "特殊裝甲": "特殊装甲"
    }
    battle_field_translation = {
        "室內戰": "屋内",
        "野戰": "屋外",
        "城鎮戰": "市街地"
    }
    boss_name_translation = {
        "薇娜": "ビナー",
        "赫賽德": "ケセド",
        "白&黑": "シロ&クロ",
        "耶羅尼姆斯": "ヒエロニムス",
        "KAITEN FX Mk.0": "KAITEN FX Mk.0",
        "佩洛洛吉拉": "ペロロジラ",
        "霍德": "ホド",
        "高茲": "ゴズ",
        "葛利果": "グレゴリオ",
        "氣墊船": "ホバークラフト",
        "黑影": "クロカゲ",
        "Geburah": "ゲブラ"
    }
    
    # 進行翻譯
    jp_armor = armor_translation.get(armor_type, armor_type)
    jp_battle_field = battle_field_translation.get(battle_field, battle_field)
    jp_boss_name = boss_name_translation.get(boss_name, boss_name)
    
    # 由於使用者提供學生名稱為中文，因此需要先取得學生中文與日文對照資料
    jp_url = 'https://schaledb.com/data/jp/students.json'
    tw_url = 'https://schaledb.com/data/tw/students.json'
    try:
        jp_response = requests.get(jp_url)
        tw_response = requests.get(tw_url)
        jp_students = jp_response.json()
        tw_students = tw_response.json()
    except Exception as e:
        print(f"下載學生資料失敗: {e}")
        # 若下載失敗，直接使用使用者提供的原始資料
        translated_include = [s.strip() for s in include_students.split(",") if s.strip()] if include_students else []
        translated_exclude = [s.strip() for s in exclude_students.split(",") if s.strip()] if exclude_students else []
    else:
        # 建立「中文名稱 -> 日文名稱」對照表
        cn_to_jp_mapping = {}
        for student_id, tw_student in tw_students.items():
            jp_student = jp_students.get(student_id)
            if tw_student and jp_student:
                tw_name = tw_student.get("Name")
                jp_name = jp_student.get("Name")
                if tw_name and jp_name:
                    cn_to_jp_mapping[tw_name] = jp_name
        # 將使用者提供的 includeStudents 轉換成日文
        translated_include = []
        if include_students:
            for name in [s.strip() for s in include_students.split(",") if s.strip()]:
                translated_include.append(cn_to_jp_mapping.get(name, name))
        # 將使用者提供的 excludeStudents 轉換成日文
        translated_exclude = []
        if exclude_students:
            for name in [s.strip() for s in exclude_students.split(",") if s.strip()]:
                translated_exclude.append(cn_to_jp_mapping.get(name, name))
    
    payload = {
        "armor": jp_armor,
        "battleField": jp_battle_field,
        "bilibiliDisplay": bilibiliDisplay_bool,
        "bossName": jp_boss_name,
        "considerHelper": considerHelper_bool,
        "difficulty": difficulty,
        "excludeStudents": translated_exclude,
        "includeStudents": translated_include,
        "uniqueFormation": True,
        "unit": "0"  # 0 = 不考慮幾刀，1 = 優先找一刀的組合，2 = 優先找兩刀的組合
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    
    # 發送 POST 請求
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    try:
        data = response.json()
    except json.JSONDecodeError:
        print("無法解析 JSON 響應:", response.text)
        data = {"response" : response.text}    
    with open("cache.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print("✅ 已將資料寫入 cache.json")



