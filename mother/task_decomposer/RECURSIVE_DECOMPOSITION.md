# 递归任务分解系统
# 解决"大任务无法一次分解"的问题

## 用户的核心问题

1. **DeepSeek 一次分解不够细** - 复杂任务需要多级分解
2. **如何保证分解正确** - 需要验证机制
3. **是否达到原子级** - 需要检查标准  
4. **超过50行会不会截断** - 继续分解，不是截断

## 解决方案：递归分解 + 验证机制

### 三级架构

```
Level 1: EPIC（史诗级）
  例："构建完整的数据处理系统"
  │
  ├── Level 2: STORY（用户故事）
  │     例："实现数据获取模块"
  │     │
  │     ├── Level 3: TASK（任务）
  │     │     例："实现HTTP请求功能"
  │     │     │
  │     │     └── Level 4: ATOMIC（原子任务）
  │     │           例："编写fetch_data函数（<50行）"
  │     │           ✓ 可执行、可验证
```

### 核心组件

#### 1. DecompositionValidator（分解验证器）

检查分解是否正确：

```python
# 验证维度
1. 覆盖度检查 - 子任务是否覆盖父任务所有方面
2. 重叠检查 - 子任务之间是否有重复
3. 粒度检查 - 子任务数量是否合适（2-10个）
```

**验证失败示例**：
```
父任务："实现数据处理系统"
子任务：
  1. "分析需求"
  2. "设计架构" 
  3. "实现功能"  ← 太粗，需要继续分解
  4. "测试验证"

验证结果：❌ 失败
原因："实现功能"粒度太粗，预估代码>200行
建议：继续分解为"实现数据获取"、"实现数据清洗"等
```

#### 2. AtomicChecker（原子级检查器）

检查是否达到原子级别：

```python
检查维度：
1. 描述复杂度（0-10分）
2. 预估代码行数
3. 动作数量（<=2个）
4. 概念数量（<=3个）

阈值：
- 代码行数 <= 50
- 复杂度 <= 5
- 动作数 <= 2
- 概念数 <= 3
```

**未达到原子级示例**：
```
任务："实现数据获取、清洗、存储功能"

检查结果：❌ 未达到原子级
预估代码行数：150行
动作数量：3个（获取、清洗、存储）
概念数量：5个

建议：分解为3个原子任务
  1. "实现数据获取（<50行）"
  2. "实现数据清洗（<50行）"
  3. "实现数据存储（<50行）"
```

#### 3. RecursiveDecomposer（递归分解器）

递归分解直到达到原子级：

```python
def decompose(task, depth=0):
    # 1. 识别级别
    level = identify_level(task)
    
    # 2. 如果已经是原子级，返回
    if is_atomic(task):
        return AtomicTask(task)
    
    # 3. 如果达到最大深度，强制原子化
    if depth >= MAX_DEPTH:
        return ForceAtomic(task)
    
    # 4. 分解为子任务
    subtasks = decompose_once(task)
    
    # 5. 验证分解
    if not validate(subtasks):
        subtasks = retry_decomposition(task)
    
    # 6. 递归分解子任务
    for subtask in subtasks:
        decompose(subtask, depth + 1)
```

## 实际运行示例

### 示例1：简单任务（一次分解）

```
输入："Write a function to fetch data"

[Decompose] Level: TASK
  [Decompose] Level: ATOMIC - "Write fetch_data function"

结果：1个原子任务，代码<50行
```

### 示例2：中等复杂任务（两级分解）

```
输入："Build a web scraping system"

[Decompose] Level: EPIC
  [Decompose] Level: STORY - "Design architecture"
    [Decompose] Level: ATOMIC - "Define data models"
    [Decompose] Level: ATOMIC - "Design API interfaces"
  
  [Decompose] Level: STORY - "Implement scraper"
    [Decompose] Level: TASK - "HTTP client"
      [Decompose] Level: ATOMIC - "Implement fetch_html()"
    [Decompose] Level: TASK - "HTML parser"
      [Decompose] Level: ATOMIC - "Implement extract_data()"
  
  [Decompose] Level: STORY - "Data storage"
    [Decompose] Level: ATOMIC - "Implement save_to_db()"

结果：7个原子任务，每个<50行
```

### 示例3：复杂任务（三级分解 + 验证失败重试）

```
输入："Build enterprise data platform with ETL, analytics, and visualization"

第1轮分解：
  [Decompose] Level: EPIC
    子任务：
      1. "Design system architecture" 
      2. "Implement ETL pipeline"     ← 验证失败（太粗）
      3. "Build analytics engine"     ← 验证失败（太粗）
      4. "Create visualization"       ← 验证失败（太粗）
  
  验证结果：❌ 3个子任务粒度太粗
  原因：每个预估>200行代码

第2轮分解（重试）：
  [Decompose] Level: EPIC
    子任务：
      1. "Design system architecture"
        
      2. "Implement ETL pipeline"     ← 继续分解
         [Decompose] Level: STORY
           - "Extract data from sources"
           - "Transform data format"
           - "Load to warehouse"
      
      3. "Build analytics engine"     ← 继续分解
         [Decompose] Level: STORY
           - "Implement aggregation functions"
           - "Build query optimizer"
      
      4. "Create visualization"       ← 继续分解
         [Decompose] Level: STORY
           - "Design chart components"
           - "Implement dashboard"

第3轮分解（达到原子级）：
  "Extract data from sources"
    [Decompose] Level: TASK
      - "Implement database connector (<50行)" ✓
      - "Implement API client (<50行)" ✓
      - "Implement file reader (<50行)" ✓

最终结果：
- 总分解轮数：3轮
- 原子任务数：15个
- 每个任务：<50行代码
- 验证通过率：100%
```

