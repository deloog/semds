"""
SEMDS 环境配置加载器

自动从 .env 文件加载环境变量
"""

import os
from pathlib import Path
from typing import Any, Optional


def load_env(env_file: str = ".env") -> dict:
    """
    从 .env 文件加载环境变量。

    Args:
        env_file: 环境变量文件路径 (默认: .env)

    Returns:
        加载的变量字典
    """
    # 从项目根目录查找
    project_root = Path(__file__).parent.parent
    env_path = project_root / env_file

    if not env_path.exists():
        # 尝试从当前目录查找
        env_path = Path(env_file)

    if not env_path.exists():
        print(f"[WARN]  未找到 {env_file} 文件，使用系统环境变量")
        return {}

    loaded = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue

            # 解析 KEY=VALUE
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # 如果环境变量已存在，不覆盖
                if key not in os.environ:
                    os.environ[key] = value
                    loaded[key] = value

    if loaded:
        print(f"[OK] Loaded {len(loaded)} variables from {env_path}")

    return loaded


def check_api_key() -> tuple[bool, str]:
    """
    检查是否配置了至少一个 API Key。

    Returns:
        (是否就绪, 提示信息)
    """
    api_keys = ["DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]

    for key in api_keys:
        if os.environ.get(key):
            return True, f"[OK] 已配置: {key}"

    return False, (
        "[FAIL] 未找到 API Key\n"
        "请在 .env 文件中设置以下任一环境变量:\n"
        "  - DEEPSEEK_API_KEY (推荐)\n"
        "  - ANTHROPIC_API_KEY\n"
        "  - OPENAI_API_KEY"
    )


def get_active_llm_config() -> Optional[dict[str, Any]]:
    """
    获取当前激活的 LLM 配置。

    Returns:
        配置字典，包含 backend, api_key, base_url, model
    """
    # 优先检查 DeepSeek
    if os.environ.get("DEEPSEEK_API_KEY"):
        return {
            "backend": "deepseek",
            "api_key": os.environ["DEEPSEEK_API_KEY"],
            "base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        }

    # 检查 Anthropic
    if os.environ.get("ANTHROPIC_API_KEY"):
        return {
            "backend": "anthropic",
            "api_key": os.environ["ANTHROPIC_API_KEY"],
            "base_url": "https://api.anthropic.com",
            "model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        }

    # 检查 OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        return {
            "backend": "openai",
            "api_key": os.environ["OPENAI_API_KEY"],
            "base_url": "https://api.openai.com/v1",
            "model": os.environ.get("OPENAI_MODEL", "gpt-4"),
        }

    return None


if __name__ == "__main__":
    # 测试加载
    load_env()

    # 检查 API Key
    ready, message = check_api_key()
    print(f"\n{message}")

    # 显示配置
    config = get_active_llm_config()
    if config:
        print("\n当前 LLM 配置:")
        print(f"  Backend: {config['backend']}")
        print(f"  Model: {config['model']}")
        print(f"  API Key: {'*' * 8}{config['api_key'][-4:]}")
