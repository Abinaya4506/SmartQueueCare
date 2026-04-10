import pandas as pd
from sklearn.linear_model import LinearRegression
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

# Feature columns (same for both models)
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

# ---------------- LINEAR REGRESSION ----------------
lr_model = LinearRegression()
lr_model.fit(X_train, y_train)
lr_pred = lr_model.predict(X_test)

lr_mae = mean_absolute_error(y_test, lr_pred)
lr_r2 = r2_score(y_test, lr_pred)

# ---------------- RANDOM FOREST REGRESSION ----------------
rf_model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)
rf_model.fit(X_train, y_train)
rf_pred = rf_model.predict(X_test)

rf_mae = mean_absolute_error(y_test, rf_pred)
rf_r2 = r2_score(y_test, rf_pred)

# ---------------- COMPARISON OUTPUT ----------------
print("MODEL COMPARISON – WAIT TIME PREDICTION")

print("\nLinear Regression:")
print("Mean Absolute Error:", round(lr_mae, 2))
print("R2 Score:", round(lr_r2, 2))

print("\nRandom Forest Regression:")
print("Mean Absolute Error:", round(rf_mae, 2))
print("R2 Score:", round(rf_r2, 2))

print("\nConclusion:")
if rf_r2 > lr_r2:
    print("Random Forest Regression performs better due to non-linear modeling.")
else:
    print("Linear Regression performs sufficiently well for the given dataset.")
