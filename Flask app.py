@app.route("/manage", methods=["GET", "POST"])
def manage():
    global holidays, work_status

    try:
        if request.method == "POST":
            action = request.form.get("action")
            date = request.form.get("date")
            if not date:
                return redirect(url_for("manage"))

            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

            if action == "add_holiday":
                if date not in holidays:
                    holidays.append(date)
            elif action == "remove_holiday":
                if date in holidays:
                    holidays.remove(date)
            elif action == "add_late":
                time = request.form.get("time")
                if time:
                    work_status["遅刻"][str(date)] = time
            elif action == "remove_late":
                if str(date) in work_status["遅刻"]:
                    del work_status["遅刻"][str(date)]
            elif action == "add_early":
                time = request.form.get("time")
                if time:
                    work_status["早退"][str(date)] = time
            elif action == "remove_early":
                if str(date) in work_status["早退"]:
                    del work_status["早退"][str(date)]

            # データを保存
            save_data({"holidays": holidays, "work_status": work_status})

            return redirect(url_for("manage"))

    except Exception as e:
        # エラー内容をログに出力
        print(f"Error: {e}")
        return "エラーが発生しました。詳細は管理者に問い合わせてください。", 500

    return render_template("manage.html", holidays=holidays, work_status=work_status)
