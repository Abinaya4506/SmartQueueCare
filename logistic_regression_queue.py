import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Load dataset
data = pd.read_csv("hospital_wait_time.csv")

# Clean column names
data.columns = data.columns.str.strip().str.lower()

# Encode urgency level
urgency_map = {"low": 0, "medium": 1, "high": 2}
data["urgency level"] = data["urgency level"].str.lower().map(urgency_map)

# Create queue congestion labels
def classify_wait(time):
    if time < 30:
        return 0    # LOW
    elif time < 60:
        return 1    # MEDIUM
    else:
        return 2    # HIGH

data["queue_level"] = data["total wait time (min)"].apply(classify_wait)

# Feature columns (REAL CSV FEATURES)
feature_cols = [
    "urgency level",
    "specialist availability",
    "nurse-to-patient ratio",
    "facility size (beds)"
]

X = data[feature_cols].fillna(data[feature_cols].mean())
y = data["queue_level"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train Logistic Regression model
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Predict
y_pred = model.predict(X_test)

# Evaluation
print("LOGISTIC REGRESSION – QUEUE CONGESTION CLASSIFICATION")
print("Accuracy:", round(accuracy_score(y_test, y_pred), 2))

print("\nClassification Report:")
print(classification_report(
    y_test,
    y_pred,
    target_names=["LOW", "MEDIUM", "HIGH"]
))

# -------- SAMPLE INPUT (NO WARNINGS) --------
sample_input = pd.DataFrame([{
    "urgency level": 1,                 # Medium
    "specialist availability": 2,       # Specialists
    "nurse-to-patient ratio": 6,         # Ratio
    "facility size (beds)": 25           # Beds
}])

predicted_class = model.predict(sample_input)[0]
labels = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}

print("\nSample Input:")
print("Urgency Level: Medium")
print("Specialists Available: 2")
print("Nurse-to-Patient Ratio: 6")
print("Facility Size: 25 beds")

print("\nPredicted Queue Congestion Level:")
print(labels[predicted_class])
