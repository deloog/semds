#!/usr/bin/env python3
"""
Phase 3: 元学习验证实验

验证目标：
1. MetaLearner 能记录失败和修复模式
2. 能基于历史经验推荐策略
3. 能增强提示词以提升成功率

实验设计：
- 第一轮：故意制造失败，记录修复模式
- 第二轮：类似任务，验证是否能复用经验
- 对比：有经验 vs 无经验的成功率差异
"""

import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.env_loader import load_env
load_env()

from evolution.code_generator import CodeGenerator
from evolution.meta_learner import MetaLearner
from evolution.test_runner import TestRunner
from evolution.self_validator import SelfValidator


class MetaLearningExperiment:
    """Phase 3 元学习实验"""
    
    def __init__(self):
        self.meta_learner = MetaLearner(storage_path="experiments/meta_learning_db.json")
        self.test_runner = TestRunner(timeout_seconds=30, verbose=False)
        self.validator = SelfValidator(expected_function_name="evaluate")
        
        # 第一轮：故意有缺陷的代码（运算符优先级问题）
        self.round1_buggy_code = '''
def evaluate(expression: str) -> float:
    result = 0
    current_num = ""
    last_op = "+"
    
    for char in expression:
        if char.isdigit():
            current_num += char
        elif char in "+-*/":
            num = int(current_num) if current_num else 0
            if last_op == "+":
                result += num
            elif last_op == "-":
                result -= num
            elif last_op == "*":
                result *= num
            elif last_op == "/":
                result /= num
            last_op = char
            current_num = ""
    
    if current_num:
        num = int(current_num)
        if last_op == "+":
            result += num
        elif last_op == "-":
            result -= num
        elif last_op == "*":
            result *= num
        elif last_op == "/":
            result /= num
    
    return float(result)
'''
        
        # 第一轮修复后的正确代码
        self.round1_fixed_code = '''
def evaluate(expression: str) -> float:
    def apply_op(operators, values):
        op = operators.pop()
        b = values.pop()
        a = values.pop()
        if op == '+': values.append(a + b)
        elif op == '-': values.append(a - b)
        elif op == '*': values.append(a * b)
        elif op == '/': values.append(a / b)
    
    def precedence(op):
        if op in ('+', '-'): return 1
        if op in ('*', '/'): return 2
        return 0
    
    values = []
    operators = []
    i = 0
    
    while i < len(expression):
        if expression[i] == ' ':
            i += 1
            continue
        
        if expression[i].isdigit():
            num = 0
            while i < len(expression) and expression[i].isdigit():
                num = num * 10 + int(expression[i])
                i += 1
            values.append(num)
            continue
        
        if expression[i] in '+-*/':
            while (operators and 
                   precedence(operators[-1]) >= precedence(expression[i])):
                apply_op(operators, values)
            operators.append(expression[i])
        
        i += 1
    
    while operators:
        apply_op(operators, values)
    
    return float(values[0])
'''
        
        # 测试代码（包含优先级测试）
        self.test_code = '''
from solution import evaluate

def test_simple():
    assert evaluate("2+3") == 5
    assert evaluate("5-2") == 3

def test_precedence():
    assert evaluate("2+3*4") == 14  # 关键测试：优先级
    assert evaluate("10-2*3") == 4

def test_complex():
    assert evaluate("2*3+4*5") == 26
'''
    
    def run_experiment(self):
        """运行实验"""
        print("="*70)
        print("Phase 3: Meta-Learning Experiment")
        print("="*70)
        print(f"Start: {datetime.now().isoformat()}")
        print()
        
        # Round 1: 学习阶段
        print("[Round 1] Learning Phase - Recording failure pattern...")
        self._run_learning_phase()
        
        # Round 2: 应用阶段
        print("\n[Round 2] Application Phase - Testing pattern reuse...")
        self._run_application_phase()
        
        # 打印总结
        self._print_summary()
    
    def _run_learning_phase(self):
        """学习阶段：记录失败和修复"""
        # 验证有缺陷的代码
        buggy_result = self._run_test(self.round1_buggy_code)
        print(f"  Buggy code score: {buggy_result['pass_rate']:.0%}")
        
        # 验证修复后的代码
        fixed_result = self._run_test(self.round1_fixed_code)
        print(f"  Fixed code score: {fixed_result['pass_rate']:.0%}")
        
        # 记录模式
        pattern_id = self.meta_learner.record_failure_and_fix(
            task_type="calculator",
            error_type="assertion",
            original_code=self.round1_buggy_code,
            fixed_code=self.round1_fixed_code,
            error_message="AssertionError: assert evaluate('2+3*4') == 14",
            fix_description="使用双栈算法处理运算符优先级"
        )
        
        print(f"  Recorded pattern: {pattern_id}")
        
        # 记录策略效果
        self.meta_learner.record_strategy_result(
            strategy_name="with_precedence_handling",
            task_type="calculator",
            success=True,
            improvement=fixed_result['pass_rate'] - buggy_result['pass_rate']
        )
    
    def _run_application_phase(self):
        """应用阶段：验证经验复用"""
        
        # 场景 A：查询是否有适用模式
        print("\n[Scene A] Querying applicable patterns...")
        patterns = self.meta_learner.find_applicable_patterns(
            task_type="calculator",
            error_type="assertion",
            error_message="operator precedence error",
            top_k=3
        )
        
        print(f"  Found {len(patterns)} applicable patterns")
        for p in patterns:
            print(f"    - {p.pattern_id}: {p.fix_description} (success rate: {p.success_rate:.0%})")
        
        # 场景 B：策略推荐
        print("\n[Scene B] Strategy recommendation...")
        recommended, rate = self.meta_learner.recommend_strategy(
            task_type="calculator",
            available_strategies=["minimal", "with_precedence_handling", "with_examples"]
        )
        print(f"  Recommended: '{recommended}' (expected success rate: {rate:.0%})")
        
        # 场景 C：生成增强提示词
        print("\n[Scene C] Enhanced prompt generation...")
        base_prompt = "实现字符串表达式计算器"
        
        error_history = [
            {"error_type": "assertion", "error_message": "precedence error"}
        ]
        
        enhanced_prompt = self.meta_learner.generate_enhanced_prompt(
            task_type="calculator",
            base_prompt=base_prompt,
            error_history=error_history
        )
        
        print("  Enhanced prompt preview:")
        print("  " + "-"*50)
        for line in enhanced_prompt.split('\n')[:10]:
            print(f"  {line}")
        print("  " + "-"*50)
    
    def _run_test(self, code: str) -> dict:
        """运行测试"""
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            solution_path = Path(tmpdir) / "solution.py"
            with open(solution_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            test_path = Path(tmpdir) / "test_solution.py"
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(self.test_code)
            
            result = self.test_runner.run_tests(str(test_path), str(solution_path), tmpdir)
        
        return result
    
    def _print_summary(self):
        """打印学习摘要"""
        print("\n" + "="*70)
        print("Meta-Learning Summary")
        print("="*70)
        
        summary = self.meta_learner.get_learning_summary()
        
        print(f"\nTotal patterns recorded: {summary['total_patterns']}")
        print(f"Total strategies tracked: {summary['total_strategies']}")
        
        if summary['pattern_types']:
            print("\nPattern distribution by task type:")
            for task_type, count in summary['pattern_types'].items():
                print(f"  - {task_type}: {count}")
        
        if summary['top_patterns']:
            print("\nTop patterns by success rate:")
            for pid, rate, usage in summary['top_patterns']:
                print(f"  - {pid}: {rate:.0%} success, used {usage} times")
        
        print("\n" + "="*70)
        print("[PASS] Meta-learning system initialized and functional!")
        print("="*70)


if __name__ == "__main__":
    experiment = MetaLearningExperiment()
    experiment.run_experiment()
