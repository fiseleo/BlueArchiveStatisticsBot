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



