"""Start Challenge 3 evolution directly"""

import os

os.chdir("d:/semds")

from core.env_loader import load_env

load_env()

import asyncio

from api.evolution_runner import start_evolution_task
from storage.database import get_session_factory
from storage.models import Task


async def main():
    Session = get_session_factory()
    session = Session()

    # Find Challenge 3 task
    task = (
        session.query(Task)
        .filter(Task.name == "Challenge 3: Extreme Sorting")
        .order_by(Task.created_at.desc())
        .first()
    )

    if not task:
        print("Challenge 3 task not found!")
        return

    task_id = task.id
    print(f"Starting evolution for: {task_id}")
    print(f"Current gen: {task.current_generation}")

    # Mark as running
    task.status = "running"
    session.commit()
    session.close()

    # Start evolution
    try:
        runner = await start_evolution_task(task_id, max_generations=1000)
        print(f"Evolution started! Runner: {runner}")

        # Keep running
        while runner.is_running():
            await asyncio.sleep(10)
            print("Evolution in progress...")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
