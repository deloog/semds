"""
SEMDS Code Generator - Layer 1

代码生成器，负责调用Claude API生成代码实现。

本模块提供：
- CodeGenerator: 代码生成器类
- GENERATION_PROMPT: 代码生成提示模板
"""

import os
import re
from typing import Any, Optional, Type, Union

# 尝试导入LLM库
Anthropic: Optional[Type[Any]] = None
OpenAI: Optional[Type[Any]] = None

try:
    from anthropic import Anthropic
except ImportError:
    pass

try:
    from openai import OpenAI
except ImportError:
    pass


# 代码生成提示模板
GENERATION_PROMPT = """你是一个Python专家，任务是实现以下函数规格。

## 任务描述
{task_description}

## 目标函数签名
```python
{function_signature}
```

## 需求列表
{requirements}

## 前代实现（如有）
```python
{previous_code}
```

## 前代得分
- 内生分（测试通过率）: {intrinsic_score}
- 失败的测试用例: {failed_tests}
- 外生分（一致性验证）: {extrinsic_score}

## 本代进化策略
- 变异类型: {mutation_type}
- 重点改进方向: {improvement_focus}

## 要求
1. 只输出函数实现代码，不要包含测试代码
2. 不要使用任何外部库
3. 代码必须完整可执行
4. 不要添加任何解释文字

```python
"""

# 代码提取正则表达式
CODE_EXTRACTION_PATTERN = r"```python\n(.*?)\n```"


