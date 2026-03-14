"""
Evolution Orchestrator 模块 - 进化流程编排器

协调所有组件完成完整的进化循环：
1. 代码生成（CodeGenerator）
2. 测试执行（TestRunner）
3. 质量评估（DualEvaluator）
4. 策略优化（StrategyOptimizer）
5. 终止检测（TerminationChecker）
6. 版本控制（GitManager）

生成最终进化报告。
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.git_manager import GitManager
from evolution.code_generator import CodeGenerator
from evolution.dual_evaluator import DualEvaluator
from evolution.strategy_optimizer import StrategyOptimizer
from evolution.termination_checker import (
    TerminationChecker,
    TerminationConfig,
)
from evolution.test_runner import TestRunner


def extract_function_signature(code: str) -> str:
    """
    从代码中提取函数签名。
    
    查找第一个函数定义的签名，如 "def add(a, b)" -> "add(a, b)"
    
    Args:
        code: Python 代码字符串
        
    Returns:
        函数签名字符串，如果没有找到则返回 "solution()"
    """
    if not code:
        return "solution()"
    
    # 匹配函数定义: def function_name(args) -> return_type:
    pattern = r'def\s+(\w+)\s*\(([^)]*)\)'
    match = re.search(pattern, code)
    
    if match:
        func_name = match.group(1)
        args = match.group(2).strip()
        return f"{func_name}({args})"
    
    return "solution()"


@dataclass
class GenerationResult:
    """单代进化结果"""

    generation: int
    code: str
    score: float
    strategy: Dict[str, Any]
    passed_tests: bool
    evaluation_report: Optional[Dict[str, Any]] = None


@dataclass
class EvolutionResult:
    """完整进化结果"""

    generations: int
    best_score: float
    best_code: str
    success: bool
    termination_reason: str
    history: List[GenerationResult] = field(default_factory=list)


class EvolutionOrchestrator:
    """进化编排器

    协调所有组件完成代码进化任务。

    Example:
        >>> orchestrator = EvolutionOrchestrator(task_id="calculator")
        >>> result = orchestrator.evolve(
        ...     requirements=["Write add function"],
        ...     test_code="assert add(1,2)==3",
        ...     max_generations=50
        ... )
        >>> print(f"Best score: {result.best_score}")
    """

    def __init__(
        self,
        task_id: str,
        code_generator: CodeGenerator = None,
        test_runner: TestRunner = None,
        dual_evaluator: DualEvaluator = None,
        strategy_optimizer: StrategyOptimizer = None,
        termination_checker: TerminationChecker = None,
        git_manager: GitManager = None,
        termination_config: TerminationConfig = None,
    ):
        """初始化编排器

        Args:
            task_id: 任务唯一标识
            code_generator: 代码生成器
            test_runner: 测试运行器
            dual_evaluator: 双轨评估器
            strategy_optimizer: 策略优化器
            termination_checker: 终止检查器
            git_manager: Git管理器
            termination_config: 终止条件配置
        """
        self.task_id = task_id
        self.code_generator = code_generator or CodeGenerator()
        self.test_runner = test_runner or TestRunner()
        self.dual_evaluator = dual_evaluator or DualEvaluator()
        self.strategy_optimizer = strategy_optimizer or StrategyOptimizer(task_id)
        self.termination_checker = termination_checker or TerminationChecker(
            termination_config
        )
        self.git_manager = git_manager

        # 进化状态
        self.history: List[GenerationResult] = []
        self.best_score: float = 0.0
        self.best_code: str = ""
        self.current_generation: int = 0

    def evolve(
        self,
        requirements: List[str],
        test_code: str,
        max_generations: int = None,
    ) -> EvolutionResult:
        """运行完整进化过程

        Args:
            requirements: 功能需求描述列表
            test_code: 测试代码
            max_generations: 最大代数（覆盖配置）

        Returns:
            EvolutionResult: 进化结果
        """
        # 设置最大代数
        if max_generations is not None:
            self.termination_checker.config.max_generations = max_generations

        # 进化循环
        while True:
            self.current_generation += 1

            # 运行单代
            gen_result = self.run_single_generation(
                generation=self.current_generation,
                requirements=requirements,
                test_code=test_code,
            )

            # 存储历史
            self.history.append(gen_result)

            # 更新最佳
            if gen_result.score > self.best_score:
                self.best_score = gen_result.score
                self.best_code = gen_result.code

            # 检查终止条件
            decision = self.termination_checker.check(
                current_gen=self.current_generation,
                current_score=self.best_score,
            )

            if decision.should_terminate:
                return EvolutionResult(
                    generations=self.current_generation,
                    best_score=self.best_score,
                    best_code=self.best_code,
                    success=decision.is_success,
                    termination_reason=decision.reason,
                    history=self.history,
                )

            # 报告结果给策略优化器
            self.report_generation_result(gen_result, success=gen_result.passed_tests)

    def run_single_generation(
        self,
        generation: int,
        requirements: List[str],
        test_code: str,
    ) -> GenerationResult:
        """运行单代进化

        Args:
            generation: 当前代数
            requirements: 功能需求
            test_code: 测试代码

        Returns:
            GenerationResult: 代结果
        """
        # 1. 选择策略
        strategy = self.strategy_optimizer.select_strategy()

        # 2. 生成代码
        try:
            # 构建 task_spec 字典
            task_spec = {
                "description": "Implement solution based on requirements",
                "function_signature": "def solution():",
                "requirements": requirements,
            }
            
            gen_result = self.code_generator.generate(
                task_spec=task_spec,
                temperature=strategy.get("generation_temperature", 0.5),
            )
            # 从返回字典中提取代码
            code = gen_result.get("code", "") if isinstance(gen_result, dict) else str(gen_result)
        except Exception as e:
            # 生成失败返回空代码
            print(f"Code generation error: {e}")
            code = ""

        # 3. 运行测试
        try:
            test_result = self.test_runner.run_tests_with_code(code, test_code)
            passed_tests = (
                len(test_result.get("passed", [])) > 0 
                and len(test_result.get("failed", [])) == 0
            )
        except Exception as e:
            print(f"Test execution error: {e}")
            passed_tests = False

        # 4. 评估质量
        try:
            # 从代码中提取实际函数签名
            func_signature = extract_function_signature(code)
            evaluation = self.dual_evaluator.evaluate(
                code=code,
                function_signature=func_signature,
                requirements=requirements,
            )
            score = evaluation.get("final_score", 0.0)
        except Exception as e:
            print(f"Evaluation error: {e}")
            score = 0.0
            evaluation = None

        # 5. Git提交（如果配置了）
        if self.git_manager and code:
            try:
                self._commit_generation(generation, code, score)
            except Exception:
                pass  # Git提交失败不影响进化

        return GenerationResult(
            generation=generation,
            code=code,
            score=score,
            strategy=strategy,
            passed_tests=passed_tests,
            evaluation_report=evaluation,
        )

    def report_generation_result(self, result: GenerationResult, success: bool) -> None:
        """报告代结果给策略优化器

        Args:
            result: 代结果
            success: 是否成功
        """
        self.strategy_optimizer.report_result(
            strategy=result.strategy,
            success=success,
            score=result.score,
        )

    def _commit_generation(
        self, generation: int, code: str, score: float
    ) -> Optional[str]:
        """提交到Git

        Args:
            generation: 代数
            code: 代码
            score: 得分

        Returns:
            提交hash或None
        """
        if not self.git_manager:
            return None

        # 写入临时文件并提交
        # 简化为直接提交（实际应该写入文件）
        try:
            commit_hash = self.git_manager.commit_generation(
                task_id=self.task_id,
                gen_number=generation,
                file_path="solution.py",
                score=score,
            )
            return commit_hash
        except Exception:
            return None
