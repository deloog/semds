# 外生评估器增强方案

## 当前问题

外生评估器（ExtrinsicEvaluator）目前只检查：
- ✅ 代码安全性（eval/exec）
- ✅ 类型注解和文档
- ❌ 算法效率（时间/空间复杂度）
- ❌ 实际行为一致性
- ❌ 硬编码/过拟合模式

导致：复杂算法代码得分偏低（0.4-0.6），简单代码反而得分高。

---

## 解决方案：三层评估体系

### 第一层：运行时性能评估

**目标**：检测算法效率（时间/空间复杂度）

```python
def _evaluate_performance(self, code: str, function_signature: str) -> float:
    """
    评估代码运行性能。
    
    方法：
    1. 生成不同规模的测试输入
    2. 测量执行时间和内存使用
    3. 判断是否符合预期复杂度
    
    Returns:
        0-1 之间的性能得分
    """
    # 示例：检测排序算法
    # O(n^2) 算法在 n=1000 时应该 < 0.1s
    # O(n log n) 算法在 n=10000 时应该 < 0.1s
    
    test_cases = [
        ([1] * 100, "small"),
        (list(range(1000)), "medium"),
        (list(range(10000)), "large"),
    ]
    
    scores = []
    for data, size in test_cases:
        time_cost = measure_execution(code, data)
        
        # 根据数据规模判断性能等级
        if size == "small" and time_cost < 0.01:
            scores.append(1.0)
        elif size == "medium" and time_cost < 0.1:
            scores.append(1.0)
        elif size == "large" and time_cost < 1.0:
            scores.append(1.0)
        else:
            scores.append(0.5)
    
    return sum(scores) / len(scores)
```

### 第二层：对抗性测试（Fuzzing）

**目标**：检测硬编码和过拟合

```python
def _fuzzing_test(self, code: str, function_signature: str) -> float:
    """
    使用模糊测试检测硬编码。
    
    方法：
    1. 在已知测试输入附近生成微小变化
    2. 检查代码是否对这些变化敏感
    3. 硬编码代码会在变化输入上失败
    
    Example:
        已知测试：fibonacci(10) == 55
        模糊测试：
        - fibonacci(9) == 34？
        - fibonacci(11) == 89？
        - fibonacci(8) == 21？
        
        硬编码代码（只处理10）会在 9/11/8 上失败
    """
    # 根据函数签名生成模糊测试用例
    fuzz_cases = generate_fuzz_cases(function_signature)
    
    pass_count = 0
    for case in fuzz_cases:
        try:
            result = execute_code(code, case.input)
            if result == case.expected:
                pass_count += 1
        except:
            pass
    
    return pass_count / len(fuzz_cases)
```

### 第三层：行为一致性分析

**目标**：检测输出是否符合数学/逻辑规律

```python
def _behavior_consistency_advanced(self, code: str, function_signature: str) -> float:
    """
    高级行为一致性检查。
    
    检查点：
    1. 单调性：fibonacci(n) < fibonacci(n+1)？
    2. 边界条件：sort([]) == []？
    3. 幂等性：reverse(reverse(s)) == s？
    4. 数学性质：add(a,b) == add(b,a)？
    """
    checks = []
    
    # 根据函数类型选择检查点
    if "sort" in function_signature:
        # 排序函数检查
        checks.append(check_idempotent(code))  # 两次排序结果相同
        checks.append(check_monotonic(code))   # 结果有序
        checks.append(check_preservation(code)) # 元素守恒
    
    elif "fibonacci" in function_signature:
        # 斐波那契检查
        checks.append(check_fibonacci_property(code))  # f(n) = f(n-1) + f(n-2)
        checks.append(check_monotonic_increasing(code))
    
    return sum(checks) / len(checks)
```

---

## 集成方案

### 修改 ExtrinsicEvaluator

```python
class EnhancedExtrinsicEvaluator:
    """增强版外生评估器"""
    
    def __init__(self):
        # 原有检查
        self.security_checker = SecurityChecker()
        self.quality_checker = CodeQualityChecker()
        
        # 新增检查
        self.performance_checker = PerformanceChecker()
        self.fuzzing_checker = FuzzingChecker()
        self.consistency_checker = BehaviorConsistencyChecker()
    
    def evaluate(self, code, function_signature, requirements):
        # 1. 原有评估（权重降低）
        security_score = self.security_checker.check(code)
        quality_score = self.quality_checker.check(code)
        
        # 2. 性能评估（新增，权重 30%）
        perf_score = self.performance_checker.evaluate(
            code, function_signature
        )
        
        # 3. 模糊测试（新增，权重 20%）
        fuzz_score = self.fuzzing_checker.test(
            code, function_signature
        )
        
        # 4. 行为一致性（新增，权重 20%）
        consistency_score = self.consistency_checker.verify(
            code, function_signature
        )
        
        # 综合得分（新权重）
        final_score = (
            security_score * 0.1 +      # 安全性（降低）
            quality_score * 0.2 +        # 代码质量（降低）
            perf_score * 0.3 +           # 性能（新增）
            fuzz_score * 0.2 +           # 鲁棒性（新增）
            consistency_score * 0.2     # 一致性（新增）
        )
        
        return {
            "score": final_score,
            "details": {
                "security": security_score,
                "quality": quality_score,
                "performance": perf_score,
                "fuzzing": fuzz_score,
                "consistency": consistency_score,
            }
        }
```

---

## 具体实现示例

