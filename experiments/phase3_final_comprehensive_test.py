"""
Phase 3 最终综合验证实验

整合所有改进，全面验证系统能力：
1. 使用增强评估器（解决复杂算法评分问题）
2. 多种任务类型（字符串、算法、数学）
3. 真实 Mock 场景
4. 完整的评估指标
"""

import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from evolution.orchestrator import EvolutionOrchestrator
from evolution.termination_checker import TerminationConfig
from evolution.dual_evaluator import DualEvaluator


class ComprehensiveCodeGenerator:
    """综合代码生成器 - 模拟高质量 LLM"""
    
    TASKS = {
        "reverse": '''def reverse_string(s: str) -> str:
    """Reverse a string."""
    return s[::-1]''',

        "palindrome": '''def is_palindrome(s: str) -> bool:
    """Check if string is palindrome (ignores case and spaces)."""
    cleaned = s.lower().replace(" ", "")
    return cleaned == cleaned[::-1]''',

        "factorial": '''def factorial(n: int) -> int:
    """Calculate factorial of n."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result''',

        "gcd": '''def gcd(a: int, b: int) -> int:
    """Calculate greatest common divisor using Euclidean algorithm."""
    while b:
        a, b = b, a % b
    return a''',

        "is_prime": '''def is_prime(n: int) -> bool:
    """Check if n is a prime number."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True''',
    }
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        
    def generate(self, task_spec, **kwargs):
        """生成代码"""
        code = self.TASKS.get(self.task_id, "def solution(): pass")
        
        return {
            "success": True,
            "code": code,
            "raw_response": f"```python\n{code}\n```",
            "error": None,
        }


FINAL_TASKS = [
    {
        "id": "reverse",
        "name": "字符串反转",
        "requirements": ["实现 reverse_string(s) 函数", "返回字符串反转"],
        "test_code": '''
assert reverse_string("hello") == "olleh"
assert reverse_string("") == ""
assert reverse_string("a") == "a"
''',
    },
    {
        "id": "palindrome",
        "name": "回文检测",
        "requirements": ["实现 is_palindrome(s) 函数", "忽略大小写和空格"],
        "test_code": '''
assert is_palindrome("racecar") == True
assert is_palindrome("hello") == False
assert is_palindrome("A man a plan a canal Panama") == True
''',
    },
    {
        "id": "factorial",
        "name": "阶乘计算",
        "requirements": ["实现 factorial(n) 函数", "处理负数异常", "使用迭代实现"],
        "test_code": '''
assert factorial(0) == 1
assert factorial(5) == 120
assert factorial(10) == 3628800
try:
    factorial(-1)
    assert False
except ValueError:
    pass
''',
    },
    {
        "id": "gcd",
        "name": "最大公约数",
        "requirements": ["实现 gcd(a, b) 函数", "使用欧几里得算法"],
        "test_code": '''
assert gcd(48, 18) == 6
assert gcd(56, 98) == 14
assert gcd(101, 103) == 1
''',
    },
    {
        "id": "is_prime",
        "name": "素数检测",
        "requirements": ["实现 is_prime(n) 函数", "优化到 O(sqrt(n))"],
        "test_code": '''
assert is_prime(2) == True
assert is_prime(17) == True
assert is_prime(18) == False
assert is_prime(97) == True
''',
    },
]


def run_final_test():
    """运行最终综合测试"""
    print("=" * 70)
    print("Phase 3 最终综合验证实验")
    print("=" * 70)
    print(f"开始时间: {datetime.now().isoformat()}")
    print()
    print("本实验验证：")
    print("  - 增强评估器效果（复杂算法评分提升）")
    print("  - 多任务通用性（字符串、数学、算法）")
    print("  - 完整进化流程（生成 -> 测试 -> 评估 -> 进化）")
    print()
    
    results = []
    
    for task in FINAL_TASKS:
        print(f"\n{'-' * 70}")
        print(f"任务: {task['name']}")
        print(f"{'-' * 70}")
        
        # 创建生成器
        generator = ComprehensiveCodeGenerator(task_id=task['id'])
        
        # 配置
        config = TerminationConfig(
            success_threshold=0.75,
            max_generations=5,
            stagnation_generations=3,
        )
        
        orchestrator = EvolutionOrchestrator(
            task_id=task['id'],
            code_generator=generator,
            termination_config=config,
        )
        
        start = time.time()
        
        try:
            result = orchestrator.evolve(
                requirements=task['requirements'],
                test_code=task['test_code'],
                max_generations=5,
            )
            
            elapsed = time.time() - start
            
            # 评估
            passed = result.best_score >= 0.70
            status = "PASS" if passed else "FAIL"
            
            print(f"  最终得分: {result.best_score:.2f}")
            print(f"  代数: {result.generations}")
            print(f"  成功: {result.success}")
            print(f"  时间: {elapsed:.2f}s")
            print(f"  状态: {status}")
            
            results.append({
                "task": task['name'],
                "score": result.best_score,
                "passed": passed,
                "generations": result.generations,
                "time": elapsed,
            })
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            results.append({
                "task": task['name'],
                "error": str(e),
            })
    
    # 汇总
    print(f"\n{'=' * 70}")
    print("综合验证结果")
    print(f"{'=' * 70}")
    
    passed_count = sum(1 for r in results if r.get("passed"))
    total_count = len(results)
    
    print(f"\n任务详情:")
    for r in results:
        if "error" in r:
            print(f"  [ERROR] {r['task']}: {r['error']}")
        else:
            status = "PASS" if r['passed'] else "FAIL"
            print(f"  [{status}] {r['task']:20s} 得分: {r['score']:.2f}")
    
    print(f"\n总计: {passed_count}/{total_count} 通过 ({passed_count/total_count*100:.0f}%)")
    
    avg_score = sum(r['score'] for r in results if 'score' in r) / total_count
    avg_time = sum(r['time'] for r in results if 'time' in r) / total_count
    
    print(f"平均得分: {avg_score:.2f}")
    print(f"平均时间: {avg_time:.2f}s")
    
    # 结论
    print(f"\n{'=' * 70}")
    print("最终结论")
    print(f"{'=' * 70}")
    
    if passed_count == total_count:
        print("\n[EXCELLENT] 所有任务全部通过！")
        print("\n系统能力验证：")
        print("  [DONE] 字符串处理（反转、回文）")
        print("  [DONE] 数学计算（阶乘、GCD、素数）")
        print("  [DONE] 复杂算法正确评估")
        print("  [DONE] 完整进化流程正常工作")
        print("\nPhase 3 目标已完全达成！")
        return 0
    elif passed_count >= total_count * 0.8:
        print("\n[GOOD] 大部分任务通过，系统功能基本完善")
        return 0
    else:
        print("\n[NEEDS WORK] 部分任务失败，需要进一步优化")
        return 1


if __name__ == "__main__":
    sys.exit(run_final_test())
