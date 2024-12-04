import os
import openpyxl
from datetime import datetime
import re
import subprocess  # 追加: subprocessモジュールをインポート

# Excelファイルのパス
excel_path = r"C:\Users\mail\Desktop\python\extracted_dates.xlsx"

# フォルダのベースパス
base_path = r"\\landisk-f9f2eb\顕微鏡画像\顕微鏡画像"

# 別のスクリプトのパス
explore_script_path = r"C:\Users\mail\Desktop\python\explore_and_write_dates.py"

def read_start_date(excel_path):
    """
    ExcelファイルのSheet1のB3セルから開始日を読み取る。
    """
    try:
        wb = openpyxl.load_workbook(excel_path)
        sheet = wb["Sheet1"]
        start_date_cell = sheet["B3"].value
        if not start_date_cell:
            raise ValueError("セルB3に開始日が入力されていません。")
        
        # start_date_cell が文字列か datetime オブジェクトかを確認
        if isinstance(start_date_cell, str):
            # 文字列の場合は strptime を使用してパース
            start_date = datetime.strptime(start_date_cell, "%Y/%m/%d").date()
        elif isinstance(start_date_cell, datetime):
            # datetime オブジェクトの場合は date を取得
            start_date = start_date_cell.date()
        else:
            raise ValueError(f"セルB3の形式が不正です。期待する形式は 'YYYY/MM/DD' または日付形式です。現在の値: {start_date_cell}")
        
        return start_date, wb, sheet
    except Exception as e:
        print(f"エクセルファイルの読み込み中にエラーが発生しました: {e}")
        input("エラーが発生しました。Enterキーを押して終了してください。")
        exit(1)

def extract_day(day_folder):
    """
    フォルダ名から日付部分のみを抽出する。
    例: "10月15日" -> 15
    """
    match = re.search(r'(\d{1,2})日$', day_folder)
    if match:
        return int(match.group(1))
    else:
        return None

def collect_dates(base_path, start_date):
    """
    フォルダ構造を探索し、開始日以降の日付を収集する。
    """
    dates = []
    try:
        for year_folder in os.listdir(base_path):
            if not year_folder.endswith("年"):
                continue
            year_str = year_folder[:-1]
            try:
                year = int(year_str)
            except ValueError:
                print(f"無効な年フォルダ名: {year_folder}")
                continue
            # 年が開始年以降であることを確認
            if year < start_date.year:
                continue
            year_path = os.path.join(base_path, year_folder)
            if not os.path.isdir(year_path):
                continue
            for month_folder in os.listdir(year_path):
                if not month_folder.endswith("月"):
                    continue
                month_str = month_folder[:-1]
                try:
                    month = int(month_str)
                except ValueError:
                    print(f"無効な月フォルダ名: {month_folder}")
                    continue
                # 年が開始年で月が開始月未満の場合スキップ
                if year == start_date.year and month < start_date.month:
                    continue
                month_path = os.path.join(year_path, month_folder)
                if not os.path.isdir(month_path):
                    continue
                for day_folder in os.listdir(month_path):
                    if not day_folder.endswith("日"):
                        continue
                    # フォルダ名から日を抽出
                    day = extract_day(day_folder)
                    if day is None:
                        print(f"無効な日フォルダ名: {day_folder}")
                        continue
                    try:
                        date = datetime(year, month, day).date()
                    except ValueError:
                        print(f"無効な日付: {year}/{month}/{day}")
                        continue
                    # 開始日以降の日付を収集
                    if date >= start_date:
                        dates.append(date)
    except Exception as e:
        print(f"フォルダ探索中にエラーが発生しました: {e}")
        input("エラーが発生しました。Enterキーを押して終了してください。")
        exit(1)
    return dates

def write_dates_to_excel(sheet, latest, second_latest, excel_path, wb):
    """
    最新の日付をB2に、2番目に新しい日付をB3に書き込む。
    """
    try:
        if latest:
            sheet["B2"] = latest.strftime("%Y/%m/%d")
        else:
            sheet["B2"] = "該当なし"
        
        if second_latest:
            sheet["B3"] = second_latest.strftime("%Y/%m/%d")
        else:
            sheet["B3"] = "該当なし"
        
        wb.save(excel_path)
        print("Excelファイルに日付を正常に書き込みました。")
    except Exception as e:
        print(f"エクセルファイルへの書き込み中にエラーが発生しました: {e}")
    finally:
        # `explore_and_write_dates.py` を実行する前に処理完了のメッセージを表示
        print("処理が完了しました。次のスクリプトを実行します。")
        
        try:
            # 別のPythonスクリプトを実行
            subprocess.run(['python', explore_script_path], check=True)
            print(f"`{explore_script_path}` を正常に実行しました。")
        except subprocess.CalledProcessError as e:
            print(f"`{explore_script_path}` の実行中にエラーが発生しました: {e}")
        except FileNotFoundError:
            print(f"`{explore_script_path}` が見つかりません。パスを確認してください。")
        
        # 最後にウィンドウが閉じないように入力待ち
        input("Enterキーを押して終了してください。")

def execute_explore_script():
    """
    `explore_and_write_dates.py` を実行する関数。
    """
    print("`explore_and_write_dates.py` を実行します。")
    try:
        result = subprocess.run(['python', explore_script_path], check=True)
        print(f"`{explore_script_path}` を正常に実行しました。")
    except subprocess.CalledProcessError as e:
        print(f"`{explore_script_path}` の実行中にエラーが発生しました: {e}")
    except FileNotFoundError:
        print(f"`{explore_script_path}` が見つかりません。パスを確認してください。")

if __name__ == "__main__":
    try:
        # 開始日を読み取る
        start_date, wb, sheet = read_start_date(excel_path)
        print(f"開始日: {start_date}")

        # フォルダから日付を収集
        dates = collect_dates(base_path, start_date)
        if not dates:
            print("開始日以降のフォルダが見つかりませんでした。")
            # `explore_and_write_dates.py` を実行
            print("次のスクリプトを実行します。")
            try:
                # 別のPythonスクリプトを実行
                subprocess.run(['python', explore_script_path], check=True)
                print(f"`{explore_script_path}` を正常に実行しました。")
            except subprocess.CalledProcessError as e:
                print(f"`{explore_script_path}` の実行中にエラーが発生しました: {e}")
            except FileNotFoundError:
                print(f"`{explore_script_path}` が見つかりません。パスを確認してください。")
            
            input("処理が完了しました。Enterキーを押して終了してください。")
        else:
            # 日付を降順にソート
            dates_sorted = sorted(dates, reverse=True)
            latest = dates_sorted[0] if len(dates_sorted) >= 1 else None
            second_latest = dates_sorted[1] if len(dates_sorted) >= 2 else None

            print(f"最新の日付: {latest}")
            print(f"2番目に新しい日付: {second_latest}")

            # Excelに書き込む
            write_dates_to_excel(sheet, latest, second_latest, excel_path, wb)
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}")
        input("エラーが発生しました。Enterキーを押して終了してください。")
