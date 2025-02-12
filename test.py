def print_student_usage_stats(usage_data: list) -> None:
    """
    輸入學生使用狀況資料（二維陣列），其中：
      - 每個子陣列有 7 筆數據（分別代表「借用」、「三星以下」、「四星」、「五星無武」、「專一」、「專二」、「專三」）
      - 整體資料共有 4 個子陣列（依檔次分別為：1000以下、5000以下、10000以下、20000以下）
    輸出格式為純文字表格，不使用 rich 套件，也不包含「共計」欄位。
    """
    # 預設檔次與欄位標題（順序與使用狀況資料對應）
    tiers = ["1000以下", "5000以下", "10000以下", "20000以下"]
    headers = ["借用", "三星以下", "四星", "五星無武", "專一", "專二", "專三"]

    # 檢查輸入資料是否符合預期
    if len(usage_data) != 4:
        print("輸入資料的陣列數量不正確，應該有四個子陣列（對應四個檔次）。")
        return
    for idx, row in enumerate(usage_data):
        if len(row) != 7:
            print(f"第 {idx+1} 個子陣列的數據不正確，應該有 7 筆數據。")
            return

    # 建立表格字串
    lines = []

    # 組合表頭
    header_line = f"{'檔次':<10}" + "".join(f"{title:^10}" for title in headers)
    lines.append(header_line)
    lines.append("-" * len(header_line))

    # 逐筆輸出每一個檔次的數據
    for tier, row in zip(tiers, usage_data):
        row_line = "".join(f"{str(cell):^10}" for cell in row)
        lines.append(f"{tier:<10}{row_line}")
    # 輸出表格    
    print(lines)


# 測試範例
if __name__ == "__main__":
    # 範例資料：四個檔次，每個檔次有 7 筆使用狀況數據
    sample_usage_data = [
        [0, 0, 0, 0, 0, 1, 999],
        [27, 0, 0, 0, 0, 22, 4958],
        [79, 0, 0, 0, 0, 173, 9797],
        [4175, 0, 0, 0, 3, 1187, 18767]
    ]
    print_student_usage_stats(sample_usage_data)