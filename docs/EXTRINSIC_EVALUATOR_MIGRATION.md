# 外生评估器版本说明与迁移指南

## 当前状况

目前存在两个版本的外生评估器：

```
evolution/
├── extrinsic_evaluator.py              # 原始版本 (18KB)
└── extrinsic_evaluator_enhanced.py     # 增强版本 (6KB)
```

## 版本对比

| 特性 | 原始版本 | 增强版本 |
|------|----------|----------|
| **代码质量检查** | ✅ 完整 | ✅ 继承 |
| **安全性检查** | ✅ 完整 | ✅ 继承 |
| **边界用例生成** | ✅ 有 | ✅ 继承 |
| **性能测试** | ❌ 无 | ✅ 新增 |
| **鲁棒性测试** | ❌ 无 | ✅ 新增（基于测试代码）|
| **复杂度分析** | ❌ 无 | ❌ 单独实现 |
| **权重配置** | 固定 | 可调整 |

## 问题分析

### 为什么有两个版本？

1. **原始版本**：Phase 1-3 TDD 开发完成，功能稳定
2. **增强版本**：为解决"复杂算法评分偏低"问题而快速实现

### 当前问题

1. **代码重复**：增强版继承自原始版，存在冗余
2. **维护困难**：两个版本需要同步更新
3. **选择困难**：用户不知道该用哪个
4. **功能分散**：Phase 2 的模糊测试/复杂度检测在实验文件中

## 整合方案

### 推荐方案：合并为统一版本

创建单一的 `extrinsic_evaluator.py`，整合所有功能：

```python
class ExtrinsicEvaluator:
    """
    统一的外生评估器。
    
    功能模块：
    1. 静态分析（安全、质量）
    2. 边界用例测试
    3. 性能测试（可选）
    4. 鲁棒性测试（可选，需 test_code）
    
    配置选项：
    - enable_performance: 启用性能测试
    - enable_robustness: 启用鲁棒性测试
    - weights: 自定义权重配置
    """
    
    def __init__(
        self,
        enable_performance: bool = True,
        enable_robustness: bool = False,
        weights: dict = None,
    ):
        self.enable_performance = enable_performance
        self.enable_robustness = enable_robustness
        self.weights = weights or {
            "security": 0.15,
            "quality": 0.25,
            "edge_cases": 0.20,
            "performance": 0.25,
            "robustness": 0.15,
        }
```

### 迁移步骤

#### Step 1: 备份当前版本
```bash
git mv evolution/extrinsic_evaluator.py evolution/extrinsic_evaluator_legacy.py
git mv evolution/extrinsic_evaluator_enhanced.py evolution/extrinsic_evaluator_v2.py
```

#### Step 2: 创建统一版本

```python
# evolution/extrinsic_evaluator.py (新版本)

from .extrinsic_evaluator_legacy import ExtrinsicEvaluator as LegacyEvaluator

class ExtrinsicEvaluator(LegacyEvaluator):
    """
    增强版外生评估器（向后兼容）
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 新增组件
        self.performance_checker = PerformanceChecker()
    
    def evaluate(self, code, function_signature, requirements, test_code=None):
        # 1. 基础评估（调用父类）
        base_result = super().evaluate(code, function_signature, requirements)
        
        # 2. 性能测试（新增）
        if self.enable_performance:
            perf_score = self._evaluate_performance(code, function_signature)
        
        # 3. 鲁棒性测试（新增）
        if test_code and self.enable_robustness:
            robust_score = self._evaluate_robustness(code, test_code)
        
        # 4. 综合得分
        final_score = self._weighted_average(
            base_result, perf_score, robust_score
        )
        
        return {
            "score": final_score,
            "details": {
                "base": base_result,
                "performance": perf_score,
                "robustness": robust_score,
            }
        }
```

#### Step 3: 更新引用

修改 `dual_evaluator.py`，使用统一版本：

```python
# 之前
from evolution.extrinsic_evaluator import ExtrinsicEvaluator

# 之后（无需修改，类名相同）
from evolution.extrinsic_evaluator import ExtrinsicEvaluator
```

#### Step 4: 迁移 Phase 2 组件

将实验文件中的组件正式集成：

```
evolution/evaluators/
├── __init__.py
├── performance_checker.py      # 从实验文件迁移
├── fuzzing_checker.py          # 从实验文件迁移
├── complexity_checker.py       # 从实验文件迁移
└── behavior_checker.py         # 从实验文件迁移
```

### 使用示例

#### 默认模式（向后兼容）
```python
# 与原始版本相同的行为
evaluator = ExtrinsicEvaluator()
result = evaluator.evaluate(code, sig, reqs)
# 评分范围：0.4-0.6（复杂算法偏低）
```

#### 增强模式（推荐新代码）
```python
# 启用所有增强功能
evaluator = ExtrinsicEvaluator(
    enable_performance=True,
    enable_robustness=True,
)
result = evaluator.evaluate(code, sig, reqs, test_code=test_code)
# 评分范围：0.7-0.9（合理反映算法质量）
```

#### 自定义权重
```python
# 针对特定任务调整权重
evaluator = ExtrinsicEvaluator(
    weights={
        "security": 0.10,
        "quality": 0.20,
        "edge_cases": 0.15,
        "performance": 0.35,  # 算法任务提高性能权重
        "robustness": 0.20,
    }
)
```

## 实施计划

### 方案 A：保守迁移（推荐）

1. 保留原始版本作为默认
2. 增强功能作为可选开关
3. 逐步测试后切换默认

**优点**：
- 向后兼容
- 风险低
- 用户可选择

### 方案 B：激进替换

1. 直接替换为增强版本
2. 默认启用所有功能
3. 更新所有测试

**优点**：
- 代码简洁
- 功能统一

**风险**：
- 可能破坏现有测试
- 评分标准变化

## 当前建议

鉴于 Phase 3 已完成，建议：

1. **短期**：保持现状，两个版本并存
2. **中期**（Next Phase）：实施方案 A 的保守迁移
3. **长期**：根据实际使用情况，决定是否完全切换

### 用户指导

**对于新用户**：
- 使用增强版本：`from evolution.extrinsic_evaluator_enhanced import EnhancedExtrinsicEvaluator`

**对于现有代码**：
- 继续使用原始版本，不受影响
- 如需优化评分，可迁移到增强版本

**对于开发**：
- 优先在实验中使用增强版本验证
- 稳定后再考虑替换核心系统

---

## 附录：当前两个版本的详细对比

### 原始版本 (extrinsic_evaluator.py)

**主要方法**：
- `_evaluate_static_analysis()` - 静态分析
- `_evaluate_edge_cases()` - 边界用例
- `_generate_edge_cases()` - 用例生成
- `_execute_with_timeout()` - 安全执行

**权重**：
- 静态分析：40%
- 边界用例：60%

### 增强版本 (extrinsic_evaluator_enhanced.py)

**主要方法**：
- 继承原始版本所有方法
- `_evaluate_performance()` - 性能测试（新增）
- `_evaluate_robustness()` - 鲁棒性测试（新增）

**权重**：
- 基础质量：30%
- 性能：40%
- 鲁棒性：30%

### 实验版本 (phase3_phase2_enhancement.py)

**独立组件**：
- `FuzzingChecker` - 模糊测试
- `ComplexityChecker` - 复杂度分析
- `BehaviorConsistencyChecker` - 行为一致性

**权重**：
- 基础质量：25%
- 鲁棒性：25%
- 复杂度：30%
- 一致性：20%
