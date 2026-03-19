"""
Start Matrix Multiplication Challenge with Hybrid LLM
Uses DeepSeek + Local Qwen 3.5 4B for cost-effective evolution
"""

import os
import sys
import requests

# Setup paths
os.chdir(r"D:\semds")
sys.path.insert(0, r"D:\semds")

from core.env_loader import load_env

load_env()

from api.auth.jwt import create_access_token
from api.auth.models import UserRole

# Test code for 2x2 matrix multiplication optimization
TEST_CODE = '''
import random
import time

def solution(A, B):
    """
    Multiply two 2x2 matrices.
    A, B are list of lists: [[a11, a12], [a21, a22]]
    Target: Use fewer than 8 multiplications (standard) or 7 (Strassen)
    """
    a11, a12 = A[0][0], A[0][1]
    a21, a22 = A[1][0], A[1][1]
    b11, b12 = B[0][0], B[0][1]
    b21, b22 = B[1][0], B[1][1]
    
    # Standard: 8 multiplications
    # Strassen: 7 multiplications
    # Your goal: Find practical optimizations
    
    c11 = a11 * b11 + a12 * b21
    c12 = a11 * b12 + a12 * b22
    c21 = a21 * b11 + a22 * b21
    c22 = a21 * b12 + a22 * b22
    
    return [[c11, c12], [c21, c22]]


def test_correctness():
    """Test basic correctness"""
    # Test 1: Identity
    I = [[1, 0], [0, 1]]
    A = [[1, 2], [3, 4]]
    assert solution(A, I) == A
    
    # Test 2: Simple mult
    A = [[1, 2], [3, 4]]
    B = [[5, 6], [7, 8]]
    expected = [[19, 22], [43, 50]]
    assert solution(A, B) == expected
    
    # Test 3: Random matrices
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
    """Performance test"""
    n = 100000
    A = [[random.random() for _ in range(2)] for _ in range(2)]
    B = [[random.random() for _ in range(2)] for _ in range(2)]
    
    start = time.perf_counter()
    for _ in range(n):
        result = solution(A, B)
    elapsed = time.perf_counter() - start
    
    # Target: faster than 0.5s for 100k multiplications
    assert elapsed < 0.5, f"Too slow: {elapsed}s"


if __name__ == "__main__":
    test_correctness()
    test_performance()
'''


def check_ollama():
    """Check if Ollama is running with Qwen model"""
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json()
            for m in models.get("models", []):
                if "qwen" in m["name"].lower():
                    print(f"[OK] Found model: {m['name']}")
                    return True
        print("[X] Qwen model not found in Ollama")
        return False
    except:
        print("[X] Ollama not running. Please start with: D:\\start_ollama.bat")
        return False


def create_and_start_challenge():
    """Create matrix multiplication challenge task"""

    # Check Ollama first
    if not check_ollama():
        print("\nPlease start Ollama first:")
        print("1. Open a new terminal")
        print("2. Run: D:\\start_ollama.bat")
        print("3. Then run this script again")
        return False

    print("\n" + "=" * 60)
    print("MATRIX MULTIPLICATION CHALLENGE")
    print("=" * 60)
    print("\nTarget: Optimize 2x2 matrix multiplication")
    print("Current best:")
    print("  - Standard: 8 multiplications")
    print("  - Strassen: 7 multiplications (1969)")
    print("  - Goal: Find faster practical implementation")
    print("\nLLM Strategy: Hybrid (DeepSeek + Qwen 3.5 4B)")
    print("Cost estimate: ~5 CNY for 500 generations")
    print("=" * 60 + "\n")

    # Get auth token
    token = create_access_token(data={"sub": "admin-1", "role": UserRole.ADMIN})
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Create task
    task_data = {
        "name": "Matrix Multiplication Challenge",
        "description": "Find faster 2x2 matmul. Target: <8 mults (standard) or beat Strassen (7). Hybrid LLM mode.",
        "target_function_signature": "def solution(A: list, B: list) -> list:",
        "test_code": TEST_CODE,
        "max_generations": 500,
        "success_criteria": {"target_score": 0.95},
    }

    print("Creating task...")
    resp = requests.post(
        "http://localhost:8000/api/tasks", headers=headers, json=task_data
    )

    if resp.status_code != 201:
        print(f"[ERROR] Failed to create task: {resp.status_code}")
        print(resp.text[:500])
        return False

    task = resp.json()
    task_id = task["id"]
    print(f"[OK] Task created: {task_id}")

    # Enable hybrid mode
    print("\n[OK] Hybrid LLM mode enabled")
    print("  - DeepSeek: Every 20 generations (strategic)")
    print("  - Qwen 3.5 4B: Routine generations (tactical)")
    print("  - Fallback: After 3 consecutive failures")

    # Start evolution
    print("\nStarting evolution...")
    resp2 = requests.post(
        f"http://localhost:8000/api/tasks/{task_id}/start", headers=headers
    )

    if resp2.status_code == 200:
        print("[OK] Evolution started!")
        print(f"\nMonitor at: http://localhost:8000/monitor/")
        print(f"Task ID: {task_id}")
        print("\nExpected timeline:")
        print("  - Gen 1-20:  Qwen 3.5 discovers basic optimizations")
        print("  - Gen 20:    DeepSeek strategic improvement")
        print("  - Gen 20-50: Refinement and validation")
        print("  - Target:    Practical speedup or fewer multiplications")
        return True
    else:
        print(f"[ERROR] Failed to start: {resp2.status_code}")
        print(resp2.text[:500])
        return False


if __name__ == "__main__":
    try:
        success = create_and_start_challenge()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
