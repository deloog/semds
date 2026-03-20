"""
Matrix Challenge Monitor - Continuous monitoring
"""

import os
import sys
import time

os.chdir(r"D:\semds")
sys.path.insert(0, r"D:\semds")


def check_status():
    from core.env_loader import load_env

    load_env()

    from storage.database import get_session_factory
    from storage.models import Generation, Task

    Session = get_session_factory()
    session = Session()

    task_id = "0493d951-8044-445a-ba34-763b3a37e505"
    task = session.query(Task).filter(Task.id == task_id).first()

    result = {}
    if task:
        result["gen"] = task.current_generation
        result["score"] = task.best_score
        result["status"] = task.status

        # Count improvements
        gens = (
            session.query(Generation)
            .filter(Generation.task_id == task_id)
            .order_by(Generation.gen_number)
            .all()
        )
        result["total_gens"] = len(gens)

        # Find best generation
        best_gen = max(gens, key=lambda g: g.final_score) if gens else None
        if best_gen:
            result["best_gen"] = best_gen.gen_number
            result["best_score"] = best_gen.final_score

    session.close()
    return result


def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def main():
    print("=" * 70)
    print("MATRIX CHALLENGE MONITOR")
    print("=" * 70)
    print("Task: 2x2 Matrix Multiplication Optimization")
    print("Target: Beat standard algorithm (8 multiplications)")
    print("Mode: DeepSeek API")
    print("=" * 70)
    print()

    start_time = time.time()
    last_gen = 0
    last_score = 0
    improvements = []

    try:
        while True:
            status = check_status()
            elapsed = time.time() - start_time

            if not status:
                print(f"[{format_time(elapsed)}] Task not found")
                time.sleep(30)
                continue

            gen = status.get("gen", 0)
            score = status.get("score", 0)

            # Detect improvements
            if score > last_score:
                improvements.append((gen, score))
                improvement_marker = " <<< IMPROVEMENT!"
            else:
                improvement_marker = ""

            # Print status every generation change or every 2 minutes
            if gen != last_gen or int(elapsed) % 120 == 0:
                print(
                    f"[{format_time(elapsed)}] Gen {gen:3d}/200 | Score: {score:5.1%} | {status.get('status', 'unknown')}{improvement_marker}"
                )
                last_gen = gen
                last_score = score

            # Check for stagnation (no improvement for 50 generations)
            if len(improvements) >= 1:
                gens_since_improvement = gen - improvements[-1][0]
                if gens_since_improvement >= 50 and gen > 50:
                    print()
                    print("=" * 70)
                    print("STAGNATION DETECTED")
                    print("=" * 70)
                    print(f"No improvement for {gens_since_improvement} generations")
                    print("Consider stopping and trying a different task")
                    print("=" * 70)

            # Stop if completed
            if status.get("status") in ["success", "failed", "aborted"]:
                print()
                print("=" * 70)
                print(f"EVOLUTION {status.get('status').upper()}")
                print("=" * 70)
                print(f"Final Generation: {gen}")
                print(f"Best Score: {score:.2%}")
                print(f"Total Improvements: {len(improvements)}")
                if improvements:
                    print("Improvement history:")
                    for g, s in improvements:
                        print(f"  Gen {g:3d}: {s:.2%}")
                break

            time.sleep(30)

    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print("MONITORING STOPPED")
        print("=" * 70)
        print(f"Ran for: {format_time(time.time() - start_time)}")
        print(f"Final Generation: {last_gen}")
        print(f"Best Score: {last_score:.2%}")
        if improvements:
            print(f"Improvements: {len(improvements)}")
            print(f"Best: Gen {improvements[-1][0]} at {improvements[-1][1]:.2%}")


if __name__ == "__main__":
    main()
