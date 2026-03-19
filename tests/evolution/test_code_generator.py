"""Code Generator 测试模块

测试 CodeGenerator 类的各项功能
包括 API 调用、代码提取、异常处理等
"""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestCodeGeneratorInit:
    """CodeGenerator 初始化测试"""

    @patch("evolution.code_generator.Anthropic")
    def test_init_with_api_key_param(self, mock_anthropic_class):
        """测试使用参数传入 API key 初始化"""
        from evolution.code_generator import CodeGenerator

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        generator = CodeGenerator(api_key="test-api-key-123", backend="anthropic")

        assert generator.api_key == "test-api-key-123"
        assert generator.model == CodeGenerator.DEFAULT_MODEL
        assert generator.default_temperature == 0.5
        mock_anthropic_class.assert_called_once_with(api_key="test-api-key-123")

    @patch("evolution.code_generator.Anthropic")
    def test_init_with_env_var(self, mock_anthropic_class):
        """测试从环境变量读取 API key"""
        from evolution.code_generator import CodeGenerator

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-api-key-456"}):
            generator = CodeGenerator(backend="anthropic")
            assert generator.api_key == "env-api-key-456"

    @patch("evolution.code_generator.Anthropic")
    def test_init_custom_model_and_temperature(self, mock_anthropic_class):
        """测试自定义模型和温度参数"""
        from evolution.code_generator import CodeGenerator

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        generator = CodeGenerator(
            api_key="test-key",
            model="claude-opus-4",
            default_temperature=0.8,
            backend="anthropic",
        )

        assert generator.model == "claude-opus-4"
        assert generator.default_temperature == 0.8

    def test_init_without_api_key_raises_error(self):
        """测试没有 API key 时抛出 ValueError"""
        from evolution.code_generator import CodeGenerator

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Deepseek API key is required"):
                CodeGenerator()

    def test_init_without_deepseek_lib_raises_error(self):
        """测试 openai 库未安装时抛出 ImportError"""
        from evolution import code_generator

        # 保存原始值
        original_openai = code_generator.OpenAI

        try:
            # 模拟 openai 库不存在
            code_generator.OpenAI = None

            with pytest.raises(ImportError, match="openai library is required"):
                code_generator.CodeGenerator(api_key="test-key")
        finally:
            # 恢复原始值
            code_generator.OpenAI = original_openai


class TestFormatRequirements:
    """测试 _format_requirements 方法"""

    @pytest.fixture
    def generator(self):
        """创建测试用的 generator"""
        with patch("evolution.code_generator.OpenAI"):
            from evolution.code_generator import CodeGenerator

            return CodeGenerator(api_key="test-key")

    def test_format_requirements_with_string(self, generator):
        """测试字符串类型的 requirements"""
        result = generator._format_requirements("这是一个需求字符串")
        assert result == "这是一个需求字符串"

    def test_format_requirements_with_list(self, generator):
        """测试列表类型的 requirements"""
        requirements = ["需求1", "需求2", "需求3"]
        result = generator._format_requirements(requirements)
        assert result == "- 需求1\n- 需求2\n- 需求3"

    def test_format_requirements_with_empty_list(self, generator):
        """测试空列表"""
        result = generator._format_requirements([])
        assert result == ""

    def test_format_requirements_with_empty_string(self, generator):
        """测试空字符串"""
        result = generator._format_requirements("")
        assert result == ""

    def test_format_requirements_with_single_item_list(self, generator):
        """测试单元素列表"""
        result = generator._format_requirements(["唯一需求"])
        assert result == "- 唯一需求"


