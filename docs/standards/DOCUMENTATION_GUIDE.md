# SEMDS 文档编写规范

**版本**: v1.0  
**目标**: 确保文档清晰、完整、可维护  
**范围**: 所有项目文档

---

## 📝 文档类型

| 类型 | 位置 | 用途 |
|------|------|------|
| **README** | 项目根目录 | 项目介绍、快速开始 |
| **API文档** | `docs/api/` | 接口说明 |
| **架构文档** | `docs/architecture/` | 系统设计 |
| **规范文档** | `docs/standards/` | 开发规范 |
| **实验报告** | `docs/experiments/` | 实验记录 |
| **代码注释** | 代码中 | 实现细节 |

---

## 📄 README 规范

### 必须包含的内容
```markdown
# 项目名称

## 一句话描述
简短描述项目是什么、解决什么问题。

## 核心特性
- 特性1
- 特性2
- 特性3

## 快速开始
### 安装
```bash
pip install xxx
```

### 使用示例
```python
from xxx import yyy
result = yyy.do_something()
```

## 项目结构
```
project/
├── src/          # 源代码
├── tests/        # 测试
└── docs/         # 文档
```

## 技术栈
- Python 3.11+
- xxx库
- yyy工具

## 许可证
MIT
```

---

## 💻 代码注释规范

### 函数/方法注释
```python
def function_name(param1: type1, param2: type2) -> return_type:
    """
    简短描述函数做什么。
    
    详细描述（如果需要）：解释算法、边界条件、
    副作用等。
    
    Args:
        param1: 参数1的说明
        param2: 参数2的说明
        
    Returns:
        返回值的说明
        
    Raises:
        ValueError: 什么情况下抛出
        TimeoutError: 什么情况下抛出
        
    Example:
        >>> result = function_name("input", 42)
        >>> print(result)
        "output"
        
    Note:
        额外的注意事项
    """
```

### 类注释
```python
class ClassName:
    """
    类的简短描述。
    
    详细描述类的用途、设计思路、使用场景。
    
    Attributes:
        attr1: 属性1说明
        attr2: 属性2说明
        
    Example:
        >>> obj = ClassName()
        >>> obj.method()
    """
```

### 模块注释
```python
"""
模块名称

模块功能描述。

Exports:
    - function1: 功能1
    - Class1: 类1
    
Note:
    使用注意事项
"""
```

### 行内注释
```python
# ✅ 解释"为什么"而不是"做什么"
result = calculate(x)  # 使用快速算法，牺牲精度换取速度

# ❌ 不要解释显而易见的代码
result = calculate(x)  # 计算结果
```

---

## 🎨 Markdown 规范

### 标题层次
```markdown
# 文档标题（只能有一个）

## 主要章节

### 子章节

#### 具体小节（尽量不用）
```

### 代码块
```markdown
```python
# 指定语言
def example():
    pass
```
```

### 表格
```markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |
| D   | E   | F   |
```

### 列表
```markdown
- 无序列表项
  - 子项
  - 子项

1. 有序列表项
2. 有序列表项
```

---

## 🔄 文档维护

### 版本控制
- 文档与代码一起版本控制
- 文档变更应在PR中说明
- 废弃功能需标记`[DEPRECATED]`

### 更新频率
- README：每次发布更新
- API文档：每次API变更更新
- 架构文档：每季度审查
- 规范文档：每季度审查

---

## ✅ 文档审查清单

```markdown
- [ ] 文档结构清晰
- [ ] 代码示例可运行
- [ ] 链接有效
- [ ] 无拼写错误
- [ ] 图片/图表清晰
```

---

**文档是代码的一部分，必须与代码同步维护**
