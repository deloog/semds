"""
Matrix Multiplication Challenge V2 - Fixed for Local LLM

Improved prompt to help Qwen 3.5 generate correct function signatures
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

# Fixed test code with clearer requirements
TEST_CODE = '''
import random
import time

def solution(A, B):
    """
    Multiply two 2x2 matrices: C = A × B
    
    Parameters:
        A: [[a11, a12], [a21, a22]]
        B: [[b11, b12], [b21, b22]]
    
    Returns:
        C: [[c11, c12], [c21, c22]]
    
    Goal: Use fewer than 8 multiplications (beat standard algorithm)
    Strassen uses 7 multiplications.
    """
    # Extract elements
    a11, a12 = A[0][0], A[0][1]
    a21, a22 = A[1][0], A[1][1]
    b11, b12 = B[0][0], B[0][1]
    b21, b22 = B[1][0], B[1][1]
    
    # Standard algorithm (8 multiplications)
    c11 = a11 * b11 + a12 * b21
    c12 = a11 * b12 + a12 * b22
    c21 = a21 * b11 + a22 * b21
    c22 = a21 * b12 + a22 * b22
    
    return [[c11, c12], [c21, c22]]


def test_correctness():
    """Test with various matrices"""
    # Test 1: Identity matrix
    I = [[1, 0], [0, 1]]
    A = [[1, 2], [3, 4]]
    result = solution(A, I)
    assert result == A, f"Identity failed: {result}"
    
    # Test 2: Simple multiplication
    A = [[1, 2], [3, 4]]
    B = [[5, 6], [7, 8]]
    result = solution(A, B)
    expected = [[19, 22], [43, 50]]
    assert result == expected, f"Simple mult failed: {result}"
    
    # Test 3: Negative numbers
    A = [[-1, 2], [3, -4]]
    B = [[5, -6], [-7, 8]]
    result = solution(A, B)
    expected = [[-19, 22], [43, -50]]
    assert result == expected, f"Negative test failed: {result}"
    
    # Test 4: Random matrices (100 tests)
    for _ in range(100):
        A = [[random.randint(-10, 10) for _ in range(2)] for _ in range(2)]
        B = [[random.randint(-10, 10) for _ in range(2)] for _ in range(2)]
        result = solution(A, B)
        
        # Verify
        expected = [
            [A[0][0]*B[0][0] + A[0][1]*B[1][0], A[0][0]*B[0][1] + A[0][1]*B[1][1]],
            [A[1][0]*B[0][0] + A[1][1]*B[1][0], A[1][0]*B[0][1] + A[1][1]*B[1][1]]
        ]
        assert result == expected, f"Random test failed: A={A}, B={B}, got {result}"


def test_performance():
    """Performance benchmark"""
    n = 100000
    A = [[random.random() for _ in range(2)] for _ in range(2)]
    B = [[random.random() for _ in range(2)] for _ in range(2)]
    
    start = time.perf_counter()
    for _ in range(n):
        result = solution(A, B)
    elapsed = time.perf_counter() - start
    
    # Score based on speed
    if elapsed < 0.01:
        score = 1.0
    elif elapsed < 0.05:
        score = 0.8
    elif elapsed < 0.1:
        score = 0.6
    else:
        score = 0.4
    
    assert elapsed < 0.5, f"Too slow: {elapsed}s"


if __name__ == "__main__":
    test_correctness()
    test_performance()
'''


def check_ollama():
    """Check Ollama status"""
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json()
            for m in models.get("models", []):
                if "qwen" in m["name"].lower():
                    print(f"[OK] Ollama ready with: {m['name']}")
                    return True
        print("[X] Qwen model not found")
        return False
    except Exception as e:
        print(f"[X] Ollama error: {e}")
        return False


def start_challenge():
    if not check_ollama():
        print("\nPlease start Ollama first:")
        print("  $env:OLLAMA_MODELS='D:\\ollama_models'")
        print("  ollama serve")
        return False

    print("\n" + "=" * 60)
    print("MATRIX MULTIPLICATION CHALLENGE V2")
    print("=" * 60)
    print("\nImprovements:")
    print("  - Better function signature examples")
    print("  - Stricter validation")
    print("  - Self-correction for common errors")
    print("\nTarget: 2x2 matmul optimization")
    print("  Standard: 8 multiplications")
    print("  Strassen: 7 multiplications")
    print("  Goal: Faster practical implementation")
    print("=" * 60 + "\n")

    token = create_access_token(data={"sub": "admin-1", "role": UserRole.ADMIN})
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    task_data = {
        "name": "Matrix Challenge V2 (Fixed)",
        "description": "2x2 matmul optimization with improved prompts for local LLM. Target: correct solution() signature.",
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
    print(f"[OK] Task: {task['id']}")

    print("\nStarting evolution...")
    resp2 = requests.post(
        f"http://localhost:8000/api/tasks/{task['id']}/start", headers=headers
    )

    if resp2.status_code == 200:
        print("[OK] Evolution started!")
        print(f"\nMonitor: http://localhost:8000/monitor/")
        print(f"Task ID: {task['id']}")
        print("\nTip: Check Gen 1-3 for correct function signature")
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
