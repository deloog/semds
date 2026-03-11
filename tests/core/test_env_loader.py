"""环境配置加载器测试模块

测试 env_loader 模块的功能
包括环境变量加载、API Key 检查、LLM 配置获取等
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestLoadEnv:
    """测试 load_env 函数"""

    def test_load_env_file_not_exists(self, monkeypatch, tmp_path, capsys):
        """测试 .env 文件不存在的情况"""
        from core.env_loader import load_env

        # 模拟 Path.exists 返回 False
        with patch.object(Path, "exists", return_value=False):
            result = load_env()

        assert result == {}
        captured = capsys.readouterr()
        assert "未找到" in captured.out or "使用系统环境变量" in captured.out

    def test_load_env_file_exists(self, tmp_path, monkeypatch):
        """测试成功加载 .env 文件"""
        from core.env_loader import load_env

        # 在当前目录创建临时 .env 文件
        env_content = """
# 这是注释
TEST_KEY1=value1
TEST_KEY2=value2
"""
        # 在当前工作目录创建临时文件
        temp_env = Path(".env.test")
        temp_env.write_text(env_content, encoding="utf-8")

        try:
            # 确保环境变量不存在
            monkeypatch.delenv("TEST_KEY1", raising=False)
            monkeypatch.delenv("TEST_KEY2", raising=False)

            result = load_env(".env.test")

            assert "TEST_KEY1" in result
            assert "TEST_KEY2" in result
            assert result["TEST_KEY1"] == "value1"
            assert result["TEST_KEY2"] == "value2"
            assert os.environ.get("TEST_KEY1") == "value1"
            assert os.environ.get("TEST_KEY2") == "value2"
        finally:
            # 清理
            if temp_env.exists():
                temp_env.unlink()

    def test_load_env_skip_existing(self, tmp_path, monkeypatch):
        """测试不覆盖已存在的环境变量"""
        from core.env_loader import load_env

        # 预先设置环境变量
        monkeypatch.setenv("EXISTING_KEY", "existing_value")

        # 在当前工作目录创建临时文件
        temp_env = Path(".env.test.skip")
        temp_env.write_text("EXISTING_KEY=env_file_value\n", encoding="utf-8")

        try:
            result = load_env(".env.test.skip")

            # 已存在的环境变量不应被覆盖
            assert "EXISTING_KEY" not in result
            assert os.environ.get("EXISTING_KEY") == "existing_value"
        finally:
            if temp_env.exists():
                temp_env.unlink()

    def test_load_env_empty_lines_and_comments(self, tmp_path, monkeypatch):
        """测试跳过空行和注释"""
        from core.env_loader import load_env

        env_content = """
# 注释行

  # 带空格的注释
KEY1=value1

KEY2=value2
# 中间注释
KEY3=value3
"""
        temp_env = Path(".env.test.comments")
        temp_env.write_text(env_content, encoding="utf-8")

        try:
            # 清理环境变量
            monkeypatch.delenv("KEY1", raising=False)
            monkeypatch.delenv("KEY2", raising=False)
            monkeypatch.delenv("KEY3", raising=False)

            result = load_env(".env.test.comments")

            assert len(result) == 3
            assert result["KEY1"] == "value1"
            assert result["KEY2"] == "value2"
            assert result["KEY3"] == "value3"
        finally:
            if temp_env.exists():
                temp_env.unlink()

    def test_load_env_special_characters(self, monkeypatch):
        """测试特殊字符值"""
        from core.env_loader import load_env

        env_content = """
