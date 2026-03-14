#!/usr/bin/env python3
"""
Phase 1.5: 约束强化验证实验

验证目标：
1. ConstraintsInjector 能有效提高首次生成成功率
2. 多个不同任务类型都能受益
3. 约束违规率 < 5%

实验设计：
- 测试3个不同复杂度的任务
- 每个任务运行3次（检查一致性）
- 对比约束注入 vs 无约束注入的效果
"""

import sys
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.env_loader import load_env
load_env()

from evolution.code_generator import CodeGenerator
from evolution.constraints_injector import (
    ConstraintsInjector, TaskSpec,
    create_calculator_task, create_list_sort_task, create_json_parser_task
)
from evolution.self_validator import SelfValidator
from evolution.test_runner import TestRunner


@dataclass
class TaskResult:
    """任务验证结果"""
    task_name: str
    attempt: int
    success: bool
    function_name_correct: bool
    score: float
    generation_time: float
    error: str = ""


class ConstraintsValidationExperiment:
    """约束强化验证实验"""
    
    def __init__(self):
        self.injector = ConstraintsInjector(emphasis_style="critical")
        self.validator = SelfValidator()
        self.test_runner = TestRunner(timeout_seconds=30, verbose=False)
        
        # 测试代码映射
        self.test_code_map = self._create_test_code_map()
    
    def _create_test_code_map(self) -> Dict[str, str]:
        """创建各任务的测试代码"""
        return {
            "string_calculator": '''
from solution import evaluate

def test_basic():
    assert evaluate("2+3") == 5
    assert evaluate("10-4") == 6
    assert evaluate("3*4") == 12
    assert evaluate("8/2") == 4

def test_precedence():
    assert evaluate("2+3*4") == 14
    assert evaluate("10-2*3") == 4
    assert evaluate("(2+3)*4") == 20
''',
            "list_sorter": '''
from solution import sort_list

def test_ascending():
    assert sort_list([3, 1, 2]) == [1, 2, 3]
    assert sort_list([1]) == [1]
    assert sort_list([]) == []

def test_descending():
    assert sort_list([3, 1, 2], reverse=True) == [3, 2, 1]

def test_no_modify_original():
    original = [3, 1, 2]
    result = sort_list(original)
    assert original == [3, 1, 2]
    assert result == [1, 2, 3]
''',
            "json_parser": '''
from solution import parse_json

def test_string():
    assert parse_json('"hello"') == "hello"
    assert parse_json('"world"') == "world"

def test_number():
    assert parse_json("123") == 123
    assert parse_json("45.67") == 45.67

def test_boolean():
    assert parse_json("true") is True
    assert parse_json("false") is False

def test_null():
    assert parse_json("null") is None
'''
        }
    
    def run_task(self, task_spec: TaskSpec, with_constraints: bool = True) -> TaskResult:
        """运行单个任务"""
        
        # 更新验证器的期望函数名
        self.validator.expected_function_name = task_spec.function_name
        
        # 初始化代码生成器
        try:
            generator = CodeGenerator()
        except Exception as e:
            return TaskResult(
                task_name=task_spec.name,
                attempt=0,
                success=False,
                function_name_correct=False,
                score=0.0,
                generation_time=0.0,
                error=f"Generator init failed: {e}"
            )
        
        # 构建提示词
        if with_constraints:
            prompt = self.injector.inject(task_spec)
        else:
            prompt = f"实现以下功能：{task_spec.description}\n函数签名：{task_spec.function_signature}"
        
        # 生成代码
        start_time = time.time()
        result = generator.generate(
            task_spec={
                "name": task_spec.name,
                "description": prompt,
                "function_signature": task_spec.function_signature
            },
            previous_code=None
        )
        gen_time = time.time() - start_time
        
        if not result["success"]:
            return TaskResult(
                task_name=task_spec.name,
                attempt=0,
                success=False,
                function_name_correct=False,
                score=0.0,
                generation_time=gen_time,
                error="Generation failed"
            )
        
        code = result["code"]
        
        # 验证函数名
        expected_name = task_spec.function_name
        is_valid, details = self.validator._check_function_signature(code)
        func_name_correct = is_valid and details.get("actual_name") == expected_name
        
        # 运行测试
        test_code = self.test_code_map.get(task_spec.name, "")
        if test_code:
            test_result = self.validator._run_test(code, self.test_runner, test_code)
            score = test_result["pass_rate"]
        else:
            score = 1.0 if func_name_correct else 0.0
        
        return TaskResult(
            task_name=task_spec.name,
            attempt=0,
            success=func_name_correct and score >= 0.9,
            function_name_correct=func_name_correct,
            score=score,
            generation_time=gen_time,
            error="" if func_name_correct else f"Function name mismatch"
        )
    
    def run_experiment(self):
        """运行完整实验"""
        
        print("="*70)
        print("Phase 1.5: Constraints Validation Experiment")
        print("="*70)
        print(f"Start: {datetime.now().isoformat()}")
        print()
        
        # 准备任务
        tasks = [
            create_calculator_task(),
            create_list_sort_task(),
            create_json_parser_task(),
        ]
        
        results_with = []
        results_without = []
        
        # 测试：有约束注入
        print("\n[Phase A] Testing WITH constraints injection...")
        print("-"*70)
        
        for task in tasks:
            print(f"\nTask: {task.name}")
            for attempt in range(3):
                result = self.run_task(task, with_constraints=True)
                result.attempt = attempt + 1
                results_with.append(result)
                status = "PASS" if result.success else "FAIL"
                print(f"  Attempt {attempt+1}: {status} (func_name: {result.function_name_correct}, score: {result.score:.0%})")
                time.sleep(1)  # 避免API限流
        
        # 测试：无约束注入
        print("\n[Phase B] Testing WITHOUT constraints injection...")
        print("-"*70)
        
        for task in tasks:
            print(f"\nTask: {task.name}")
            for attempt in range(2):  # 减少次数节省API
                result = self.run_task(task, with_constraints=False)
                result.attempt = attempt + 1
                results_without.append(result)
                status = "PASS" if result.success else "FAIL"
                print(f"  Attempt {attempt+1}: {status} (func_name: {result.function_name_correct}, score: {result.score:.0%})")
                time.sleep(1)
        
        # 打印报告
        self._print_report(results_with, results_without)
    
    def _print_report(self, results_with: List[TaskResult], results_without: List[TaskResult]):
        """打印实验报告"""
        
        print("\n" + "="*70)
        print("EXPERIMENT REPORT - Phase 1.5")
        print("="*70)
        
        # 统计数据
        def calc_stats(results: List[TaskResult]):
            total = len(results)
            success = sum(1 for r in results if r.success)
            func_correct = sum(1 for r in results if r.function_name_correct)
            avg_score = sum(r.score for r in results) / total if total else 0
            return {
                "total": total,
                "success": success,
                "func_correct": func_correct,
                "avg_score": avg_score
            }
        
        stats_with = calc_stats(results_with)
        stats_without = calc_stats(results_without)
        
        print("\nResults Comparison:")
        print("-"*70)
        print(f"{'Metric':<30} {'With Constraints':<20} {'Without':<20}")
        print("-"*70)
        print(f"{'Total attempts':<30} {stats_with['total']:<20} {stats_without['total']:<20}")
        print(f"{'Success rate':<30} {stats_with['success']/stats_with['total']:.1%}              {stats_without['success']/stats_without['total']:.1%}")
        print(f"{'Function name correct':<30} {stats_with['func_correct']/stats_with['total']:.1%}              {stats_without['func_correct']/stats_without['total']:.1%}")
        print(f"{'Average score':<30} {stats_with['avg_score']:.1%}              {stats_without['avg_score']:.1%}")
        print("-"*70)
        
        # 目标达成检查
        print("\nPhase 1.5 Goals Check:")
        print("-"*70)
        
        func_violation_rate = 1 - stats_with['func_correct'] / stats_with['total']
        first_pass_rate = stats_with['success'] / stats_with['total']
        
        goals = [
            ("Constraint violation rate < 5%", func_violation_rate < 0.05),
            ("First-pass success rate > 90%", first_pass_rate > 0.9),
        ]
        
        for goal, achieved in goals:
            status = "[PASS]" if achieved else "[FAIL]"
            print(f"{status} {goal}")
        
        print()
        print("="*70)


if __name__ == "__main__":
    experiment = ConstraintsValidationExperiment()
    experiment.run_experiment()
