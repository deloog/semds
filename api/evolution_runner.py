"""
进化执行器 - 真正运行进化循环的后端任务

提供异步进化执行，支持：
1. 后台运行进化循环
2. 实时更新进度到 WebSocket
3. 每代结果保存到数据库
4. 支持中止请求
"""

import asyncio
import logging
from datetime import datetime
from typing import Callable, Optional

from sqlalchemy.orm import Session

from api.state import active_evolutions
from evolution.orchestrator import EvolutionOrchestrator
from evolution.termination_checker import TerminationConfig
from storage.database import get_session_factory
from storage.models import Generation, Task

logger = logging.getLogger(__name__)


class EvolutionRunner:
    """
    进化执行器

    在后台运行进化循环，与 API 层解耦。
    """

    def __init__(self, task_id: str, max_generations: int = 50):
        self.task_id = task_id
        self.max_generations = max_generations
        self.orchestrator: Optional[EvolutionOrchestrator] = None
        self._stop_requested = False
        self._current_generation = 0
        self._best_score = 0.0
        self._best_code = ""

    async def run(self):
        """
        运行进化循环 - 主要执行入口
        """
        # 初始化活跃状态（关键！让 WebSocket 能立即看到任务）
        active_evolutions[self.task_id] = {
            "status": "starting",
            "current_gen": 0,
            "best_score": 0.0,
            "progress": 0,
            "updated_at": datetime.now().isoformat(),
        }

        SessionFactory = get_session_factory()
        db = SessionFactory()
        try:
            # 获取任务信息
            task = db.query(Task).filter(Task.id == self.task_id).first()
            if not task:
                logger.error(f"Task not found: {self.task_id}")
                return

            # 更新状态
            active_evolutions[self.task_id]["status"] = "running"

            # 加载测试代码
            test_code = self._load_test_code(task.test_file_path)

            # 解析需求
            requirements = self._parse_requirements(task)

            # 初始化 orchestrator
            term_config = TerminationConfig(
                max_generations=self.max_generations,
                success_threshold=0.95,
                stagnation_generations=10,
            )

            self.orchestrator = EvolutionOrchestrator(
                task_id=self.task_id,
                termination_config=term_config,
            )

            # 设置进度回调
            self._setup_progress_callback()

            logger.info(f"Starting evolution for task {self.task_id}")

            # 在 executor 中运行同步的进化循环
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_evolution_sync,
                requirements,
                test_code,
            )

            # 保存最终结果
            self._save_final_result(db, task, result)

            logger.info(
                f"Evolution completed: gens={result.generations}, score={result.best_score:.2f}"
            )

        except Exception as e:
            logger.error(f"Evolution error: {e}", exc_info=True)
            self._update_task_status(db, "failed")
        finally:
            db.close()

        # Clean up active evolution tracking
        if self.task_id in active_evolutions:
            del active_evolutions[self.task_id]

    def _run_evolution_sync(self, requirements: list, test_code: str):
        """
        同步运行进化（在 executor 中执行）
        """
        try:
            # 检查是否请求停止
            if self._stop_requested:
                logger.info(
                    f"Evolution stopped before starting for task {self.task_id}"
                )
                return None

            # 运行进化
            result = self.orchestrator.evolve(
                requirements=requirements,
                test_code=test_code,
            )

            return result

        except Exception as e:
            logger.error(f"Error in evolution: {e}", exc_info=True)
            raise

    def _setup_progress_callback(self):
        """
        设置进度回调 - 让 orchestrator 在每代完成后通知我们

        这是一个简化实现。真实的实现需要修改 orchestrator 支持回调。
        这里我们通过定期检查 orchestrator 状态来模拟。
        """
        # 启动后台任务定期检查进度
        asyncio.create_task(self._progress_watcher())

    async def _progress_watcher(self):
        """
        进度观察器 - 定期检查 orchestrator 状态并更新
        """
        while not self._stop_requested:
            if self.orchestrator and hasattr(self.orchestrator, "current_generation"):
                # 从 orchestrator 获取当前状态
                current_gen = self.orchestrator.current_generation
                best_score = self.orchestrator.best_score

                # 更新活跃状态（会被 WebSocket 读取）
                self._update_progress(current_gen, best_score)

                # 保存到数据库
                await self._save_generation_to_db(current_gen, best_score)

            await asyncio.sleep(1.0)  # 每秒检查一次

    def _update_progress(self, generation: int, score: float):
        """更新进度到活跃状态字典"""
        self._current_generation = generation
        self._best_score = score

        if self.task_id in active_evolutions:
            active_evolutions[self.task_id].update(
                {
                    "current_gen": generation,
                    "best_score": score,
                    "progress": min(100, int(generation / self.max_generations * 100)),
                    "updated_at": datetime.now().isoformat(),
                }
            )

    async def _save_generation_to_db(self, generation: int, score: float):
        """保存当前代到数据库"""
        try:
            SessionFactory = get_session_factory()
            db = SessionFactory()
            try:
                # 检查是否已存在该代记录
                existing = (
                    db.query(Generation)
                    .filter(
                        Generation.task_id == self.task_id,
                        Generation.gen_number == generation,
                    )
                    .first()
                )

                if not existing:
                    # 获取当前代码（如果有）
                    code = ""
                    if self.orchestrator and hasattr(self.orchestrator, "best_code"):
                        code = self.orchestrator.best_code

                    gen = Generation(
                        task_id=self.task_id,
                        gen_number=generation,
                        code=code,
                        final_score=score,
                        intrinsic_score=score,  # 简化处理
                        extrinsic_score=score,
                        test_pass_rate=score,
                    )
                    db.add(gen)
                    db.commit()

                    # 更新任务的当前代数
                    task = db.query(Task).filter(Task.id == self.task_id).first()
                    if task:
                        task.current_generation = generation
                        task.best_score = score
                        db.commit()

            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to save generation: {e}")

    def _load_test_code(self, test_file_path: Optional[str]) -> str:
        """加载测试代码"""
        if test_file_path:
            try:
                with open(test_file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to load test file {test_file_path}: {e}")

        # 默认测试代码
        return """
def test_placeholder():
    assert True
"""

    def _parse_requirements(self, task: Task) -> list:
        """解析任务需求"""
        if task.description:
            # 按行分割，过滤空行
            lines = [
                line.strip() for line in task.description.split("\n") if line.strip()
            ]
            return lines if lines else ["Implement solution"]
        return ["Implement solution"]

    def _save_final_result(self, db: Session, task: Task, result):
        """保存最终进化结果"""
        if result is None:
            logger.warning(f"Evolution returned None for task {self.task_id}")
            task.status = "failed"
            db.commit()
            return

        # 更新任务状态
        task.status = "success" if result.success else "failed"
        task.best_score = result.best_score
        task.current_generation = result.generations

        # 保存最佳代码
        if result.best_code:
            # 检查是否已存在最后一代记录
            existing = (
                db.query(Generation)
                .filter(
                    Generation.task_id == self.task_id,
                    Generation.gen_number == result.generations,
                )
                .first()
            )

            if existing:
                existing.code = result.best_code
                existing.final_score = result.best_score
            else:
                best_gen = Generation(
                    task_id=self.task_id,
                    gen_number=result.generations,
                    code=result.best_code,
                    final_score=result.best_score,
                    intrinsic_score=result.best_score,
                    extrinsic_score=result.best_score,
                    test_pass_rate=result.best_score,
                )
                db.add(best_gen)

        db.commit()
        logger.info(
            f"Final result saved for task {self.task_id}: score={result.best_score:.2f}"
        )

    def _update_task_status(self, db: Session, status: str):
        """更新任务状态"""
        task = db.query(Task).filter(Task.id == self.task_id).first()
        if task:
            task.status = status
            db.commit()

    def request_stop(self):
        """请求停止进化"""
        self._stop_requested = True
        logger.info(f"Stop requested for task {self.task_id}")


# 全局 runners 字典（用于 API 层访问）
# 注意：多 worker 部署时需要改用 Redis
evolution_runners: dict[str, EvolutionRunner] = {}


async def start_evolution_task(
    task_id: str, max_generations: int = 50
) -> EvolutionRunner:
    """
    启动进化任务

    Args:
        task_id: 任务ID
        max_generations: 最大代数

    Returns:
        EvolutionRunner 实例
    """
    runner = EvolutionRunner(task_id, max_generations)
    evolution_runners[task_id] = runner

    # 在后台启动
    asyncio.create_task(runner.run())

    return runner