KEY_WITH_EQUALS=val=ue=with=equals
KEY_WITH_SPACES=  value with spaces  
KEY_EMPTY=
"""
        temp_env = Path(".env.test.special")
        temp_env.write_text(env_content, encoding="utf-8")

        try:
            monkeypatch.delenv("KEY_WITH_EQUALS", raising=False)
            monkeypatch.delenv("KEY_WITH_SPACES", raising=False)
            monkeypatch.delenv("KEY_EMPTY", raising=False)

            result = load_env(".env.test.special")

            assert result["KEY_WITH_EQUALS"] == "val=ue=with=equals"
            assert result["KEY_WITH_SPACES"] == "value with spaces"
            assert result["KEY_EMPTY"] == ""
        finally:
            if temp_env.exists():
                temp_env.unlink()

    def test_load_env_custom_filename(self, monkeypatch):
        """测试使用自定义文件名"""
        from core.env_loader import load_env

        # 创建自定义名称的 env 文件
        temp_env = Path("custom.env")
        temp_env.write_text("CUSTOM_KEY=custom_value\n", encoding="utf-8")

        try:
            monkeypatch.delenv("CUSTOM_KEY", raising=False)

            result = load_env("custom.env")

            assert result["CUSTOM_KEY"] == "custom_value"
        finally:
            if temp_env.exists():
                temp_env.unlink()


class TestCheckApiKey:
    """测试 check_api_key 函数"""

    def test_check_api_key_deepseek_configured(self, monkeypatch):
        """测试 DeepSeek API Key 已配置"""
        from core.env_loader import check_api_key

        monkeypatch.setenv("DEEPSEEK_API_KEY", "test_deepseek_key")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        ready, message = check_api_key()

        assert ready is True
        assert "DEEPSEEK_API_KEY" in message

    def test_check_api_key_anthropic_configured(self, monkeypatch):
        """测试 Anthropic API Key 已配置"""
        from core.env_loader import check_api_key

        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_key")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        ready, message = check_api_key()

        assert ready is True
        assert "ANTHROPIC_API_KEY" in message

    def test_check_api_key_openai_configured(self, monkeypatch):
        """测试 OpenAI API Key 已配置"""
        from core.env_loader import check_api_key

        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")

        ready, message = check_api_key()

        assert ready is True
        assert "OPENAI_API_KEY" in message

    def test_check_api_key_none_configured(self, monkeypatch):
        """测试没有配置任何 API Key"""
        from core.env_loader import check_api_key

        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        ready, message = check_api_key()

        assert ready is False
        assert "未找到" in message or "API Key" in message
        assert "DEEPSEEK_API_KEY" in message
        assert "ANTHROPIC_API_KEY" in message
        assert "OPENAI_API_KEY" in message

    def test_check_api_key_priority_deepseek(self, monkeypatch):
        """测试 DeepSeek 优先于其他 Key"""
        from core.env_loader import check_api_key

        # 同时设置多个 Key
        monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek_key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic_key")
        monkeypatch.setenv("OPENAI_API_KEY", "openai_key")

        ready, message = check_api_key()

        assert ready is True
        assert "DEEPSEEK_API_KEY" in message


class TestGetActiveLlmConfig:
    """测试 get_active_llm_config 函数"""

    def test_get_active_llm_config_deepseek(self, monkeypatch):
        """测试获取 DeepSeek 配置"""
        from core.env_loader import get_active_llm_config

        monkeypatch.setenv("DEEPSEEK_API_KEY", "test_deepseek_key")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        config = get_active_llm_config()

        assert config is not None
        assert config["backend"] == "deepseek"
        assert config["api_key"] == "test_deepseek_key"
        assert config["base_url"] == "https://api.deepseek.com"
        assert config["model"] == "deepseek-chat"

    def test_get_active_llm_config_deepseek_custom(self, monkeypatch):
        """测试 DeepSeek 自定义配置"""
        from core.env_loader import get_active_llm_config

        monkeypatch.setenv("DEEPSEEK_API_KEY", "test_deepseek_key")
        monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://custom.deepseek.com")
        monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-coder")

        config = get_active_llm_config()

        assert config["backend"] == "deepseek"
        assert config["base_url"] == "https://custom.deepseek.com"
        assert config["model"] == "deepseek-coder"

    def test_get_active_llm_config_anthropic(self, monkeypatch):
        """测试获取 Anthropic 配置"""
        from core.env_loader import get_active_llm_config

        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_key")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        config = get_active_llm_config()

        assert config is not None
        assert config["backend"] == "anthropic"
        assert config["api_key"] == "test_anthropic_key"
        assert config["base_url"] == "https://api.anthropic.com"
        assert config["model"] == "claude-sonnet-4-20250514"

    def test_get_active_llm_config_anthropic_custom_model(self, monkeypatch):
        """测试 Anthropic 自定义模型"""
        from core.env_loader import get_active_llm_config

        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_key")
        monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-4")

        config = get_active_llm_config()

        assert config["backend"] == "anthropic"
        assert config["model"] == "claude-opus-4"

    def test_get_active_llm_config_openai(self, monkeypatch):
        """测试获取 OpenAI 配置"""
        from core.env_loader import get_active_llm_config

        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")

        config = get_active_llm_config()

        assert config is not None
        assert config["backend"] == "openai"
        assert config["api_key"] == "test_openai_key"
        assert config["base_url"] == "https://api.openai.com/v1"
        assert config["model"] == "gpt-4"

    def test_get_active_llm_config_openai_custom_model(self, monkeypatch):
        """测试 OpenAI 自定义模型"""
        from core.env_loader import get_active_llm_config

        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4-turbo")

        config = get_active_llm_config()

        assert config["backend"] == "openai"
        assert config["model"] == "gpt-4-turbo"

    def test_get_active_llm_config_priority(self, monkeypatch):
        """测试配置优先级：DeepSeek > Anthropic > OpenAI"""
        from core.env_loader import get_active_llm_config

        # 设置所有 Key，验证优先级
        monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek_key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic_key")
        monkeypatch.setenv("OPENAI_API_KEY", "openai_key")

        config = get_active_llm_config()
        assert config["backend"] == "deepseek"

        # 移除 DeepSeek，应该返回 Anthropic
        monkeypatch.delenv("DEEPSEEK_API_KEY")
        config = get_active_llm_config()
        assert config["backend"] == "anthropic"

        # 移除 Anthropic，应该返回 OpenAI
        monkeypatch.delenv("ANTHROPIC_API_KEY")
        config = get_active_llm_config()
        assert config["backend"] == "openai"

    def test_get_active_llm_config_none(self, monkeypatch):
        """测试没有配置任何 LLM"""
        from core.env_loader import get_active_llm_config

        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        config = get_active_llm_config()

        assert config is None


class TestIntegration:
    """集成测试：测试完整工作流"""

    def test_load_env_and_get_config(self, monkeypatch):
        """测试加载环境文件后获取配置"""
        from core.env_loader import check_api_key, get_active_llm_config, load_env

        # 创建临时 .env 文件
        temp_env = Path(".env.test.integration")
        env_content = """
