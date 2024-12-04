import pandas as pd

def load_holidays():
    """holidays.txtから休業日をリストとして読み込む"""
    with open('holidays.txt', 'r') as file:
        holidays = [line.strip() for line in file if line.strip()]
    return holidays

def is_holiday(date, holidays):
    """指定した日付が休業日かどうかを判定"""
    return date in holidays

def process_date_data(date):
    """指定された日付が休業日かを判定し、データをExcelから取得する"""
    holidays = load_holidays()
    if is_holiday(date, holidays):
        return f"{date}は休業日です。"
    
    file_path = 'data.xlsx'
    try:
        df = pd.read_excel(file_path)
        specific_day_data = df[df['Date'] == date]
        return specific_day_data.to_dict()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None