### 1. 性能测试实现

```python
# evolution/evaluators/performance_checker.py

import time
import tracemalloc
from typing import List, Tuple

class PerformanceChecker:
    """性能检查器"""
    
    THRESHOLDS = {
        "fast": 0.01,      # 10ms
        "normal": 0.1,     # 100ms
        "slow": 1.0,       # 1s
    }
    
    def measure(self, code: str, test_input) -> Tuple[float, int]:
        """
        测量代码执行时间和内存。
        
        Returns:
            (execution_time_ms, peak_memory_kb)
        """
        # 启动内存跟踪
        tracemalloc.start()
        
        # 计时执行
        start = time.perf_counter()
        try:
            exec(code)  # 执行代码定义
            # 调用函数
            result = eval(f"solution({test_input})")
        finally:
            elapsed = time.perf_counter() - start
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
        
        return elapsed * 1000, peak / 1024  # ms, KB
    
    def evaluate_complexity(self, code: str, signature: str) -> str:
        """
        推测算法复杂度。
        
        通过不同规模输入的执行时间增长趋势判断：
        - O(1): 时间不随输入增长
        - O(n): 时间线性增长
        - O(n^2): 时间平方增长
        """
        sizes = [10, 100, 1000]
        times = []
        
        for size in sizes:
            test_data = self._generate_test_data(signature, size)
            elapsed, _ = self.measure(code, test_data)
            times.append(elapsed)
        
        # 分析增长趋势
        if times[1] / times[0] < 2:
            return "O(1) or O(log n)"
        elif times[2] / times[1] < 5:
            return "O(n)"
        elif times[2] / times[1] < 50:
            return "O(n log n)"
        else:
            return "O(n^2) or worse"
```

### 2. 模糊测试实现

```python
# evolution/evaluators/fuzzing_checker.py

import random
import copy

class FuzzingChecker:
    """模糊测试检查器"""
    
    def generate_mutations(self, base_cases: List[dict]) -> List[dict]:
        """
        基于已知测试用例生成变异。
        
        变异策略：
        1. 数值 +/- 1
        2. 边界值（0, -1, 极大值）
        3. 空值/None
        4. 类型变化（int -> float）
        """
        mutations = []
        
        for case in base_cases:
            # 数值变异
            if isinstance(case["input"], int):
                mutations.append({"input": case["input"] + 1, "type": "increment"})
                mutations.append({"input": case["input"] - 1, "type": "decrement"})
                mutations.append({"input": case["input"] * 2, "type": "double"})
            
            # 列表变异
            if isinstance(case["input"], list):
                mutations.append({"input": case["input"] + [999], "type": "append"})
                mutations.append({"input": case["input"][:-1], "type": "truncate"})
                mutations.append({"input": [], "type": "empty"})
        
        return mutations
    
    def test_robustness(self, code: str, signature: str, base_cases: List[dict]) -> float:
        """
        测试代码对输入变化的鲁棒性。
        
        Returns:
            通过率（0-1）
        """
        mutations = self.generate_mutations(base_cases)
        
        passed = 0
        for case in mutations:
            try:
                result = self._execute(code, signature, case["input"])
                # 检查是否有异常行为（崩溃/超时）
                if result is not None or result != "ERROR":
                    passed += 1
            except:
                pass  # 失败不计入，因为可能是正确的（如无效输入）
        
        return passed / len(mutations)
```

---

## 渐进式实施方案

### Phase 1: 快速修复（1-2 天）

**目标**：解决当前复杂算法得分过低问题

**实施内容**：
1. **修改外生评估器权重**
   - 降低质量检查权重（0.4 → 0.2）
   - 增加行为一致性权重（基于测试通过率）

2. **添加简单性能检查**
   - 执行时间测量
   - 超时检测（>5秒扣分）

**预期效果**：复杂算法得分提升至 0.7-0.8

### Phase 2: 增强评估（1 周）

**目标**：全面评估算法正确性和效率

**实施内容**：
1. **实现模糊测试**
   - 基于已知测试生成变异
   - 检测硬编码模式

2. **添加复杂度检测**
   - 多规模输入测试
   - 复杂度等级判断

**预期效果**：能区分 O(n) 和 O(n^2) 实现

### Phase 3: 智能评估（2 周）

**目标**：自适应不同任务类型的评估

**实施内容**：
1. **任务类型识别**
   - 自动识别排序/搜索/数学等类型
   - 应用对应的检查规则

2. **对抗性测试**
   - 构造边界情况
   - 压力测试

**预期效果**：接近人工代码审查水平

---

## 影响评估

### 正面影响

1. **更准确的质量评估**
   - 高效算法获得应得的高分
   - 硬编码被正确识别和惩罚

2. **更好的进化方向**
   - 系统会偏好真正优秀的实现
   - 避免"应试教育"陷阱

3. **提升最终代码质量**
   - 产出的代码更高效、更鲁棒

### 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 性能测试开销大 | 评估变慢 | 使用小数据集，限制超时 |
| 误杀正确代码 | 好代码得分低 | 多维度检查，不依赖单一指标 |
| 复杂度分析不准确 | 误判 | 保守估计，允许一定误差 |

---

## 总结

**短期方案**：调整权重，增加简单性能检查（1-2天）
**中期方案**：实现模糊测试和复杂度检测（1周）
**长期方案**：智能任务识别和对抗性测试（2周）

建议优先实施 **Phase 1**，能快速改善当前问题。