DEEPSEEK_API_KEY=integration_test_key
DEEPSEEK_MODEL=deepseek-coder
"""
        temp_env.write_text(env_content, encoding="utf-8")

        try:
            # 清理环境变量
            monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
            monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)

            # 加载环境变量
            loaded = load_env(".env.test.integration")
            assert "DEEPSEEK_API_KEY" in loaded

            # 检查 API Key
            ready, message = check_api_key()
            assert ready is True

            # 获取配置
            config = get_active_llm_config()
            assert config is not None
            assert config["backend"] == "deepseek"
            assert config["api_key"] == "integration_test_key"
            assert config["model"] == "deepseek-coder"
        finally:
            if temp_env.exists():
                temp_env.unlink()

    def test_env_priority_over_file(self, monkeypatch):
        """测试环境变量优先于 .env 文件"""
        from core.env_loader import get_active_llm_config, load_env

        # 预先设置环境变量
        monkeypatch.setenv("DEEPSEEK_API_KEY", "env_var_key")
        monkeypatch.setenv("DEEPSEEK_MODEL", "env_var_model")

        # 创建临时 .env 文件（应该被忽略）
        temp_env = Path(".env.test.priority")
        env_content = """
DEEPSEEK_API_KEY=file_key
DEEPSEEK_MODEL=file_model
"""
        temp_env.write_text(env_content, encoding="utf-8")

        try:
            # 加载 .env 文件
            load_env(".env.test.priority")

            # 验证环境变量没有被覆盖
            config = get_active_llm_config()
            assert config["api_key"] == "env_var_key"
            assert config["model"] == "env_var_model"
        finally:
            if temp_env.exists():
                temp_env.unlink()


class TestEdgeCases:
    """边界情况测试"""

    def test_load_env_malformed_lines(self, monkeypatch):
        """测试格式错误的行"""
        from core.env_loader import load_env

        # 注意: =VALUE_WITHOUT_KEY 会导致空key，Windows不允许，所以去掉
        env_content = """
