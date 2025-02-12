

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