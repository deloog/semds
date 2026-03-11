# SEMDS 性能规范

**版本**: v1.0  
**强制执行**: ✅ 是  
**适用范围**: 所有代码

---

## 🎯 性能目标

```
┌─────────────────────────────────────────────────────────┐
│ API响应时间                                              │
│   - 简单查询: < 100ms (P95)                              │
│   - 复杂查询: < 500ms (P95)                              │
│   - 代码生成: < 30s (单次调用)                           │
├─────────────────────────────────────────────────────────┤
│ 资源使用                                                 │
│   - 内存: < 512MB (单个任务)                             │
│   - CPU: < 80% (峰值)                                    │
│   - 磁盘I/O: 最小化                                      │
├─────────────────────────────────────────────────────────┤
│ 吞吐量                                                   │
│   - API: > 100 RPS                                       │
│   - 代码生成: > 10 gen/min                               │
└─────────────────────────────────────────────────────────┘
```

---

## ⏱️ 时间性能

### 响应时间分级

| 等级 | 时间      | 使用场景           | 优化策略   |
| ---- | --------- | ------------------ | ---------- |
| 瞬时 | <10ms     | 健康检查、配置读取 | 内存缓存   |
| 快速 | 10-100ms  | 简单API查询        | 数据库索引 |
| 正常 | 100-500ms | 复杂查询           | 异步处理   |
| 慢速 | 0.5-2s    | 批量操作           | 后台任务   |
| 异步 | >2s       | 代码生成、进化     | 任务队列   |

### 测量方法

```python
import time
from functools import wraps
from typing import Callable
import logging

logger = logging.getLogger("semds.performance")

def measure_time(func: Callable) -> Callable:
    """测量函数执行时间。"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                f"{func.__name__} took {elapsed:.2f}ms",
                extra={
                    "function": func.__name__,
                    "duration_ms": elapsed,
                    "type": "timing"
                }
            )
    return async_wrapper

# 使用
@measure_time
async def generate_code(task: TaskSpec) -> GenerationResult:
    # ...
```

---

## 💾 内存管理

### 内存使用规范

```python
# ✅ 正确处理大对象
def process_large_file(filepath: str):
    """流式处理大文件，避免一次性加载。"""
    with open(filepath, 'r') as f:
        for line in f:  # 逐行读取
            process_line(line)

# ❌ 错误：一次性加载
def bad_process(filepath: str):
    with open(filepath, 'r') as f:
        lines = f.readlines()  # 内存爆炸！
        for line in lines:
            process_line(line)
```

### 生成器使用

```python
# ✅ 使用生成器节省内存
def generate_candidates(population_size: int):
    """惰性生成候选代码。"""
    for i in range(population_size):
        yield generate_single_candidate(i)

# 使用
for candidate in generate_candidates(10000):  # 不会占用大量内存
    evaluate(candidate)
```

### 资源清理

```python
from contextlib import contextmanager

@contextmanager
def memory_intensive_operation():
    """确保资源清理。"""
    large_object = None
    try:
        large_object = create_large_object()
        yield large_object
    finally:
        # 显式释放
        if large_object:
            large_object.cleanup()
            del large_object
        import gc
        gc.collect()
```

---

## 🗄️ 数据库性能

### 查询优化

```python
# ✅ 使用索引
# 在models.py中
class Generation(Base):
    __tablename__ = "generations"

    task_id = Column(String, index=True)  # 外键索引
    gen_number = Column(Integer, index=True)  # 查询用
    created_at = Column(DateTime, index=True)  # 排序用

# ✅ 批量操作
# 一次性插入多条
def save_generations(generations: list[Generation]):
    with session.begin():
        session.bulk_save_objects(generations)

# ❌ 逐条插入
def bad_save(generations: list[Generation]):
    for gen in generations:  # N次数据库往返
        session.add(gen)
        session.commit()
```

### 查询模式

```python
# ✅ 预加载关联数据
from sqlalchemy.orm import joinedload

tasks = session.query(Task).options(
    joinedload(Task.generations)
).all()

# ✅ 只查询需要的列
tasks = session.query(Task.id, Task.name).all()

# ❌ 加载所有数据再过滤
tasks = session.query(Task).all()  # 加载全部
for task in tasks:
    if task.status == "running":  # Python端过滤
        process(task)

# ✅ 数据库端过滤
running_tasks = session.query(Task).filter(
    Task.status == "running"
).all()
```

