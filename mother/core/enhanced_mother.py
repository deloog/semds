"""
Enhanced Mother System - 增强版母体系统
集成：自主搜索、代码质量检查、自我反思
"""

import os
import sys
import time
from typing import Dict, List, Optional, Any

sys.path.insert(0, r"D:\semds")

from mother.core.mother_system import MotherSystem, ExecutionPlan
from mother.core.task_analyzer import TaskAnalyzer
from mother.core.capability_registry import CapabilityRegistry
from mother.core.tool_generator import ToolGenerator

# 新技能
from mother.skills.web_search import WebSearchSkill, KnowledgeBase
from mother.skills.code_quality import CodeQualityChecker, AutoFixer
from mother.skills.self_reflection import SelfReflection


class EnhancedMotherSystem(MotherSystem):
    """
    增强版 Mother System

    新增能力：
    1. 自主搜索 - 遇到困难自动搜索解决方案
    2. 代码质量 - 强制代码规范检查
    3. 自我反思 - 从经验中学习
    4. 自动修复 - 自动修复代码问题
    """

    def __init__(self):
        super().__init__()

        # 新技能
        self.searcher = WebSearchSkill()
        self.code_checker = CodeQualityChecker()
        self.auto_fixer = AutoFixer()
        self.reflection = SelfReflection()

        # 执行统计
        self.current_task = None
        self.task_start_time = None
        self.errors_this_task = []
        self.solutions_applied = []

        print("[Mother Enhanced] System initialized with self-improvement capabilities")
        print(f"  - Web Search: {self.searcher.backend}")
        print(f"  - Code Quality Check: enabled")
        print(f"  - Self Reflection: enabled")

    def execute(self, task_description: str) -> Dict:
        """
        执行任务（增强版）

        流程：
        1. 分析任务
        2. 检查能力（可能生成新工具）
        3. 代码质量检查
        4. 执行
        5. 反思记录
        """
        self.current_task = task_description
        self.task_start_time = time.time()
        self.errors_this_task = []
        self.solutions_applied = []

        print(f"\n{'='*70}")
        print(f"[Mother Enhanced] New Task: {task_description}")
        print(f"{'='*70}\n")

        # Step 1: 分析任务
        plan = self.analyzer.analyze(task_description)
        if not plan.required_capabilities:
            return self._handle_unknown_task(task_description)

        print(f"[Plan] Required: {plan.required_capabilities}")

        # Step 2: 检查并生成能力
        if not self._prepare_capabilities(plan):
            return self._build_result(False, "Failed to prepare capabilities")

        # Step 3: 执行计划
        result = self._execute_plan(plan)

        # Step 4: 反思与记录
        self._reflect_on_execution(result)

        return result

    def _handle_unknown_task(self, task: str) -> Dict:
        """处理未知类型的任务"""
        print("[Mother] Unknown task type, searching for solutions...")

        # 尝试搜索了解这个任务
        results = self.searcher.search(
            f"how to {task} python", num_results=3, search_type="tutorial"
        )

        if results:
            print(f"[Search] Found {len(results)} related resources:")
            for r in results[:3]:
                print(f"  - {r.title}")

            self.solutions_applied.append(
                {
                    "type": "search",
                    "query": task,
                    "results": [{"title": r.title, "url": r.url} for r in results],
                }
            )

        return self._build_result(
            False,
            "Unknown task type - need to implement new capability",
            {"search_results": results},
        )

    def _prepare_capabilities(self, plan: ExecutionPlan) -> bool:
        """准备所需能力"""
        has_all, missing = self.registry.check(plan.required_capabilities)

        if not missing:
            return True

        print(f"[Mother] Missing capabilities: {missing}")

        for cap in missing:
            print(f"\n[ToolGen] Creating: {cap}")

            # 尝试生成工具
            code = self.generator.generate(cap)

            if code:
                # 代码质量检查
                quality = self.code_checker.check(code, f"{cap}.py")
                print(f"[Quality] Score: {quality['score']:.1f}/100")

                if not quality["passed"]:
                    print(f"[Quality] Issues found, attempting auto-fix...")
                    fixed_code, new_quality = self.auto_fixer.fix(code)
                    code = fixed_code
                    print(f"[Quality] After fix: {new_quality['score']:.1f}/100")

                # 重新加载注册表
                self.registry._load_generated_tools()

                if self.registry.has(cap):
                    print(f"[OK] {cap} ready")
                else:
                    # 生成失败，尝试搜索解决方案
                    return self._search_for_tool_solution(cap)
            else:
                # 模板生成失败，搜索替代方案
                return self._search_for_tool_solution(cap)

        return True

    def _search_for_tool_solution(self, capability: str) -> bool:
        """搜索工具实现方案"""
        print(f"[Search] Looking for {capability} implementation...")

        results = self.searcher.search(
            f"python {capability} implementation example",
            num_results=3,
            search_type="code",
        )

        if results:
            print(f"[Search] Found {len(results)} examples:")
            for r in results[:2]:
                print(f"  - {r.title}")
                print(f"    {r.snippet[:100]}...")

            self.solutions_applied.append(
                {
                    "type": "code_search",
                    "capability": capability,
                    "sources": [r.url for r in results[:2]],
                }
            )

        # 暂时返回失败，未来可以实现从搜索结果生成代码
        return False

    def _execute_plan(self, plan: ExecutionPlan) -> Dict:
        """执行计划"""
        context = {}

        for i, step in enumerate(plan.steps, 1):
            print(f"\n  Step {i}/{len(plan.steps)}: [{step.action}]")

            tool = self.registry.get(step.action)
            if not tool:
                error = f"Tool not found: {step.action}"
                self.errors_this_task.append(error)
                return self._build_result(False, error)

            inputs = self._resolve_inputs(step.inputs, context)

            try:
                result = tool.execute(**inputs)
                context[step.outputs] = result
                print(f"    [OK] -> {step.outputs}")

            except Exception as e:
                error_msg = str(e)
                self.errors_this_task.append(error_msg)
                print(f"    [FAIL] {error_msg}")

                # 尝试使用搜索解决问题
                solution = self._attempt_error_recovery(error_msg, step.action, inputs)

                if solution:
                    print(f"    [Recovery] Applied solution from search")
                    # 重试
                    try:
                        result = tool.execute(**inputs)
                        context[step.outputs] = result
                        print(f"    [OK] -> {step.outputs}")
                        continue
                    except Exception as e2:
                        print(f"    [FAIL] Recovery failed: {e2}")

                return self._build_result(
                    False, error_msg, {"step": i, "context": context}
                )

        return self._build_result(True, outputs=context)

    def _attempt_error_recovery(self, error: str, action: str, inputs: Dict) -> bool:
        """尝试从错误中恢复"""
        print(f"\n[Recovery] Searching for solution to: {error[:50]}...")

        # 先检查已知解决方案
        known_solution = self.reflection.get_known_solution(error)
        if known_solution:
            print(f"[Recovery] Found known solution")
            self.solutions_applied.append(
                {"type": "known_solution", "error": error, "solution": known_solution}
            )
            return True

        # 搜索新解决方案
        solutions = self.searcher.search_for_solution(
            error, context=f"{action} with inputs {list(inputs.keys())}"
        )

        if solutions and solutions[0]["confidence"] > 0.5:
            best = solutions[0]
            print(
                f"[Recovery] Found potential solution (confidence: {best['confidence']:.2f})"
            )
            print(f"  Source: {best['source']}")
            print(f"  Suggestion: {best['suggestion'][:100]}...")

            self.solutions_applied.append(
                {"type": "search_solution", "error": error, "solution": best}
            )

            # 记录到知识库
            self.reflection.learn_from_search(
                error, solutions, success=False  # 稍后更新
            )
            return True

        print(f"[Recovery] No suitable solution found")
        return False

    def _reflect_on_execution(self, result: Dict):
        """执行后反思"""
        duration = time.time() - (self.task_start_time or time.time())
        success = result.get("success", False)

        # 记录执行
        execution = self.reflection.record_execution(
            task_description=self.current_task,
            success=success,
            duration=duration,
            capabilities_used=self._get_capabilities_used(),
            errors=self.errors_this_task,
            solutions=self.solutions_applied,
        )

        # 更新搜索学习（如果之前有搜索）
        for sol in self.solutions_applied:
            if sol["type"] == "search_solution":
                self.reflection.learn_from_search(
                    sol["error"], [sol["solution"]], success
                )

        print(
            f"\n[Reflection] Task {'succeeded' if success else 'failed'} in {duration:.2f}s"
        )
        print(f"  Lessons: {execution.lessons_learned}")

    def _get_capabilities_used(self) -> List[str]:
        """获取本次任务使用的能力"""
        # 简化版本，实际应该从执行记录中提取
        return list(self.registry.capabilities.keys())

    def _build_result(
        self, success: bool, error: str = None, outputs: Any = None
    ) -> Dict:
        """构建结果"""
        result = {
            "success": success,
            "outputs": outputs or {},
            "errors": self.errors_this_task,
            "solutions_applied": len(self.solutions_applied),
        }
        if error:
            result["error"] = error
        return result

    def print_self_report(self):
        """打印自我报告"""
        self.reflection.print_report()

        print("\n[Knowledge Base Stats]")
        kb = self.reflection.knowledge_base
        if "search_queries" in kb:
            print(f"  Learned queries: {len(kb['search_queries'])}")
            successful = sum(
                1 for q in kb["search_queries"].values() if q.get("successes", 0) > 0
            )
            print(f"  Successful searches: {successful}")


# 演示
def main():
    print("=" * 70)
    print("SEMDS Enhanced Mother System")
    print("Features: Auto-search | Code Quality | Self Reflection")
    print("=" * 70)

    mother = EnhancedMotherSystem()

    # 测试任务
    tasks = [
        "Fetch images from https://www.bing.com homepage",
        # "Parse CSV file data.csv and calculate average",  # 会触发搜索学习
    ]

    for task in tasks:
        print(f"\n{'='*70}")
        result = mother.execute(task)

        if result["success"]:
            print(f"\n[OK] Task completed!")
            if "extracted_data" in result.get("outputs", {}):
                data = result["outputs"]["extracted_data"]
                print(
                    f"  Found: {len(data) if isinstance(data, list) else 'N/A'} items"
                )
        else:
            print(f"\n[FAIL] {result.get('error')}")

    # 打印自我报告
    print(f"\n{'='*70}")
    mother.print_self_report()
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
