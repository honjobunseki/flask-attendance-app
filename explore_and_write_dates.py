import os
import xlwings as xw
from datetime import datetime
import re
import traceback
import logging
from logging.handlers import RotatingFileHandler

# ログの設定（ローテーションを追加）
handler = RotatingFileHandler("process.log", maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # タイムスタンプとレベルを非表示にする
    handlers=[
        handler,
        logging.StreamHandler()
    ]
)

def extract_reception_number_from_filename(filename):
    filename = re.sub(r'^[^A-Za-z0-9]+', '', filename)
    match = re.search(r'([A-Za-z]{1,3}\d+|\d+)[\s　]', filename)
    if match:
        reception_number = match.group(1)
        logging.debug(f"Extracted reception number '{reception_number}' from filename '{filename}'.")
        return reception_number
    else:
        logging.error(f"Could not extract reception number from filename '{filename}'. Skipping file.")
        return None

def extract_date_from_folder(folder_name):
    try:
        match = re.search(r'(\d{1,2})月(\d{1,2})日', folder_name)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            logging.debug(f"Extracted date {month}月{day}日 from folder name '{folder_name}'.")
            return month, day
        else:
            logging.error(f"Could not extract month and day from folder name '{folder_name}'.")
            return None
    except Exception as e:
        logging.error(f"Error extracting date from folder name '{folder_name}': {e}")
        return None

def extract_year_from_folder(folder_name):
    match = re.match(r'^(\d{4})', folder_name)
    if match:
        return match.group(1)
    return None

def extract_date_from_path(file_path):
    try:
        path_parts = file_path.split(os.sep)
        year = None
        for part in path_parts:
            match = re.match(r'^(\d{4})$', part)
            if match:
                year = int(match.group(1))
                break
        if not year:
            logging.error(f"Year not found in path: '{file_path}'")
            return None, None, None
        day_folder = None
        for part in reversed(path_parts):
            if re.search(r'\d{1,2}月\d{1,2}日', part):
                day_folder = part
                break
        if not day_folder:
            logging.error(f"Day folder not found in path: '{file_path}'")
            return None, None, None
        month_day = extract_date_from_folder(day_folder)
        if month_day:
            month, day = month_day
            return year, month, day
        else:
            logging.error(f"Month and day not found in folder name: '{day_folder}'")
            return None, None, None
    except Exception as e:
        logging.error(f"Error extracting date from path '{file_path}': {e}")
        return None, None, None

