# Mother System Coding Standards
# 代码规范约束 - 强制遵循

## 1. 类型约束 (Type Safety)
- 所有函数必须有类型注解
- 使用 mypy --strict 检查
- 禁止 Any 类型，必须用具体类型或 Union

## 2. 文档约束 (Documentation)
- 所有公共函数必须有 docstring
- 使用 Google 风格文档
- 复杂逻辑必须加行内注释

## 3. 错误处理 (Error Handling)
- 禁止裸 except:，必须捕获具体异常
- 所有外部调用必须有重试机制
- 错误日志必须包含上下文

## 4. 测试约束 (Testing)
- 新代码必须有单元测试
- 覆盖率不得低于 80%
- 使用 pytest 框架

## 5. 代码风格 (Style)
- 遵循 PEP 8
- 使用 black 格式化
- 行长度不超过 100 字符

## 6. 安全检查 (Security)
- 禁止 eval/exec
- 禁止硬编码密钥
- 输入必须验证
