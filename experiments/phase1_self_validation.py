#!/usr/bin/env python3
"""
Phase 1: 基础自验证实验

验证目标：
1. 实现 SelfValidator 类，自动检测代码生成错误
2. 函数名不匹配问题能够被自动检测并修正
3. 字符串计算器实验达到 90%+ 通过率

实验设计：
- 运行字符串计算器进化实验
- 每次代码生成后，SelfValidator 进行验证
- 如果函数名错误，自动提示修正并重试
- 最多重试3次
"""

import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.env_loader import load_env
load_env()

from evolution.code_generator import CodeGenerator
from evolution.test_runner import TestRunner
import re
import ast


class SelfValidator:
    """
    自我验证器 - 自动检测代码生成错误
    
    Phase 1 实现：
    - 语法检查
    - 函数签名检查（函数名、参数）
    - 基础测试运行
    """
    
    def __init__(self, expected_function_name: str = "evaluate"):
        self.expected_function_name = expected_function_name
        self.validation_history = []
    
    def validate(self, code: str, test_runner: TestRunner = None, 
                 test_code: str = None) -> tuple[bool, str, dict]:
        """
        验证代码并给出修正建议
        
        Returns:
            (是否通过, 修正提示, 详细信息)
        """
        # Level 1: 语法检查
        syntax_valid, syntax_error = self._check_syntax(code)
        if not syntax_valid:
            self.validation_history.append({
                "timestamp": datetime.now().isoformat(),
                "level": "syntax",
                "passed": False,
                "error": syntax_error
            })
            return False, f"Syntax error: {syntax_error}. Please fix and regenerate.", {"level": "syntax"}
        
        # Level 2: 函数签名检查
        function_valid, function_info = self._check_function_signature(code)
        if not function_valid:
            actual_name = function_info.get("actual_name", "unknown")
            self.validation_history.append({
                "timestamp": datetime.now().isoformat(),
                "level": "function_name",
                "passed": False,
                "expected": self.expected_function_name,
                "actual": actual_name
            })
            return False, (
                f"Function name error: Expected '{self.expected_function_name}', "
                f"but got '{actual_name}'. "
                f"Function signature must be: def {self.expected_function_name}(expression: str) -> float. "
                f"Please regenerate with correct function name."
            ), {"level": "function_name", "expected": self.expected_function_name, "actual": actual_name}
        
        # Level 3: 测试运行（如果提供了测试）
        if test_runner and test_code:
            test_result = self._run_test(code, test_runner, test_code)
            if test_result["pass_rate"] < 1.0:
                failed_count = len(test_result.get("failed", []))
                total_count = test_result.get("total_tests", 0)
                self.validation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "level": "test",
                    "passed": False,
                    "pass_rate": test_result["pass_rate"],
                    "failed_count": failed_count
                })
                return False, (
                    f"Tests failed: {failed_count}/{total_count} failed. "
                    f"Pass rate: {test_result['pass_rate']:.1%}. "
                    f"Please analyze and fix the implementation."
                ), {"level": "test", "result": test_result}
        
        # 全部通过
        self.validation_history.append({
            "timestamp": datetime.now().isoformat(),
            "level": "all",
            "passed": True
        })
        return True, "All validations passed.", {"level": "all"}
    
    def _check_syntax(self, code: str) -> tuple[bool, str]:
        """检查Python语法"""
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, str(e)
    
    def _check_function_signature(self, code: str) -> tuple[bool, dict]:
        """检查函数签名是否正确"""
        info = {"found": False, "actual_name": None}
        
        # 尝试解析AST
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    info["found"] = True
                    info["actual_name"] = node.name
                    
                    if node.name == self.expected_function_name:
                        return True, info
        except:
            pass
        
        # AST解析失败，使用正则表达式备用
        pattern = r"def\s+(\w+)\s*\("
        matches = re.findall(pattern, code)
        if matches:
            info["found"] = True
            info["actual_name"] = matches[0]
            if matches[0] == self.expected_function_name:
                return True, info
        
        return False, info
    
    def _run_test(self, code: str, test_runner: TestRunner, test_code: str) -> dict:
        """运行测试"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 写入代码
            solution_path = Path(tmpdir) / "solution.py"
            with open(solution_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # 写入测试
            test_path = Path(tmpdir) / "test_solution.py"
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(test_code)
            
            # 运行测试
            result = test_runner.run_tests(str(test_path), str(solution_path), tmpdir)
        
        return result
    
    def get_validation_summary(self) -> dict:
        """获取验证历史摘要"""
        if not self.validation_history:
            return {"total": 0}
        
        total = len(self.validation_history)
        passed = sum(1 for v in self.validation_history if v["passed"])
        failed = total - passed
        
        by_level = {}
        for v in self.validation_history:
            level = v["level"]
            if level not in by_level:
                by_level[level] = {"total": 0, "passed": 0}
            by_level[level]["total"] += 1
            if v["passed"]:
                by_level[level]["passed"] += 1
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "by_level": by_level
        }


class SelfEvolvingExperiment:
    """自进化实验 - Phase 1"""
    
    def __init__(self, max_generations: int = 10, max_retries: int = 3):
        self.max_generations = max_generations
        self.max_retries = max_retries
        self.validator = SelfValidator(expected_function_name="evaluate")
        self.test_runner = TestRunner(timeout_seconds=30, verbose=False)
        
        # 计算器测试代码
        self.test_code = '''
from solution import evaluate

def test_single_number():
    assert evaluate("5") == 5
    assert evaluate("3.14") == 3.14

def test_simple_addition():
    assert evaluate("2 + 3") == 5

def test_simple_subtraction():
    assert evaluate("5 - 3") == 2

def test_simple_multiplication():
    assert evaluate("4 * 3") == 12

def test_simple_division():
    assert evaluate("10 / 2") == 5.0

def test_operator_precedence():
    assert evaluate("2 + 3 * 4") == 14
    assert evaluate("10 - 2 * 3") == 4

def test_parentheses():
    assert evaluate("(2 + 3) * 4") == 20
    assert evaluate("(10 - 4)") == 6

def test_whitespace():
    assert evaluate("  2  +  3  ") == 5
    assert evaluate("2+3*4") == 14
'''
    
    def run_generation_with_validation(self, generator: CodeGenerator, 
                                       gen_num: int, previous_feedback: str = None) -> dict:
        """运行一代进化，包含自验证和重试机制"""
        
        print(f"\n{'='*70}")
        print(f"Generation {gen_num}")
        print(f"{'='*70}")
        
        # 构建任务规格
        task_spec = {
            "name": "string_calculator",
            "description": "实现字符串表达式计算器",
            "target_function_signature": "def evaluate(expression: str) -> float",
            "requirements": [
                "函数签名必须严格为: def evaluate(expression: str) -> float",
                "支持四则运算: +, -, *, /",
                "正确处理运算符优先级",
                "支持括号嵌套",
                "处理空格"
            ]
        }
        
        # 如果有前代反馈，添加到任务描述
        if previous_feedback:
            task_spec["feedback"] = previous_feedback
            print(f"[Feedback] {previous_feedback}")
        
        # 尝试生成和验证（带重试）
        for retry in range(self.max_retries):
            if retry > 0:
                print(f"\n[Retry {retry}/{self.max_retries-1}]")
            
            # 生成代码
            print("Generating code...")
            start_time = time.time()
            
            result = generator.generate(
                task_spec=task_spec,
                previous_code=None  # Phase 1 不使用前代代码
            )
            
            gen_time = time.time() - start_time
            
            if not result["success"]:
                print(f"  [FAIL] Generation failed: {result.get('error')}")
                if retry == self.max_retries - 1:
                    return {"success": False, "score": 0.0, "code": None}
                continue
            
            code = result["code"]
            print(f"  [OK] Generated in {gen_time:.2f}s ({len(code)} chars)")
            
            # 自验证
            print("Running self-validation...")
            is_valid, feedback, details = self.validator.validate(
                code, self.test_runner, self.test_code
            )
            
            if is_valid:
                print(f"  [PASS] All validations passed")
                # 运行完整测试获取详细结果
                test_result = self.validator._run_test(code, self.test_runner, self.test_code)
                return {
                    "success": True,
                    "code": code,
                    "score": test_result["pass_rate"],
                    "generation_time": gen_time,
                    "retries": retry,
                    "test_result": test_result
                }
            else:
                print(f"  [FAIL] {feedback}")
                if retry < self.max_retries - 1:
                    print(f"  [RETRY] Will regenerate with feedback")
                    previous_feedback = feedback
                else:
                    print(f"  [MAX RETRIES] Using best attempt")
                    # 即使验证失败，也返回最后一次尝试
                    test_result = self.validator._run_test(code, self.test_runner, self.test_code)
                    return {
                        "success": True,
                        "code": code,
                        "score": test_result["pass_rate"],
                        "generation_time": gen_time,
                        "retries": retry,
                        "test_result": test_result,
                        "validation_failed": True
                    }
        
        return {"success": False, "score": 0.0, "code": None}
    
    def run_experiment(self):
        """运行完整实验"""
        
        print("="*70)
        print("Phase 1: Self-Validation Experiment")
        print("="*70)
        print(f"Start: {datetime.now().isoformat()}")
        print(f"Max generations: {self.max_generations}")
        print(f"Max retries per generation: {self.max_retries}")
        print()
        
        # 初始化代码生成器
        try:
            generator = CodeGenerator()
            print("[OK] CodeGenerator initialized")
        except Exception as e:
            print(f"[FAIL] Failed to initialize CodeGenerator: {e}")
            return
        
        # 运行多代进化
        history = []
        best_score = 0.0
        best_code = None
        
        start_time = time.time()
        
        for gen in range(self.max_generations):
            result = self.run_generation_with_validation(generator, gen)
            
            if result["success"]:
                history.append(result)
                
                score = result["score"]
                retries = result.get("retries", 0)
                
                print(f"\n[Result] Score: {score:.2%}, Retries: {retries}")
                
                # 更新最佳
                if score > best_score:
                    best_score = score
                    best_code = result["code"]
                    print(f"[NEW BEST] Generation {gen}")
                
                # 检查是否达到目标
                if score >= 0.9:
                    print(f"\n[TARGET REACHED] Score {score:.2%} >= 90%")
                    break
            else:
                print(f"\n[SKIP] Generation {gen} failed")
            
            # 延迟避免API限流
            if gen < self.max_generations - 1:
                time.sleep(2)
        
        elapsed = time.time() - start_time
        
        # 打印最终报告
        self._print_report(history, best_score, best_code, elapsed)
    
    def _print_report(self, history: list, best_score: float, best_code: str, elapsed: float):
        """打印实验报告"""
        
        print("\n" + "="*70)
        print("EXPERIMENT REPORT - Phase 1")
        print("="*70)
        print(f"Total generations: {len(history)}")
        print(f"Best score: {best_score:.2%}")
        print(f"Total time: {elapsed:.2f}s")
        print()
        
        # 验证统计
        validation_summary = self.validator.get_validation_summary()
        print("Validation statistics:")
        print(f"  Total validations: {validation_summary['total']}")
        print(f"  Passed: {validation_summary['passed']}")
        print(f"  Failed: {validation_summary['failed']}")
        print(f"  Pass rate: {validation_summary['pass_rate']:.1%}")
        print()
        
        # 进化轨迹
        print("Evolution trajectory:")
        print("-"*70)
        print(f"{'Gen':<6} {'Score':<10} {'Retries':<10} {'Status'}")
        print("-"*70)
        
        for i, h in enumerate(history):
            retries = h.get("retries", 0)
            status = "BEST" if h["code"] == best_code else ""
            print(f"{i:<6} {h['score']:<10.2%} {retries:<10} {status}")
        
        print("-"*70)
        print()
        
        # 最佳代码
        if best_code:
            print("Best code:")
            print("="*70)
            print(best_code)
            print("="*70)
        
        # Phase 1 目标检查
        print("\n" + "="*70)
        print("Phase 1 Goals Check")
        print("="*70)
        
        goals = {
            "SelfValidator implemented": True,
            "Auto-retry mechanism working": len(history) > 0 and any(h.get("retries", 0) > 0 for h in history),
            "Score >= 90%": best_score >= 0.9,
        }
        
        for goal, achieved in goals.items():
            status = "[PASS]" if achieved else "[FAIL]"
            print(f"{status} {goal}")
        
        all_passed = all(goals.values())
        print()
        if all_passed:
            print("[SUCCESS] Phase 1 goals achieved! Ready for Phase 2.")
        else:
            print("[PARTIAL] Some goals not achieved. Review and adjust.")
        
        print("="*70)


if __name__ == "__main__":
    experiment = SelfEvolvingExperiment(max_generations=5, max_retries=3)
    experiment.run_experiment()
