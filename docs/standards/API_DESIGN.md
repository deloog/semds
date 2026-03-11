# SEMDS API设计规范

**版本**: v1.0  
**强制执行**: ✅ 是  
**适用范围**: REST API, WebSocket API, Python API

---

## 🎯 核心原则

```
1. 一致性 - 相同的模式解决相同的问题
2. 可预测性 - 接口行为符合直觉
3. 可扩展性 - 预留扩展点，不破坏现有功能
4. 可发现性 - 文档清晰，错误信息有用
```

---

## 📐 REST API设计

### URL设计

```
# ✅ 正确的URL设计
GET    /api/tasks              # 列表
POST   /api/tasks              # 创建
GET    /api/tasks/{id}         # 详情
PUT    /api/tasks/{id}         # 全量更新
PATCH  /api/tasks/{id}         # 部分更新
DELETE /api/tasks/{id}         # 删除

# 动作使用POST + 动词
POST   /api/tasks/{id}/start   # 启动进化
POST   /api/tasks/{id}/pause   # 暂停

# ❌ 错误的URL设计
GET    /api/getTasks           # 包含动词
POST   /api/tasks/create       # 多余动词
GET    /api/tasks/{id}/delete  # 应该用DELETE
```

### 响应格式

```python
# 成功响应
{
    "success": true,
    "data": {
        "id": "task-123",
        "name": "calculator",
        "status": "running"
    },
    "meta": {
        "timestamp": "2024-03-07T10:00:00Z",
        "request_id": "req-abc-123"
    }
}

# 列表响应
{
    "success": true,
    "data": [
        {"id": "task-1", "name": "calc1"},
        {"id": "task-2", "name": "calc2"}
    ],
    "meta": {
        "total": 100,
        "page": 1,
        "page_size": 20,
        "has_more": true
    }
}

# 错误响应
{
    "success": false,
    "error": {
        "code": "TASK_NOT_FOUND",
        "message": "Task with id 'xxx' not found",
        "details": {
            "task_id": "xxx"
        },
        "suggestion": "Check if the task ID is correct or create a new task"
    },
    "meta": {
        "timestamp": "2024-03-07T10:00:00Z",
        "request_id": "req-abc-123"
    }
}
```

### HTTP状态码

| 状态码 | 使用场景 | 示例 |
|-------|---------|------|
| 200 | 成功 | GET成功 |
| 201 | 创建成功 | POST创建资源 |
| 204 | 成功无返回 | DELETE成功 |
| 400 | 请求错误 | 参数验证失败 |
| 401 | 未认证 | 缺少API密钥 |
| 403 | 无权限 | 访问其他用户资源 |
| 404 | 不存在 | 资源未找到 |
| 409 | 冲突 | 资源已存在 |
| 422 | 业务逻辑错误 | 无法启动已暂停的任务 |
| 429 | 限流 | 请求太频繁 |
| 500 | 服务器错误 | 内部错误 |

### 分页规范

```python
# 请求参数
GET /api/tasks?page=1&page_size=20&sort=-created_at

# 参数说明
# page: 页码，从1开始
# page_size: 每页数量，默认20，最大100
# sort: 排序字段，-表示降序

# 响应
{
    "success": true,
    "data": [...],
    "meta": {
        "total": 95,
        "page": 1,
        "page_size": 20,
        "total_pages": 5,
        "has_next": true,
        "has_prev": false
    }
}
```

---

## 🔌 WebSocket设计

### 连接管理

```javascript
// 连接URL
ws://localhost:8000/ws/tasks/{task_id}

// 连接消息
{
    "type": "subscribe",
    "channels": ["progress", "logs"]
}
```

### 消息格式

```javascript
// 服务端推送
{
    "type": "generation.completed",
    "timestamp": "2024-03-07T10:00:00Z",
    "data": {
        "generation": 5,
        "score": 0.85,
        "code": "def calculate(a, b): ..."
    }
}

// 错误推送
{
    "type": "error",
    "timestamp": "2024-03-07T10:00:00Z",
    "error": {
        "code": "SANDBOX_TIMEOUT",
        "message": "Code execution timed out"
    }
}
```

---

## 🐍 Python API设计

### 模块设计

