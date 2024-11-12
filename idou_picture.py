import os
import shutil

# 移動元と移動先のベースディレクトリを設定
source_base_path = r"\\landisk-f9f2eb\bunseki 共有 2023\●●アスベスト　顕微鏡画像\過去分"
destination_base_path = r"\\landisk-f9f2eb\顕微鏡画像\顕微鏡画像"
unclassified_path = os.path.join(destination_base_path, "未分類")

def get_last_folder_name(path):
    """フォルダのパスから受付番号を取得する関数"""
    return os.path.basename(path)

def find_destination_folder(receipt_number):
    """指定された受付番号に一致する移動先フォルダを探索する関数"""
    for year_folder in os.listdir(destination_base_path):
        year_path = os.path.join(destination_base_path, year_folder)
        if os.path.isdir(year_path) and year_folder.endswith("年"):
            for month_folder in os.listdir(year_path):
                month_path = os.path.join(year_path, month_folder)
                if os.path.isdir(month_path) and month_folder.endswith("月"):
                    for day_folder in os.listdir(month_path):
                        day_path = os.path.join(month_path, day_folder)
                        if os.path.isdir(day_path):
                            # 受付番号に一致するフォルダを探す
                            target_path = os.path.join(day_path, receipt_number)
                            if os.path.isdir(target_path):
                                print(f"移動先フォルダが見つかりました: {target_path}")
                                return target_path
    return None

def move_files(source_folder, destination_folder):
    """元フォルダから移動先フォルダにファイルを移動する関数"""
    if not os.listdir(destination_folder):  # 移動先フォルダが空の場合のみ移動
        for file_name in os.listdir(source_folder):
            source_file = os.path.join(source_folder, file_name)
            destination_file = os.path.join(destination_folder, file_name)
            try:
                shutil.copy2(source_file, destination_file)
            except Exception as e:
                print(f"ファイル {source_file} の移動中にエラーが発生しました: {e}")
        print(f"{source_folder} のファイルを {destination_folder} に移動しました。")
        # 移動が完了したら元フォルダを削除
        shutil.rmtree(source_folder)
        print(f"{source_folder} を削除しました。")
    else:
        print(f"{destination_folder} は空でないため、ファイルを移動しません。")

# 移動元フォルダ内の各サブフォルダを探索
for sub_folder in os.listdir(source_base_path):
    sub_folder_path = os.path.join(source_base_path, sub_folder)
    if os.path.isdir(sub_folder_path):
        for inner_folder in os.listdir(sub_folder_path):
            inner_folder_path = os.path.join(sub_folder_path, inner_folder)
            if os.path.isdir(inner_folder_path):
                # 受付番号を取得
                receipt_number = get_last_folder_name(inner_folder_path)
                print(f"受付番号 {receipt_number} に対する移動先フォルダを探索中...")
                
                # 移動先フォルダを探索
                destination_folder = find_destination_folder(receipt_number)
                
                # 移動先フォルダが見つからない場合は「未分類」に移動
                if not destination_folder:
                    print(f"受付番号 {receipt_number} に一致する移動先フォルダが見つからないため、未分類に移動します。")
                    destination_folder = os.path.join(unclassified_path, receipt_number)
                    os.makedirs(destination_folder, exist_ok=True)
                
                # ファイルを移動し、元フォルダを削除
                move_files(inner_folder_path, destination_folder)