VALID_KEY=valid_value
MALFORMED_LINE_WITHOUT_EQUALS
KEY_WITH_MULTIPLE=equals=signs=here
"""
        temp_env = Path(".env.test.malformed")
        temp_env.write_text(env_content, encoding="utf-8")

        try:
            monkeypatch.delenv("VALID_KEY", raising=False)
            monkeypatch.delenv("KEY_WITH_MULTIPLE", raising=False)

            result = load_env(".env.test.malformed")

            # 有效行应该被加载
            assert result["VALID_KEY"] == "valid_value"
            assert result["KEY_WITH_MULTIPLE"] == "equals=signs=here"
            # 无效行应该被忽略
            assert len(result) == 2
        finally:
            if temp_env.exists():
                temp_env.unlink()

    def test_load_env_unicode_content(self, monkeypatch):
        """测试 Unicode 内容"""
        from core.env_loader import load_env

        env_content = """
UNICODE_KEY=中文值
EMOJI_KEY=🚀🎉
"""
        temp_env = Path(".env.test.unicode")
        temp_env.write_text(env_content, encoding="utf-8")

        try:
            monkeypatch.delenv("UNICODE_KEY", raising=False)
            monkeypatch.delenv("EMOJI_KEY", raising=False)

            result = load_env(".env.test.unicode")

            assert result["UNICODE_KEY"] == "中文值"
            assert result["EMOJI_KEY"] == "🚀🎉"
        finally:
            if temp_env.exists():
                temp_env.unlink()

    def test_load_env_quoted_values(self, monkeypatch):
        """测试带引号的值"""
        from core.env_loader import load_env

        env_content = """
QUOTED_KEY="quoted_value"
SINGLE_QUOTED='single_quoted'
MIXED_QUOTES="mixed'
"""
        temp_env = Path(".env.test.quoted")
        temp_env.write_text(env_content, encoding="utf-8")

        try:
            monkeypatch.delenv("QUOTED_KEY", raising=False)
            monkeypatch.delenv("SINGLE_QUOTED", raising=False)
            monkeypatch.delenv("MIXED_QUOTES", raising=False)

            result = load_env(".env.test.quoted")

            # 引号应该作为值的一部分保留
            assert result["QUOTED_KEY"] == '"quoted_value"'
            assert result["SINGLE_QUOTED"] == "'single_quoted'"
            assert result["MIXED_QUOTES"] == "\"mixed'"
        finally:
            if temp_env.exists():
                temp_env.unlink()

    def test_empty_api_key_considered_unset(self, monkeypatch):
        """测试空字符串 API Key 被视为未设置"""
        from core.env_loader import check_api_key, get_active_llm_config

        monkeypatch.setenv("DEEPSEEK_API_KEY", "")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        config = get_active_llm_config()
        assert config is None

        ready, _ = check_api_key()
        assert ready is False
