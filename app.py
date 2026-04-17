from flask import Flask, request, jsonify, render_template, Response
from openai import OpenAI
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import uuid
import csv
import sqlite3

load_dotenv()

app = Flask(__name__)
DB_FILE = "incidents.db"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY,
            reporter_name TEXT NOT NULL,
            victim_name TEXT,
            original_incident TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            summary TEXT NOT NULL,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

def load_history():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT id, reporter_name, victim_name, original_incident, timestamp,
               summary, category, severity, action, status
        FROM incidents
        ORDER BY timestamp DESC
    """).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def save_incident(record):
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO incidents (
            id, reporter_name, victim_name, original_incident, timestamp,
            summary, category, severity, action, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record["id"],
        record["reporter_name"],
        record["victim_name"],
        record["original_incident"],
        record["timestamp"],
        record["summary"],
        record["category"],
        record["severity"],
        record["action"],
        record["status"]
    ))
    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/history", methods=["GET"])
def get_history():
    history = load_history()
    return jsonify(history)

@app.route("/delete/<string:incident_id>", methods=["DELETE"])
def delete_incident(incident_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM incidents WHERE id = ?", (incident_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

@app.route("/clear", methods=["DELETE"])
def clear_history():
    conn = get_db_connection()
    conn.execute("DELETE FROM incidents")
    conn.commit()
    conn.close()

    return jsonify({"success": True})

@app.route("/download_csv", methods=["GET"])
def download_csv():
    history = load_history()

    def generate():
        header = [
            "id",
            "reporter_name",
            "victim_name",
            "original_incident",
            "timestamp",
            "summary",
            "category",
            "severity",
            "action",
            "status"
        ]
        yield ",".join(header) + "\n"

        for item in history:
            row = [
                str(item.get("id", "")).replace(",", " "),
                str(item.get("reporter_name", "")).replace(",", " "),
                str(item.get("victim_name", "")).replace(",", " "),
                str(item.get("original_incident", "")).replace(",", " "),
                str(item.get("timestamp", "")).replace(",", " "),
                str(item.get("summary", "")).replace(",", " "),
                str(item.get("category", "")).replace(",", " "),
                str(item.get("severity", "")).replace(",", " "),
                str(item.get("action", "")).replace(",", " "),
                str(item.get("status", "")).replace(",", " ")
            ]
            yield ",".join(row) + "\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=incident_history.csv"}
    )

@app.route("/update_status/<string:incident_id>", methods=["PUT"])
def update_status(incident_id):
    new_status = request.json.get("status", "Open")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE incidents SET status = ? WHERE id = ?",
        (new_status, incident_id)
    )

    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"success": False, "error": "Incident not found"}), 404

    conn.commit()
    conn.close()

    return jsonify({"success": True})

@app.route("/analyze", methods=["POST"])
def analyze():
    reporter_name = request.form.get("reporter_name", "").strip()
    victim_name = request.form.get("victim_name", "").strip()
    incident = request.form.get("incident", "").strip()

    if not reporter_name:
        return jsonify({"error": "Reporter name is required."}), 400
    if not incident:
        return jsonify({"error": "Incident description cannot be empty."}), 400
    if len(incident) < 10:
        return jsonify({"error": "Incident description must be at least 10 characters."}), 400

    print("Reporter:", reporter_name)
    print("Victim:", victim_name)
    print("Incident:", incident)

    prompt = f"""
You are an AI safety assistant.

Analyze ONLY the incident provided below.
Return ONLY a valid JSON object.

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
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    result = response.choices[0].message.content

    try:
        data = json.loads(result)

        record = {
            "id": str(uuid.uuid4()),
            "reporter_name": reporter_name,
            "victim_name": victim_name,
            "original_incident": incident,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "summary": data["summary"],
            "category": data["category"],
            "severity": data["severity"],
            "action": data["action"],
            "status": "Open"
        }
        save_incident(record)

        return jsonify(record)

    except (json.JSONDecodeError, KeyError) as e:
        print("JSON parsing error:", e)
        print("Raw AI result:", result)
        return jsonify({"error": "Invalid AI response"}), 500


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))