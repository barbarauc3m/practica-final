# python3 servicio-web.py

from flask import Flask
from datetime import datetime

app = Flask(__name__)

@app.route("/datetime", methods=["GET"])
def get_datetime():
    now = datetime.now()
    formatted = now.strftime("%d/%m/%Y %H:%M:%S")
    return formatted


if __name__ == "__main__":
    # Lo ejecutamos en localhost:8000 (puedes cambiar el puerto si lo necesitas)
    app.run(host="127.0.0.1", port=8000)