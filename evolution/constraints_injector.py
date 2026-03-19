"""
约束注入器 - Phase 1.5 核心组件

将任务约束自动注入到 LLM 提示词中，提高首次生成成功率。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Example:
    """输入输出示例"""

    input: Any
    output: Any
    description: str = ""


@dataclass
class TaskSpec:
    """标准化任务规格"""

    name: str
    description: str
    function_signature: str
    constraints: List[str] = field(default_factory=list)
    examples: List[Example] = field(default_factory=list)

    def __post_init__(self) -> None:
        """自动提取函数名和参数"""
        import re

        match = re.match(r"def\s+(\w+)\s*\((.*?)\)", self.function_signature)
        if match:
            self._function_name = match.group(1)
            self._parameters = match.group(2)
        else:
            self._function_name = None
            self._parameters = None

    @property
    def function_name(self) -> Optional[str]:
        return getattr(self, "_function_name", None)

    @property
    def parameters(self) -> Optional[str]:
        return getattr(self, "_parameters", None)


class ConstraintsInjector:
    """
    约束注入器

    将 TaskSpec 中的约束自动格式化为强化的提示词。
    """

    def __init__(self, emphasis_style: str = "strong"):
        """
        Args:
            emphasis_style: 强调风格 ("normal", "strong", "critical")
        """
        self.emphasis_style = emphasis_style
        self._emphasis_markers = {
            "normal": ("注意", "请确保"),
            "strong": ("【重要】", "必须"),
            "critical": ("【关键约束 - 违反将导致失败】", "严格必须"),
        }

    def inject(self, task_spec: TaskSpec, base_prompt: str = "") -> str:
        """
        将约束注入到提示词中

        Returns:
            增强后的完整提示词
        """
        header, requirement = self._emphasis_markers[self.emphasis_style]

        sections = []

        # 基础描述
        if base_prompt:
            sections.append(base_prompt)
        else:
            sections.append(f"实现以下功能：{task_spec.description}")

        # 核心约束部分
        constraints_text = self._format_constraints(task_spec, requirement)
        sections.append(constraints_text)

        # 示例部分（如果有）
        if task_spec.examples:
            examples_text = self._format_examples(task_spec.examples)
            sections.append(examples_text)

        return "\n\n".join(sections)

    def _format_constraints(self, task_spec: TaskSpec, requirement: str) -> str:
        """格式化约束部分"""
        header, _ = self._emphasis_markers[self.emphasis_style]

        lines = [f"{header} 约束条件"]
        lines.append("=" * 50)

        # 函数签名约束（最重要）
        lines.append(f"{requirement} 使用以下函数签名（一字不差）：")
        lines.append(f"  {task_spec.function_signature}")
        lines.append("")

        # 详细约束
        if task_spec.constraints:
            lines.append(f"{requirement} 遵守以下约束：")
            for i, constraint in enumerate(task_spec.constraints, 1):
                lines.append(f"  {i}. {constraint}")
            lines.append("")

        # 违反后果
        if self.emphasis_style == "critical":
            lines.append("警告：违反以上任何约束将导致代码验证失败！")

        return "\n".join(lines)

    def _format_examples(self, examples: List[Example]) -> str:
        """格式化示例部分"""
        lines = ["输入输出示例"]
        lines.append("-" * 30)

        for i, ex in enumerate(examples, 1):
            if ex.description:
                lines.append(f"{i}. {ex.description}")
            lines.append(f"   输入: {repr(ex.input)}")
            lines.append(f"   输出: {repr(ex.output)}")
            lines.append("")

        return "\n".join(lines)

    def create_validation_hint(self, task_spec: TaskSpec) -> str:
        """
        创建验证提示（用于 SelfValidator）

        Returns:
            验证规则描述
        """
        lines = [
            f"Expected function name: {task_spec.function_name}",
            f"Expected signature: {task_spec.function_signature}",
        ]
        if task_spec.constraints:
            lines.append("Additional constraints:")
            for c in task_spec.constraints:
                lines.append(f"  - {c}")
        return "\n".join(lines)


def create_calculator_task() -> TaskSpec:
    """创建字符串计算器任务（Phase 1 验证通过）"""
    return TaskSpec(
        name="string_calculator",
        description="实现字符串表达式计算器，支持四则运算、括号、运算符优先级",
        function_signature="def evaluate(expression: str) -> float",
        constraints=[
            "函数名必须是 'evaluate'",
            "参数名必须是 'expression'",
            "返回类型必须是 float",
            "支持运算符: +, -, *, /",
            "正确处理运算符优先级",
            "支持括号嵌套",
            "自动处理空格",
        ],
        examples=[
            Example("2+3", 5.0, "简单加法"),
            Example("2+3*4", 14.0, "运算符优先级"),
            Example("(2+3)*4", 20.0, "括号优先级"),
        ],
    )


def create_list_sort_task() -> TaskSpec:
    """创建列表排序任务"""
    return TaskSpec(
        name="list_sorter",
        description="实现列表排序，支持升序和降序",
        function_signature="def sort_list(lst: list, reverse: bool = False) -> list",
        constraints=[
            "函数名必须是 'sort_list'",
            "第一个参数名必须是 'lst'",
            "第二个参数名必须是 'reverse'",
            "返回排序后的列表（不修改原列表）",
            "支持空列表",
            "保持元素类型一致",
        ],
        examples=[
            Example([3, 1, 2], [1, 2, 3], "升序排序"),
            Example([3, 1, 2], [3, 2, 1], "降序排序"),
            Example([], [], "空列表"),
        ],
    )


def create_json_parser_task() -> TaskSpec:
    """创建简易 JSON 解析任务"""
    return TaskSpec(
        name="json_parser",
        description="解析简易 JSON 字符串（仅支持字符串、数字、布尔、null）",
        function_signature="def parse_json(json_str: str) -> any",
        constraints=[
            "函数名必须是 'parse_json'",
            "参数名必须是 'json_str'",
            "支持字符串（双引号包裹）",
            "支持数字（整数和浮点数）",
            "支持布尔值（true/false）",
            "支持 null",
        ],
        examples=[
            Example('"hello"', "hello", "字符串"),
            Example("123", 123, "整数"),
            Example("true", True, "布尔值"),
            Example("null", None, "null"),
        ],
    )
