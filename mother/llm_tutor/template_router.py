"""
Template Router - 模板路由器
务实的方案：本地模型做选择，模板做生成
"""

import json
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class CodeTemplate:
    """代码模板"""

    name: str
    description: str
    template: str
    variables: List[str]
    complexity: str  # simple, medium, complex


class TemplateRouter:
    """
    模板路由器

    核心策略：
    1. 本地模型只负责识别任务类型（简单分类）
    2. 根据类型选择预定义的高质量模板
    3. 本地模型提取模板变量（简单信息抽取）
    4. 填充模板生成最终代码

    优势：
    - 本地模型只做擅长的事（分类、提取）
    - 生成的代码 100% 符合规范
    - 不需要"训练"模型
    """

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, CodeTemplate]:
        """加载代码模板库"""
        return {
            "http_get": CodeTemplate(
                name="http_get",
                description="HTTP GET request with error handling",
                template='''
def {func_name}(url: str) -> str:
    """
    {docstring}
    
    Args:
        url: URL to fetch
        
    Returns:
        Response text or error message
    """
    import requests
    
    # Input validation
    if not isinstance(url, str):
        return "{error_invalid_url}"
    
    if not url.startswith(("http://", "https://")):
        return "{error_invalid_scheme}"
    
    # Security: block internal addresses
    if any(blocked in url for blocked in ["localhost", "127.0.0.1", "0.0.0.0"]):
        return "{error_blocked}"
    
    try:
        response = requests.get(url, timeout={timeout})
        response.raise_for_status()
        return response.text
    except requests.Timeout:
        return "{error_timeout}"
    except requests.RequestException as e:
        return f"{error_request}: {{e}}"
''',
                variables=[
                    "func_name",
                    "docstring",
                    "timeout",
                    "error_invalid_url",
                    "error_invalid_scheme",
                    "error_blocked",
                    "error_timeout",
                    "error_request",
                ],
                complexity="simple",
            ),
            "html_parser": CodeTemplate(
                name="html_parser",
                description="Parse HTML to extract data",
                template='''
def {func_name}(html: str) -> list:
    """
    {docstring}
    
    Args:
        html: HTML string to parse
        
    Returns:
        List of extracted {data_type}
    """
    import re
    
    # Input validation
    if not isinstance(html, str):
        return []
    
    if len(html) > {max_size}:
        return []
    
    # Extract {data_type}
    pattern = r'{regex_pattern}'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    return matches
''',
                variables=[
                    "func_name",
                    "docstring",
                    "data_type",
                    "max_size",
                    "regex_pattern",
                ],
                complexity="simple",
            ),
            "csv_parser": CodeTemplate(
                name="csv_parser",
                description="Parse CSV string safely",
                template='''
def {func_name}(csv_data: str) -> list:
    """
    {docstring}
    
    Args:
        csv_data: CSV formatted string
        
    Returns:
        List of dictionaries
    """
    import csv
    from io import StringIO
    
    # Input validation
    if not isinstance(csv_data, str):
        return [{{"error": "Input must be string"}}]
    
    if len(csv_data) > {max_size}:
        return [{{"error": "Input too large"}}]
    
    try:
        reader = csv.DictReader(StringIO(csv_data))
        rows = []
        for i, row in enumerate(reader):
            if i >= {max_rows}:
                break
            rows.append(dict(row))
        return rows
    except csv.Error as e:
        return [{{"error": f"CSV parse error: {{e}}"}}]
''',
                variables=["func_name", "docstring", "max_size", "max_rows"],
                complexity="simple",
            ),
            "json_parser": CodeTemplate(
                name="json_parser",
                description="Parse JSON with validation",
                template='''
def {func_name}(json_str: str) -> dict:
    """
    {docstring}
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        Parsed data or error dict
    """
    import json
    
    # Input validation
    if not isinstance(json_str, str):
        return {{"success": False, "error": "Input must be string", "data": None}}
    
    if len(json_str) > {max_size}:
        return {{"success": False, "error": "Input too large", "data": None}}
    
    if not json_str.strip():
        return {{"success": False, "error": "Empty input", "data": None}}
    
    try:
        data = json.loads(json_str)
        return {{"success": True, "data": data, "error": None}}
    except json.JSONDecodeError as e:
        return {{"success": False, "error": f"Invalid JSON: {{e}}", "data": None}}
''',
                variables=["func_name", "docstring", "max_size"],
                complexity="simple",
            ),
        }

    def route_task(self, task_description: str) -> Optional[str]:
        """
        根据任务描述路由到合适的模板

        这个函数可以用本地模型实现，也可以用简单的规则匹配

        Args:
            task_description: 任务描述

        Returns:
            模板名称或 None
        """
        task_lower = task_description.lower()

        # 简单的关键词匹配（可以用本地模型改进）
        routing_rules = [
            ("http_get", ["fetch", "get", "http", "request", "download"]),
            ("html_parser", ["html", "parse", "extract", "scrape", "web"]),
            ("csv_parser", ["csv", "comma", "spreadsheet", "table"]),
            ("json_parser", ["json", "parse json", "json string"]),
        ]

        scores = {}
        for template_name, keywords in routing_rules:
            score = sum(1 for kw in keywords if kw in task_lower)
            if score > 0:
                scores[template_name] = score

        if scores:
            return max(scores, key=scores.get)

        return None

    def extract_variables(
        self, task_description: str, template_name: str
    ) -> Dict[str, str]:
        """
        从任务描述中提取模板变量

        可以用本地模型做 NER（命名实体识别）
        但这里先用规则实现

        Args:
            task_description: 任务描述
            template_name: 模板名称

        Returns:
            变量字典
        """
        defaults = {
            "func_name": "process_data",
            "docstring": "Process data safely",
            "timeout": "30",
            "max_size": "10000000",
            "max_rows": "10000",
            "error_invalid_url": "Invalid URL",
            "error_invalid_scheme": "URL must start with http:// or https://",
            "error_blocked": "Access to internal addresses blocked",
            "error_timeout": "Request timed out",
            "error_request": "Request failed",
            "data_type": "data",
            "regex_pattern": "<.*?>",
        }

        # 尝试从任务中提取函数名
        task_lower = task_description.lower()

        if "fetch" in task_lower or "get" in task_lower:
            defaults["func_name"] = "fetch_data"
            defaults["docstring"] = "Fetch data from URL"
        elif "parse" in task_lower:
            defaults["func_name"] = "parse_content"
            defaults["docstring"] = "Parse content safely"
        elif "download" in task_lower:
            defaults["func_name"] = "download_file"
            defaults["docstring"] = "Download file from URL"

        # 提取 URL 中的域名作为提示
        url_match = re.search(r"https?://([^\s/]+)", task_description)
        if url_match:
            domain = url_match.group(1)
            if "image" in task_lower or "img" in task_lower:
                defaults["data_type"] = "image URLs"
                defaults["regex_pattern"] = "<img[^>]+src=[\"']([^\"']+)[\"']"
                defaults["docstring"] = f"Extract image URLs from {domain}"

        return defaults

    def generate_code(
        self, task_description: str, use_local_model: bool = False
    ) -> Tuple[str, str]:
        """
        生成代码

        Args:
            task_description: 任务描述
            use_local_model: 是否使用本地模型提取变量

        Returns:
            (生成的代码, 使用的模板名)
        """
        # 1. 路由到模板
        template_name = self.route_task(task_description)

        if not template_name:
            return ("# No suitable template found", "none")

        template = self.templates[template_name]

        # 2. 提取变量
        if use_local_model:
            # 这里可以接入本地模型
            variables = self._extract_with_local_model(task_description, template)
        else:
            variables = self.extract_variables(task_description, template_name)

        # 3. 填充模板
        code = template.template.format(**variables)

        return (code.strip(), template_name)

    def _extract_with_local_model(
        self, task: str, template: CodeTemplate
    ) -> Dict[str, str]:
        """
        使用本地模型提取变量（预留接口）

        注意：这是本地模型能做的"简单任务"
        - 识别函数应该叫什么
        - 识别超时时间
        - 识别数据类型
        """
        # TODO: 接入 Ollama/Qwen
        # prompt = f"""
        # Task: {task}
        # Template: {template.name}
        # Variables needed: {template.variables}
        # Extract values from task description.
        # """
        # return local_model.extract_json(prompt)

        # 暂时用规则 fallback
        return self.extract_variables(task, template.name)

    def list_templates(self) -> List[str]:
        """列出所有可用模板"""
        return [
            f"{name}: {t.description} ({t.complexity})"
            for name, t in self.templates.items()
        ]

    def add_template(self, template: CodeTemplate):
        """添加新模板"""
        self.templates[template.name] = template


