# SEMDS AI代码审查规范

**版本**: v1.0  
**目标**: 确保AI生成的代码符合质量标准  
**适用范围**: AI Agent生成的所有代码

---

## 🎯 审查原则

### 1. 机器审查优先
- 静态分析工具自动检查
- 单元测试自动验证
- 只有机器无法判断的才需人工审查

### 2. 分层审查
- **L0 自动审查**: 格式、类型、基础安全
- **L1 AI自我审查**: 逻辑正确性、边界条件
- **L2 人类审查**: 架构合理性、长期维护性

### 3. 增量审查
- 只审查变更部分
- 已有代码信任但可抽查
- 关注新增风险点

---

## 🤖 AI自我审查清单

AI生成代码后，必须自我检查以下项目：

### 功能正确性
```python
# ✅ 检查清单（AI自检）
checklist = [
    "所有分支都有测试覆盖",
    "边界条件已处理",
    "错误输入有防御",
    "资源正确释放",
    "无死循环风险",
    "无递归溢出风险",
]
```

**自检报告格式**:
```python
def self_review(code: str, task_spec: dict) -> ReviewReport:
    """AI自我审查报告。"""
    return ReviewReport(
        code_complexity=calculate_complexity(code),
        test_coverage=estimate_coverage(code, task_spec),
        potential_issues=static_analysis(code),
        confidence_score=0.85,  # 0-1
        recommends_human_review=confidence_score < 0.9
    )
```

---

## 🔍 审查维度

### 维度1: 安全性 (Security)

#### 危险模式检测
```python
DANGEROUS_PATTERNS = {
    "eval_exec": [
        r"eval\s*\(",
        r"exec\s*\(",
        r"__import__\s*\(",
    ],
    "file_access": [
        r"open\s*\([^)]*['\"]/(?:etc|root|home)",
        r"os\.system\s*\(",
        r"subprocess\.call\s*\(",
    ],
    "network": [
        r"socket\.",
        r"urllib\.request",
        r"requests\.(?:get|post)",
    ],
    "data_exposure": [
        r"print\s*\([^)]*password",
        r"logger\.(?:debug|info).*api_key",
    ]
}

def security_scan(code: str) -> List[SecurityIssue]:
    """安全扫描。"""
    issues = []
    for category, patterns in DANGEROUS_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, code):
                issues.append(SecurityIssue(
                    category=category,
                    pattern=pattern,
                    severity="HIGH" if category in ["eval_exec", "file_access"] else "MEDIUM"
                ))
    return issues
```

#### 安全级别标记
```python
class SecurityLevel(Enum):
    SAFE = "safe"           # 无危险操作
    CAUTION = "caution"     # 有潜在风险但受控
    UNSAFE = "unsafe"       # 存在危险操作
    CRITICAL = "critical"   # 严重安全风险

def assess_security_level(code: str, context: ExecutionContext) -> SecurityLevel:
    """评估代码安全级别。"""
    issues = security_scan(code)
    
    if any(i.severity == "CRITICAL" for i in issues):
        return SecurityLevel.CRITICAL
    
    if any(i.severity == "HIGH" for i in issues):
        if context.is_sandboxed and context.readonly_fs:
            return SecurityLevel.CAUTION
        return SecurityLevel.UNSAFE
    
    if issues:
        return SecurityLevel.CAUTION
    
    return SecurityLevel.SAFE
```

### 维度2: 质量 (Quality)

