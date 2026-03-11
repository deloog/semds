# SEMDS 配置管理规范

**版本**: v1.0  
**强制执行**: ✅ 是  
**适用范围**: 所有配置文件、环境变量

---

## 🎯 核心原则

```
1. 环境隔离 - 开发/测试/生产配置分离
2. 敏感信息安全 - 密钥不提交到代码库
3. 显式优于隐式 - 配置项有默认值和文档
4. 可验证性 - 配置可以被验证和审计
```

---

## 📁 配置文件结构

```
.
├── .env.example          # 环境变量模板（提交到git）
├── .env                  # 本地环境变量（不提交）
├── .env.production       # 生产环境配置（不提交，安全存储）
├── config/
│   ├── __init__.py
│   ├── default.py        # 默认配置
│   ├── development.py    # 开发环境
│   ├── testing.py        # 测试环境
│   └── production.py     # 生产环境
└── pyproject.toml        # 工具配置
```

---

## 🔐 环境变量管理

### .env.example（模板）

```bash
# SEMDS 环境变量模板
# 复制此文件为 .env 并填入实际值

# ============================================
# 必需配置
# ============================================

# LLM API密钥（必需）
ANTHROPIC_API_KEY=your_api_key_here
OPENAI_API_KEY=optional_openai_key

# 数据库（必需）
DATABASE_URL=sqlite:///semds.db

# ============================================
# 应用配置
# ============================================

# 环境: development, testing, production
ENVIRONMENT=development

# 调试模式（生产环境必须为false）
DEBUG=true

# 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# ============================================
# 安全配置
# ============================================

# 生成随机密钥: openssl rand -hex 32
SECRET_KEY=change_this_in_production

# JWT过期时间（小时）
JWT_EXPIRATION_HOURS=24

# ============================================
# 性能配置
# ============================================

# 并发任务数
MAX_CONCURRENT_TASKS=3

# 代码生成超时（秒）
GENERATION_TIMEOUT=30

# 沙盒内存限制（MB）
SANDBOX_MEMORY_LIMIT=128

# ============================================
# 可选配置
# ============================================

# Sentry DSN（错误追踪）
# SENTRY_DSN=https://xxx@yyy.ingest.sentry.io/zzz

# Redis缓存URL
# REDIS_URL=redis://localhost:6379/0
```

### .gitignore

```gitignore
# 环境变量（敏感信息）
.env
.env.*
!.env.example

# 其他敏感文件
*.pem
*.key
secrets/
```

---

## 🐍 Python配置类

### 配置基类

```python
# config/default.py

import os
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """SEMDS配置基类。"""
    
    # 环境
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    
    # 安全
    SECRET_KEY: str = Field(..., min_length=32)
    JWT_EXPIRATION_HOURS: int = Field(default=24)
    
    # API密钥
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # 数据库
    DATABASE_URL: str = Field(default="sqlite:///semds.db")
    
    # 性能
    MAX_CONCURRENT_TASKS: int = Field(default=3, ge=1, le=10)
    GENERATION_TIMEOUT: int = Field(default=30, ge=5, le=300)
    SANDBOX_MEMORY_LIMIT: int = Field(default=128, ge=64, le=1024)
    
    # 可选
    SENTRY_DSN: Optional[str] = None
    REDIS_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """验证日志级别。"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v, values):
        """验证密钥强度。"""
        if values.get("ENVIRONMENT") == "production" and v == "change_this_in_production":
            raise ValueError("Production SECRET_KEY must be changed!")
        return v
```

### 环境特定配置

```python
# config/development.py
from .default import Settings

class DevelopmentSettings(Settings):
    """开发环境配置。"""
    
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # 开发友好设置
    GENERATION_TIMEOUT: int = 60  # 更长超时方便调试

# config/production.py
from .default import Settings

class ProductionSettings(Settings):
    """生产环境配置。"""
    
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    
    # 生产优化
    MAX_CONCURRENT_TASKS: int = 5
    
    class Config:
        env_file = ".env.production"
```

