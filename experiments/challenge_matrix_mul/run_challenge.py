"""
Challenge: Matrix Multiplication Optimization

Goal: Find faster 2x2 or 3x3 matrix multiplication algorithm
Current best: 
- 2x2: 7 multiplications (Strassen, 1969)
- 3x3: 23 multiplications (Laderman, 1976)

If SEMDS finds <7 for 2x2, it's a breakthrough!
"""

TEST_CODE = '''
import random
import time

def solution(A, B):
    """
    Multiply two 2x2 matrices.
    A, B are list of lists: [[a11, a12], [a21, a22]]
    Return: 2x2 result matrix
    """
    # Standard algorithm uses 8 multiplications
    # Strassen uses 7
    # Can you find a faster way?
    
    a11, a12 = A[0][0], A[0][1]
    a21, a22 = A[1][0], A[1][1]
    b11, b12 = B[0][0], B[0][1]
    b21, b22 = B[1][0], B[1][1]
    
    # Standard implementation (8 multiplications)
    c11 = a11 * b11 + a12 * b21
    c12 = a11 * b12 + a12 * b22
    c21 = a21 * b11 + a22 * b21
    c22 = a21 * b12 + a22 * b22
    
    return [[c11, c12], [c21, c22]]


def test_correctness():
    """Test basic correctness"""
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
    
    # Test 3: Random matrices
    for _ in range(100):
        A = [[random.randint(-10, 10) for _ in range(2)] for _ in range(2)]
        B = [[random.randint(-10, 10) for _ in range(2)] for _ in range(2)]
        result = solution(A, B)
        
        # Verify against standard implementation
        expected = [
            [A[0][0]*B[0][0] + A[0][1]*B[1][0], A[0][0]*B[0][1] + A[0][1]*B[1][1]],
            [A[1][0]*B[0][0] + A[1][1]*B[1][0], A[1][0]*B[0][1] + A[1][1]*B[1][1]]
        ]
        assert result == expected, f"Random test failed"


def test_performance():
    """Test performance on many multiplications"""
    n = 10000
    A = [[random.random() for _ in range(2)] for _ in range(2)]
    B = [[random.random() for _ in range(2)] for _ in range(2)]
    
    start = time.perf_counter()
    for _ in range(n):
        result = solution(A, B)
    elapsed = time.perf_counter() - start
    
    # Target: <0.01s for 10000 multiplications
    assert elapsed < 0.01, f"Too slow: {elapsed}s"


if __name__ == "__main__":
    test_correctness()
    test_performance()
'''

if __name__ == "__main__":
    print("Matrix Multiplication Challenge")
    print("================================")
    print("Target: Find 2x2 matmul with <7 multiplications (beats Strassen)")
    print("Or: Find practical optimizations that run faster on real hardware")
    print()
    print("To start:")
    print("1. Create task via API with this test code")
    print("2. Run evolution for 100-500 generations") 
    print("3. Check if solution uses fewer multiplications or runs faster")
