@app.route("/manage", methods=["GET", "POST"])
def manage():
    global holidays, work_status

    if request.method == "POST":
        action = request.form.get("action")
        date = request.form.get("date")
        if not date:
            return redirect(url_for("manage"))

        try:
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            # 不正な日付の場合はリダイレクト
            return redirect(url_for("manage"))

        if action == "add_holiday":
            if date not in holidays:
                try:
                    holidays.append(date)
                except Exception as e:
                    print(f"Error adding holiday: {e}")
        elif action == "remove_holiday":
            if date in holidays:
                try:
                    holidays.remove(date)
                except Exception as e:
                    print(f"Error removing holiday: {e}")
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
        try:
            save_data({"holidays": holidays, "work_status": work_status})
        except Exception as e:
            print(f"Error saving data: {e}")

        return redirect(url_for("manage"))

    return render_template("manage.html", holidays=holidays, work_status=work_status)