### 配置工厂

```python
# config/__init__.py
import os
from typing import Type

from .default import Settings
from .development import DevelopmentSettings
from .production import ProductionSettings
from .testing import TestingSettings

def get_settings() -> Settings:
    """获取当前环境配置。"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    settings_map: dict[str, Type[Settings]] = {
        "development": DevelopmentSettings,
        "testing": TestingSettings,
        "production": ProductionSettings,
    }
    
    settings_class = settings_map.get(env, DevelopmentSettings)
    return settings_class()

# 全局配置实例
settings = get_settings()
```

---

## 🔍 配置验证

### 启动时验证

```python
# core/validate_config.py

def validate_configuration():
    """启动时验证配置。"""
    errors = []
    warnings = []
    
    # 必需配置
    if not settings.ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY is required")
    
    # 安全警告
    if settings.ENVIRONMENT == "production":
        if settings.DEBUG:
            errors.append("DEBUG must be False in production")
        if len(settings.SECRET_KEY) < 32:
            errors.append("SECRET_KEY too weak")
        if "change_this" in settings.SECRET_KEY.lower():
            errors.append("Default SECRET_KEY must be changed")
    
    # 性能警告
    if settings.MAX_CONCURRENT_TASKS > 10:
        warnings.append("MAX_CONCURRENT_TASKS > 10 may cause resource issues")
    
    # 报告结果
    if errors:
        raise ConfigurationError(f"Config errors: {errors}")
    
    if warnings:
        logger.warning(f"Config warnings: {warnings}")
    
    logger.info("Configuration validated successfully")
```

---

## 📝 配置文档

### 配置项文档

```python
# config/README.md
"""
# 配置说明

## 必需配置

### ANTHROPIC_API_KEY
- **类型**: string
- **必需**: 是
- **描述**: Claude API密钥
- **获取方式**: https://console.anthropic.com/

### DATABASE_URL
- **类型**: string
- **必需**: 是
- **默认**: sqlite:///semds.db
- **描述**: 数据库连接URL

## 可选配置

### MAX_CONCURRENT_TASKS
- **类型**: integer
- **范围**: 1-10
- **默认**: 3
- **描述**: 最大并发进化任务数
- **建议**: 根据CPU核心数设置

### GENERATION_TIMEOUT
- **类型**: integer
- **单位**: 秒
- **范围**: 5-300
- **默认**: 30
- **描述**: 代码生成超时时间
"""
```

---

## 🔄 配置变更流程

### 添加新配置项

```markdown
1. 在 config/default.py 添加字段
2. 添加验证器（如需要）
3. 更新 .env.example
4. 更新配置文档
5. 更新 CHANGELOG
```

### 配置变更检查清单

```markdown
- [ ] 配置项有默认值
- [ ] 配置项有验证
- [ ] .env.example已更新
- [ ] 文档已更新
- [ ] 各环境配置已检查
```

---

## 🚫 禁止事项

```markdown
❌ 禁止将密钥提交到git
❌ 禁止使用默认密钥生产环境
❌ 禁止在代码中硬编码配置
❌ 禁止不同环境使用相同密钥
❌ 禁止日志输出敏感配置
```

---

## ✅ 配置检查清单

```markdown
## 配置检查清单

### 开发环境
- [ ] .env文件已创建
- [ ] 必需配置已填写
- [ ] DEBUG=true
- [ ] LOG_LEVEL=DEBUG

### 测试环境
- [ ] 使用独立数据库
- [ ] 使用测试API密钥
- [ ] 资源限制较低

### 生产环境
- [ ] DEBUG=false
- [ ] 密钥已更改
- [ ] LOG_LEVEL=WARNING
- [ ] 配置了监控
- [ ] 配置了告警
```

---

**最后更新**: 2026-03-07  
**维护者**: 运维团队
