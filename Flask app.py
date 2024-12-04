from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# Sample data for demonstration
holidays = ["2024-12-25"]
late_arrival = {"2024-12-15": "10:00"}
early_leave = {"2024-12-20": "15:00"}

@app.route("/")
def index():
    return render_template("calendar.html", holidays=holidays, late_arrival=late_arrival, early_leave=early_leave)

@app.route("/manage", methods=["GET", "POST"])
def manage():
    if request.method == "POST":
        date = request.form["date"]
        action = request.form["action"]
        if action == "add_holiday":
            holidays.append(date)
        elif action == "remove_holiday" and date in holidays:
            holidays.remove(date)
        elif action == "add_late":
            late_time = request.form["time"]
            late_arrival[date] = late_time
        elif action == "remove_late" and date in late_arrival:
            del late_arrival[date]
        elif action == "add_early":
            early_time = request.form["time"]
            early_leave[date] = early_time
        elif action == "remove_early" and date in early_leave:
            del early_leave[date]
        return redirect(url_for("manage"))
    return render_template("manage.html", holidays=holidays, late_arrival=late_arrival, early_leave=early_leave)

if __name__ == "__main__":
    # Use the PORT environment variable for deployment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
