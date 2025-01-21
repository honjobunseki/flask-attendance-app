@app.route("/manage", methods=["GET", "POST"])
def manage():
    global holidays, work_status

    if request.method == "POST":
        date = request.form.get("date")
        action = request.form.get("action")
        time = request.form.get("time")
        go_home = request.form.get("go_home")  # "on" or None
        additional_info = "直帰予定" if go_home == "on" else None

        if action == "add_holiday":
            with conn.cursor() as cur:
                cur.execute("INSERT INTO holidays (holiday_date) VALUES (%s) ON CONFLICT DO NOTHING;", (date,))
                conn.commit()
                holidays = load_holidays()
                flash(f"{date} を休日として追加しました。")

        elif action == "delete_holiday":
            with conn.cursor() as cur:
                cur.execute("DELETE FROM holidays WHERE holiday_date = %s;", (date,))
                conn.commit()
                holidays = load_holidays()
                flash(f"{date} の休日を削除しました。")

        elif action == "add_late":
            with conn.cursor() as cur:
                cur.execute("INSERT INTO work_status (status_date, status_type, time) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;",
                            (date, "遅刻", time))
                conn.commit()
                work_status = load_work_status()
                flash(f"{date} に遅刻予定 {time} を追加しました。")

        elif action == "delete_late":
            with conn.cursor() as cur:
                cur.execute("DELETE FROM work_status WHERE status_date = %s AND status_type = %s;", (date, "遅刻"))
                conn.commit()
                work_status = load_work_status()
                flash(f"{date} の遅刻予定を削除しました。")

        elif action == "add_early":
            with conn.cursor() as cur:
                cur.execute("INSERT INTO work_status (status_date, status_type, time) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;",
                            (date, "早退", time))
                conn.commit()
                work_status = load_work_status()
                flash(f"{date} に早退予定 {time} を追加しました。")

        elif action == "delete_early":
            with conn.cursor() as cur:
                cur.execute("DELETE FROM work_status WHERE status_date = %s AND status_type = %s;", (date, "早退"))
                conn.commit()
                work_status = load_work_status()
                flash(f"{date} の早退予定を削除しました。")

        elif action == "add_outside":
            with conn.cursor() as cur:
                cur.execute("INSERT INTO work_status (status_date, status_type, additional_info) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;",
                            (date, "外出中", additional_info))
                conn.commit()
                work_status = load_work_status()
                flash(f"{date} に外出中を追加しました（{additional_info or '直帰なし'}）。")

        elif action == "delete_outside":
            with conn.cursor() as cur:
                cur.execute("DELETE FROM work_status WHERE status_date = %s AND status_type = %s;", (date, "外出中"))
                conn.commit()
                work_status = load_work_status()
                flash(f"{date} の外出中を削除しました。")

        elif action == "add_break":
            with conn.cursor() as cur:
                cur.execute("INSERT INTO work_status (status_date, status_type) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                            (date, "休憩中"))
                conn.commit()
                work_status = load_work_status()
                flash(f"{date} に休憩中を追加しました。")

        elif action == "delete_break":
            with conn.cursor() as cur:
                cur.execute("DELETE FROM work_status WHERE status_date = %s AND status_type = %s;", (date, "休憩中"))
                conn.commit()
                work_status = load_work_status()
                flash(f"{date} の休憩中を削除しました。")

    return render_template("manage.html", holidays=holidays, work_status=work_status)
