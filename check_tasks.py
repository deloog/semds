"""Check all tasks status"""
import os
os.chdir('d:/semds')

from core.env_loader import load_env
load_env()

from storage.database import get_session_factory
from storage.models import Task

Session = get_session_factory()
session = Session()

tasks = session.query(Task).order_by(Task.updated_at.desc()).all()

print("=" * 80)
print(f"Total tasks: {len(tasks)}")
print("=" * 80)
print()

running = [t for t in tasks if t.status == 'running']
print(f"Running tasks: {len(running)}")
print("-" * 80)
for t in running:
    print(f"  {t.name[:45]:45s} | Gen {t.current_generation:4d} | Score {t.best_score:.2%}")
print()

print("Recent 10 tasks:")
print("-" * 80)
for t in tasks[:10]:
    status_icon = "●" if t.status == 'running' else "○"
    print(f"  {status_icon} {t.name[:40]:40s} | Gen {t.current_generation:4d} | {t.status:10s} | {t.best_score:.2%}")

session.close()
