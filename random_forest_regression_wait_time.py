import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# Load dataset
data = pd.read_csv("hospital_wait_time.csv")

# Clean column names
data.columns = data.columns.str.strip().str.lower()

# Encode urgency level
urgency_map = {"low": 0, "medium": 1, "high": 2}
data["urgency level"] = data["urgency level"].str.lower().map(urgency_map)

# Feature columns (SAME as Linear Regression)
feature_cols = [
    "urgency level",
    "specialist availability",
    "nurse-to-patient ratio",
    "facility size (beds)"
]

X = data[feature_cols].fillna(data[feature_cols].mean())
y = data["total wait time (min)"].fillna(
    data["total wait time (min)"].mean()
)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train Random Forest Regressor
rf_model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)
rf_model.fit(X_train, y_train)

# Predict on test set
rf_predictions = rf_model.predict(X_test)

# Evaluation
print("RANDOM FOREST REGRESSION – WAIT TIME PREDICTION")
print("Mean Absolute Error:", round(mean_absolute_error(y_test, rf_predictions), 2))
print("R2 Score:", round(r2_score(y_test, rf_predictions), 2))

# -------- SAMPLE INPUT (WITH COLUMN NAMES → NO WARNING) --------
sample_input = pd.DataFrame([{
    "urgency level": 2,                 # High
    "specialist availability": 3,       # Specialists
    "nurse-to-patient ratio": 5,         # Ratio
    "facility size (beds)": 30           # Beds
}])

predicted_minutes = int(rf_model.predict(sample_input)[0])

# Convert minutes to hours & minutes
hours = predicted_minutes // 60
minutes = predicted_minutes % 60

print("\nSample Input:")
print("Urgency Level: High")
print("Specialists Available: 3")
print("Nurse-to-Patient Ratio: 5")
print("Facility Size: 30 beds")

print("\nPredicted Waiting Time:")
print(f"{predicted_minutes} minutes")
print(f"≈ {hours} hour(s) {minutes} minute(s)")
