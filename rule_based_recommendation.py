# RULE-BASED RECOMMENDATION SYSTEM
# Uses predefined hospital operational rules

urgency = "High"
specialists = 2
nurse_ratio = 6
beds = 20
predicted_wait_time = 86   # minutes (from regression output)

print("RULE-BASED RECOMMENDATION SYSTEM")

print("Urgency Level:", urgency)
print("Specialists Available:", specialists)
print("Nurse-to-Patient Ratio:", nurse_ratio)
print("Facility Size (Beds):", beds)
print("Predicted Waiting Time:", predicted_wait_time, "minutes")

# Rule logic
if predicted_wait_time > 60 and specialists < 3:
    recommendation = "CRITICAL: Add specialists or redirect patients."
elif predicted_wait_time > 30 and nurse_ratio > 5:
    recommendation = "MODERATE: Increase nursing staff."
elif beds < 15:
    recommendation = "WARNING: Limited bed availability."
else:
    recommendation = "NORMAL: Hospital operating within capacity."

print("\nSystem Recommendation:")
print(recommendation)
