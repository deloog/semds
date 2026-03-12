"""
Skills Library 模块 - 技能库管理

管理：
1. Prompt模板（Jinja2渲染）
2. 已验证的策略注册表（按任务类型组织）
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class SkillsLibrary:
    """技能库

    管理Prompt模板和已验证的进化策略。

    Example:
        >>> library = SkillsLibrary("skills/templates")
        >>> prompt = library.render_template("evolution.j2", {
        ...     "task": "calculator",
        ...     "generation": 5
        ... })
        >>> library.register_verified_strategy(
        ...     {"mutation_type": "conservative", "score": 0.9},
        ...     task_type="math"
        ... )
        >>> best = library.get_best_strategy("math")
    """

    DEFAULT_TEMPLATES_DIR = "skills/templates"

    def __init__(self, templates_dir: str = None):
        """初始化技能库

        Args:
            templates_dir: 模板目录路径，默认使用 skills/templates
        """
        self.templates_dir = Path(templates_dir or self.DEFAULT_TEMPLATES_DIR)

        # 初始化Jinja2环境
        if self.templates_dir.exists():
            self._jinja_env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            self._jinja_env = None

        # 策略注册表：{task_type: [strategy, ...]}
        self._strategies: Dict[str, List[Dict[str, Any]]] = {}

    def load_template(self, template_name: str) -> Any:
        """加载模板

        Args:
            template_name: 模板文件名（如 "prompt.j2"）

        Returns:
            Jinja2模板对象

        Raises:
            FileNotFoundError: 如果模板不存在
        """
        if self._jinja_env is None:
            raise FileNotFoundError(
                f"Templates directory not found: {self.templates_dir}"
            )

        try:
            return self._jinja_env.get_template(template_name)
        except TemplateNotFound:
            raise FileNotFoundError(f"Template not found: {template_name}")

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """渲染模板

        Args:
            template_name: 模板文件名
            context: 渲染上下文变量

        Returns:
            渲染后的字符串
        """
        template = self.load_template(template_name)
        return template.render(**context)

    def register_verified_strategy(
        self, strategy: Dict[str, Any], task_type: str
    ) -> None:
        """注册已验证的策略

        Args:
            strategy: 策略字典（应包含 score 字段）
            task_type: 任务类型（如 "math", "string"）
        """
        if task_type not in self._strategies:
            self._strategies[task_type] = []

        # 确保策略有默认得分
        if "score" not in strategy:
            strategy["score"] = 0.0

        self._strategies[task_type].append(strategy)

    def get_strategies_for_task(
        self, task_type: str, sorted_by_score: bool = False
    ) -> List[Dict[str, Any]]:
        """获取任务类型的所有策略

        Args:
            task_type: 任务类型
            sorted_by_score: 是否按得分降序排序

        Returns:
            策略列表
        """
        strategies = self._strategies.get(task_type, [])

        if sorted_by_score:
            return sorted(strategies, key=lambda s: s.get("score", 0.0), reverse=True)

        return list(strategies)

    def get_best_strategy(self, task_type: str) -> Optional[Dict[str, Any]]:
        """获取任务类型的最佳策略

        Args:
            task_type: 任务类型

        Returns:
            最佳策略（得分最高），如果没有则返回None
        """
        strategies = self._strategies.get(task_type, [])

        if not strategies:
            return None

        return max(strategies, key=lambda s: s.get("score", 0.0))

    def get_strategy_stats(self, task_type: str) -> Dict[str, Any]:
        """获取策略统计信息

        Args:
            task_type: 任务类型

        Returns:
            统计字典，包含 count, average_score 等
        """
        strategies = self._strategies.get(task_type, [])

        if not strategies:
            return {"count": 0, "average_score": 0.0}

        scores = [s.get("score", 0.0) for s in strategies]
        average_score = sum(scores) / len(scores)

        return {
            "count": len(strategies),
            "average_score": round(average_score, 4),
        }
