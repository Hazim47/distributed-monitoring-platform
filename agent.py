import time
import requests
import psutil

BACKEND_URL = "http://backend:9000/metrics"

print("### AGENT STARTED ###")

while True:
    data = {
        "agent_id": "agent-1",
        "hostname": "pc-1",
        "cpu": psutil.cpu_percent(interval=1),
        "ram": psutil.virtual_memory().percent,
    }

    try:
        r = requests.post(BACKEND_URL, json=data, timeout=5)
        print("STATUS:", r.status_code)
    except Exception as e:
        print("ERROR:", e)

    time.sleep(5)
