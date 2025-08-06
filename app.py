from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime
import json
import time
import threading
import os

app = Flask(__name__)

DATABASE = 'smarthome.db'

# --- Simulated Device States ---
simulated_devices = {
    "light_1": {"name": "Living Room Light", "status": "off"},
    "fan_1": {"name": "Bedroom Fan", "status": "off"},
    "door_lock_1": {"name": "Front Door Lock", "status": "locked"},
    "thermostat_1": {"name": "Thermostat", "status": "off", "temperature": 22}
}

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            action TEXT NOT NULL,
            value TEXT,
            schedule_time TEXT NOT NULL,
            is_executed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_schedule_task(device_id, action, value, schedule_time):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO schedules (device_id, action, value, schedule_time) VALUES (?, ?, ?, ?)",
              (device_id, action, value, schedule_time))
    conn.commit()
    conn.close()

def get_pending_schedules():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, device_id, action, value, schedule_time FROM schedules WHERE is_executed = 0 ORDER BY schedule_time ASC")
    rows = c.fetchall()
    conn.close()
    schedules = []
    for row in rows:
        schedules.append({
            "id": row[0],
            "device_id": row[1],
            "action": row[2],
            "value": row[3],
            "schedule_time": row[4]
        })
    return schedules

def mark_schedule_executed(task_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE schedules SET is_executed = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def delete_schedule_task(task_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM schedules WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# --- Device Control Logic ---
def control_device(device_id, action, value=None):
    if device_id not in simulated_devices:
        return False, "Device not found"

    device = simulated_devices[device_id]

    if action == "on":
        device["status"] = "on"
        return True, f"{device['name']} turned ON"
    elif action == "off":
        device["status"] = "off"
        return True, f"{device['name']} turned OFF"
    elif action == "locked":
        if device_id == "door_lock_1":
            device["status"] = "locked"
            return True, f"{device['name']} locked"
        else:
            return False, "Invalid action for this device"
    elif action == "unlocked":
        if device_id == "door_lock_1":
            device["status"] = "unlocked"
            return True, f"{device['name']} unlocked"
        else:
            return False, "Invalid action for this device"
    elif action == "set_temp" and value is not None:
        if device_id == "thermostat_1":
            try:
                temp = int(value)
                device["status"] = "on"
                device["temperature"] = temp
                return True, f"{device['name']} set to {temp}°C"
            except ValueError:
                return False, "Invalid temperature value"
        else:
            return False, "Invalid action for this device"
    else:
        return False, "Invalid action"

# --- Scheduler Thread ---
def scheduler_loop():
    while True:
        current_time = datetime.now()
        pending_tasks = get_pending_schedules()

        for task in pending_tasks:
            try:
                schedule_dt = datetime.fromisoformat(task["schedule_time"])
            except ValueError:
                continue  # Skip invalid datetime

            if current_time >= schedule_dt:
                success, message = control_device(task["device_id"], task["action"], task["value"])
                if success:
                    print(f"Executed scheduled task {task['id']}: {message}")
                    mark_schedule_executed(task["id"])
                else:
                    print(f"Failed to execute scheduled task {task['id']}: {message}")
        time.sleep(1)

scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
scheduler_thread.start()

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/devices', methods=['GET'])
def get_devices():
    return jsonify(simulated_devices)

@app.route('/control', methods=['POST'])
def control():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400

    data = request.json
    device_id = data.get('device_id')
    action = data.get('action')
    value = data.get('value')

    if not all([device_id, action]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    success, message = control_device(device_id, action, value)
    if success:
        return jsonify({"status": "success", "message": message, "device_state": simulated_devices.get(device_id)})
    else:
        return jsonify({"status": "error", "message": message}), 400

@app.route('/schedule', methods=['POST'])
def schedule_task():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400

    data = request.json
    device_id = data.get('device_id')
    action = data.get('action')
    value = data.get('value')
    schedule_time_str = data.get('schedule_time')

    if not all([device_id, action, schedule_time_str]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    try:
        if len(schedule_time_str) == 16:  # if no seconds
            schedule_time_str += ":00"
        schedule_dt = datetime.fromisoformat(schedule_time_str)

        if schedule_dt < datetime.now():
            return jsonify({"status": "error", "message": "Schedule time must be in the future"}), 400

        add_schedule_task(device_id, action, value, schedule_dt.isoformat())
        return jsonify({"status": "success", "message": "Task scheduled successfully!"})
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid schedule time format. Use YYYY-MM-DDTHH:MM"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/schedules', methods=['GET'])
def get_schedules():
    schedules = get_pending_schedules()
    for schedule in schedules:
        schedule['device_name'] = simulated_devices.get(schedule['device_id'], {}).get('name', 'Unknown Device')
    return jsonify(schedules)

@app.route('/schedule/<int:task_id>', methods=['DELETE'])
def delete_schedule(task_id):
    delete_schedule_task(task_id)
    return jsonify({"status": "success", "message": f"Task {task_id} deleted."})

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    if not os.path.exists('templates/index.html'):
        with open('templates/index.html', 'w') as f:
            f.write("<h1>Smart Home Dashboard</h1><p>This is a placeholder frontend. Replace with your UI.</p>")

    init_db()
    app.run(debug=True)