---

## 🔄 并发优化

### 异步模式

```python
import asyncio
from typing import List

# ✅ 并发执行独立任务
async def evaluate_population(codes: List[str]) -> List[Score]:
    """并发评估多个代码。"""
    tasks = [evaluate_code(code) for code in codes]
    return await asyncio.gather(*tasks)

# ✅ 使用信号量限制并发
async def limited_api_calls(prompts: List[str], max_concurrent: int = 5):
    """限制并发API调用。"""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def call_with_limit(prompt):
        async with semaphore:
            return await call_llm_api(prompt)

    tasks = [call_with_limit(p) for p in prompts]
    return await asyncio.gather(*tasks)
```

### 连接池

```python
from sqlalchemy import create_engine

# ✅ 使用连接池
engine = create_engine(
    "sqlite:///semds.db",
    pool_size=10,           # 连接池大小
    max_overflow=20,        # 最大溢出连接
    pool_timeout=30,        # 连接超时
    pool_recycle=3600,      # 连接回收时间
)
```

---

## 📊 监控与告警

### 性能指标收集

```python
from dataclasses import dataclass
from typing import Dict
import time

@dataclass
class PerformanceMetrics:
    """性能指标。"""
    request_count: int = 0
    total_latency_ms: float = 0
    error_count: int = 0

    @property
    def avg_latency_ms(self) -> float:
        if self.request_count == 0:
            return 0
        return self.total_latency_ms / self.request_count

    @property
    def error_rate(self) -> float:
        if self.request_count == 0:
            return 0
        return self.error_count / self.request_count

# 全局指标存储
_metrics: Dict[str, PerformanceMetrics] = {}

def record_metric(endpoint: str, latency_ms: float, error: bool = False):
    """记录性能指标。"""
    if endpoint not in _metrics:
        _metrics[endpoint] = PerformanceMetrics()

    metric = _metrics[endpoint]
    metric.request_count += 1
    metric.total_latency_ms += latency_ms
    if error:
        metric.error_count += 1

    # 告警检查
    if metric.avg_latency_ms > 500:
        logger.warning(f"High latency on {endpoint}: {metric.avg_latency_ms:.2f}ms")
    if metric.error_rate > 0.05:
        logger.error(f"High error rate on {endpoint}: {metric.error_rate:.2%}")
```

---

## 🚀 优化策略

### 缓存策略

```python
from functools import lru_cache
import redis

# 内存缓存（函数级别）
@lru_cache(maxsize=128)
def parse_strategy_config(config_str: str) -> StrategyConfig:
    """解析策略配置（缓存结果）。"""
    return json.loads(config_str)

# Redis缓存（分布式）
redis_client = redis.Redis()

def get_cached_generation(task_id: str, gen_number: int):
    """从缓存获取生成结果。"""
    cache_key = f"gen:{task_id}:{gen_number}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # 缓存未命中，从数据库获取
    result = fetch_from_db(task_id, gen_number)
    redis_client.setex(cache_key, 3600, json.dumps(result))
    return result
```

### 懒加载

```python
class Task:
    """任务对象，支持懒加载。"""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self._generations = None

    @property
    def generations(self):
        """懒加载生成历史。"""
        if self._generations is None:
            self._generations = load_generations(self.task_id)
        return self._generations
```

---

## ✅ 性能检查清单

```markdown
## 性能检查清单

### 设计阶段

- [ ] 确定了性能目标
- [ ] 识别了性能瓶颈点
- [ ] 设计了缓存策略
- [ ] 考虑了扩展性

### 编码阶段

- [ ] 避免N+1查询
- [ ] 使用批量操作
- [ ] 正确处理大对象
- [ ] 使用生成器处理大数据

### 测试阶段

- [ ] 有性能基准测试
- [ ] 有负载测试
- [ ] 有内存泄漏检测
- [ ] 监控关键指标

### 部署阶段

- [ ] 配置了性能监控
- [ ] 设置了告警阈值
- [ ] 有性能回退方案
```

---

**最后更新**: 2026-03-07  
**维护者**: 性能优化团队
