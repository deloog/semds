"""
Task Analyzer - 将自然语言任务转化为执行计划
MVP 版本：简单的意图识别和步骤拆解
"""

from typing import List, Dict, Any


class ExecutionStep:
    """执行步骤"""

    def __init__(
        self, action: str, inputs: Dict[str, Any], outputs: str, description: str
    ):
        self.action = action
        self.inputs = inputs
        self.outputs = outputs
        self.description = description

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "description": self.description,
        }


class ExecutionPlan:
    """执行计划"""

    def __init__(
        self, task: str, steps: List[ExecutionStep], required_capabilities: List[str]
    ):
        self.task = task
        self.steps = steps
        self.required_capabilities = required_capabilities


class TaskAnalyzer:
    """任务分析器 - MVP 版本使用规则匹配"""

    TASK_PATTERNS = {
        "scrape": {
            "keywords": ["fetch", "get", "download", "crawl", "scrape", "monitor"],
            "steps": [
                ExecutionStep(
                    action="http_client",
                    inputs={"url": "{{target_url}}", "method": "GET"},
                    outputs="html_content",
                    description="Fetch webpage content",
                ),
                ExecutionStep(
                    action="html_parser",
                    inputs={"html": "{{html_content}}"},
                    outputs="extracted_data",
                    description="Parse HTML for data",
                ),
            ],
            "required_capabilities": ["http_client", "html_parser"],
        },
        "analyze_csv": {
            "keywords": ["csv", "table", "spreadsheet"],
            "steps": [],
            "required_capabilities": ["csv_reader"],
        },
        "visualize": {
            "keywords": ["chart", "graph", "visualize", "plot"],
            "steps": [],
            "required_capabilities": ["chart_generator"],
        },
    }

    def analyze(self, task_description: str) -> ExecutionPlan:
        """分析任务，生成执行计划"""
        task_lower = task_description.lower()

        # 1. 尝试匹配预设模式
        matched_pattern = None
        for pattern_name, pattern in self.TASK_PATTERNS.items():
            for keyword in pattern["keywords"]:
                if keyword.lower() in task_lower:
                    matched_pattern = pattern
                    break
            if matched_pattern:
                break

        if matched_pattern:
            params = self._extract_params(task_description)

            steps = []
            for step_template in matched_pattern["steps"]:
                step = ExecutionStep(
                    action=step_template.action,
                    inputs=self._fill_params(step_template.inputs, params),
                    outputs=step_template.outputs,
                    description=step_template.description,
                )
                steps.append(step)

            return ExecutionPlan(
                task=task_description,
                steps=steps,
                required_capabilities=matched_pattern["required_capabilities"].copy(),
            )

        # Fallback：返回空计划
        return ExecutionPlan(task=task_description, steps=[], required_capabilities=[])

    def _extract_params(self, task: str) -> Dict[str, str]:
        """从任务描述中提取参数"""
        import re

        params = {}

        # 提取 URL
        url_match = re.search(r"https?://[^\s\"\'>]+", task)
        if url_match:
            params["target_url"] = url_match.group(0)

        return params

    def _fill_params(self, template: Dict, params: Dict) -> Dict:
        """填充模板参数"""
        result = {}
        for key, value in template.items():
            if (
                isinstance(value, str)
                and value.startswith("{{")
                and value.endswith("}}")
            ):
                param_name = value[2:-2]
                result[key] = params.get(param_name, value)
            else:
                result[key] = value
        return result


if __name__ == "__main__":
    analyzer = TaskAnalyzer()
    plan = analyzer.analyze("爬取 https://www.bing.com 首页的图片")
    print(f"Task: {plan.task}")
    print(f"Capabilities: {plan.required_capabilities}")
    for step in plan.steps:
        print(f"  - {step.action}: {step.description}")
