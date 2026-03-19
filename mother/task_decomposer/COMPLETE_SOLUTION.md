# SEMDS Task Decomposition: Complete Solution
# 完整解决方案：任务分解 + 智能组装

## 用户的核心担忧

> "分解会不会导致文件数量的暴涨？"
> "本来一个文件200-300代码的，会不会变成五六个文件？"

**答案：不会！因为有智能组装机制。**

---

## 核心概念分离

### 两个不同的目的

| | 任务分解 | 代码组装 |
|---|---|---|
| **目的** | 为了AI执行和验证 | 为了人类维护和阅读 |
| **粒度** | 原子级（<50行） | 模块级（100-300行） |
| **关注** | 正确性、可验证性 | 可读性、可维护性 |
| **产出** | 执行计划 | 物理文件 |

### 关键洞察

> **逻辑分解 ≠ 物理分解**

- **逻辑上**：分解为原子任务（便于AI处理）
- **物理上**：组装为合适模块（便于人类维护）

---

## 完整流程

```
用户输入: "构建数据处理系统"
    │
    ▼
[递归分解器]
    │
    ├── Epic: "构建数据处理系统"
    │     ├── Story: "数据获取"
    │     │     ├── Task: "HTTP客户端"
    │     │     │     ├── Atomic: "fetch_data()" (<50行)
    │     │     │     ├── Atomic: "validate_input()" (<50行)
    │     │     │     └── Atomic: "handle_error()" (<50行)
    │     │     └── Task: "API接口"
    │     │           └── Atomic: "call_api()" (<50行)
    │     ├── Story: "数据处理"
    │     │     ├── Atomic: "parse_json()" (<50行)
    │     │     ├── Atomic: "transform_data()" (<50行)
    │     │     └── Atomic: "validate_output()" (<50行)
    │     └── Story: "数据存储"
    │           ├── Atomic: "connect_db()" (<50行)
    │           ├── Atomic: "save_record()" (<50行)
    │           └── Atomic: "close_connection()" (<50行)
    │
    ▼
[TDD执行器]
    │
    ├── 执行每个原子任务
    ├── 验证通过才继续
    └── 记录执行轨迹
    │
    ▼
[智能组装器]
    │
    ├── 按功能域分组
    │     ├── 获取相关 -> data_fetcher.py
    │     ├── 处理相关 -> data_processor.py
    │     └── 存储相关 -> data_storage.py
    │
    ├── 优化文件大小
    │     ├── <50行 -> 合并
    │     ├── 50-300行 -> 保留
    │     └── >300行 -> 拆分
    │
    └── 最终产出
          ├── data_fetcher.py (150行)
          ├── data_processor.py (180行)
          ├── data_storage.py (120行)
          └── test_data_system.py (200行)
```

---

## 智能组装策略

### 1. 功能域分组

```python
# 原子任务
- fetch_data()          # 获取数据
- validate_input()      # 验证输入
- parse_json()          # 解析JSON
- transform_data()      # 转换数据
- validate_output()     # 验证输出
- save_to_db()          # 保存数据库
- handle_error()        # 错误处理
- log_operation()       # 记录日志

# 组装后
data_fetcher.py:        # 数据获取模块
  - fetch_data()
  - validate_input()

data_processor.py:      # 数据处理模块
  - parse_json()
  - transform_data()
  - validate_output()

data_storage.py:        # 数据存储模块
  - save_to_db()
  - handle_error()
  - log_operation()
```

### 2. 文件大小控制

| 大小 | 处理策略 | 示例 |
|------|---------|------|
| <50行 | 与其他合并 | 小工具函数 -> utils.py |
| 50-150行 | 理想大小，保留 | 独立模块 |
| 150-300行 | 可接受，保留 | 复杂模块 |
| >300行 | 拆分 | 拆分为core.py + utils.py |

### 3. 组装规则

```python
ASSEMBLY_RULES = {
    # 按功能域分组
    'group_by_domain': True,
    
    # 测试文件分离
    'separate_tests': True,
    
    # 导入语句合并
    'merge_imports': True,
    
    # 文档单独文件
    'separate_docs': False,  # 可以内联
    
    # 目标文件大小
    'target_size': {
        'min': 50,
        'ideal': 150,
        'max': 300
    }
}
```

---

## 实际对比

### 场景：构建数据处理系统

#### 不使用组装（文件爆炸）

```
project/
├── fetch_data.py           (20行)  ❌ 太小
├── validate_input.py       (15行)  ❌ 太小
├── parse_json.py           (18行)  ❌ 太小
├── transform_data.py       (25行)  ❌ 太小
├── validate_output.py      (20行)  ❌ 太小
├── save_to_db.py           (30行)  ❌ 太小
├── handle_error.py         (15行)  ❌ 太小
├── log_operation.py        (12行)  ❌ 太小
└── test_fetch.py           (40行)
    ...

total: 20个文件
average: 20行/文件
maintainability: POOR
```

#### 使用智能组装（合理文件数）

```
project/
├── data_fetcher.py         (140行)  ✓ 合适
│   ├── fetch_data()
│   ├── validate_input()
│   └── retry_with_backoff()
│
├── data_processor.py       (165行)  ✓ 合适
│   ├── parse_json()
│   ├── transform_data()
│   └── validate_output()
│
├── data_storage.py         (125行)  ✓ 合适
│   ├── save_to_db()
│   ├── handle_error()
│   └── log_operation()
│
└── test_data_system.py     (210行)  ✓ 测试集中
    ├── TestDataFetcher
    ├── TestDataProcessor
    └── TestDataStorage

total: 4个文件
average: 160行/文件
maintainability: GOOD
```

