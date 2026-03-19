# SEMDS Mother System - 自主任务母体设计

## 愿景

SEMDS 不再是简单的代码优化器，而是一个**自主任务执行母体**：

```
接收任务 → 分析需求 → 检查能力 → 缺失? → 自写工具 → 执行任务 → 验证结果
                ↓                              ↑
                └────────── 已有能力 ──────────┘
```

## 核心能力

### 1. 任务理解引擎 (Task Understanding)

```python
class TaskAnalyzer:
    def analyze(self, natural_language_task: str) -> ExecutionPlan:
        # 示例输入：
        # "帮我爬取知乎热榜，分析情绪，生成词云"
        
        # 输出执行计划：
        {
            "steps": [
                {"action": "scrape", "target": "zhihu_hot", "output": "raw_data"},
                {"action": "analyze", "input": "raw_data", "method": "sentiment", "output": "sentiment_scores"},
                {"action": "visualize", "input": "sentiment_scores", "type": "wordcloud", "output": "image.png"}
            ],
            "required_capabilities": ["http_client", "html_parser", "sentiment_analyzer", "visualizer"]
        }
```

### 2. 能力检查器 (Capability Checker)

```python
class CapabilityRegistry:
    def __init__(self):
        self.capabilities = {
            "http_client": HTTPClient(),
            "file_io": FileIO(),
            "json_parser": JSONParser(),
            # ... 基础能力
        }
    
    def check(self, required: List[str]) -> Tuple[bool, List[str]]:
        """检查是否有所需能力，返回缺失列表"""
        missing = [c for c in required if c not in self.capabilities]
        return len(missing) == 0, missing
```

### 3. 工具生成器 (Tool Generator) - 核心创新

当发现缺少能力时，SEMDS **自己写代码**创建工具：

```python
class ToolGenerator:
    def generate(self, capability_name: str, requirement: str) -> str:
        """
        示例：缺少 "sentiment_analyzer"
        
        SEMDS 自动生成：
        ```python
        # tools/sentiment_analyzer.py
        class SentimentAnalyzer:
            def analyze(self, text: str) -> float:
                # 简单基于词库的实现
                positive_words = ['好', '棒', '优秀', '喜欢']
                negative_words = ['差', '糟', '讨厌', '恶心']
                
                score = 0
                for word in positive_words:
                    if word in text:
                        score += 1
                for word in negative_words:
                    if word in text:
                        score -= 1
                
                return score / max(len(text) / 10, 1)
        ```
        """
        # 使用 DeepSeek 生成工具代码
        code = self.llm.generate_tool_code(capability_name, requirement)
        
        # 自动测试验证
        if self.validator.test_tool(code, capability_name):
            self.save_tool(code, capability_name)
            return code
        else:
            # 修复并重试
            return self.generate_with_repair(capability_name, requirement, code)
```

### 4. 自主执行循环 (Autonomous Loop)

```python
class MotherSystem:
    def execute(self, task: str):
        # 1. 理解任务
        plan = self.analyzer.analyze(task)
        
        # 2. 检查能力
        has_all, missing = self.capability.check(plan.required_capabilities)
        
        # 3. 动态生成缺失能力
        for cap in missing:
            print(f"[Mother] Missing capability: {cap}, generating...")
            tool_code = self.tool_generator.generate(cap, plan.requirements[cap])
            self.capability.register(cap, tool_code)
        
        # 4. 执行计划
        results = {}
        for step in plan.steps:
            tool = self.capability.get(step.action)
            result = tool.execute(step.input, **step.params)
            results[step.output] = result
        
        # 5. 验证结果
        if self.validator.verify(results, plan.expected_output):
            return results
        else:
            # 自我修正
            return self.repair_and_retry(task, plan, results)
```

## 实际场景示例

### 场景 1：自主爬虫任务

**用户输入**：
```
"监控淘宝某商品价格，降价到 500 以下时发邮件通知我"
```

