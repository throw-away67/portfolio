import requests
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import pickle
from sklearn.metrics import mean_squared_error

latitude = 50.0755
longitude = 14.4378

end_date = datetime.utcnow().date()
start_date = end_date - timedelta(days=90)

url = (
    f"https://archive-api.open-meteo.com/v1/archive?"
    f"latitude={latitude}&longitude={longitude}"
    f"&start_date={start_date}&end_date={end_date}"
    f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,pressure_msl"
)

response = requests.get(url)
data = response.json()

df = pd.DataFrame({
    "time": data["hourly"]["time"],
    "temperature": data["hourly"]["temperature_2m"],
    "humidity": data["hourly"]["relative_humidity_2m"],
    "wind_speed": data["hourly"]["wind_speed_10m"],
    "pressure": data["hourly"]["pressure_msl"]
})

df["time"] = pd.to_datetime(df["time"])

df = df.tail(3000)
df.reset_index(drop=True, inplace=True)
df["target_temp"] = df["temperature"].shift(-1)

df = df.dropna()

df.to_csv("weather_1500_rows.csv", index=False)

features = ["temperature", "humidity", "wind_speed", "pressure"]
scaler = MinMaxScaler()
X = scaler.fit_transform(df[features].values)
y = df["target_temp"].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
rmse = mean_squared_error(y_test, y_pred)
print("RMSE:", rmse)

with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)