class TestExtractCode:
    """测试 extract_code 方法"""

    @pytest.fixture
    def generator(self):
        """创建测试用的 generator"""
        with patch("evolution.code_generator.Anthropic"):
            from evolution.code_generator import CodeGenerator

            return CodeGenerator(api_key="test-key")

    def test_extract_code_with_python_tag(self, generator):
        """测试标准 ```python 代码块格式"""
        response = """
这是一些说明文字
```python
def add(a, b):
    return a + b
```
更多说明
"""
        result = generator.extract_code(response)
        assert result == "def add(a, b):\n    return a + b"

    def test_extract_code_with_multiple_code_blocks(self, generator):
        """测试多个代码块时提取第一个"""
        response = """
```python
def first():
    pass
```
中间说明
```python
def second():
    pass
```
"""
        result = generator.extract_code(response)
        assert result == "def first():\n    pass"

    def test_extract_code_without_python_tag(self, generator):
        """测试只有 ``` 标签的代码块"""
        response = """
说明文字
```
def fallback():
    return 42
```
"""
        result = generator.extract_code(response)
        assert result == "def fallback():\n    return 42"

    def test_extract_code_with_trailing_backticks(self, generator):
        """测试代码块尾部有 ``` 的情况"""
        response = """```python
def test():
    pass
```
"""
        result = generator.extract_code(response)
        assert result == "def test():\n    pass"

    def test_extract_code_no_code_block_with_def(self, generator):
        """测试没有代码块但包含 def 关键字"""
        response = '''这是一个解释
def standalone_func():
    """文档字符串"""
    return True
更多解释'''
        result = generator.extract_code(response)
        assert "def standalone_func():" in result
        assert "return True" in result

    def test_extract_code_no_code_block_with_class(self, generator):
        """测试没有代码块但包含 class 关键字"""
        response = """解释文字
class MyClass:
    def method(self):
        return "hello"
结束"""
        result = generator.extract_code(response)
        assert "class MyClass:" in result
        assert "def method(self):" in result

    def test_extract_code_no_match_returns_none(self, generator):
        """测试没有代码时返回 None"""
        response = "这是纯文本，没有代码"
        result = generator.extract_code(response)
        assert result is None

    def test_extract_code_empty_response(self, generator):
        """测试空响应"""
        result = generator.extract_code("")
        assert result is None

    def test_extract_code_multiline_function(self, generator):
        """测试多行复杂函数"""
        response = '''```python
def complex_func(a, b, c):
    """复杂函数文档"""
    if a > 0:
        if b > 0:
            return a + b
        else:
            return a - b
    return c
```'''
        result = generator.extract_code(response)
        assert "def complex_func(a, b, c):" in result
        assert '"""复杂函数文档"""' in result


