import io
from pathlib import Path
import sys
import requests
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 定義 URL
urls = {
    "students.json": "https://schaledb.com/data/tw/students.json",
    "localization.json": "https://schaledb.com/data/tw/localization.json"
}
JSON_DIR = Path(__file__).parent / "Json"
STUDENTS_JSON = JSON_DIR / "students.json"
JSON_DIR.mkdir(exist_ok=True) 

# 下載並保存 JSON 文件
for filename, url in urls.items():
    Save_Path = JSON_DIR / filename
    response = requests.get(url)
    if response.status_code == 200:
        with open(Save_Path, "w", encoding="utf-8") as file:
            json.dump(response.json(), file, ensure_ascii=False, indent=4)
        print(f"下載完成: {Save_Path}")
    else:
        print(f"下載失敗: {filename}, 狀態碼: {response.status_code}")

# 讀取 students.json
with open(STUDENTS_JSON, "r", encoding="utf-8") as file:
    students = json.load(file)

# 資料夾名稱
students_folder = "studentsimage"
bg_folder = "CollectionBG"
output_json_path =  JSON_DIR / "id_name_mapping.json"

# 確保資料夾存在
os.makedirs(students_folder, exist_ok=True)
os.makedirs(bg_folder, exist_ok=True)

# 下載圖片函數
def download_image(url, save_path):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return save_path
        else:
            return f"下載失敗: {url}, 狀態碼: {response.status_code}"
    except Exception as e:
        return f"錯誤: {e}"

# 生成下載任務
download_tasks = []
with ThreadPoolExecutor(max_workers=10) as executor:  # 設置最多 10 個並行下載
    futures = {}

    for student_id, student_data in students.items():
        # 學生圖片
        student_image_url = f"https://schaledb.com/images/student/collection/{student_id}.webp"
        student_image_path = os.path.join(students_folder, f"{student_id}.webp")
        futures[executor.submit(download_image, student_image_url, student_image_path)] = student_image_path

        # 背景圖片
        if "CollectionBG" in student_data:
            bg_image_url = f"https://schaledb.com/images/background/{student_data['CollectionBG']}.jpg"
            bg_image_path = os.path.join(bg_folder, f"{student_data['CollectionBG']}.jpg")
            futures[executor.submit(download_image, bg_image_url, bg_image_path)] = bg_image_path

    # 進度條顯示
    for future in tqdm(as_completed(futures), total=len(futures), desc="下載中"):
        result = future.result()
        if isinstance(result, str) and "失敗" in result:
            print(result)

print("所有圖片下載完成。")


id_name_mapping = {str(student["Id"]): student["Name"] for student in students.values()}
with open(output_json_path, "w", encoding="utf-8") as file:
    json.dump(id_name_mapping, file, ensure_ascii=False, indent=4)
print(f"已成功生成 {output_json_path}")