#### 代码质量评分
```python
class QualityMetrics:
    """代码质量指标。"""
    
    def __init__(self, code: str):
        self.code = code
        self.ast_tree = ast.parse(code)
    
    def complexity(self) -> int:
        """圈复杂度。"""
        # 使用 mccabe 或类似工具
        return calculate_cyclomatic_complexity(self.ast_tree)
    
    def maintainability_index(self) -> float:
        """可维护性指数。"""
        # 基于 Halstead 指标和圈复杂度
        return calculate_maintainability_index(self.code)
    
    def documentation_coverage(self) -> float:
        """文档覆盖率。"""
        functions = [node for node in ast.walk(self.ast_tree) 
                    if isinstance(node, ast.FunctionDef)]
        documented = sum(1 for f in functions 
                        if ast.get_docstring(f))
        return documented / len(functions) if functions else 0
    
    def overall_score(self) -> float:
        """综合质量分数 (0-100)。"""
        weights = {
            'complexity': 0.3,
            'maintainability': 0.4,
            'documentation': 0.3
        }
        
        complexity_score = max(0, 100 - self.complexity() * 5)
        maintainability_score = self.maintainability_index()
        documentation_score = self.documentation_coverage() * 100
        
        return (
            weights['complexity'] * complexity_score +
            weights['maintainability'] * maintainability_score +
            weights['documentation'] * documentation_score
        )
```

#### 质量阈值
```python
QUALITY_THRESHOLDS = {
    "complexity_max": 10,           # 圈复杂度不超过10
    "maintainability_min": 70,      # 可维护性指数不低于70
    "documentation_min": 0.8,       # 文档覆盖率不低于80%
    "line_length_max": 88,          # 行长度不超过88
    "function_length_max": 50,      # 函数长度不超过50行
}

def meets_quality_standards(metrics: QualityMetrics) -> Tuple[bool, List[str]]:
    """检查是否满足质量标准。"""
    violations = []
    
    if metrics.complexity() > QUALITY_THRESHOLDS["complexity_max"]:
        violations.append(f"Complexity {metrics.complexity()} > {QUALITY_THRESHOLDS['complexity_max']}")
    
    if metrics.maintainability_index() < QUALITY_THRESHOLDS["maintainability_min"]:
        violations.append(f"Maintainability {metrics.maintainability_index():.1f} < {QUALITY_THRESHOLDS['maintainability_min']}")
    
    if metrics.documentation_coverage() < QUALITY_THRESHOLDS["documentation_min"]:
        violations.append(f"Documentation {metrics.documentation_coverage():.1%} < {QUALITY_THRESHOLDS['documentation_min']:.0%}")
    
    return len(violations) == 0, violations
```

### 维度3: 一致性 (Consistency)

#### 风格一致性检查
```python
def check_style_consistency(code: str, project_style: StyleGuide) -> List[StyleViolation]:
    """检查代码风格与项目一致。"""
    violations = []
    
    # 命名风格
    if detect_naming_style(code) != project_style.naming_style:
        violations.append(StyleViolation("naming", "命名风格不一致"))
    
    # 引号风格
    if detect_quote_style(code) != project_style.quote_style:
        violations.append(StyleViolation("quotes", "引号风格不一致"))
    
    # 缩进风格
    if detect_indent_style(code) != project_style.indent_style:
        violations.append(StyleViolation("indent", "缩进风格不一致"))
    
    return violations
```

### 维度4: 可测试性 (Testability)

```python
def assess_testability(code: str) -> TestabilityReport:
    """评估代码可测试性。"""
    
    issues = []
    
    # 检查硬编码依赖
    if has_hardcoded_dependencies(code):
        issues.append("存在硬编码依赖，难以mock")
    
    # 检查全局状态
    if uses_global_state(code):
        issues.append("使用全局状态，测试隔离困难")
    
    # 检查I/O操作
    io_functions = detect_io_operations(code)
    if io_functions and not has_abstraction(code, io_functions):
        issues.append("I/O操作未抽象，难以测试")
    
    # 检查副作用
    if has_unexpected_side_effects(code):
        issues.append("存在意外副作用")
    
    return TestabilityReport(
        testable=len(issues) == 0,
        issues=issues,
        mock_points=identify_mock_points(code),
        test_recommendations=generate_test_recommendations(code)
    )
```

---

## 📊 审查流程

### 自动审查 (L0)
```python
def automated_review(code: str, context: Context) -> L0ReviewResult:
    """L0级自动审查。"""
    
    results = {
        "format": run_black_check(code),
        "types": run_mypy_check(code),
        "lint": run_ruff_check(code),
        "security": security_scan(code),
        "complexity": check_complexity(code),
    }
    
    passed = all(r.passed for r in results.values())
    
    return L0ReviewResult(
        passed=passed,
        results=results,
        auto_fixable=all(r.auto_fixable for r in results.values()),
    )
```

