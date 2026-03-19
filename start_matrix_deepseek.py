"""
Matrix Multiplication Challenge - DeepSeek Mode

Uses DeepSeek API for high-quality code generation.
Expected cost: ~10-15 CNY for 200 generations
"""

import os
import sys
import requests

os.chdir(r"D:\semds")
sys.path.insert(0, r"D:\semds")

from core.env_loader import load_env

load_env()

from api.auth.jwt import create_access_token
from api.auth.models import UserRole

# Clear test code for DeepSeek
TEST_CODE = '''
import random
import time

def solution(A, B):
    """
    Multiply two 2x2 matrices.
    A, B are list of lists: [[a11, a12], [a21, a22]]
    Return: 2x2 result matrix
    
    Goal: Optimize for speed, possibly fewer multiplications.
    """
    a11, a12 = A[0][0], A[0][1]
    a21, a22 = A[1][0], A[1][1]
    b11, b12 = B[0][0], B[0][1]
    b21, b22 = B[1][0], B[1][1]
    
    # Standard algorithm: 8 multiplications
    c11 = a11 * b11 + a12 * b21
    c12 = a11 * b12 + a12 * b22
    c21 = a21 * b11 + a22 * b21
    c22 = a21 * b12 + a22 * b22
    
    return [[c11, c12], [c21, c22]]


def test_correctness():
    """Test with various matrices"""
    # Identity test
    I = [[1, 0], [0, 1]]
    A = [[1, 2], [3, 4]]
    assert solution(A, I) == A
    
    # Simple multiplication
    A = [[1, 2], [3, 4]]
    B = [[5, 6], [7, 8]]
    expected = [[19, 22], [43, 50]]
    assert solution(A, B) == expected
    
    # 100 random tests
    for _ in range(100):
        A = [[random.randint(-10, 10) for _ in range(2)] for _ in range(2)]
        B = [[random.randint(-10, 10) for _ in range(2)] for _ in range(2)]
        result = solution(A, B)
        expected = [
            [A[0][0]*B[0][0] + A[0][1]*B[1][0], A[0][0]*B[0][1] + A[0][1]*B[1][1]],
            [A[1][0]*B[0][0] + A[1][1]*B[1][0], A[1][0]*B[0][1] + A[1][1]*B[1][1]]
        ]
        assert result == expected


def test_performance():
    """Performance test - 100k multiplications"""
    n = 100000
    A = [[random.random() for _ in range(2)] for _ in range(2)]
    B = [[random.random() for _ in range(2)] for _ in range(2)]
    
    start = time.perf_counter()
    for _ in range(n):
        result = solution(A, B)
    elapsed = time.perf_counter() - start
    
    assert elapsed < 0.5, f"Too slow: {elapsed}s"


if __name__ == "__main__":
    test_correctness()
    test_performance()
'''


def start_challenge():
    print("=" * 60)
    print("MATRIX MULTIPLICATION CHALLENGE")
    print("Mode: DeepSeek API (High Quality)")
    print("=" * 60)
    print("\nTarget: Optimize 2x2 matrix multiplication")
    print("  Standard: 8 multiplications")
    print("  Strassen: 7 multiplications (1969)")
    print("  Goal: Find faster implementation")
    print("\nCost estimate: ~10-15 CNY for 200 generations")
    print("=" * 60 + "\n")

    token = create_access_token(data={"sub": "admin-1", "role": UserRole.ADMIN})
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    task_data = {
        "name": "Matrix Challenge (DeepSeek)",
        "description": "2x2 matrix multiplication optimization using DeepSeek API. Target: correct code with speed improvements.",
        "target_function_signature": "def solution(A: list, B: list) -> list:",
        "test_code": TEST_CODE,
        "max_generations": 200,
        "success_criteria": {"target_score": 0.95},
    }

    print("Creating task...")
    resp = requests.post(
        "http://localhost:8000/api/tasks", headers=headers, json=task_data
    )

    if resp.status_code != 201:
        print(f"[ERROR] {resp.status_code}: {resp.text[:500]}")
        return False

    task = resp.json()
    print(f"[OK] Task created: {task['id']}")

    print("\nStarting evolution...")
    resp2 = requests.post(
        f"http://localhost:8000/api/tasks/{task['id']}/start", headers=headers
    )

    if resp2.status_code == 200:
        print("[OK] Evolution started with DeepSeek!")
        print(f"\nMonitor: http://localhost:8000/monitor/")
        print(f"Task ID: {task['id']}")
        print("\nTimeline:")
        print("  Gen 1-10:  DeepSeek establishes correct base")
        print("  Gen 10-50: Optimization discoveries")
        print("  Gen 50-200: Refinement and validation")
        return True
    else:
        print(f"[ERROR] {resp2.text[:500]}")
        return False


if __name__ == "__main__":
    try:
        success = start_challenge()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
