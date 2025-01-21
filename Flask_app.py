@app.route("/manage", methods=["GET", "POST"])
def manage():
    global holidays, work_status

    if request.method == "POST":
        form_type = request.form.get("form_type")  # フォームの種類を取得
        date = request.form.get("date")  # 入力された日付を取得
        status_type = request.form.get("status_type", None)  # ステータスの種類を取得（任意）

        if not date:  # 日付が入力されていない場合
            flash("日付を入力してください。", "error")
            return redirect(url_for("manage"))

        try:
            with conn.cursor() as cur:
                if form_type == "add_holiday":
                    # 休みを追加
                    cur.execute("INSERT INTO holidays (holiday_date) VALUES (%s) ON CONFLICT DO NOTHING;", (date,))
                    flash("休みを追加しました。", "success")

                elif form_type == "delete_holiday":
                    # 休みを削除
                    cur.execute("DELETE FROM holidays WHERE holiday_date = %s;", (date,))
                    flash("休みを削除しました。", "success")

                elif form_type == "add_late":
                    # 遅刻を追加
                    time = request.form.get("time")
                    cur.execute(
                        "INSERT INTO work_status (status_date, status_type, time) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;",
                        (date, "遅刻", time),
                    )
                    flash("遅刻を追加しました。", "success")

                elif form_type == "delete_status":
                    # 勤務状態を削除
                    if status_type:
                        cur.execute("DELETE FROM work_status WHERE status_date = %s AND status_type = %s;", (date, status_type))
                        flash(f"{status_type}を削除しました。", "success")
                    else:
                        flash("ステータスの種類が指定されていません。", "error")

                elif form_type == "add_early":
                    # 早退を追加
                    time = request.form.get("time")
                    cur.execute(
                        "INSERT INTO work_status (status_date, status_type, time) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;",
                        (date, "早退", time),
                    )
                    flash("早退を追加しました。", "success")

                elif form_type == "add_outside":
                    # 外出中を追加
                    additional_info = "直帰予定" if request.form.get("go_home") else None
                    cur.execute(
                        "INSERT INTO work_status (status_date, status_type, additional_info) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;",
                        (date, "外出中", additional_info),
                    )
                    flash("外出中を追加しました。", "success")

                elif form_type == "add_break":
                    # 休憩中を追加
                    cur.execute(
                        "INSERT INTO work_status (status_date, status_type) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                        (date, "休憩中"),
                    )
                    flash("休憩中を追加しました。", "success")

                conn.commit()  # データベースへの変更をコミット

        except Exception as e:
            flash(f"エラーが発生しました: {e}", "error")
            conn.rollback()  # エラー発生時にロールバック

    # 最新のデータをロード
    holidays = load_holidays()
    work_status = load_work_status()
    return render_template("manage.html", holidays=holidays, work_status=work_status)