## 超过50行的处理策略

### 不是截断，而是继续分解

**错误做法（截断）**：
```python
# 原始代码（100行）
def process_data():
    # 行1-50: 获取数据
    ...
    # 行51-100: 被截断！❌
```

**正确做法（分解）**：
```python
# 分解为两个原子任务

# 任务1: fetch_data (<50行)
def fetch_data(url: str) -> dict:
    ...

# 任务2: process_data (<50行)  
def process_data(raw_data: dict) -> dict:
    ...

# 组合使用
def main():
    raw = fetch_data(url)      # 调用原子任务1
    result = process_data(raw) # 调用原子任务2
    return result
```

## 保证分解正确的机制

### 1. 覆盖度验证

```python
def check_coverage(parent, subtasks):
    parent_keywords = extract_keywords(parent)
    subtask_keywords = union(extract_keywords(t) for t in subtasks)
    
    coverage_rate = len(parent_keywords & subtask_keywords) / len(parent_keywords)
    
    if coverage_rate < 0.7:  # 覆盖率<70%
        return False, f"Missing: {parent_keywords - subtask_keywords}"
    
    return True, "Coverage OK"
```

### 2. 重叠检测

```python
def check_overlap(subtasks):
    for i, task1 in enumerate(subtasks):
        for task2 in subtasks[i+1:]:
            similarity = jaccard_similarity(
                extract_keywords(task1),
                extract_keywords(task2)
            )
            if similarity > 0.8:  # 80%相似度
                return f"Overlap: {task1} and {task2}"
    return None
```

### 3. 粒度检查

```python
def check_granularity(subtasks):
    if len(subtasks) < 2:
        return False, "Too few subtasks"
    if len(subtasks) > 10:
        return False, "Too many subtasks"
    
    for task in subtasks:
        if len(task) < 10:  # 描述太短
            return False, f"Task too vague: {task}"
    
    return True, "Granularity OK"
```

## 运行演示

```bash
python mother/task_decomposer/recursive_decomposer.py
```

**输出示例**：
```
Task: "Build web scraping system"
[Decompose] Level: EPIC
  [Decompose] Level: STORY - "Design architecture"
    [Decompose] Level: ATOMIC - "Define interfaces"
  [Decompose] Level: STORY - "Implement scraper"
    [Decompose] Level: TASK - "HTTP client"
      [Decompose] Level: ATOMIC - "fetch_html() <50行"
    [Decompose] Level: TASK - "Parser"
      [Decompose] Level: ATOMIC - "extract_data() <50行"

Total atomic tasks: 7
All tasks validated ✓
```

## 集成到 SEMDS

```python
from mother.task_decomposer.recursive_decomposer import RecursiveDecomposer
from mother.task_decomposer.tdd_executor import TDDExecutor

class EnhancedMotherSystem:
    def execute_complex_task(self, description: str):
        # 1. 递归分解直到原子级
        decomposer = RecursiveDecomposer(max_depth=3)
        root = decomposer.decompose(description)
        
        # 2. 获取所有原子任务
        atomic_tasks = root.get_all_atomic_tasks()
        print(f"Decomposed into {len(atomic_tasks)} atomic tasks")
        
        # 3. 使用TDD执行每个原子任务
        executor = TDDExecutor()
        for task in atomic_tasks:
            success = executor.execute_task(task)
            if not success:
                return {
                    "success": False,
                    "failed_task": task.name,
                    "completed": f"{i}/{len(atomic_tasks)}"
                }
        
        # 4. 组合最终结果
        final_code = executor.generate_final_code()
        
        return {
            "success": True,
            "code": final_code,
            "tasks_completed": len(atomic_tasks),
            "decomposition_tree": root
        }
```

## 总结

**解决了什么问题**：
1. ✅ DeepSeek 一次分解不够 -> **递归分解**
2. ✅ 如何保证分解正确 -> **三重验证（覆盖度、重叠、粒度）**
3. ✅ 是否达到原子级 -> **AtomicChecker 检查**
4. ✅ 超过50行 -> **继续分解，不是截断**

**关键保证**：
- 每个原子任务 < 50 行代码
- 每个原子任务可独立验证
- 分解过程有验证，失败可重试
- 执行轨迹证明完整性（不会说13/20完成，实际没做）

**这就是工程化的解决方案**。