**SEMDS 思考过程**：
```
[Analyzer] 任务拆解：
  1. 爬取淘宝商品页面
  2. 提取价格信息
  3. 比较价格与阈值
  4. 发送邮件通知

[Capability Check] 能力检查：
  ✓ http_client (已有)
  ✓ email_sender (已有)
  ✗ html_parser (缺失)
  ✗ price_extractor (缺失)

[Tool Generator] 生成工具：
  - 生成 tools/html_parser.py
  - 生成 tools/price_extractor.py
  - 自动测试：验证能正确提取价格

[Executor] 执行：
  - 每 5 分钟爬取一次
  - 价格 < 500 时触发邮件
  - 记录监控日志
```

### 场景 2：自主数据分析

**用户输入**：
```
"分析这个 CSV 文件，找出销售额最高的 5 个产品，生成柱状图"
```

**SEMDS 思考过程**：
```
[Analyzer] 识别需求：
  - 输入：CSV 文件
  - 处理：排序 + 筛选 Top 5
  - 输出：柱状图

[Capability Check]：
  ✗ csv_reader (缺失 - 需要 pandas)
  ✗ chart_generator (缺失 - 需要 matplotlib)

[Tool Generator]：
  - 生成代码导入 pandas
  - 生成 matplotlib 绘图代码
  - 验证：能读取 CSV 并生成图片

[Execution]：
  - 读取 CSV
  - groupby 产品求和
  - sort_values 取 Top 5
  - plt.bar 生成图表
```

## 技术架构

```
┌─────────────────────────────────────────┐
│           User Interface                │
│  (Natural Language Task Input)          │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│        Task Understanding Engine        │
│  - Intent Recognition                   │
│  - Requirement Extraction               │
│  - Step Planning                        │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       Capability Registry               │
│  - Check available tools                │
│  - Identify gaps                        │
└─────────────────┬───────────────────────┘
                  ↓ (if gaps found)
┌─────────────────────────────────────────┐
│        Tool Generator (Core)            │
│  - Analyze requirement                  │
│  - Generate code                        │
│  - Self-test                            │
│  - Register new capability              │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       Autonomous Executor               │
│  - Load tools dynamically               │
│  - Execute step by step                 │
│  - Handle errors                        │
│  - Retry with repair                    │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       Result Validator                  │
│  - Verify output format                 │
│  - Check constraints                    │
│  - Self-correction if failed            │
└─────────────────────────────────────────┘
```

## 当前 SEMDS 改造计划

### Phase 1: 基础架构（1-2 周）

1. **添加任务理解模块**
   - 使用 DeepSeek 进行意图识别
   - 将自然语言转换为执行计划

2. **实现能力注册表**
   - 现有能力：文件读写、网络请求、数据解析
   - 动态加载机制

3. **基础工具生成**
   - 针对常见缺失能力（爬虫、解析器、可视化）

### Phase 2: 自主能力（2-3 周）

1. **闭环执行系统**
   - 观察-思考-行动循环
   - 错误自动修复

2. **工具进化**
   - 生成的工具也可以被优化
   - 形成工具进化历史

3. **元学习**
   - 记录哪些工具生成策略有效
   - 形成策略库

### Phase 3: 高级特性（1 月+）

1. **多步骤复杂任务**
2. **长期记忆（之前任务的复用）**
3. **自主发现优化机会**

## 首个演示任务

**目标**：让 SEMDS 自己写个爬虫工具并完成任务

**用户输入**：
```
"获取 Bing 首页的图片 URL 列表"
```

**预期 SEMDS 行为**：
1. 分析需要 HTTP 请求和 HTML 解析
2. 发现没有 html_parser 工具
3. 自动生成 html_parser.py（使用 BeautifulSoup 或正则）
4. 执行爬取任务
5. 返回 URL 列表

---

**这就是"母体"的雏形：不是被限制在固定能力圈内，而是能根据需求无限扩展自己的能力边界。**

你想从哪个 Phase 开始实现？我可以先帮你搭建任务理解 + 工具生成的基础框架。
