"""
Challenge 3: Sorting Algorithm - Initial Solution
Baseline: Bubble Sort (intentionally slow)
Target: Evolution should discover O(n log n) algorithm
"""


def solution(arr):
    """
    Sort array in ascending order.

    Args:
        arr: List of integers

    Returns:
        Sorted list of integers
    """
    # Bubble sort - O(n^2)
    # This is intentionally inefficient as a starting point
    # Evolution should discover better algorithms

    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
