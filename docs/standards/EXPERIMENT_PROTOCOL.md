# SEMDS 实验设计规范

**版本**: v1.0  
**适用阶段**: Phase 1-5  
**目标**: 确保实验可复现、可验证、可扩展

---

## 🎯 实验设计原则

### 1. 可复现性 (Reproducibility)
- 所有实验必须有随机种子控制
- 环境配置必须文档化
- 代码版本必须记录

### 2. 对照实验 (Controlled)
- 每次只改变一个变量
- 必须有对照组（baseline）
- 统计显著性必须计算

### 3. 可测量性 (Measurable)
- 指标必须量化
- 数据必须持久化
- 结果必须可视化

---

## 📋 实验类型

### 类型1: 功能验证实验
**目的**: 验证系统基本功能是否正常

**示例**:
- 计算器进化实验
- 单次生成测试
- 沙盒隔离验证

**要求**:
- 最少运行3次取平均
- 成功率 > 95%
- 记录所有失败案例

### 类型2: 性能基准实验
**目的**: 建立性能基线，用于后续对比

**示例**:
- 不同后端API响应时间对比
- 沙盒执行开销测量
- 数据库写入性能测试

**要求**:
- 至少100次迭代
- 记录均值、中位数、P95、P99
- 绘制分布直方图

### 类型3: 策略对比实验 (A/B Test)
**目的**: 比较不同进化策略的效果

**示例**:
- 保守 vs 激进变异策略
- 不同温度参数对比
- Thompson Sampling vs 随机选择

**要求**:
- 至少30个样本/组
- 计算p-value
- 效应量(effect size) > 0.5

### 类型4: 端到端验证实验
**目的**: 验证完整流程

**示例**:
- 多代进化直到达标
- 多任务并发执行
- 故障恢复测试

**要求**:
- 覆盖所有终止条件
- 验证资源清理
- 检查状态一致性

---

## 🧪 实验设计模板

### 基本信息
```python
EXPERIMENT_CONFIG = {
    "id": "exp_20240307_001",
    "name": "DeepSeek vs Claude代码生成质量对比",
    "type": "策略对比实验",
    "hypothesis": "Claude在复杂任务上表现优于DeepSeek",
    
    "date_created": "2024-03-07",
    "author": "AI Agent / Human",
    "reviewer": "Human",
    
    "status": "pending",  # pending/running/completed/failed
}
```

### 实验参数
```python
PARAMETERS = {
    # 固定参数（对照）
    "task": "calculator",
    "test_suite": "calculator_v1",
    "max_generations": 20,
    
    # 变化参数（实验组）
    "backend": ["deepseek", "claude"],  # 实验变量
    "temperature": 0.5,  # 固定
    
    # 随机控制
    "random_seed": 42,
}
```

### 评估指标
```python
METRICS = {
    # 主要指标
    "primary": {
        "name": "pass_rate",
        "description": "测试通过率",
        "target": 0.95,
        "unit": "percentage"
    },
    
    # 次要指标
    "secondary": [
        {
            "name": "generations_to_success",
            "description": "达到目标所需代数",
            "lower_is_better": True
        },
        {
            "name": "code_size",
            "description": "生成代码大小",
            "unit": "characters"
        },
        {
            "name": "execution_time",
            "description": "总执行时间",
            "unit": "seconds"
        }
    ]
}
```

---

## 📊 实验执行流程

### 阶段1: 准备
```python
def experiment_setup(config: ExperimentConfig) -> ExperimentContext:
    """实验准备阶段。"""
    
    # 1. 环境检查
    validate_environment()
    
    # 2. 设置随机种子
    set_random_seed(config.random_seed)
    
    # 3. 创建实验目录
    exp_dir = create_experiment_directory(config.id)
    
    # 4. 记录系统状态
    record_system_state(exp_dir)
    
    # 5. 初始化数据库
    init_experiment_database(config)
    
    return ExperimentContext(config, exp_dir)
```

### 阶段2: 执行
```python
def experiment_run(context: ExperimentContext) -> None:
    """实验执行阶段。"""
    
    for trial in range(config.num_trials):
        for variant in config.variants:
            # 记录开始
            trial_start = time.now()
            
            try:
                # 执行实验
                result = run_trial(variant)
                
                # 记录结果
                record_result(trial, variant, result)
                
            except Exception as e:
                # 记录失败
                record_failure(trial, variant, e)
                
            # 间隔避免限流
            time.sleep(config.trial_interval)
```

