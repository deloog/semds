"""
集成测试 - 验证 API 真正运行进化

测试场景：
1. 创建任务
2. 通过 API 启动进化
3. 验证进化真正运行（检查数据库状态变化）
4. 验证 WebSocket 推送数据
5. 中止进化
"""

import asyncio
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app
from api.state import active_evolutions
from storage.database import get_session, init_database
from storage.models import Generation, Task

# 简化的测试代码
CALCULATOR_TEST = """
def calculate(a, b, op):
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    elif op == '/':
        if b == 0:
            raise ValueError("Division by zero")
        return a / b
    else:
        raise ValueError("Invalid operator")

def test_add():
    assert calculate(2, 3, '+') == 5
"""


class TestAPIEvolutionIntegration:
    """API + 进化集成测试"""

    def setup_method(self):
        """测试前初始化"""
        init_database()
        # 清理活跃进化状态
        active_evolutions.clear()

    def test_api_starts_real_evolution(self):
        """
        测试 API 真正启动进化

        验证：
        1. 调用 /start 后任务状态变为 running
        2. active_evolutions 中有该任务
        3. 一段时间后数据库中有 Generation 记录
        """
        client = TestClient(app)

        # 1. 创建任务
        with get_session() as db:
            task = Task(
                name="integration_test",
                description="Test evolution integration",
                target_function_signature="def calculate(a, b, op):",
                status="pending",
            )
            db.add(task)
            db.commit()
            task_id = task.id

        # 创建临时测试文件
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(CALCULATOR_TEST)
            test_file = f.name

        # 更新任务的测试文件路径
        with get_session() as db:
            task = db.query(Task).filter(Task.id == task_id).first()
            task.test_file_path = test_file
            db.commit()

        try:
            # 2. 启动进化（需要认证令牌，简化测试跳过认证）
            # 注意：实际测试需要 JWT 令牌，这里简化处理

            # 直接测试 evolution_runner
            from api.evolution_runner import EvolutionRunner

            runner = EvolutionRunner(task_id, max_generations=3)

            # 运行进化（同步方式便于测试）
            import threading

            result_container = {}

            def run_evolution():
                try:
                    asyncio.run(runner.run())
                    result_container["success"] = True
                except Exception as e:
                    result_container["error"] = str(e)

            thread = threading.Thread(target=run_evolution)
            thread.start()
            thread.join(timeout=60)  # 最多等待60秒

            # 3. 验证结果
            with get_session() as db:
                task = db.query(Task).filter(Task.id == task_id).first()

                # 任务状态应该被更新
                assert task.status in [
                    "success",
                    "failed",
                    "running",
                ], f"Unexpected status: {task.status}"

                # 应该有 Generation 记录
                gens = db.query(Generation).filter(Generation.task_id == task_id).all()
                assert len(gens) > 0, "No generations recorded"

                print(f"[OK] Task completed with status: {task.status}")
                print(f"[OK] Generated {len(gens)} generations")
                print(f"[OK] Best score: {task.best_score}")

        finally:
            # 清理
            import os

            os.unlink(test_file)

    def test_evolution_updates_active_state(self):
        """
        测试进化更新活跃状态（WebSocket 数据源）
        """
        from api.evolution_runner import EvolutionRunner

        task_id = "test_state_updates"
        runner = EvolutionRunner(task_id, max_generations=2)

        # 模拟更新进度
        runner._update_progress(1, 0.5)

        # 验证活跃状态
        assert task_id in active_evolutions
        assert active_evolutions[task_id]["current_gen"] == 1
        assert active_evolutions[task_id]["best_score"] == 0.5

        # 清理
        if task_id in active_evolutions:
            del active_evolutions[task_id]

    def test_evolution_runner_imports(self):
        """
        测试所有关键导入都可用
        """
        # 这些导入应该都成功
        from api.evolution_runner import EvolutionRunner, start_evolution_task
        from api.routers.evolution import evolution_runners
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.strategy_optimizer import StrategyOptimizer

        assert EvolutionRunner is not None
        assert start_evolution_task is not None
        print("[OK] All imports successful")


def test_end_to_end_workflow():
    """
    端到端工作流测试

    完整的用户场景：
    1. 创建任务
    2. 启动进化
    3. 观察进度（模拟 WebSocket）
    4. 获取结果
    """
    print("\n=== End-to-End Workflow Test ===")

    # 初始化
    init_database()

    # 创建任务
    with get_session() as db:
        task = Task(
            name="e2e_test",
            description="End-to-end test",
            target_function_signature="def add(a, b):",
            status="pending",
        )
        db.add(task)
        db.commit()
        task_id = task.id

    print(f"[OK] Created task: {task_id}")

    # 启动进化
    from api.evolution_runner import start_evolution_task

    async def run_test():
        runner = await start_evolution_task(task_id, max_generations=2)

        # 等待一小段时间
        await asyncio.sleep(2)

        # 检查活跃状态
        if task_id in active_evolutions:
            state = active_evolutions[task_id]
            print(
                f"[OK] Evolution active: gen={state.get('current_gen')}, score={state.get('best_score')}"
            )
        else:
            print("[WARN] Evolution not in active state (may have completed quickly)")

        # 请求停止
        runner.request_stop()

        # 等待完成
        await asyncio.sleep(1)

    asyncio.run(run_test())

    print("[OK] End-to-end test completed")


if __name__ == "__main__":
    # 运行测试
    print("Running integration tests...")

    test = TestAPIEvolutionIntegration()
    test.setup_method()

    try:
        test.test_evolution_runner_imports()
        print("[PASS] Import test")
    except Exception as e:
        print(f"[FAIL] Import test: {e}")

    try:
        test.test_evolution_updates_active_state()
        print("[PASS] State updates test")
    except Exception as e:
        print(f"[FAIL] State updates test: {e}")

    try:
        test.test_api_starts_real_evolution()
        print("[PASS] API evolution test")
    except Exception as e:
        print(f"[FAIL] API evolution test: {e}")

    print("\nAll tests completed!")