class CodeGenerator:
    """
    代码生成器，支持多种LLM API生成Python代码实现。

    支持的LLM:
    - Deepseek (默认, 推荐)
    - Anthropic Claude
    - OpenAI GPT

    Attributes:
        client: API客户端
        model: 使用的模型名称
        default_temperature: 默认温度参数
        backend: LLM后端类型
    """

    # 默认模型
    DEFAULT_MODEL = "deepseek-chat"
    DEFAULT_BACKEND = "deepseek"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        default_temperature: float = 0.5,
        backend: str = None,
        base_url: Optional[str] = None,
    ):
        """
        初始化代码生成器。

        Args:
            api_key: API密钥，默认从环境变量读取
            model: 使用的模型名称
            default_temperature: 默认温度参数（0.0-1.0）
            backend: LLM后端 (deepseek/anthropic/openai)
            base_url: API基础URL（用于自定义端点）

        Raises:
            ValueError: 如果API密钥未提供
            ImportError: 如果所需库未安装
        """
        self.backend = backend or os.environ.get("LLM_BACKEND", self.DEFAULT_BACKEND)
        self.model = model
        self.default_temperature = default_temperature

        # 根据后端类型初始化
        if self.backend == "deepseek":
            self._init_deepseek(api_key, base_url)
        elif self.backend == "anthropic":
            self._init_anthropic(api_key)
        elif self.backend == "openai":
            self._init_openai(api_key, base_url)
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

    def _init_deepseek(self, api_key: Optional[str], base_url: Optional[str]):
        """初始化Deepseek客户端"""
        if OpenAI is None:
            raise ImportError(
                "openai library is required for Deepseek. "
                "Install it with: pip install openai"
            )

        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Deepseek API key is required. "
                "Provide it via api_key parameter or "
                "DEEPSEEK_API_KEY environment variable."
            )

        # Deepseek使用OpenAI兼容接口
        base_url = base_url or os.environ.get(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
        )
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url,
        )

    def _init_anthropic(self, api_key: Optional[str]):
        """初始化Anthropic客户端"""
        if Anthropic is None:
            raise ImportError(
                "anthropic library is required. "
                "Install it with: pip install anthropic"
            )

        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key is required. "
                "Provide it via api_key parameter or "
                "ANTHROPIC_API_KEY environment variable."
            )

        self.client = Anthropic(api_key=self.api_key)

    def _init_openai(self, api_key: Optional[str], base_url: Optional[str]):
        """初始化OpenAI客户端"""
        if OpenAI is None:
            raise ImportError(
                "openai library is required. " "Install it with: pip install openai"
            )

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. "
                "Provide it via api_key parameter or "
                "OPENAI_API_KEY environment variable."
            )

        kwargs = {"api_key": self.api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)

    def generate(
        self,
        task_spec: dict,
        previous_code: Optional[str] = None,
        previous_score: Optional[dict] = None,
        failed_tests: Optional[list] = None,
        strategy: Optional[dict] = None,
        temperature: Optional[float] = None,
    ) -> dict:
        """
        调用Claude API生成代码实现。

        Args:
            task_spec: 任务规格字典，包含：
                - description: 任务描述
                - function_signature: 目标函数签名
                - requirements: 需求列表（字符串或列表）
            previous_code: 前代实现的代码（如果有）
            previous_score: 前代得分字典，包含：
                - intrinsic_score: 内生分（测试通过率）
                - extrinsic_score: 外生分（一致性验证）
            failed_tests: 失败的测试用例列表
            strategy: 进化策略字典，包含：
                - mutation_type: 变异类型（conservative/aggressive/hybrid）
                - improvement_focus: 重点改进方向
            temperature: 温度参数（覆盖默认值）

        Returns:
            字典包含：
            - success: bool - 是否成功
            - code: str - 生成的代码（如果成功）
            - raw_response: str - 原始API响应
            - error: str - 错误信息（如果失败）
        """
        # 准备提示参数
        prompt_params = {
            "task_description": task_spec.get("description", ""),
            "function_signature": task_spec.get("function_signature", ""),
            "requirements": self._format_requirements(
                task_spec.get("requirements", [])
            ),
            "previous_code": previous_code or "# 这是第一代，无前代代码",
            "intrinsic_score": (
                previous_score.get("intrinsic_score", "N/A")
                if previous_score
                else "N/A"
            ),
            "extrinsic_score": (
                previous_score.get("extrinsic_score", "N/A")
                if previous_score
                else "N/A"
            ),
            "failed_tests": ", ".join(failed_tests) if failed_tests else "无",
            "mutation_type": (
                strategy.get("mutation_type", "conservative")
                if strategy
                else "conservative"
            ),
            "improvement_focus": (
                strategy.get("improvement_focus", "提高测试通过率")
                if strategy
                else "实现基本功能"
            ),
        }

        # 构建完整提示
        prompt = GENERATION_PROMPT.format(**prompt_params)

        try:
            # 根据后端类型调用API
            if self.backend == "deepseek" or self.backend == "openai":
                # OpenAI/Deepseek格式
                messages = [
                    {
                        "role": "system",
                        "content": "你是一个专业的Python程序员。只输出代码，"
                        "不输出任何解释。代码必须放在```python代码块中。",
                    },
                    {"role": "user", "content": prompt},
                ]
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature or self.default_temperature,
                    max_tokens=4096,
                )
                raw_response = response.choices[0].message.content
            else:
                # Anthropic格式
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=temperature or self.default_temperature,
                    system="你是一个专业的Python程序员。只输出代码，不输出任何解释。代码必须放在```python代码块中。",
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.content[0]
                if hasattr(content, "text"):
                    raw_response = content.text
                else:
                    raw_response = str(content)

            # 提取代码
            extracted_code = self.extract_code(raw_response)

            if extracted_code:
                return {
                    "success": True,
                    "code": extracted_code,
                    "raw_response": raw_response,
                    "error": None,
                }
            else:
                return {
                    "success": False,
                    "code": None,
                    "raw_response": raw_response,
                    "error": "Failed to extract code from response",
                }

        except Exception as e:
            return {
                "success": False,
                "code": None,
                "raw_response": None,
                "error": f"API call failed: {str(e)}",
            }

    def extract_code(self, response: str) -> Optional[str]:
        """
        从Claude响应中提取Python代码块。

        使用正则表达式匹配 ```python...``` 格式的代码块。

        Args:
            response: Claude API的原始响应文本

        Returns:
            提取的代码字符串，如果没有找到代码块则返回None
        """
        # 使用非贪婪匹配查找代码块
        matches = re.findall(CODE_EXTRACTION_PATTERN, response, re.DOTALL)

        if matches:
            # 返回第一个匹配的代码块
            code: str = matches[0].strip()
            # 去除可能的尾部```
            if code.endswith("```"):
                code = code[:-3].strip()
            return code

        # 如果没有找到代码块，尝试查找普通代码块
        # 有些模型可能只输出 ``` 而不带 python 标签
        fallback_pattern = r"```\n(.*?)\n```"
        fallback_matches = re.findall(fallback_pattern, response, re.DOTALL)
        if fallback_matches:
            fallback_code: str = fallback_matches[0].strip()
            if fallback_code.endswith("```"):
                fallback_code = fallback_code[:-3].strip()
            return fallback_code

        # 如果还是没有找到，检查整个响应是否就是代码
        # 简单判断：如果包含def或class关键字，可能就是代码
        if "def " in response or "class " in response:
            # 尝试去除可能的解释文字
            lines = response.split("\n")
            code_lines = []
            in_code = False
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("def ") or stripped.startswith("class "):
                    in_code = True
                if in_code:
                    code_lines.append(line)
            if code_lines:
                return "\n".join(code_lines).strip()

        return None

    def _format_requirements(self, requirements: Union[str, list]) -> str:
        """
        格式化需求列表为字符串。

        Args:
            requirements: 需求列表（字符串或列表）

        Returns:
            格式化后的需求字符串
        """
        if isinstance(requirements, str):
            return requirements

        if isinstance(requirements, list):
            return "\n".join(f"- {req}" for req in requirements)

        return str(requirements)  # type: ignore[unreachable]


if __name__ == "__main__":
    # 简单测试

    # 检查API密钥
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("请设置ANTHROPIC_API_KEY环境变量")
        exit(1)

    # 创建生成器
    generator = CodeGenerator()

    # 测试任务
    task_spec = {
        "description": "实现一个简单的加法函数",
        "function_signature": "def add(a: float, b: float) -> float:",
        "requirements": ["返回两个数的和", "支持浮点数"],
    }

    # 生成代码
    result = generator.generate(task_spec)

    if result["success"]:
        print("生成的代码：")
        print(result["code"])
    else:
        print(f"生成失败: {result['error']}")
        print(f"原始响应: {result['raw_response']}")
