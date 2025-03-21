
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

# CSV 資料來源網址
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT1hFKXsxRA06SbB84DTe6gKcOympw3dKnDL2NMLgl7dqwnjy4SDcOBLbrRFbfkoZ_T3LUxWQo_KDeh/pub?output=csv"
# 學生資料來源網址
jp_url = 'https://schaledb.com/data/jp/students.json'
tw_url = 'https://schaledb.com/data/tw/students.json'

def csv_to_json(csv_url: str, output_filename: str = "output.json"):
    """
    讀取 Google Sheets CSV 並輸出為 JSON 檔 (僅做空值處理，不替換任何名稱)
    """
    # 讀取 CSV
    df = pd.read_csv(csv_url)
    # 將所有 NaN 轉成 None (以便最終 JSON 輸出為 null)
    df = df.where(pd.notnull(df), None)
    # 轉為 list of dict
    json_str = df.to_json(orient='records', force_ascii=False)
    json_pretty = json.dumps(json.loads(json_str), indent=4, ensure_ascii=False)
    
    # 輸出成 JSON
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(json_pretty)
    
    print(f"✅ 已將 CSV 轉為 JSON：{output_filename}")

def replace_student_names(input_json: str, output_json: str):
    """
    讀取 CSV 轉換後的 JSON，進行學生名稱整段替換（含括號）以及 armor、boss-name、battle-field 欄位的翻譯，
    再輸出最終 JSON 檔
    """
    # 1) 建立中文->日文、以及日文->中文的學生對照表
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
    # boss-name 對照：請依需求調整
    boss_name_mapping = {
        "ビナー" : "薇娜",
        "ケセド" : "赫賽德",
        "シロ&クロ" : "白&黑",
        "ヒエロニムス" : "耶羅尼姆斯",
        "KAITEN FX Mk.0" : "KAITEN FX Mk.0",
        "ペロロジラ" : "佩洛洛吉拉",
        "ホド" : "霍德",
        "ゴズ" : "高茲",
        "グレゴリオ" : "葛利果",
        "ホバークラフト" : "氣墊船",
        "クロカゲ" : "黑影",
        "ゲブラ" : "Geburah",
        "コクマー" : "Chokmah"

        # 若有其他 boss-name 對照，可在此加入
    }
    # armor 對照
    armor_mapping = {
        "弾力装甲": "彈力裝甲",
        "特殊装甲": "特殊裝甲",
        "重装甲": "重裝甲",
        "軽装備": "輕裝備"
        # 如有其他 armor 對照，請自行補充
    }
    # battle-field 對照
    battle_field_mapping = {
        "市街地": "城鎮戰",
        "屋外": "野戰",
        "屋内": "室內戰"
        # 如有其他 battle-field 對照，可加入
    }
    
    # 3) 讀取第一階段產生的 JSON
    with open(input_json, "r", encoding="utf-8") as f:
        records = json.load(f)
    
    # 4) 替換學生名稱 (student1 ~ student60)，直接整段比對，不拆分括號
    for rec in records:
        for i in range(1, 61):
            key = f"student{i}"
            if key not in rec or rec[key] is None:
                break  # 遇到空值則停止後續欄位的處理
            original_name = rec[key]  # 例如 "サヤ（私服）"
            if original_name in jp_to_cn_mapping:
                rec[key] = jp_to_cn_mapping[original_name]  # 替換為中文，例如 "沙耶(私服)"
    
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



