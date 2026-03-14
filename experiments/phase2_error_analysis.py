#!/usr/bin/env python3
"""
Phase 2: 错误分析验证实验

验证目标：
1. ErrorAnalyzer 能准确解析测试失败信息
2. 结构化反馈能帮助 LLM 理解问题
3. 基于反馈的修复能提高通过率

实验设计：
- 运行一个有缺陷的代码（如 Phase 1 早期的 calculator）
- 使用 ErrorAnalyzer 分析失败
- 将分析结果反馈给 LLM 要求修复
- 对比修复前后的得分
"""

import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.env_loader import load_env
load_env()

from evolution.code_generator import CodeGenerator
from evolution.error_analyzer import ErrorAnalyzer
from evolution.test_runner import TestRunner
from evolution.self_validator import SelfValidator


class ErrorAnalysisExperiment:
    """Phase 2 错误分析实验"""
    
    def __init__(self):
        self.analyzer = ErrorAnalyzer()
        self.test_runner = TestRunner(timeout_seconds=30, verbose=False)
        self.validator = SelfValidator(expected_function_name="evaluate")
        
        # 故意有缺陷的代码（常见新手错误）
        self.buggy_code = '''
def evaluate(expression: str) -> float:
    """
    字符串表达式计算器 - 有缺陷版本
    """
    # 缺陷1: 没有处理空格
    # 缺陷2: 没有处理运算符优先级
    # 缺陷3: 简单的从左到右计算
    
    result = 0
    current_num = ""
    last_op = "+"
    
    for char in expression:
        if char.isdigit() or char == ".":
            current_num += char
        elif char in "+-*/":
            num = float(current_num) if current_num else 0
            
            if last_op == "+":
                result += num
            elif last_op == "-":
                result -= num
            elif last_op == "*":
                result *= num
            elif last_op == "/":
                result /= num if num != 0 else 1
            
            last_op = char
            current_num = ""
    
    # 处理最后一个数字
    if current_num:
        num = float(current_num)
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
        
        # 测试代码
        self.test_code = '''
from solution import evaluate

def test_simple():
    assert evaluate("2+3") == 5

def test_precedence():
    assert evaluate("2+3*4") == 14  # 缺陷：当前返回 20

def test_parentheses():
    assert evaluate("(2+3)*4") == 20

def test_whitespace():
    assert evaluate(" 2 + 3 ") == 5
'''
    
    def run_experiment(self):
        """运行实验"""
        print("="*70)
        print("Phase 2: Error Analysis Experiment")
        print("="*70)
        print(f"Start: {datetime.now().isoformat()}")
        print()
        
        # Step 1: 运行有缺陷的代码
        print("[Step 1] Running buggy code...")
        buggy_result = self._run_test(self.buggy_code)
        print(f"  Score: {buggy_result['pass_rate']:.0%}")
        print(f"  Failed: {len(buggy_result.get('failed', []))}")
        
        # Step 2: 使用 ErrorAnalyzer 分析
        print("\n[Step 2] Analyzing failures...")
        
        # 构造模拟的 pytest 输出
        test_output = self._construct_test_output(buggy_result)
        
        analysis = self.analyzer.analyze(test_output, total_tests=4)
        print(f"  Total: {analysis.total_tests}")
        print(f"  Failed: {analysis.failed_tests}")
        print(f"  Error types: {[f.error_type.value for f in analysis.failures]}")
        
        # Step 3: 格式化为 LLM 反馈
        print("\n[Step 3] Formatting feedback for LLM...")
        feedback = self.analyzer.format_for_llm(analysis, self.buggy_code)
        print(feedback[:500] + "...")
        
        # Step 4: 使用反馈尝试修复
        print("\n[Step 4] Attempting to fix with LLM...")
        fixed_code = self._attempt_fix(feedback)
        
        if fixed_code:
            fixed_result = self._run_test(fixed_code)
            print(f"  Fixed score: {fixed_result['pass_rate']:.0%}")
            
            # 对比
            print("\n" + "="*70)
            print("COMPARISON")
            print("="*70)
            print(f"Before: {buggy_result['pass_rate']:.0%}")
            print(f"After:  {fixed_result['pass_rate']:.0%}")
            print(f"Improvement: +{(fixed_result['pass_rate'] - buggy_result['pass_rate']):.0%}")
            
            if fixed_result['pass_rate'] > buggy_result['pass_rate']:
                print("\n[PASS] Error analysis helped improve the code!")
            else:
                print("\n[NEUTRAL] No improvement (may need stronger feedback)")
        else:
            print("  [FAIL] Fix attempt failed")
    
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
    
    def _construct_test_output(self, result: dict) -> str:
        """从 TestRunner 结果构造 pytest 风格的输出"""
        lines = []
        
        total = result.get('total_tests', 0)
        passed = len(result.get('passed', []))
        failed = len(result.get('failed', []))
        
        lines.append(f"{passed} passed, {failed} failed")
        
        # 使用原始输出（如果可用）
        raw_output = result.get('raw_output', '')
        if raw_output:
            return raw_output
        
        # 备选：从失败列表构造
        for test_name in result.get('failed', []):
            lines.append(f"\nFAILED test_solution.py::{test_name}")
            lines.append(f"E   AssertionError: Test failed")
        
        return "\n".join(lines)
    
    def _attempt_fix(self, feedback: str) -> str:
        """尝试使用 LLM 修复代码"""
        try:
            generator = CodeGenerator()
            
            task_spec = {
                "name": "calculator_fix",
                "description": f"""
Fix the following code based on test failure feedback.

CURRENT CODE:
{self.buggy_code}

FEEDBACK:
{feedback}

Requirements:
1. Fix ALL issues mentioned in the feedback
2. Maintain the function signature: def evaluate(expression: str) -> float
3. Ensure proper handling of operator precedence (* and / before + and -)
4. Handle whitespace properly
5. Support parentheses if mentioned in tests
""",
                "function_signature": "def evaluate(expression: str) -> float"
            }
            
            result = generator.generate(task_spec=task_spec, previous_code=self.buggy_code)
            
            if result["success"]:
                return result["code"]
            else:
                return None
                
        except Exception as e:
            print(f"  Error: {e}")
            return None


if __name__ == "__main__":
    experiment = ErrorAnalysisExperiment()
    experiment.run_experiment()