### 阶段3: 分析
```python
def experiment_analyze(context: ExperimentContext) -> AnalysisReport:
    """实验分析阶段。"""
    
    # 1. 加载数据
    data = load_experiment_data(context)
    
    # 2. 统计分析
    stats = calculate_statistics(data)
    
    # 3. 显著性检验
    significance = perform_statistical_tests(data)
    
    # 4. 可视化
    generate_plots(data, context.output_dir)
    
    # 5. 生成报告
    return generate_report(stats, significance)
```

---

## 📈 数据分析要求

### 描述统计
必须计算:
- 样本数量 (n)
- 均值 (mean)
- 标准差 (std)
- 最小值/最大值
- 中位数
- 25th/75th 百分位

### 推断统计
```python
from scipy import stats

def compare_groups(group_a: list, group_b: list) -> TestResult:
    """两组对比的统计检验。"""
    
    # 正态性检验
    _, p_normal_a = stats.shapiro(group_a)
    _, p_normal_b = stats.shapiro(group_b)
    
    if p_normal_a > 0.05 and p_normal_b > 0.05:
        # 正态分布：t检验
        t_stat, p_value = stats.ttest_ind(group_a, group_b)
        test_type = "t-test"
    else:
        # 非正态：Mann-Whitney U检验
        u_stat, p_value = stats.mannwhitneyu(group_a, group_b)
        test_type = "Mann-Whitney U"
    
    # 效应量 (Cohen's d)
    cohens_d = calculate_cohens_d(group_a, group_b)
    
    return TestResult(
        test_type=test_type,
        statistic=t_stat if test_type == "t-test" else u_stat,
        p_value=p_value,
        effect_size=cohens_d,
        significant=p_value < 0.05 and abs(cohens_d) > 0.5
    )
```

---

## 📊 可视化要求

### 必须生成的图表

1. **进化轨迹图**
```python
def plot_evolution_trajectory(generations: List[Generation]):
    """绘制每代得分变化。"""
    # x轴：代数
    # y轴：通过率
    # 标记：策略变化点
```

2. **对比箱线图**
```python
def plot_comparison_boxplot(results: Dict[str, List[float]]):
    """多组对比箱线图。"""
    # 展示分布差异
    # 标注统计显著性
```

3. **热力图**（多参数实验）
```python
def plot_parameter_heatmap(
    param1_values: list,
    param2_values: list,
    scores: np.ndarray
):
    """参数空间热力图。"""
```

---

## 📝 实验报告模板

```markdown
# 实验报告: [实验名称]

## 1. 摘要
- 假设: [假设内容]
- 结果: [是否证实]
- 结论: [一句话结论]

## 2. 方法
### 2.1 实验设计
- 类型: [功能验证/性能基准/策略对比/端到端]
- 变量: [独立变量]
- 控制: [控制变量]

### 2.2 参数配置
```json
{完整参数配置}
```

### 2.3 评估指标
- 主要指标: [指标定义]
- 次要指标: [列表]

## 3. 结果
### 3.1 原始数据
[数据表格或链接]

### 3.2 统计分析
| 指标 | 对照组 | 实验组 | p-value | 效应量 |
|------|--------|--------|---------|--------|
| ... | ... | ... | ... | ... |

### 3.3 可视化
[图表嵌入]

## 4. 讨论
### 4.1 发现
- [发现1]
- [发现2]

### 4.2 局限性
- [局限1]
- [局限2]

### 4.3 后续工作
- [建议1]

## 5. 附录
### 5.1 环境信息
- Python版本: x.x.x
- 依赖版本: [列表]

### 5.2 复现指令
```bash
python experiments/your_experiment.py --config config.json
```
```

---

## ✅ 实验审查清单

提交实验报告前必须检查：

- [ ] 随机种子已设置
- [ ] 至少运行3次（功能验证）或30次（策略对比）
- [ ] 所有指标已量化
- [ ] 统计检验已完成
- [ ] 图表已生成
- [ ] 原始数据已保存
- [ ] 复现指令已提供
- [ ] 局限性已讨论

---

## 🚫 常见错误

### ❌ 错误: 样本量太小
```python
# 坏：只运行1次
result = run_experiment()

# 好：运行足够多次
results = [run_experiment() for _ in range(30)]
```

### ❌ 错误: 伪复现
```python
# 坏：每次运行时改变多个变量
run(backend="deepseek", temperature=0.5)
run(backend="claude", temperature=0.7)  # 温度也变了！

# 好：只改变一个变量
for backend in ["deepseek", "claude"]:
    run(backend=backend, temperature=0.5)  # 温度固定
```

### ❌ 错误: 忽视随机性
```python
# 坏：不设置随机种子
result = generate_code()  # 每次结果不同

# 好：控制随机性
set_seed(42)
result = generate_code()  # 可复现
```

---

**所有实验必须通过审查才能视为完成**
