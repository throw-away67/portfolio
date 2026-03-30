import pickle
import numpy as np
from flask import Flask, render_template_string, request

app = Flask(__name__)

def load_model():
    with open("model.pkl", "rb") as f:
        return pickle.load(f)

def load_scaler():
    with open("scaler.pkl", "rb") as f:
        return pickle.load(f)

model = load_model()
scaler = load_scaler()

form_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Predikce Teploty</title>
</head>
<body>
    <h1>Predikce teploty za hodinu</h1>
    <form method="post">
        <label>Teplota (°C):</label><br>
        <input type="number" name="temp" step="any" required><br>
        <label>Vlhkost (%):</label><br>
        <input type="number" name="humidity" step="any" required><br>
        <label>Rychlost větru (m/s):</label><br>
        <input type="number" name="wind" step="any" required><br>
        <label>Tlak (hPa):</label><br>
        <input type="number" name="pressure" step="any" required><br>
        <br>
        <button type="submit">Předpovědět</button>
    </form>
    {% if prediction is not none %}
        <h2>Odhadovaná teplota za hodinu: {{ prediction }} °C</h2>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None
    if request.method == "POST":
        temp = float(request.form["temp"])
        humidity = float(request.form["humidity"])
        wind = float(request.form["wind"])
        pressure = float(request.form["pressure"])
        input_array = np.array([[temp, humidity, wind, pressure]])
        input_scaled = scaler.transform(input_array)
        predicted_temp = model.predict(input_scaled)[0]
        prediction = f"{predicted_temp:.2f}"
    return render_template_string(form_html, prediction=prediction)

if __name__ == "__main__":
    app.run(debug=True)