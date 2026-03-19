"""
Challenge 3: Extreme Sorting Performance
Run 1000 generations to evolve a sorting algorithm approaching C qsort performance.

Usage:
    python experiments/challenge_3_sorting/run_challenge.py
"""
import os
import sys
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.env_loader import load_env
load_env()

import requests
from api.auth.jwt import create_access_token
from api.auth.models import UserRole


# Configuration
API_BASE = "http://localhost:8000/api"
TEST_CODE = '''
import random
import time
from typing import List


def generate_random_array(size: int) -> List[int]:
    return [random.randint(-1000000, 1000000) for _ in range(size)]


def solution(arr):
    """Sort array - to be evolved"""
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def test_correctness():
    """Test basic correctness"""
    test_cases = [
        ([], []),
        ([1], [1]),
        ([2, 1], [1, 2]),
        ([3, 1, 2], [1, 2, 3]),
        ([3, 1, 3, 2, 1], [1, 1, 2, 3, 3]),
        ([5, 5, 5], [5, 5, 5]),
        ([-3, -1, -2], [-3, -2, -1]),
    ]
    for inp, expected in test_cases:
        result = solution(inp.copy())
        assert result == expected, f"Failed: {inp} -> {result}, expected {expected}"


def test_performance_small():
    """Test performance on 1000 elements (target < 0.01s)"""
    arr = generate_random_array(1000)
    start = time.perf_counter()
    result = solution(arr.copy())
    elapsed = time.perf_counter() - start
    assert result == sorted(arr), "Wrong result"
    assert elapsed < 0.5, f"Too slow: {elapsed:.3f}s"


def test_performance_medium():
    """Test performance on 10000 elements (target < 0.03s)"""
    arr = generate_random_array(10000)
    start = time.perf_counter()
    result = solution(arr.copy())
    elapsed = time.perf_counter() - start
    assert result == sorted(arr), "Wrong result"
    # Score based on time: faster is better
    # Base score 0.5, bonus up to 0.5 for speed
    score = 0.5 + max(0, 0.5 - elapsed * 10)
    return score


def test_performance_large():
    """Test performance on 100000 elements (target < 0.1s)"""
    arr = generate_random_array(100000)
    start = time.perf_counter()
    result = solution(arr.copy())
    elapsed = time.perf_counter() - start
    assert result == sorted(arr), "Wrong result"
    # Score based on time
    score = max(0, 1.0 - elapsed)
    return score


if __name__ == "__main__":
    test_correctness()
    test_performance_small()
    test_performance_medium()
    test_performance_large()
'''


def get_auth_token():
    """Get admin auth token"""
    return create_access_token(
        data={'sub': 'admin-1', 'role': UserRole.ADMIN},
        expires_delta=None
    )


def create_task():
    """Create the sorting challenge task"""
    token = get_auth_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    task_data = {
        'name': 'Challenge 3: Extreme Sorting',
        'description': 'Evolve a sorting algorithm approaching C qsort performance. Target: <0.1s for 100k integers.',
        'target_function_signature': 'def solution(arr: list) -> list:',
        'test_code': TEST_CODE,
        'max_generations': 1000,
        'success_criteria': {'target_score': 0.95}
    }
    
    print("Creating Challenge 3 task...")
    resp = requests.post(f'{API_BASE}/tasks', headers=headers, json=task_data)
    
    if resp.status_code == 201:
        task = resp.json()
        print(f"[OK] Task created: {task['id']}")
        return task['id']
    else:
        print(f"[FAIL] Failed to create task: {resp.status_code}")
        print(resp.text)
        return None


def start_evolution(task_id):
    """Start evolution for the task"""
    token = get_auth_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"\nStarting evolution (1000 generations)...")
    resp = requests.post(f'{API_BASE}/tasks/{task_id}/start', headers=headers)
    
    if resp.status_code == 200:
        print("[OK] Evolution started!")
        return True
    else:
        print(f"[FAIL] Failed to start: {resp.status_code}")
        print(resp.text)
        return False


def monitor_progress(task_id, interval=10):
    """Monitor evolution progress"""
    token = get_auth_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    print("\n" + "=" * 70)
    print("MONITORING EVOLUTION")
    print("=" * 70)
    print(f"{'Generation':>12} {'Best Score':>12} {'Status':>12} {'Time':>12}")
    print("-" * 70)
    
    start_time = time.time()
    last_gen = 0
    
    while True:
        time.sleep(interval)
        
        resp = requests.get(f'{API_BASE}/tasks/{task_id}', headers=headers)
        if resp.status_code != 200:
            print(f"Error fetching status: {resp.status_code}")
            continue
        
        task = resp.json()
        gen = task['current_generation']
        score = task['best_score']
        status = task['status']
        elapsed = time.time() - start_time
        
        # Only print if generation changed
        if gen != last_gen:
            print(f"{gen:>12} {score:>11.2%} {status:>12} {elapsed:>10.0f}s")
            last_gen = gen
            
            # Check if completed
            if status in ['success', 'failed', 'aborted']:
                print("-" * 70)
                print(f"\nEvolution completed!")
                print(f"Final generation: {gen}")
                print(f"Best score: {score:.2%}")
                print(f"Total time: {elapsed:.0f}s")
                return
        
        # Print heartbeat every 60 seconds even if no change
        if int(elapsed) % 60 == 0 and int(elapsed) > 0:
            print(f"{gen:>12} {score:>11.2%} {status:>12} {elapsed:>10.0}s ...")


def main():
    print("=" * 70)
    print("CHALLENGE 3: EXTREME SORTING PERFORMANCE")
    print("=" * 70)
    print("Goal: Evolve sorting algorithm approaching C qsort")
    print("Target: <0.1s for 100,000 integers")
    print("Baseline: Bubble sort O(n^2)")
    print("=" * 70)
    
    # Create task
    task_id = create_task()
    if not task_id:
        print("\nFailed to create task. Exiting.")
        return 1
    
    # Start evolution
    if not start_evolution(task_id):
        print("\nFailed to start evolution. Exiting.")
        return 1
    
    # Monitor
    try:
        monitor_progress(task_id)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped. Evolution continues in background.")
        print(f"View progress at: http://localhost:8000/monitor/")
        print(f"Task ID: {task_id}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
