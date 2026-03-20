"""
Few-shot Optimizer - Few-shot 示例优化器
为本地模型生成高质量的 few-shot 学习示例
"""

import json
import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class FewShotPrompt:
    """Few-shot 提示"""

    system_prompt: str
    examples: List[Dict]  # [{input, output, explanation}]
    instruction: str


class FewShotOptimizer:
    """
    Few-shot 优化器

    策略：
    1. 收集 SEMDS 生成的优质代码（高分通过质量检查）
    2. 对比本地模型生成的低分代码
    3. 生成对比示例，展示"好"vs"坏"的区别
    4. 在 prompt 中加入这些示例，提升本地模型输出质量
    """

    def __init__(self):
        self.examples_dir = "mother/llm_tutor/few_shot_examples"
        os.makedirs(self.examples_dir, exist_ok=True)

        # 加载所有示例
        self.examples = self._load_all_examples()

    def _load_all_examples(self) -> Dict[str, List[Dict]]:
        """加载所有 few-shot 示例"""
        examples = {}

        for filename in os.listdir(self.examples_dir):
            if filename.endswith(".json"):
                task_type = filename[:-5]  # 去掉 .json
                filepath = os.path.join(self.examples_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        examples[task_type] = json.load(f)
                except:
                    examples[task_type] = []

        return examples

    def _save_examples(self, task_type: str):
        """保存示例"""
        filepath = os.path.join(self.examples_dir, f"{task_type}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.examples.get(task_type, []), f, indent=2, ensure_ascii=False)

    def add_example(
        self,
        task_type: str,
        task_description: str,
        bad_code: str,
        good_code: str,
        improvements: List[str],
    ):
        """
        添加对比示例

        Args:
            task_type: 任务类型，如 "http_client", "parser"
            task_description: 任务描述
            bad_code: 本地模型生成的代码
            good_code: SEMDS 优化后的代码
            improvements: 改进点列表
        """
        example = {
            "task": task_description,
            "bad": bad_code,
            "good": good_code,
            "improvements": improvements,
        }

        if task_type not in self.examples:
            self.examples[task_type] = []

        self.examples[task_type].append(example)

        # 只保留最新的 10 个示例
        self.examples[task_type] = self.examples[task_type][-10:]

        self._save_examples(task_type)

        print(
            f"[FewShot] Added example for {task_type} ({len(self.examples[task_type])} total)"
        )

    def get_optimized_prompt(
        self, task_type: str, new_task: str, n_examples: int = 2
    ) -> FewShotPrompt:
        """
        获取优化后的 few-shot prompt

        Args:
            task_type: 任务类型
            new_task: 新任务描述
            n_examples: 示例数量

        Returns:
            优化后的提示
        """
        # 系统提示
        system_prompt = """You are a Python code generator that writes minimal, secure, and robust code.

Core Principles:
1. MINIMALISM - Write the least code necessary
2. SECURITY - Never trust input, always validate
3. ROBUSTNESS - Handle all errors gracefully

Rules:
- Add type hints for all parameters and return values
- Add docstrings explaining the function
- Validate inputs with isinstance() checks
- Use try/except for error handling
- Set size limits for inputs (e.g., MAX_SIZE = 10_000_000)
- Never use eval(), exec(), or other dangerous functions
"""

        # 获取相关示例
        examples = self.examples.get(task_type, [])

        # 选择最近的 n 个示例
        selected = examples[-n_examples:] if examples else []

        # 构建示例列表
        formatted_examples = []
        for ex in selected:
            formatted_examples.append(
                {
                    "input": f"Task: {ex['task']}",
                    "output": ex["good"],
                    "explanation": f"Key improvements: {', '.join(ex['improvements'][:3])}",
                }
            )

        # 任务指令
        instruction = f"""
Now write code for this task following the same principles:

Task: {new_task}

Write minimal, secure, robust Python code:
"""

        return FewShotPrompt(
            system_prompt=system_prompt,
            examples=formatted_examples,
            instruction=instruction,
        )

    def format_prompt_for_local_llm(self, prompt: FewShotPrompt) -> str:
        """
        将 FewShotPrompt 格式化为本地模型可用的字符串

        Args:
            prompt: FewShotPrompt 对象

        Returns:
            格式化的提示字符串
        """
        parts = []

        # 系统提示
        parts.append("SYSTEM:")
        parts.append(prompt.system_prompt)
        parts.append("")

        # 示例
        if prompt.examples:
            parts.append("EXAMPLES:")
            for i, ex in enumerate(prompt.examples, 1):
                parts.append(f"\nExample {i}:")
                parts.append(f"{ex['input']}")
                parts.append(f"\nSolution:")
                parts.append(f"```python")
                parts.append(ex["output"])
                parts.append("```")
                parts.append(f"\nNote: {ex['explanation']}")
            parts.append("")

        # 指令
        parts.append(prompt.instruction)

        return "\n".join(parts)

    def get_prompt_for_ollama(self, task_type: str, new_task: str) -> str:
        """
        获取适用于 Ollama 本地模型的优化提示

        Args:
            task_type: 任务类型
            new_task: 新任务描述

        Returns:
            格式化提示
        """
        prompt = self.get_optimized_prompt(task_type, new_task)
        return self.format_prompt_for_local_llm(prompt)

    def print_examples_stats(self):
        """打印示例统计"""
        print("\n" + "=" * 60)
        print("Few-shot Examples Library")
        print("=" * 60)

        if not self.examples:
            print("No examples collected yet.")
            return

        for task_type, examples in self.examples.items():
            print(f"\n{task_type}: {len(examples)} examples")
            for i, ex in enumerate(examples[-3:], 1):
                print(f"  {i}. {ex['task'][:50]}...")
                print(f"     Improvements: {', '.join(ex['improvements'][:2])}")

        print("=" * 60)


# 便捷函数
def get_enhanced_prompt(task_type: str, task: str) -> str:
    """获取增强后的提示"""
    optimizer = FewShotOptimizer()
    return optimizer.get_prompt_for_ollama(task_type, task)


if __name__ == "__main__":
    # 测试
    optimizer = FewShotOptimizer()

    # 添加一个示例
    optimizer.add_example(
        task_type="http_client",
        task_description="Fetch data from URL",
        bad_code="def fetch(url): return requests.get(url).text",
        good_code='''def fetch(url: str) -> str:
    """Fetch data from URL safely."""
    if not isinstance(url, str):
        raise ValueError("URL must be string")
    return requests.get(url, timeout=30).text''',
        improvements=["Type hints", "Input validation", "Timeout"],
    )

    # 获取优化后的提示
    prompt = optimizer.get_prompt_for_ollama(
        task_type="http_client", new_task="Download image from URL"
    )

    print("Optimized prompt for local LLM:")
    print("=" * 60)
    print(prompt)
    print("=" * 60)

    optimizer.print_examples_stats()
