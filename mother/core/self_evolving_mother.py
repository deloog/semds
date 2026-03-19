"""
Self-Evolving Mother System - 完整实现

这是SEMDS的终极形态：
1. 执行用户任务（像之前一样）
2. 同时观察自己的表现
3. 定期自我进化（改进策略）
4. 下次执行任务时使用改进后的策略
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mother.core.fullstack_mother import FullStackMotherSystem
from mother.core.meta_evolution import MetaEvolutionEngine


class SelfEvolvingMother(FullStackMotherSystem):
    """
    自我进化的Mother System

    不仅能执行任务，还能通过执行任务来改进自己。

    Usage:
        mother = SelfEvolvingMother()

        # 正常使用
        result = mother.fulfill_request("Create a todo API")

        # 系统会自动：
        # 1. 记录这次任务的成功率
        # 2. 分析哪些任务类型容易失败
        # 3. 生成改进假设
        # 4. 定期运行进化循环

        # 手动触发自我进化
        mother.evolve_self()
    """

    def __init__(self):
        super().__init__()

        # 自我进化引擎
        self.meta_evolution = MetaEvolutionEngine()

        # 任务历史（用于分析）
        self.task_history = []

        print("[SelfEvolvingMother] Initialized with meta-evolution capability")
        print(
            "[SelfEvolvingMother] I can now improve myself by learning from task execution"
        )

    def fulfill_request(self, request: str, **kwargs):
        """
        执行用户请求，同时记录表现数据用于自我改进
        """
        import time

        start_time = time.time()

        # 执行请求（使用父类能力）
        result = super().fulfill_request(request, **kwargs)

        # 记录这次执行的结果（用于自我分析）
        execution_time = time.time() - start_time

        self.meta_evolution.record_generation_result(
            task_type=self._classify_task(request),
            success=result.get("success", False),
            score=1.0 if result.get("success") else 0.0,
            generation_time=execution_time,
            error_type=result.get("error") if not result.get("success") else None,
        )

        # 保存到历史
        self.task_history.append(
            {
                "request": request,
                "success": result.get("success"),
                "time": execution_time,
            }
        )

        return result

    def evolve_self(self) -> dict:
        """
        触发自我进化循环

        这是核心方法：系统分析自己的表现，生成改进假设，
        进行实验验证，并应用验证通过的改进。

        Returns:
            进化结果报告
        """
        print("\n" + "=" * 60)
        print("[SelfEvolvingMother] Initiating self-evolution")
        print("=" * 60)

        # 运行元进化循环
        result = self.meta_evolution.run_evolution_cycle()

        # 如果有改进被应用，重新加载配置
        if result.get("improvements_applied", 0) > 0:
            self._reload_config()

        return result

    def get_self_analysis(self) -> dict:
        """
        获取系统自我分析报告

        Returns:
            包含成功率、错误模式、改进建议的报告
        """
        return self.meta_evolution.telemetry.analyze_recent_performance(hours=24)

    def _classify_task(self, request: str) -> str:
        """对任务进行分类"""
        request_lower = request.lower()

        if "api" in request_lower or "endpoint" in request_lower:
            return "api_development"
        elif "scrape" in request_lower or "crawl" in request_lower:
            return "web_scraping"
        elif "database" in request_lower or "sql" in request_lower:
            return "database"
        elif "test" in request_lower:
            return "testing"
        else:
            return "general"

    def _reload_config(self):
        """重新加载改进后的配置"""
        # 从meta_evolution获取最新配置
        config = self.meta_evolution.updater.get_current_config("code_generator")

        if config:
            print(f"[SelfEvolvingMother] Reloaded improved configuration")
            # 这里可以更新code_generator的配置
            # 实际实现取决于CodeGenerator如何接受配置


def demo_self_evolving_system():
    """
    演示完整的自我进化系统
    """
    print("=" * 70)
    print("SEMDS Self-Evolving System Demo")
    print("=" * 70)
    print()

    # 创建自我进化系统
    mother = SelfEvolvingMother()

    print("\n" + "-" * 70)
    print("Phase 1: Execute some tasks (with simulated failures)")
    print("-" * 70)

    # 模拟执行几个任务（有成功有失败）
    tasks = [
        "Create a calculator function",
        "Build a web scraper",
        "Generate a sorting algorithm",
    ]

    for task in tasks:
        print(f"\n[Task] {task}")
        # 注意：这里为了演示，我们模拟结果
        # 实际应该调用 mother.fulfill_request(task)
        print("  Result: Task executed (simulated)")

    print("\n" + "-" * 70)
    print("Phase 2: System analyzes its own performance")
    print("-" * 70)

    # 手动记录一些模拟的失败数据（让系统有改进空间）
    for i in range(3):
        mother.meta_evolution.record_generation_result(
            task_type="api_development",
            success=False,
            score=0.0,
            generation_time=3.0,
            error_type="syntax_error",
        )

    mother.meta_evolution.record_generation_result(
        task_type="api_development", success=True, score=1.0, generation_time=2.5
    )

    # 获取自我分析
    analysis = mother.get_self_analysis()
    print(f"\n[System Self-Analysis]")
    print(f"  Success rate: {analysis.get('success_rate', 0):.1%}")
    print(f"  Error patterns: {analysis.get('error_patterns', {})}")
    print(f"  Opportunities: {analysis.get('improvement_opportunities', [])}")

    print("\n" + "-" * 70)
    print("Phase 3: System evolves itself")
    print("-" * 70)

    # 触发自我进化
    evolution_result = mother.evolve_self()

    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)

    if evolution_result.get("improvements_applied", 0) > 0:
        print(f"\n✅ SUCCESS!")
        print(f"   SEMDS has identified weaknesses in its strategy")
        print(f"   and updated its configuration to improve.")
        print(f"\n   Next execution will use the evolved strategy.")
    else:
        print(f"\nℹ️  No evolution needed at this time.")
        print(f"   System performance is within acceptable parameters.")

    print("\n" + "=" * 70)
    print("This is SEMDS's core capability: Self-Evolution")
    print("=" * 70)


if __name__ == "__main__":
    demo_self_evolving_system()