def get_starting_date_from_excel(excel_file):
    try:
        logging.debug(f"Opening Excel file with xlwings: {excel_file}")
        with xw.App(visible=False) as app:
            wb = app.books.open(excel_file)
            sheet = wb.sheets['Sheet1']
            starting_date = sheet.range('B3').value
            logging.debug(f"Value read from Excel (B3): {starting_date} (type: {type(starting_date)})")
            wb.close()

            if starting_date is None:
                logging.error("Cell B3 is empty. Please enter a valid date in cell B3.")
                return None
            if isinstance(starting_date, datetime):
                pass
            elif isinstance(starting_date, float):
                starting_date = datetime.fromordinal(datetime(1899, 12, 30).toordinal() + int(starting_date))
            elif isinstance(starting_date, str):
                for fmt in ('%Y/%m/%d', '%Y-%m-%d', '%Y.%m.%d', '%Y年%m月%d日', '%Y%m%d'):
                    try:
                        starting_date = datetime.strptime(starting_date, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    logging.error(f"Date format not recognized: {starting_date}")
                    return None
            else:
                logging.error(f"Unhandled date type: {type(starting_date)}")
                return None
            logging.debug(f"Starting date found: {starting_date}")
            return starting_date
    except Exception as e:
        logging.error(f"Error reading starting date from Excel with xlwings: {e}")
        traceback.print_exc()
        return None

def search_folders(base_folder, target_folder, start_date):
    try:
        logging.debug(f"Checking base folder: {base_folder}")
        if not os.path.exists(base_folder):
            raise FileNotFoundError(f"Base folder not found: {base_folder}")
        
        for root, dirs, files in os.walk(base_folder):
            relative_path = os.path.relpath(root, base_folder)
            path_parts = relative_path.split(os.sep)

            if relative_path == '.':
                dirs[:] = [d for d in dirs if re.match(r'^(\d{4})', d)]
                continue

            if len(path_parts) == 1:
                year_folder = path_parts[0]
                year = extract_year_from_folder(year_folder)
                if not year:
                    logging.warning(f"Year not found in folder name: '{year_folder}'. Skipping folder.")
                    dirs[:] = []
                    continue
                year = int(year)
                
                if year < start_date.year:
                    logging.debug(f"Skipping entire year folder: {root} (Year: {year})")
                    dirs[:] = []
                    continue
                elif year == start_date.year:
                    dirs[:] = [d for d in dirs if re.match(r'^(\d{1,2})月', d)]
                else:
                    dirs[:] = [d for d in dirs if re.match(r'^(\d{1,2})月', d)]
                continue

            if len(path_parts) == 2:
                month_folder = path_parts[1]
                month_match = re.match(r'^(\d{1,2})月', month_folder)
                if not month_match:
                    logging.warning(f"Month not found or invalid in folder name: '{root}'. Skipping folder.")
                    dirs[:] = []
                    continue
                month = int(month_match.group(1))
                year = int(path_parts[0])

                try:
                    folder_year_month = datetime(year, month, 1)
                except ValueError as ve:
                    logging.error(f"Invalid year/month extracted from folder '{root}': {ve}. Skipping folder.")
                    dirs[:] = []
                    continue

                if folder_year_month < datetime(start_date.year, start_date.month, 1):
                    logging.debug(f"Skipping entire month folder: {root} (Year: {year}, Month: {month})")
                    dirs[:] = []
                    continue

                if year == start_date.year and month == start_date.month:
                    dirs[:] = [d for d in dirs if re.match(r'^\d{1,2}月\d{1,2}日', d)]
                else:
                    dirs[:] = [d for d in dirs if re.match(r'^\d{1,2}月\d{1,2}日', d)]
                continue

            if len(path_parts) == 3:
                day_folder = path_parts[2]
                day_match = re.match(r'^(\d{1,2})月(\d{1,2})日', day_folder)
                if not day_match:
                    logging.warning(f"Day not found or invalid in folder name: '{root}'. Skipping folder.")
                    dirs[:] = []
                    continue
                month = int(day_match.group(1))
                day = int(day_match.group(2))
                year = int(path_parts[0])

                folder_date = datetime(year, month, day)
                if folder_date < start_date:
                    logging.debug(f"Skipping entire day folder: {root} (Date: {folder_date})")
                    dirs[:] = []
                    continue

                for file in files:
                    if file.endswith('.xlsx') or file.endswith('.xlsm'):
                        file_path = os.path.join(root, file)
                        filename = os.path.basename(file)
                        reception_number = extract_reception_number_from_filename(filename)
                        
                        if reception_number:
                            year_extracted, month_extracted, day_extracted = extract_date_from_path(file_path)
                            if not all([year_extracted, month_extracted, day_extracted]):
                                logging.warning(f"Could not extract date from path '{file_path}'. Skipping file.")
                                continue
                            
                            try:
                                folder_date_file = datetime(year_extracted, month_extracted, day_extracted)
                            except ValueError as ve:
                                logging.error(f"Invalid date extracted from path '{file_path}': {ve}. Skipping file.")
                                continue
                            
                            if folder_date_file < start_date:
                                logging.debug(f"Folder date {folder_date_file} is before start date {start_date}. Skipping file {file_path}.")
                                continue
                            
                            target_year_folder = os.path.join(target_folder, f'{year_extracted}年')
                            target_month_folder = os.path.join(target_year_folder, f'{month_extracted}月')
                            target_day_folder = os.path.join(target_month_folder, f'{month_extracted}月{day_extracted}日')
                            reception_folder = os.path.join(target_day_folder, f'{reception_number}')
                            
                            if os.path.exists(reception_folder):
                                logging.debug(f"Reception folder '{reception_folder}' already exists. Skipping file {file_path}.")
                                continue
                            
                            try:
                                os.makedirs(reception_folder, exist_ok=True)
                                logging.info(f"フォルダを作成しました {month_extracted}月{day_extracted}日 {reception_number}")
                            except Exception as mkdir_e:
                                logging.error(f"Error creating folder '{reception_folder}': {mkdir_e}. Skipping file {file_path}.")
                                continue
                        else:
                            logging.error(f"Could not extract reception number from filename '{filename}'. Skipping file.")
                            continue
                continue

            dirs[:] = []
            continue

    except Exception as e:
        logging.error(f"Error searching folders: {e}")
        traceback.print_exc()

def main():
    base_folder = r'\\landisk-f9f2eb\bunseki 共有 2023\アスベスト　お客様管理●\★依頼書\★依頼書'
    target_folder = r'\\landisk-f9f2eb\顕微鏡画像\顕微鏡画像'
    excel_file = r'C:\Users\mail\Desktop\python\extracted_dates.xlsx'

    start_date = get_starting_date_from_excel(excel_file)
    if not start_date:
        logging.error("No valid starting date found. Exiting.")
        return

    search_folders(base_folder, target_folder, start_date)

if __name__ == "__main__":
    main()
    input("処理が完了しました。Enterキーを押して終了してください...")
