incident = input("Enter the incident description: ").lower()

print("\n--- Incident Report Analysis ---")

if "slip" in incident or "fell" in incident or "fall" in incident:
    category = "Slip/Fall"
elif "machine" in incident or "equipment" in incident:
    category = "Equipment Issue"
elif "fire" in incident or "smoke" in incident:
    category = "Fire Hazard"
elif "injury" in incident or "hurt" in incident:
    category = "Personal Injury"
else:
    category = "General Incident"

if "hospital" in incident or "ambulance" in incident or "serious" in incident:
    severity = "High"
elif "injury" in incident or "fell" in incident or "slip" in incident:
    severity = "Medium"
else:
    severity = "Low"

if severity == "High":
    action = "Notify supervisor immediately and start emergency response steps."
elif severity == "Medium":
    action = "Document the incident, investigate the cause, and monitor the situation."
else:
    action = "Record the issue and review if preventive action is needed."

print("Category:", category)
print("Severity:", severity)
print("Recommended Action:", action)