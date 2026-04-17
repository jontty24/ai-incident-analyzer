from openai import OpenAI
from datetime import datetime
import json
import os
import csv


print("\n\nFresh run started\n")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

all_incidents = []



while True:
    incident = input("\nEnter incident (or type 'exit' to stop): ")


    if incident.lower() == "exit":
        break

    prompt = f"""
You are an AI safety assistant.

Analyze the incident and return ONLY a valid JSON object.

Use one of these categories only:
- Slip/Fall
- Equipment Issue
- Fire Hazard
- Personal Injury
- General Incident

Rules:
- The summary must be concise and professionally written.
- Do not copy the incident text word-for-word unless necessary.
- Normalize the wording for a workplace incident report.
- Severity must be one of: Low, Medium, High.
- Action must be specific and practical.

Format:
{{
  "summary": "",
  "category": "",
  "severity": "Low/Medium/High",
  "action": ""
}}

Incident:
{incident}

Return only JSON. No extra text.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )


    result = response.choices[0].message.content
    print("\n--- AI Incident Analysis ---")

    try:
        data = json.loads(result)
        
        record = {
        "original_incident": incident,
        "timestamp": datetime.now().isoformat(),
        "summary": data["summary"],
        "category": data["category"],
        "severity": data["severity"],
        "action": data["action"]
    }
        all_incidents.append(record)

        print("\n--- Structured Output ---")
        
        print("Summary:", data["summary"])
        print("Category:", data["category"])
        print("Severity:", data["severity"])
        print("Action:", data["action"])

    except Exception as e:
        print("Raw output:", result)
        print("Error:", e)

with open("incident_output.json", "w") as file:
    json.dump(all_incidents, file, indent=4)

with open("incident_output.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=[
        "original_incident",
        "timestamp",
        "summary",
        "category",
        "severity",
        "action"
    ])
    writer.writeheader()
    writer.writerows(all_incidents)

print("\nAll incidents saved to incident_output.json")