# 便捷函数
def quick_generate(task: str) -> str:
    """快速生成代码"""
    router = TemplateRouter()
    code, template = router.generate_code(task)
    return code


if __name__ == "__main__":
    # 测试
    router = TemplateRouter()

    print("=" * 70)
    print("Template Router - Practical Code Generation")
    print("=" * 70)
    print()
    print("Available templates:")
    for t in router.list_templates():
        print(f"  - {t}")

    test_tasks = [
        "Fetch weather data from API",
        "Parse HTML to extract image URLs",
        "Read CSV file and return rows",
        "Parse JSON string safely",
    ]

    for task in test_tasks:
        print(f"\n{'='*70}")
        print(f"Task: {task}")
        print(f"{'='*70}")

        code, template = router.generate_code(task)

        print(f"Template used: {template}")
        print(f"\nGenerated code ({len(code)} chars):")
        print("-" * 70)
        print(code[:500])
        if len(code) > 500:
            print("...")
        print("-" * 70)

        # 检查代码质量特征
        features = []
        if "isinstance(" in code:
            features.append("input validation")
        if "try:" in code:
            features.append("error handling")
        if "->" in code:
            features.append("type hints")
        if '"""' in code:
            features.append("docstrings")

        print(f"Features: {', '.join(features)}")
