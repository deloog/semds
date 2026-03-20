"""
Task Decomposer - 任务分解器

核心洞察：
1. AI 幻觉严重，大任务容易遗漏步骤
2. AI 急于完成，导致质量差
3. 解决方案：将任务分解到原子级别，每个小任务可验证

分解原则：
- 每个任务输出 < 50 行代码
- 每个任务有明确的输入/输出/验证标准
- 任务之间依赖关系清晰
- 小模型能独立完成
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


class TaskType(Enum):
    """任务类型"""

    ANALYSIS = "analysis"  # 分析任务（无代码输出）
    INTERFACE = "interface"  # 定义接口/函数签名
    TEST = "test"  # 编写测试
    IMPLEMENT = "implement"  # 实现代码
    VALIDATE = "validate"  # 验证/检查
    REFACTOR = "refactor"  # 重构
    DOCUMENT = "document"  # 文档


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AtomicTask:
    """
    原子任务

    必须小到：
    - 输出 < 50 行代码
    - 能在 1 分钟内完成
    - 有明确的完成标准
    """

    id: str
    name: str
    description: str
    task_type: TaskType

    # 输入输出定义
    inputs: Dict[str, str] = field(default_factory=dict)
    expected_output: str = ""
    validation_criteria: List[str] = field(default_factory=list)

    # 依赖关系
    depends_on: List[str] = field(default_factory=list)

    # 执行信息
    max_tokens: int = 500  # 限制输出长度
    max_lines: int = 50  # 限制代码行数

    # 状态
    status: TaskStatus = TaskStatus.PENDING
    actual_output: str = ""
    validation_result: Optional[bool] = None
    error_message: str = ""


@dataclass
class TaskGraph:
    """任务图"""

    tasks: Dict[str, AtomicTask]
    execution_order: List[str]

    def get_ready_tasks(self) -> List[AtomicTask]:
        """获取可以执行的任务（依赖已完成）"""
        ready = []
        for task_id in self.execution_order:
            task = self.tasks[task_id]
            if task.status == TaskStatus.PENDING:
                # 检查依赖是否都完成
                deps_completed = all(
                    self.tasks[dep].status == TaskStatus.COMPLETED
                    for dep in task.depends_on
                )
                if deps_completed:
                    ready.append(task)
        return ready

    def get_completion_rate(self) -> float:
        """获取完成率"""
        if not self.tasks:
            return 0.0
        completed = sum(
            1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED
        )
        return completed / len(self.tasks)

    def get_failed_tasks(self) -> List[AtomicTask]:
        """获取失败的任务"""
        return [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]


class TaskDecomposer:
    """
    任务分解器

    将复杂编程任务分解为原子级小任务
    """

    def __init__(self):
        self.decomposition_patterns = self._load_patterns()

    def _load_patterns(self) -> Dict:
        """加载分解模式"""
        return {
            "function_implementation": {
                "steps": [
                    (TaskType.ANALYSIS, "分析需求", []),
                    (TaskType.INTERFACE, "定义函数签名", ["分析需求"]),
                    (TaskType.TEST, "编写测试用例", ["定义函数签名"]),
                    (TaskType.IMPLEMENT, "实现核心逻辑", ["编写测试用例"]),
                    (TaskType.VALIDATE, "运行测试验证", ["实现核心逻辑"]),
                    (TaskType.REFACTOR, "重构优化", ["运行测试验证"]),
                ]
            },
            "class_implementation": {
                "steps": [
                    (TaskType.ANALYSIS, "分析类职责", []),
                    (TaskType.INTERFACE, "定义类接口", ["分析类职责"]),
                    (TaskType.TEST, "编写单元测试", ["定义类接口"]),
                    (TaskType.IMPLEMENT, "实现 __init__", ["编写单元测试"]),
                    (TaskType.IMPLEMENT, "实现核心方法", ["实现 __init__"]),
                    (TaskType.VALIDATE, "运行所有测试", ["实现核心方法"]),
                ]
            },
            "data_pipeline": {
                "steps": [
                    (TaskType.ANALYSIS, "分析数据流", []),
                    (TaskType.INTERFACE, "定义数据模型", ["分析数据流"]),
                    (TaskType.IMPLEMENT, "实现数据获取", ["定义数据模型"]),
                    (TaskType.IMPLEMENT, "实现数据清洗", ["实现数据获取"]),
                    (TaskType.IMPLEMENT, "实现数据转换", ["实现数据清洗"]),
                    (TaskType.IMPLEMENT, "实现数据存储", ["实现数据转换"]),
                    (TaskType.TEST, "编写集成测试", ["实现数据存储"]),
                    (TaskType.VALIDATE, "验证完整流程", ["编写集成测试"]),
                ]
            },
        }

    def decompose(self, task_description: str) -> TaskGraph:
        """
        分解任务

        Args:
            task_description: 任务描述

        Returns:
            任务图
        """
        print(f"\n[Decomposer] Analyzing task: {task_description[:50]}...")

        # 1. 识别任务类型
        task_category = self._categorize_task(task_description)
        print(f"[Decomposer] Detected category: {task_category}")

        # 2. 获取分解模式
        pattern = self.decomposition_patterns.get(
            task_category, self._generate_generic_pattern()
        )

        # 3. 生成原子任务
        tasks = {}
        task_names = {}  # 用于建立依赖关系

        for i, (task_type, name, deps) in enumerate(pattern["steps"]):
            task_id = f"task_{i:02d}"

            # 将依赖的名称转换为 ID
            dep_ids = [task_names[dep] for dep in deps if dep in task_names]

            # 生成具体任务
            atomic_task = self._generate_atomic_task(
                task_id=task_id,
                task_type=task_type,
                name=name,
                description=task_description,
                depends_on=dep_ids,
                step_index=i,
            )

            tasks[task_id] = atomic_task
            task_names[name] = task_id

        # 4. 计算执行顺序（拓扑排序）
        execution_order = self._topological_sort(tasks)

        print(f"[Decomposer] Decomposed into {len(tasks)} atomic tasks")

        return TaskGraph(tasks=tasks, execution_order=execution_order)

    def _categorize_task(self, description: str) -> str:
        """识别任务类型"""
        desc_lower = description.lower()

        if "class" in desc_lower or "implement a class" in desc_lower:
            return "class_implementation"
        elif any(
            word in desc_lower for word in ["pipeline", "workflow", "etl", "process"]
        ):
            return "data_pipeline"
        elif any(word in desc_lower for word in ["function", "implement", "write a"]):
            return "function_implementation"
        else:
            return "function_implementation"  # 默认

    def _generate_generic_pattern(self) -> Dict:
        """生成通用分解模式"""
        return {
            "steps": [
                (TaskType.ANALYSIS, "分析需求", []),
                (TaskType.INTERFACE, "定义接口", ["分析需求"]),
                (TaskType.TEST, "编写测试", ["定义接口"]),
                (TaskType.IMPLEMENT, "实现代码", ["编写测试"]),
                (TaskType.VALIDATE, "验证实现", ["实现代码"]),
            ]
        }

    def _generate_atomic_task(
        self,
        task_id: str,
        task_type: TaskType,
        name: str,
        description: str,
        depends_on: List[str],
        step_index: int,
    ) -> AtomicTask:
        """生成原子任务详情"""

        # 根据任务类型设置验证标准
        validation_criteria = []

        if task_type == TaskType.INTERFACE:
            validation_criteria = [
                "Must have type hints",
                "Must have docstring",
                "Function signature is clear",
            ]
        elif task_type == TaskType.TEST:
            validation_criteria = [
                "At least 3 test cases",
                "Covers edge cases",
                "Tests are independent",
            ]
        elif task_type == TaskType.IMPLEMENT:
            validation_criteria = [
                "Code is less than 50 lines",
                "All tests pass",
                "No syntax errors",
            ]
        elif task_type == TaskType.VALIDATE:
            validation_criteria = [
                "All tests pass",
                "Code quality score > 80",
                "No obvious bugs",
            ]

        # 生成任务描述
        task_desc = f"{name} for: {description}"

        # 根据步骤生成期望输出
        expected_output = self._generate_expected_output(task_type, name)

        return AtomicTask(
            id=task_id,
            name=name,
            description=task_desc,
            task_type=task_type,
            inputs={},
            expected_output=expected_output,
            validation_criteria=validation_criteria,
            depends_on=depends_on,
            max_tokens=500,
            max_lines=50,
        )

    def _generate_expected_output(self, task_type: TaskType, name: str) -> str:
        """生成期望输出描述"""
        outputs = {
            TaskType.ANALYSIS: "List of requirements and constraints",
            TaskType.INTERFACE: "Function/class signature with type hints",
            TaskType.TEST: "Complete test code with 3+ test cases",
            TaskType.IMPLEMENT: "Working implementation (< 50 lines)",
            TaskType.VALIDATE: "Test results and quality report",
            TaskType.REFACTOR: "Improved code with same functionality",
            TaskType.DOCUMENT: "Complete documentation",
        }
        return outputs.get(task_type, "Code or analysis")

    def _topological_sort(self, tasks: Dict[str, AtomicTask]) -> List[str]:
        """拓扑排序确定执行顺序"""
        # 简单的拓扑排序实现
        in_degree = {task_id: 0 for task_id in tasks}

        for task in tasks.values():
            for dep in task.depends_on:
                if dep in tasks:
                    in_degree[task.id] += 1

        # Kahn's algorithm
        queue = [tid for tid, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # 找到依赖 current 的任务
            for task in tasks.values():
                if current in task.depends_on:
                    in_degree[task.id] -= 1
                    if in_degree[task.id] == 0:
                        queue.append(task.id)

        return result

    def print_task_graph(self, graph: TaskGraph):
        """打印任务图"""
        print("\n" + "=" * 70)
        print("Task Decomposition Result")
        print("=" * 70)
        print(f"Total tasks: {len(graph.tasks)}")
        print(f"Completion rate: {graph.get_completion_rate():.0%}")
        print()

        for task_id in graph.execution_order:
            task = graph.tasks[task_id]
            deps = ", ".join(task.depends_on) if task.depends_on else "None"
            status = task.status.value.upper()

            print(f"[{status}] {task_id}: {task.name}")
            print(f"  Type: {task.task_type.value}")
            print(f"  Depends on: {deps}")
            print(f"  Max lines: {task.max_lines}")
            print()


# 便捷函数
def decompose_task(description: str) -> TaskGraph:
    """快速分解任务"""
    decomposer = TaskDecomposer()
    return decomposer.decompose(description)


if __name__ == "__main__":
    # 测试
    decomposer = TaskDecomposer()

    test_tasks = [
        "Write a function to fetch data from API",
        "Implement a class for CSV parser",
        "Create a data pipeline to process logs",
    ]

    for task in test_tasks:
        print("\n" + "=" * 70)
        graph = decomposer.decompose(task)
        decomposer.print_task_graph(graph)
