"""Fix stuck tasks and start Challenge 3"""

import os

os.chdir("d:/semds")

from core.env_loader import load_env

load_env()

from storage.database import get_session_factory
from storage.models import Task

Session = get_session_factory()
session = Session()

# Reset all running tasks to pending (they're stuck)
running_tasks = session.query(Task).filter(Task.status == "running").all()
print(f"Resetting {len(running_tasks)} stuck 'running' tasks to 'pending'")
for t in running_tasks:
    t.status = "pending"
    print(f"  - {t.name}")

session.commit()

# Find Challenge 3 task
task = (
    session.query(Task)
    .filter(Task.name == "Challenge 3: Extreme Sorting")
    .order_by(Task.created_at.desc())
    .first()
)

if task:
    print(f"\nFound Challenge 3 task: {task.id}")
    print(f"Current status: {task.status}")
    print(f"Current generation: {task.current_generation}")

    # Reset to pending
    task.status = "pending"
    session.commit()
    print("Reset to pending")
else:
    print("Challenge 3 task not found!")

session.close()
print(
    "\nDone. Now go to http://localhost:8000/monitor/ and click 'Start' on Challenge 3 task"
)