### AI自我审查 (L1)
```python
def ai_self_review(generated_code: str, task_spec: dict) -> L1ReviewResult:
    """AI生成代码的自我审查。"""
    
    # 1. 逻辑验证
    logic_issues = verify_logic(generated_code, task_spec)
    
    # 2. 边界条件检查
    boundary_issues = check_boundary_conditions(generated_code, task_spec)
    
    # 3. 错误处理检查
    error_handling = check_error_handling(generated_code)
    
    # 4. 估算测试覆盖率
    coverage_estimate = estimate_test_coverage(generated_code, task_spec)
    
    # 5. 计算置信度
    confidence = calculate_confidence(
        logic_issues, boundary_issues, error_handling, coverage_estimate
    )
    
    return L1ReviewResult(
        confidence=confidence,
        issues=logic_issues + boundary_issues + error_handling,
        coverage_estimate=coverage_estimate,
        recommends_improvement=confidence < 0.9,
    )
```

### 人类审查 (L2)
```python
def human_review_context(code: str, l0_result: L0ReviewResult, l1_result: L1ReviewResult) -> L2ReviewContext:
    """为人类审查准备上下文。"""
    
    return L2ReviewContext(
        code=code,
        l0_summary=l0_result.summary(),
        l1_summary=l1_result.summary(),
        
        # 突出显示需要人类判断的部分
        architecture_concerns=identify_architecture_concerns(code),
        long_term_maintainability=assess_long_term_impact(code),
        business_logic_alignment=check_alignment_with_business_logic(code),
        
        # 建议审查重点
        focus_areas=suggest_focus_areas(l0_result, l1_result),
    )
```

---

## ✅ 审查通过标准

### L0 自动审查通过标准
```python
L0_PASS_CRITERIA = {
    "format": "代码通过black格式化",
    "types": "所有类型检查通过",
    "lint": "无严重lint错误",
    "security": "无高危安全漏洞",
    "complexity": "圈复杂度 <= 10",
}
```

### L1 AI自我审查通过标准
```python
L1_PASS_CRITERIA = {
    "confidence": "置信度 >= 0.9",
    "logic_issues": "无逻辑错误",
    "boundary_coverage": "边界条件已处理",
    "error_handling": "异常处理完善",
    "testability": "代码可测试",
}
```

### L2 人类审查通过标准
```python
L2_PASS_CRITERIA = {
    "architecture": "符合架构规范",
    "maintainability": "可长期维护",
    "business_alignment": "符合业务需求",
    "no_red_flags": "无重大警示",
}
```

---

## 🚫 审查红线

以下情况**绝对禁止**合并：

1. **安全红线**
   - 包含 `eval()` 或 `exec()`
   - 未授权的文件系统访问
   - 网络请求未声明

2. **质量红线**
   - 圈复杂度 > 20
   - 无任何测试
   - 存在已知bug

3. **架构红线**
   - 违反Layer隔离原则
   - 引入循环依赖
   - 破坏向后兼容性

---

## 📋 审查报告模板

```markdown
# 代码审查报告

## 基本信息
- 代码ID: [hash]
- 生成时间: [timestamp]
- AI Agent: [name]
- 任务: [description]

## L0 自动审查
| 检查项 | 状态 | 详情 |
|--------|------|------|
| 格式 | ✅/❌ | ... |
| 类型 | ✅/❌ | ... |
| 安全 | ✅/❌ | ... |

## L1 AI自我审查
- 置信度: [0-1]
- 发现的问题: [list]
- 建议改进: [list]

## L2 人类审查（如需要）
- 审查人: [name]
- 关注点: [areas]
- 决定: [PASS/NEEDS_WORK/REJECT]

## 最终状态
- [ ] L0 通过
- [ ] L1 通过
- [ ] L2 通过（如需要）
- [ ] 已合并
```

---

**所有AI生成代码必须通过审查才能进入代码库**
