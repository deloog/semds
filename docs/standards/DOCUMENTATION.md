# SEMDS 文档规范

**版本**: v1.0  
**强制执行**: ✅ 是  
**适用范围**: 所有文档

---

## 🎯 核心原则

```
1. 代码即文档 - 好的代码+docstring胜过单独文档
2. 单一真相源 - 信息不重复，一处更新处处生效
3. 渐进式详细 - 从概览到细节分层组织
4. 可执行性 - 示例代码可直接运行
```

---

## 📚 文档类型

### 文档分类

| 类型 | 位置 | 受众 | 更新频率 |
|-----|------|-----|---------|
| 架构文档 | docs/architecture/ | 开发者 | 架构变更时 |
| API文档 | docs/api/ | API用户 | API变更时 |
| 开发规范 | docs/standards/ | 开发者 | 规范变更时 |
| 用户指南 | docs/guides/ | 最终用户 | 功能发布时 |
| 路线图 | docs/roadmaps/ | 项目管理 | 迭代规划时 |
| 代码注释 | 源码中 | 开发者 | 代码变更时 |

---

## 📝 代码文档

### Docstring规范

```python
# ✅ Google风格
def generate_code(
    task: TaskSpec,
    strategy: Strategy,
    timeout: float = 30.0
) -> GenerationResult:
    """生成代码实现。
    
    使用指定的策略和LLM后端生成代码。
    支持迭代优化，可以使用previous_attempts传入
    之前的尝试结果。
    
    Args:
        task: 任务规格，包含需求描述
        strategy: 进化策略配置
        timeout: 生成超时时间（秒），默认30
        
    Returns:
        GenerationResult包含:
        - code: 生成的代码
        - success: 是否成功
        - execution_time_ms: 执行时间
        
    Raises:
        GenerationError: 生成失败
        TimeoutError: 生成超时
        ValueError: 参数无效
        
    Example:
        >>> task = TaskSpec(name="calc", requirements=["add", "sub"])
        >>> result = await generator.generate(task, strategy)
        >>> if result.success:
        ...     print(result.code)
    """
    pass

# ✅ NumPy风格
class CodeGenerator:
    """代码生成器。
    
    负责调用LLM API生成代码实现。
    
    Parameters
    ----------
    backend : str
        LLM后端名称
    api_key : str
        API密钥
    config : GenerationConfig, optional
        生成配置
        
    Attributes
    ----------
    backend : str
        当前使用的后端
    config : GenerationConfig
        当前配置
        
    Methods
    -------
    generate(task)
        生成代码
    validate_config()
        验证配置
    """
    pass
```

### 注释规范

```python
# ✅ 解释为什么，而非是什么
# 使用指数退避避免API限流
for attempt in range(max_retries):
    delay = base_delay * (2 ** attempt)
    await asyncio.sleep(delay)

# ❌ 重复代码 obvious 的内容
# 增加计数器
counter += 1

# ✅ 标记TODO（必须关联Issue）
# TODO(#123): 添加缓存机制提升性能
def expensive_operation():
    pass

# ✅ 解释复杂算法
# 使用动态规划计算最优策略
# dp[i][j] 表示前i代使用策略j的最大得分
dp = [[0] * n_strategies for _ in range(n_generations)]
```

---

## 📖 README规范

### 模块README

```markdown
# 模块名称

一句话描述模块用途。

## 职责

- 职责1
- 职责2

## 主要组件

| 组件 | 职责 |
|-----|------|
| ComponentA | 做X |
| ComponentB | 做Y |

## 使用示例

```python
from module import Component

component = Component()
result = component.do_something()
```

## 测试

```bash
pytest tests/test_module.py -v
```
```

---

## 📘 架构文档

### 架构决策记录(ADR)

```markdown
# ADR-XXX: 决策标题

## 状态
- 提议 / 已接受 / 已废弃

## 背景
描述需要解决的问题。

## 决策
描述做出的决策。

## 后果
正面后果和负面后果。

## 替代方案
考虑过的其他方案及未选择的原因。
```

---

## 📋 文档同步规范

### 代码变更时

```markdown
## 文档同步检查清单

代码修改后，检查并更新：

- [ ] 代码中的docstring
- [ ] 模块README.md
- [ ] API文档（如修改API）
- [ ] 架构图（如修改架构）
- [ ] 用户指南（如影响用户）
- [ ] CHANGELOG.md
```

### 文档更新流程

```
代码变更
    ↓
检查受影响文档
    ↓
更新docstring
    ↓
更新相关Markdown文档
    ↓
验证示例代码可运行
    ↓
提交（包含文档变更）
```

---

## 🎨 文档格式

### Markdown规范

```markdown
# 一级标题 - 文档标题

## 二级标题 - 主要章节

### 三级标题 - 小节

**粗体**用于强调
`代码`用于代码和文件名

- 列表项1
- 列表项2

1. 有序1
2. 有序2

| 表格 | 列2 |
|-----|-----|
| 数据 | 数据 |

> 引用块

```python
# 代码块
print("hello")
```
```

---

## ✅ 文档质量检查

```markdown
## 文档检查清单

### 完整性
- [ ] 所有公共API有docstring
- [ ] 复杂算法有注释
- [ ] 有使用示例
- [ ] 有错误处理说明

### 准确性
- [ ] 示例代码可运行
- [ ] 链接可访问
- [ ] 版本信息正确
- [ ] 与代码一致

### 可读性
- [ ] 无错别字
- [ ] 语法正确
- [ ] 结构清晰
- [ ] 长度适中
```

---

**最后更新**: 2026-03-07  
**维护者**: 文档团队