class TestGenerate:
    """测试 generate 方法"""

    @pytest.fixture
    def task_spec(self):
        """示例任务规格"""
        return {
            "description": "实现加法函数",
            "function_signature": "def add(a: int, b: int) -> int:",
            "requirements": ["返回两个整数之和", "处理正数和负数"],
        }

    @pytest.fixture
    def mock_response(self):
        """创建 mock API 响应"""
        response = MagicMock()
        response.content = [
            MagicMock(text="```python\ndef add(a, b):\n    return a + b\n```")
        ]
        return response

    def test_generate_success(self, task_spec, mock_response):
        """测试成功生成代码"""
        with patch("evolution.code_generator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            from evolution.code_generator import CodeGenerator

            generator = CodeGenerator(api_key="test-key", backend="anthropic")
            result = generator.generate(task_spec)

            assert result["success"] is True
            assert result["code"] == "def add(a, b):\n    return a + b"
            assert result["error"] is None
            assert "```python" in result["raw_response"]

    def test_generate_with_previous_code_and_score(self, task_spec, mock_response):
        """测试带前代代码和得分的生成"""
        with patch("evolution.code_generator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            from evolution.code_generator import CodeGenerator

            generator = CodeGenerator(api_key="test-key", backend="anthropic")
            previous_code = "def old_add(a, b): return a"
            previous_score = {"intrinsic_score": 0.5, "extrinsic_score": 0.3}
            failed_tests = ["test_add_large_numbers"]
            strategy = {"mutation_type": "aggressive", "improvement_focus": "处理大数"}

            result = generator.generate(
                task_spec,
                previous_code=previous_code,
                previous_score=previous_score,
                failed_tests=failed_tests,
                strategy=strategy,
            )

            assert result["success"] is True
            # 验证 API 被调用
            mock_client.messages.create.assert_called_once()

    def test_generate_with_custom_temperature(self, task_spec, mock_response):
        """测试自定义温度参数"""
        with patch("evolution.code_generator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            from evolution.code_generator import CodeGenerator

            generator = CodeGenerator(api_key="test-key", backend="anthropic")
            result = generator.generate(task_spec, temperature=0.9)

            # 验证调用时使用了自定义温度
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["temperature"] == 0.9

    def test_generate_api_error(self, task_spec):
        """测试 API 调用异常"""
        with patch("evolution.code_generator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception(
                "API Rate Limit Exceeded"
            )
            mock_anthropic.return_value = mock_client

            from evolution.code_generator import CodeGenerator

            generator = CodeGenerator(api_key="test-key", backend="anthropic")
            result = generator.generate(task_spec)

            assert result["success"] is False
            assert result["code"] is None
            assert "API call failed" in result["error"]
            assert "Rate Limit Exceeded" in result["error"]

    def test_generate_no_code_extracted(self, task_spec):
        """测试无法从响应中提取代码"""
        with patch("evolution.code_generator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            response = MagicMock()
            response.content = [MagicMock(text="没有代码，只有解释文字")]
            mock_client.messages.create.return_value = response
            mock_anthropic.return_value = mock_client

            from evolution.code_generator import CodeGenerator

            generator = CodeGenerator(api_key="test-key", backend="anthropic")
            result = generator.generate(task_spec)

            assert result["success"] is False
            assert result["code"] is None
            assert "Failed to extract code" in result["error"]

    def test_generate_response_content_without_text(self, task_spec):
        """测试响应 content 没有 text 属性的情况"""
        with patch("evolution.code_generator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            response = MagicMock()
            # 创建一个没有 text 属性的 content
            content_obj = MagicMock()
            del content_obj.text  # 删除 text 属性
            content_obj.__str__ = lambda self: "```python\ndef test():\n    pass\n```"
            response.content = [content_obj]
            mock_client.messages.create.return_value = response
            mock_anthropic.return_value = mock_client

            from evolution.code_generator import CodeGenerator

            generator = CodeGenerator(api_key="test-key", backend="anthropic")
            result = generator.generate(task_spec)

            # 应该使用 str() 转换
            assert result["success"] is True

    def test_generate_with_string_requirements(self, task_spec, mock_response):
        """测试字符串类型的 requirements"""
        task_spec["requirements"] = "单一需求字符串"

        with patch("evolution.code_generator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            from evolution.code_generator import CodeGenerator

            generator = CodeGenerator(api_key="test-key", backend="anthropic")
            result = generator.generate(task_spec)

            assert result["success"] is True

    def test_generate_with_empty_optional_params(self, task_spec, mock_response):
        """测试空的可选参数"""
        with patch("evolution.code_generator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            from evolution.code_generator import CodeGenerator

            generator = CodeGenerator(api_key="test-key", backend="anthropic")
            result = generator.generate(
                task_spec,
                previous_code=None,
                previous_score=None,
                failed_tests=None,
                strategy=None,
            )

            assert result["success"] is True


class TestCodeGeneratorIntegration:
    """集成测试 - 模拟完整流程"""

    def test_full_generation_workflow(self):
        """测试完整的生成流程"""
        task_spec = {
            "description": "实现阶乘函数",
            "function_signature": "def factorial(n: int) -> int:",
            "requirements": ["计算n的阶乘", "n为负数时抛出ValueError", "支持n=0返回1"],
        }

        mock_response_text = """```python
def factorial(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
```"""

        with patch("evolution.code_generator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            response = MagicMock()
            response.content = [MagicMock(text=mock_response_text)]
            mock_client.messages.create.return_value = response
            mock_anthropic.return_value = mock_client

            from evolution.code_generator import CodeGenerator

            generator = CodeGenerator(
                api_key="test-key", default_temperature=0.3, backend="anthropic"
            )
            result = generator.generate(task_spec)

            assert result["success"] is True
            assert "def factorial(n: int) -> int:" in result["code"]
            assert "raise ValueError" in result["code"]
            assert "return 1" in result["code"]

            # 验证 API 调用参数
            call_args = mock_client.messages.create.call_args
            assert call_args[1]["model"] == CodeGenerator.DEFAULT_MODEL
            assert call_args[1]["temperature"] == 0.3
            assert call_args[1]["max_tokens"] == 4096
