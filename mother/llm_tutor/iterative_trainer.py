"""
Iterative Trainer - 迭代训练器
实现"本地模型生成 -> SEMDS 检查 -> 反馈 -> 改进"的闭环
"""

import os
import sys
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

sys.path.insert(0, "D:\\semds")

from evolution.code_generator import CodeGenerator
from mother.skills.code_optimizer import CodeOptimizer
from mother.llm_tutor.few_shot_optimizer import FewShotOptimizer


@dataclass
class TrainingIteration:
    """训练迭代记录"""

    iteration: int
    local_model_output: str
    local_model_score: float
    semds_feedback: str
    improved_output: str
    improved_score: float


@dataclass
class TrainingSession:
    """训练会话"""

    session_id: str
    task: str
    iterations: List[TrainingIteration]
    final_score: float
    improvement: float  # 最终分数 - 初始分数


class IterativeTrainer:
    """
    迭代训练器

    流程：
    1. 本地模型（Ollama/Qwen）生成代码
    2. SEMDS 检查代码质量
    3. 如果分数低，生成具体反馈
    4. 本地模型根据反馈重新生成
    5. 循环直到质量达标或达到最大迭代次数

    目标：让本地模型学会如何写出符合原则的代码
    """

    def __init__(self):
        # 本地模型（学生）
        self.local_model = CodeGenerator(backend="ollama")
        # 代码优化器
        self.optimizer = CodeOptimizer()
        # Few-shot 优化器
        self.few_shot = FewShotOptimizer()
        # 训练记录
        self.training_db = "mother/llm_tutor/training_sessions.json"
        self.sessions = self._load_sessions()

    def _load_sessions(self) -> List[Dict]:
        """加载训练会话"""
        if os.path.exists(self.training_db):
            try:
                with open(self.training_db, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return []

    def _save_session(self, session: TrainingSession):
        """保存训练会话"""
        self.sessions.append(asdict(session))
        os.makedirs(os.path.dirname(self.training_db), exist_ok=True)
        with open(self.training_db, "w", encoding="utf-8") as f:
            json.dump(self.sessions, f, indent=2, ensure_ascii=False)

    def train(
        self,
        task: str,
        task_type: str = "general",
        max_iterations: int = 5,
        target_score: float = 80.0,
    ) -> TrainingSession:
        """
        训练本地模型完成特定任务

        Args:
            task: 任务描述
            task_type: 任务类型（用于 few-shot 示例）
            max_iterations: 最大迭代次数
            target_score: 目标质量分数

        Returns:
            训练会话记录
        """
        session_id = f"train_{int(time.time())}"
        iterations = []

        print(f"\n[Trainer] Starting training session: {session_id}")
        print(f"[Trainer] Task: {task}")
        print(f"[Trainer] Target score: {target_score}")

        # 获取增强后的提示
        enhanced_prompt = self.few_shot.get_prompt_for_ollama(task_type, task)

        for i in range(max_iterations):
            print(f"\n--- Iteration {i+1}/{max_iterations} ---")

            # 1. 本地模型生成代码
            if i == 0:
                # 第一次使用增强提示
                local_code = self._generate_with_local_model(task, enhanced_prompt)
            else:
                # 后续使用反馈改进
                feedback = iterations[-1]["feedback"]
                local_code = self._generate_with_feedback(task, local_code, feedback)

            # 2. 评估本地模型输出
            local_score = self._evaluate_code(local_code)
            print(f"[Trainer] Local model score: {local_score}/100")

            # 3. 检查是否达标
            if local_score >= target_score:
                print(f"[Trainer] Target reached! Stopping early.")
                iterations.append(
                    TrainingIteration(
                        iteration=i + 1,
                        local_model_output=local_code[:500],
                        local_model_score=local_score,
                        semds_feedback="Target reached",
                        improved_output=local_code[:500],
                        improved_score=local_score,
                    )
                )
                break

            # 4. SEMDS 生成反馈
            feedback = self._generate_feedback(local_code)
            print(f"[Trainer] Feedback: {feedback[:100]}...")

            # 5. 用强模型生成改进版本（作为参考）
            improved = self._generate_with_teacher(task, local_code, feedback)
            improved_score = self._evaluate_code(improved)
            print(f"[Trainer] Teacher model score: {improved_score}/100")

            iterations.append(
                TrainingIteration(
                    iteration=i + 1,
                    local_model_output=local_code[:500],
                    local_model_score=local_score,
                    semds_feedback=feedback,
                    improved_output=improved[:500],
                    improved_score=improved_score,
                )
            )

            # 记录学习示例
            self.few_shot.add_example(
                task_type=task_type,
                task_description=task,
                bad_code=local_code,
                good_code=improved,
                improvements=self._extract_improvements(local_code, improved),
            )

        # 计算改进
        initial_score = iterations[0].local_model_score if iterations else 0
        final_score = iterations[-1].local_model_score if iterations else 0
        improvement = final_score - initial_score

        session = TrainingSession(
            session_id=session_id,
            task=task,
            iterations=iterations,
            final_score=final_score,
            improvement=improvement,
        )

        self._save_session(session)

        print(f"\n[Trainer] Session complete")
        print(f"[Trainer] Initial score: {initial_score:.1f}")
        print(f"[Trainer] Final score: {final_score:.1f}")
        print(f"[Trainer] Improvement: {improvement:+.1f}")

        return session

    def _generate_with_local_model(self, task: str, prompt: str) -> str:
        """使用本地模型生成代码"""
        task_spec = {
            "description": f"{prompt}\n\nTask: {task}",
            "function_signature": "def solution(...)",
            "requirements": ["Add type hints", "Add error handling", "Validate inputs"],
        }

        result = self.local_model.generate(task_spec)

        if result["success"]:
            return result["code"]
        else:
            return "# Generation failed"

    def _generate_with_feedback(self, task: str, previous: str, feedback: str) -> str:
        """使用反馈让本地模型改进"""
        prompt = f"""
Previous attempt:
```python
{previous}
```

Feedback for improvement:
{feedback}

Please rewrite the code following the feedback.
"""

        return self._generate_with_local_model(task, prompt)

    def _evaluate_code(self, code: str) -> float:
        """评估代码质量"""
        result = self.optimizer.optimize(code)
        return result["optimized_score"]

    def _generate_feedback(self, code: str) -> str:
        """生成改进反馈"""
        result = self.optimizer.optimize(code)

        feedback_parts = []

        for issue in result["issues"]:
            if issue.severity == "error":
                feedback_parts.append(f"- {issue.code}: {issue.message}")

        if not feedback_parts:
            feedback_parts.append("Code is good but could be improved:")
            for issue in result["issues"][:3]:
                feedback_parts.append(f"- {issue.message}")

        return "\n".join(feedback_parts)

    def _generate_with_teacher(
        self, task: str, student_code: str, feedback: str
    ) -> str:
        """使用教师模型（DeepSeek）生成改进版本"""
        # 临时切换到 deepseek
        teacher = CodeGenerator(backend="deepseek")

        task_spec = {
            "description": f"{task}\n\nCurrent code:\n{student_code}\n\nImprove following:\n{feedback}",
            "function_signature": "def improved_function(...)",
            "requirements": ["Type hints", "Error handling", "Input validation"],
        }

        result = teacher.generate(task_spec)

        if result["success"]:
            return result["code"]
        else:
            return student_code  # 失败则返回原代码

    def _extract_improvements(self, bad: str, good: str) -> List[str]:
        """提取改进点"""
        improvements = []

        if "isinstance(" in good and "isinstance(" not in bad:
            improvements.append("Added input validation")
        if "try:" in good and "try:" not in bad:
            improvements.append("Added error handling")
        if ("->" in good or ":" in good) and ("->" not in bad and ":" not in bad):
            improvements.append("Added type hints")
        if '"""' in good and '"""' not in bad:
            improvements.append("Added docstrings")

        return improvements if improvements else ["General improvement"]

    def print_training_stats(self):
        """打印训练统计"""
        print("\n" + "=" * 60)
        print("Iterative Trainer Statistics")
        print("=" * 60)

        if not self.sessions:
            print("No training sessions yet.")
            return

        print(f"\nTotal sessions: {len(self.sessions)}")

        # 统计改进情况
        improvements = [s["improvement"] for s in self.sessions]
        avg_improvement = sum(improvements) / len(improvements)

        print(f"Average improvement: {avg_improvement:+.1f} points")
        print(f"Best improvement: {max(improvements):+.1f} points")
        print(f"Worst improvement: {min(improvements):+.1f} points")

        # 最近会话
        print("\nRecent sessions:")
        for s in self.sessions[-5:]:
            print(f"  - {s['task'][:50]}...")
            print(f"    {s['final_score']:.0f} pts ({s['improvement']:+.0f})")

        print("=" * 60)


# 便捷函数
def train_local_model(task: str, task_type: str = "general") -> TrainingSession:
    """快速训练本地模型"""
    trainer = IterativeTrainer()
    return trainer.train(task, task_type)


if __name__ == "__main__":
    # 测试
    trainer = IterativeTrainer()

    session = trainer.train(
        task="Write a function to parse CSV string safely",
        task_type="parser",
        max_iterations=3,
        target_score=75,
    )

    trainer.print_training_stats()
