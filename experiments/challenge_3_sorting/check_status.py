"""Check Challenge 3 status"""

import os
import sys
import time

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from core.env_loader import load_env

load_env()

import requests

from api.auth.jwt import create_access_token
from api.auth.models import UserRole

token = create_access_token(data={"sub": "admin-1", "role": UserRole.ADMIN})
headers = {"Authorization": f"Bearer {token}"}
task_id = "ff69c252-d72c-49df-9fc8-ff4b7396d193"

print("Challenge 3: Extreme Sorting - Status")
print("=" * 60)

resp = requests.get(f"http://localhost:8000/api/tasks/{task_id}", headers=headers)
if resp.status_code == 200:
    task = resp.json()
    print(f"Task: {task['name']}")
    print(f"Generation: {task['current_generation']} / 1000")
    print(f"Best Score: {task['best_score']:.2%}")
    print(f"Status: {task['status']}")
    print(f"Created: {task['created_at']}")
    print("=" * 60)
    print("\nView live at: http://localhost:8000/monitor/")
    print(f"Task ID: {task_id}")
else:
    print(f"Error: {resp.status_code}")
    print(resp.text[:500])
