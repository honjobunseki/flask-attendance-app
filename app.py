from flask import Flask

# Flask アプリケーションの初期化
app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Flask! The app is running successfully."

if __name__ == "__main__":
    app.run(debug=True)
