"""
Challenge 3: Sorting Algorithm Evolution - Test Suite

Tests both correctness and performance.
Success criteria:
- Correctness: 100% pass on all test cases
- Performance: Target < 0.1s for 100k integers
"""
import random
import time
import sys
from typing import List


# ============== Test Data Generation ==============

def generate_random_array(size: int, min_val: int = -1000000, max_val: int = 1000000) -> List[int]:
    """Generate random array of given size"""
    return [random.randint(min_val, max_val) for _ in range(size)]


def generate_sorted_array(size: int) -> List[int]:
    """Generate already sorted array (best case)"""
    return list(range(size))


def generate_reverse_array(size: int) -> List[int]:
    """Generate reverse sorted array (worst case for some algorithms)"""
    return list(range(size, 0, -1))


def generate_few_unique_array(size: int, unique_count: int = 10) -> List[int]:
    """Generate array with few unique values"""
    return [random.randint(0, unique_count - 1) for _ in range(size)]


def generate_nearly_sorted_array(size: int, swap_count: int = 10) -> List[int]:
    """Generate nearly sorted array"""
    arr = list(range(size))
    for _ in range(swap_count):
        i, j = random.randint(0, size - 1), random.randint(0, size - 1)
        arr[i], arr[j] = arr[j], arr[i]
    return arr


# ============== Test Cases ==============

TEST_CASES_CORRECTNESS = [
    # (name, input_array, description)
    ("empty", [], "Empty array"),
    ("single", [42], "Single element"),
    ("two_sorted", [1, 2], "Two elements sorted"),
    ("two_reverse", [2, 1], "Two elements reverse"),
    ("three", [3, 1, 2], "Three elements"),
    ("duplicates", [3, 1, 3, 2, 1], "With duplicates"),
    ("all_same", [5, 5, 5, 5], "All same elements"),
    ("negative", [-3, -1, -2], "Negative numbers"),
    ("mixed", [-3, 0, 3, -1, 2], "Mixed positive/negative"),
    ("small_random", generate_random_array(100), "100 random elements"),
]

TEST_CASES_PERFORMANCE = [
    # (name, generator_func, size, time_limit_seconds)
    ("perf_random_1k", generate_random_array, 1000, 0.01),
    ("perf_random_10k", generate_random_array, 10000, 0.03),
    ("perf_random_100k", generate_random_array, 100000, 0.1),
    ("perf_sorted_100k", generate_sorted_array, 100000, 0.05),
    ("perf_reverse_100k", generate_reverse_array, 100000, 0.1),
    ("perf_few_unique_100k", generate_few_unique_array, 100000, 0.08),
    ("perf_nearly_sorted_100k", generate_nearly_sorted_array, 100000, 0.05),
]


# ============== Evaluation ==============

def evaluate_solution(solution_func) -> dict:
    """
    Evaluate a solution function.
    
    Returns:
        dict with:
        - correctness_score: 0.0 - 1.0
        - performance_score: 0.0 - 1.0
        - total_score: weighted average
        - details: per-test results
    """
    results = {
        "correctness": {},
        "performance": {},
        "correctness_score": 0.0,
        "performance_score": 0.0,
        "total_score": 0.0,
    }
    
    # Test correctness
    correct_count = 0
    for name, arr, desc in TEST_CASES_CORRECTNESS:
        try:
            expected = sorted(arr)
            start = time.perf_counter()
            result = solution_func(arr.copy())
            elapsed = time.perf_counter() - start
            
            is_correct = result == expected
            if is_correct:
                correct_count += 1
            
            results["correctness"][name] = {
                "passed": is_correct,
                "time": elapsed,
                "description": desc,
            }
        except Exception as e:
            results["correctness"][name] = {
                "passed": False,
                "error": str(e),
                "description": desc,
            }
    
    results["correctness_score"] = correct_count / len(TEST_CASES_CORRECTNESS)
    
    # Test performance (only if correctness passes)
    if results["correctness_score"] < 1.0:
        # If not 100% correct, performance score is 0
        results["performance_score"] = 0.0
        for name, _, _, _ in TEST_CASES_PERFORMANCE:
            results["performance"][name] = {"skipped": True, "reason": "correctness failed"}
    else:
        perf_scores = []
        for name, generator, size, time_limit in TEST_CASES_PERFORMANCE:
            try:
                arr = generator(size)
                start = time.perf_counter()
                result = solution_func(arr.copy())
                elapsed = time.perf_counter() - start
                
                # Verify result is correct
                if result != sorted(arr):
                    results["performance"][name] = {"passed": False, "error": "wrong result"}
                    perf_scores.append(0.0)
                    continue
                
                # Score based on time limit
                # score = min(1.0, time_limit / elapsed) - but inverted
                # If elapsed <= time_limit: full score
                # If elapsed > time_limit: partial score decreasing
                if elapsed <= time_limit:
                    score = 1.0
                else:
                    # Linear penalty: 1.0 at time_limit, 0.0 at 2*time_limit
                    ratio = (elapsed - time_limit) / time_limit
                    score = max(0.0, 1.0 - ratio)
                
                perf_scores.append(score)
                results["performance"][name] = {
                    "passed": score > 0.5,
                    "time": elapsed,
                    "limit": time_limit,
                    "score": score,
                }
            except Exception as e:
                results["performance"][name] = {"passed": False, "error": str(e)}
                perf_scores.append(0.0)
        
        results["performance_score"] = sum(perf_scores) / len(perf_scores) if perf_scores else 0.0
    
    # Weighted total: correctness is mandatory, performance is bonus
    # Must be 100% correct to get any performance points
    if results["correctness_score"] < 1.0:
        results["total_score"] = results["correctness_score"] * 0.5
    else:
        results["total_score"] = 0.5 + results["performance_score"] * 0.5
    
    return results


# ============== Main ==============

if __name__ == "__main__":
    # Import the solution to test
    import sys
    import os
    
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from solution import solution
        print("Testing solution...")
    except ImportError:
        print("Error: Cannot import solution.py")
        print("Creating default bubble sort for baseline...")
        
        def solution(arr):
            """Bubble sort - worst baseline"""
            n = len(arr)
            for i in range(n):
                for j in range(0, n - i - 1):
                    if arr[j] > arr[j + 1]:
                        arr[j], arr[j + 1] = arr[j + 1], arr[j]
            return arr
    
    # Run evaluation
    results = evaluate_solution(solution)
    
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"Correctness Score: {results['correctness_score']:.2%}")
    print(f"Performance Score: {results['performance_score']:.2%}")
    print(f"Total Score: {results['total_score']:.2%}")
    print("=" * 60)
    
    # Print details
    print("\nCorrectness Tests:")
    for name, detail in results["correctness"].items():
        status = "PASS" if detail.get("passed") else "FAIL"
        print(f"  {name:20s} [{status}] {detail.get('description', '')}")
    
    print("\nPerformance Tests:")
    for name, detail in results["performance"].items():
        if detail.get("skipped"):
            print(f"  {name:20s} [SKIP] {detail.get('reason', '')}")
        elif detail.get("passed"):
            print(f"  {name:20s} [PASS] {detail.get('time', 0):.4f}s / {detail.get('limit', 0):.4f}s")
        else:
            print(f"  {name:20s} [FAIL] {detail.get('error', 'too slow')}")
    
    # Exit with score as return code for automation
    import sys
    sys.exit(int(results['total_score'] * 100))
