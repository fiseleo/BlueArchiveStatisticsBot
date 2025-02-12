from rich.table import Table
from rich.console import Console
from PIL import Image, ImageDraw, ImageFont
import io
import pandas as pd


# -------------------------------
# 利用 Rich 產生表格文字
# -------------------------------
def generate_rich_table(title: str, headers: list, rows: list) -> str:
    """
    利用 rich 生成表格字串，能正確處理中英文混合的寬度問題。
    :param title: 表格的標題
    :param headers: 欄位表頭（例如 ["排名", "借用", "三星以下", ...]）
    :param rows: 資料列（每列為一個列表）
    :return: 表格字串
    """
    table = Table(title=title, show_lines=True)
    for header in headers:
        table.add_column(header, justify="center")
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    console = Console(record=True, width=100)
    console.print(table)
    rich_text = console.export_text()
    print("生成的 rich 表格文字：\n", rich_text)
    return rich_text

def text_to_image(text: str, font_path: str = "SarasaFixedCL-ExtraLight.ttf", font_size: int = 48,
                  target_width: int = 1920, target_height: int = 1080) -> io.BytesIO:
    """
    渲染表格為圖片，並確保表格對齊與可讀性，使用適當的等寬字體來解決邊框對不齊問題。
    """
    import os

    # **選擇適合表格的等寬字體**
    if not os.path.exists(font_path):
        print("【Debug】找不到字型檔案，改用 `SarasaFixedCL-ExtraLight.ttf` 字型。")
        font = ImageFont.truetype("SarasaFixedCL-ExtraLight.ttf", font_size)
    else:
        font = ImageFont.truetype(font_path, font_size)

    lines = text.splitlines()
    dummy_img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy_img)

    # **計算最大寬度（確保等寬字元）**
    max_char_width = font_size * 0.55  # ✅ 用 `0.55` 修正字體的實際寬度
    max_line_width = max(len(line) * max_char_width for line in lines)
    total_text_height = sum(int(font_size * 1.3) for _ in lines)  # ✅ 行距設定 `1.3` 讓字不擠

    # **確保表格置中**
    offset_x = (target_width - max_line_width) // 2
    offset_y = (target_height - total_text_height) // 2

    img = Image.new("RGB", (target_width, target_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # **用 `textbbox()` 確保對齊**
    current_y = offset_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        draw.text(((target_width - line_width) // 2, current_y), line, fill=(0, 0, 0), font=font)
        current_y += int(font_size * 1.3)

    # **儲存圖片**
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes



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