```python
# ✅ 好的模块设计 - 清晰的公开API
# semds/evolution/__init__.py

from .code_generator import CodeGenerator
from .evaluator import DualEvaluator
from .strategy_optimizer import StrategyOptimizer

__all__ = [
    "CodeGenerator",
    "DualEvaluator", 
    "StrategyOptimizer",
]
```

### 类设计

```python
# ✅ 好的类设计
class CodeGenerator:
    """代码生成器。
    
    负责调用LLM API生成代码实现。
    
    Example:
        >>> generator = CodeGenerator(backend="claude")
        >>> result = await generator.generate(task_spec)
        >>> print(result.code)
    
    Args:
        backend: LLM后端名称
        api_key: API密钥
        config: 生成配置
    """
    
    def __init__(
        self,
        backend: str,
        api_key: str,
        config: Optional[GenerationConfig] = None
    ):
        self.backend = backend
        self.api_key = api_key
        self.config = config or GenerationConfig()
    
    async def generate(
        self,
        task: TaskSpec,
        previous_attempts: Optional[List[GenerationResult]] = None
    ) -> GenerationResult:
        """生成代码。
        
        Args:
            task: 任务规格
            previous_attempts: 之前的尝试结果（用于迭代优化）
            
        Returns:
            GenerationResult包含生成的代码和元数据
            
        Raises:
            GenerationError: 生成失败
            TimeoutError: 生成超时
        """
        # 实现...
    
    def validate_config(self) -> bool:
        """验证配置有效性。
        
        Returns:
            True如果配置有效
            
        Raises:
            ValidationError: 配置无效
        """
        # 实现...
```

### 函数设计

```python
# ✅ 好的函数设计
def calculate_fitness(
    code: str,
    test_cases: list[TestCase],
    *,
    timeout: float = 30.0,
    sandbox_config: Optional[SandboxConfig] = None
) -> FitnessResult:
    """计算代码适应度。
    
    在沙盒中执行代码并计算测试通过率。
    
    Args:
        code: 被测代码
        test_cases: 测试用例列表
        timeout: 执行超时（秒），默认30
        sandbox_config: 沙盒配置（可选）
        
    Returns:
        FitnessResult包含分数和执行信息
        
    Raises:
        ValidationError: 代码语法错误
        SandboxError: 沙盒执行失败
        TimeoutError: 执行超时
    """
    # 实现...
```

---

## 🔄 API演进

### 版本控制

```
/api/v1/tasks      # v1版本
/api/v2/tasks      # v2版本（如有重大变更）
```

### 向后兼容

```python
# ✅ 向后兼容的变更

# 1. 添加可选参数
def new_function(required_arg, new_optional=None):  # ✅
    pass

# 2. 扩展响应（不删除字段）
{
    "old_field": "value",
    "new_field": "value"  # 添加新字段 ✅
}

# 3. 废弃警告
import warnings

def old_function():
    warnings.warn(
        "old_function is deprecated, use new_function instead",
        DeprecationWarning,
        stacklevel=2
    )
```

### 破坏性变更处理

```markdown
## API变更流程

### 1. 评估影响
- [ ] 统计受影响客户端
- [ ] 评估迁移成本
- [ ] 确定废弃时间表

### 2. 渐进式废弃
1. 添加新API（并存）
2. 标记旧API为废弃（添加警告）
3. 更新文档推荐新API
4. 等待一个版本周期
5. 移除旧API

### 3. 通知用户
- 变更日志
- API文档
- 邮件通知（如需要）
```

---

## ✅ API设计检查清单

```markdown
## API设计检查清单

### URL/命名
- [ ] 使用名词而非动词
- [ ] 小写+连字符（REST）
- [ ] 层级关系清晰
- [ ] 复数形式（集合资源）

### 请求/响应
- [ ] 统一的响应格式
- [ ] 错误信息清晰
- [ ] 包含请求ID用于追踪
- [ ] 适当使用HTTP状态码

### 文档
- [ ] 每个端点都有文档
- [ ] 包含请求/响应示例
- [ ] 错误情况说明
- [ ] 字段说明完整

### 兼容性
- [ ] 变更考虑向后兼容
- [ ] 废弃API有警告
- [ ] 版本控制策略
```

---

**最后更新**: 2026-03-07  
**维护者**: API设计委员会