**结果：20个文件 -> 4个文件，减少80%！**

---

## 质量保证机制

### 1. 分解阶段保证

```python
# 每个原子任务强制约束
AtomicTask:
    max_lines: 50        # 最多50行
    max_tokens: 500      # 最多500 token
    validation_criteria: [...]  # 验证标准
```

### 2. 组装阶段保证

```python
# 文件大小优化
if module.lines < 50:
    merge_with_related()   # 合并
    
elif module.lines > 300:
    split_into_two()       # 拆分
    
else:
    keep_as_is()           # 保留
```

### 3. 最终产出标准

| 指标 | 目标 | 保证 |
|------|------|------|
| 文件数量 | 3-7个 | 智能合并 |
| 文件大小 | 100-300行 | 大小检查 |
| 功能内聚 | 高 | 按域分组 |
| 测试覆盖 | 100% | 强制TDD |

---

## 代码示例

### 输入：复杂任务

```
"构建一个完整的数据处理系统，包括：
 - 从API获取数据
 - 验证数据格式
 - 解析JSON
 - 转换数据格式
 - 验证输出
 - 保存到SQLite
 - 错误处理和日志"
```

### 分解过程

```
[Decompose] Level: EPIC
  ├── Story: Data Fetching
  │     ├── Task: HTTP Client
  │     │     ├── Atomic: fetch_data() [30 lines]
  │     │     └── Atomic: validate_url() [20 lines]
  │     └── Task: API Handler
  │           └── Atomic: call_api() [35 lines]
  │
  ├── Story: Data Processing
  │     ├── Atomic: parse_json() [25 lines]
  │     ├── Atomic: transform_data() [40 lines]
  │     └── Atomic: validate_schema() [30 lines]
  │
  └── Story: Data Storage
        ├── Atomic: init_db() [25 lines]
        ├── Atomic: save_record() [35 lines]
        ├── Atomic: handle_error() [30 lines]
        └── Atomic: log_operation() [20 lines]
```

### 组装结果

```python
# data_system.py (280行)
"""
Complete data processing system.
Auto-generated by SEMDS.
"""

import requests
import json
import sqlite3
import logging
from typing import Dict, List, Optional

# ============ Data Fetching ============

def fetch_data(url: str, timeout: int = 30) -> Dict:
    """Fetch data from API."""
    validate_url(url)
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return {"data": response.json(), "status": response.status_code}
    except requests.RequestException as e:
        return {"error": str(e)}

def validate_url(url: str) -> None:
    """Validate URL format."""
    if not isinstance(url, str):
        raise ValueError("URL must be string")
    if not url.startswith(("http://", "https://")):
        raise ValueError("Invalid URL scheme")

# ============ Data Processing ============

def parse_json(raw: str) -> Dict:
    """Parse JSON string."""
    return json.loads(raw)

def transform_data(raw: Dict) -> Dict:
    """Transform to standard format."""
    return {
        "id": raw.get("id"),
        "name": raw.get("name", "").strip(),
        "value": float(raw.get("value", 0))
    }

def validate_schema(data: Dict) -> bool:
    """Validate data schema."""
    required = ["id", "name", "value"]
    return all(k in data for k in required)

# ============ Data Storage ============

def init_db(db_path: str = "data.db") -> sqlite3.Connection:
    """Initialize database."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            name TEXT,
            value REAL
        )
    """)
    return conn

def save_record(conn: sqlite3.Connection, data: Dict) -> bool:
    """Save record to database."""
    try:
        conn.execute(
            "INSERT INTO records VALUES (?, ?, ?)",
            (data["id"], data["name"], data["value"])
        )
        conn.commit()
        return True
    except Exception as e:
        handle_error(e)
        return False

def handle_error(error: Exception) -> None:
    """Handle errors."""
    logging.error(f"Error: {error}")

def log_operation(operation: str, status: str) -> None:
    """Log operations."""
    logging.info(f"{operation}: {status}")

# 1个文件，280行，完整功能！
```

---

## 总结

### 回答了用户的担忧

**Q: 分解会导致文件爆炸吗？**
**A: 不会，因为：**

1. **逻辑分解**：为了AI执行（原子级<50行）
2. **物理组装**：为了人类维护（模块级100-300行）
3. **智能合并**：相关功能自动合并
4. **大小控制**：<50行合并，>300行拆分

**结果：20个原子任务 -> 4个文件（减少80%）**

### 最佳实践

```
用户任务
    │
    ├── 递归分解（直到原子级）
    │     └── 产生 20 个原子任务
    │
    ├── TDD执行（逐个验证）
    │     └── 确保每个任务正确
    │
    └── 智能组装（按功能域）
          └── 产生 4 个文件

最终结果：
  - 质量高（每个部分都验证过）
  - 可维护（合理文件数）
  - 可追踪（执行轨迹证明完整）
```

### 核心洞察

> **"分解是为了做对，组装是为了做好。"**

- 分解保证**正确性**（每个原子任务可验证）
- 组装保证**可维护性**（合理文件组织）
- 两者结合，**鱼和熊掌兼得**！
