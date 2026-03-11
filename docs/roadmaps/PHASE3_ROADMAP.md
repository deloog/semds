# SEMDS Phase 3 原子化开发路线图

**文档版本**: v1.0  
**对应规格**: SEMDS_v1.1_SPEC.md Phase 3  
**目标**: 实现完整进化循环

---

## 📋 Phase 3 任务总览

**时间**: 1周  
**前置依赖**: Phase 2 完成并通过验收  
**交付物**: 完整的进化循环系统  
**验收标准**: 跑通计算器实验的完整进化循环

---

## 🎯 任务分解（WBS）

### 3.1 Thompson Sampling 策略优化器

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P3-T1 | 实现 StrategyArm 类 | 3h | - | AI |
| P3-T2 | 实现 Thompson Sampling 采样 | 4h | P3-T1 | AI |
| P3-T3 | 实现策略更新逻辑 | 3h | P3-T2 | AI |
| P3-T4 | 策略状态持久化 | 2h | P3-T3 | AI |
| P3-T5 | 策略优化器单元测试 | 4h | P3-T1-P3-T4 | AI |

**详细规格**:
```python
# evolution/strategy_optimizer.py

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json

# 策略配置空间（来自规格）
STRATEGY_DIMENSIONS = {
    "mutation_type": ["conservative", "aggressive", "hybrid"],
    "validation_mode": ["lightweight", "comprehensive"],
    "generation_temperature": [0.2, 0.5, 0.8]
}

@dataclass
class StrategyArm:
    """
    Thompson Sampling策略臂
    
    使用Beta分布进行采样
    """
    key: str  # 策略组合的唯一标识
    alpha: float = 1.0  # 成功次数 + 先验
    beta: float = 1.0   # 失败次数 + 先验
    total_uses: int = 0
    
    def sample(self) -> float:
        """从Beta分布采样"""
        return np.random.beta(self.alpha, self.beta)
    
    def update(self, success: bool):
        """更新策略性能"""
        if success:
            self.alpha += 1
        else:
            self.beta += 1
        self.total_uses += 1
    
    def expected_value(self) -> float:
        """期望性能"""
        return self.alpha / (self.alpha + self.beta)

class StrategyOptimizer:
    """
    Thompson Sampling策略优化器
    
    职责:
    - 管理策略臂集合
    - 选择下一策略（采样）
    - 更新策略性能
    - 任务间策略隔离
    """
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.arms: Dict[str, StrategyArm] = {}
        self._initialize_arms()
    
    def _initialize_arms(self):
        """初始化所有策略组合"""
        # 生成所有策略组合
        import itertools
        keys = list(STRATEGY_DIMENSIONS.keys())
        values = list(STRATEGY_DIMENSIONS.values())
        
        for combo in itertools.product(*values):
            strategy = dict(zip(keys, combo))
            key = self._strategy_to_key(strategy)
            self.arms[key] = StrategyArm(key=key)
    
    def select_strategy(self) -> dict:
        """
        选择下一个策略
        
        使用Thompson Sampling:
        1. 从每个臂的Beta分布采样
        2. 选择采样值最高的臂
        3. 返回对应的策略配置
        """
        best_key = max(self.arms.keys(), key=lambda k: self.arms[k].sample())
        return self._key_to_strategy(best_key)
    
    def report_result(self, strategy: dict, success: bool, score: float):
        """
        报告策略执行结果
        
        Args:
            strategy: 使用的策略
            success: 是否成功（得分超过阈值）
            score: 具体得分
        """
        key = self._strategy_to_key(strategy)
        if key in self.arms:
            self.arms[key].update(success)
    
    def _strategy_to_key(self, strategy: dict) -> str:
        """策略字典转字符串键"""
        return json.dumps(strategy, sort_keys=True)
    
    def _key_to_strategy(self, key: str) -> dict:
        """字符串键转策略字典"""
        return json.loads(key)
    
    def get_arm_stats(self) -> List[dict]:
        """获取所有策略臂统计"""
        return [
            {
                "key": arm.key,
                "alpha": arm.alpha,
                "beta": arm.beta,
                "uses": arm.total_uses,
                "expected": arm.expected_value()
            }
            for arm in self.arms.values()
        ]
```

---

### 3.2 双轨评估器（Dual Evaluator）

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P3-T6 | 实现内生评估（测试通过率） | 3h | P3-T7 | AI |
| P3-T7 | 实现外生评估（一致性验证） | 5h | - | AI |
| P3-T8 | 实现Goodhart检测 | 3h | P3-T6,P3-T7 | AI |
| P3-T9 | 实现综合评分公式 | 2h | P3-T6-P3-T8 | AI |
| P3-T10 | 双轨评估器单元测试 | 4h | P3-T6-P3-T9 | AI |
| **P3-T10a** | **实现AI生成边界用例** | **3h** | **P3-T7** | **AI** |

**详细规格**:
```python
# evolution/dual_evaluator.py

from dataclasses import dataclass
from typing import Optional, List, Dict
import ast
import random

@dataclass
class EvaluationReport:
    """评估报告"""
    # 内生评估
    intrinsic_score: float  # 测试通过率
    pass_rate: float
    test_results: Dict[str, bool]
    execution_time_ms: float
    
    # 外生评估
    extrinsic_score: float  # 一致性验证
    consistency_score: float
    static_analysis_score: float
    edge_case_results: List[dict]
    
    # 综合
    final_score: float
    
    # Goodhart检测
    goodhart_flag: bool
    goodhart_reason: Optional[str] = None

class DualEvaluator:
    """
    双轨评估器
    
    职责:
    - 内生评估：测试通过率
    - 外生评估：行为一致性
    - Goodhart检测：防止"打游戏"
    """
    
    # 评分权重（来自规格）
    WEIGHT_PASS_RATE = 0.6
    WEIGHT_CONSISTENCY = 0.2
    WEIGHT_LATENCY = 0.1
    WEIGHT_COMPLEXITY = 0.1
    
    # Goodhart阈值
    GOODHART_PASS_THRESHOLD = 0.9
    GOODHART_CONSISTENCY_THRESHOLD = 0.5
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    def evaluate(
        self,
        code: str,
        test_report: 'TestRunReport',
        function_signature: str,
        requirements: List[str]
    ) -> EvaluationReport:
        """
        双轨评估
        
        Args:
            code: 被评估的代码
            test_report: 测试运行报告
            function_signature: 函数签名
            requirements: 需求列表
            
        Returns:
            EvaluationReport: 完整评估报告
        """
        # 内生评估
        intrinsic = self._intrinsic_evaluate(test_report)
        
        # 外生评估
        extrinsic = self._extrinsic_evaluate(code, function_signature, requirements)
        
        # 计算综合分
        final_score = self._calculate_final_score(intrinsic, extrinsic)
        
        # Goodhart检测
        goodhart_flag, goodhart_reason = self._detect_goodhart(intrinsic, extrinsic)
        
        return EvaluationReport(
            intrinsic_score=intrinsic['score'],
            pass_rate=intrinsic['pass_rate'],
            test_results=intrinsic['test_results'],
            execution_time_ms=intrinsic['execution_time_ms'],
            extrinsic_score=extrinsic['score'],
            consistency_score=extrinsic['consistency_score'],
            static_analysis_score=extrinsic['static_analysis_score'],
            edge_case_results=extrinsic['edge_case_results'],
            final_score=final_score,
            goodhart_flag=goodhart_flag,
            goodhart_reason=goodhart_reason
        )
    
    def _intrinsic_evaluate(self, test_report: 'TestRunReport') -> dict:
        """内生评估：基于测试通过率"""
        return {
            'score': test_report.pass_rate,
            'pass_rate': test_report.pass_rate,
            'test_results': {r.test_name: r.passed for r in test_report.results},
            'execution_time_ms': sum(
                r.execution_time_ms or 0 for r in test_report.results
            ) / len(test_report.results) if test_report.results else 0
        }
    
    def _extrinsic_evaluate(
        self,
        code: str,
        function_signature: str,
        requirements: List[str]
    ) -> dict:
        """
        外生评估：行为一致性验证
        
        包括:
        1. 静态代码分析
        2. 边界用例生成与测试
        3. 与参考实现对比（如有）
        """
        # 静态分析
        static_score = self._static_analysis(code)
        
        # 边界用例生成（Phase 3简化版，后期用AI生成）
        edge_cases = self._generate_edge_cases(function_signature)
        edge_results = self._test_edge_cases(code, edge_cases)
        
        # 一致性得分
        consistency = sum(r['passed'] for r in edge_results) / len(edge_results) if edge_results else 0
        
        return {
            'score': 0.5 * static_score + 0.5 * consistency,  # 简化版
            'consistency_score': consistency,
            'static_analysis_score': static_score,
            'edge_case_results': edge_results
        }
    
    def _static_analysis(self, code: str) -> float:
        """静态代码分析"""
        try:
            tree = ast.parse(code)
            
            # 检查指标
            checks = {
                'has_docstring': self._check_docstring(tree),
                'no_dangerous_patterns': self._check_dangerous_patterns(tree),
                'reasonable_complexity': self._check_complexity(tree),
                'proper_error_handling': self._check_error_handling(tree)
            }
            
            return sum(checks.values()) / len(checks)
        except SyntaxError:
            return 0.0
    
    def _check_docstring(self, tree: ast.AST) -> bool:
        """检查是否有文档字符串"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return ast.get_docstring(node) is not None
        return False
    
    def _check_dangerous_patterns(self, tree: ast.AST) -> bool:
        """检查危险模式（eval, exec等）"""
        dangerous = {'eval', 'exec', '__import__', 'compile'}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in dangerous:
                        return False
        return True
    
    def _check_complexity(self, tree: ast.AST) -> bool:
        """检查圈复杂度"""
        # 简化版：检查嵌套深度
        max_depth = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While)):
                depth = self._get_nesting_depth(node)
                max_depth = max(max_depth, depth)
        return max_depth <= 4
    
    def _check_error_handling(self, tree: ast.AST) -> bool:
        """检查错误处理完整性"""
        has_try = any(
            isinstance(node, ast.Try) for node in ast.walk(tree)
        )
        return has_try
    
    def _get_nesting_depth(self, node: ast.AST, depth: int = 0) -> int:
        """获取节点嵌套深度"""
        # 简化实现
        return depth
    
    def _generate_edge_cases(
        self, 
        function_signature: str,
        requirements: List[str],
        existing_test_scenarios: List[str]
    ) -> List[dict]:
        """
        生成边界用例（AI驱动）
        
        使用Claude API生成边界测试用例，避免依赖预设测试。
        这是防止Goodhart现象的关键。
        """
        pass
    
    def _call_claude_for_edge_cases(
        self,
        function_signature: str,
        requirements: List[str],
        existing_test_scenarios: List[str]
    ) -> List[dict]:
        """
        调用Claude API生成边界用例
        
        使用规格文档定义的EDGE_CASE_GENERATION_PROMPT模板。
        """
        import json
        from evolution.code_generator import CodeGenerator
        
        prompt = f"""
给定以下函数规格，生成10个边界测试用例（JSON格式）。
这些用例不能与现有测试重复，重点关注：
- 极端值（最大/最小/零）
- 类型边界
- 可能触发bug的特殊组合

函数: {function_signature}
需求: {requirements}
现有测试覆盖的场景: {existing_test_scenarios}

只输出JSON数组，格式：
[{{"input": {{...}}, "expected_output": ..., "description": "..."}}, ...]
"""
        # 调用API并解析JSON响应
        # 实现...
    
    def _test_edge_cases(self, code: str, edge_cases: List[dict]) -> List[dict]:
        """测试边界用例"""
        results = []
        # 实际执行测试
        # 这里简化处理，实际应在沙盒中执行
        for case in edge_cases:
            results.append({
                'desc': case['desc'],
                'passed': True,  # 简化版
                'input': case['input']
            })
        return results
    
    def _calculate_final_score(self, intrinsic: dict, extrinsic: dict) -> float:
        """计算综合评分"""
        pass_rate = intrinsic['pass_rate']
        consistency = extrinsic['consistency_score']
        
        # 延迟惩罚（执行时间越长，惩罚越大）
        latency_penalty = min(intrinsic['execution_time_ms'] / 1000, 1.0)
        
        # 简化版复杂度惩罚
        complexity_penalty = 0.0
        
        score = (
            self.WEIGHT_PASS_RATE * pass_rate +
            self.WEIGHT_CONSISTENCY * consistency +
            self.WEIGHT_LATENCY * (1 - latency_penalty) +
            self.WEIGHT_COMPLEXITY * (1 - complexity_penalty)
        )
        return min(max(score, 0.0), 1.0)
    
    def _detect_goodhart(self, intrinsic: dict, extrinsic: dict) -> tuple:
        """
        检测Goodhart现象
        
        触发条件：
        - 内生分高（pass_rate > 0.9）
        - 但外生分低（consistency < 0.5）
        """
        if (intrinsic['pass_rate'] > self.GOODHART_PASS_THRESHOLD and
            extrinsic['consistency_score'] < self.GOODHART_CONSISTENCY_THRESHOLD):
            return True, (
                f"Goodhart检测触发: 测试通过率高({intrinsic['pass_rate']:.2f}) "
                f"但一致性低({extrinsic['consistency_score']:.2f})"
            )
        return False, None
```

---

### 3.3 终止条件检查器

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P3-T11 | 实现终止条件检查 | 3h | - | AI |
| P3-T12 | 实现停滞检测 | 2h | P3-T11 | AI |
| P3-T13 | 实现Goodhart暂停逻辑 | 2h | P3-T11 | AI |
| P3-T14 | 终止检查器单元测试 | 3h | P3-T11-P3-T13 | AI |

**详细规格**:
```python
# evolution/termination_checker.py

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta

@dataclass
class TerminationConfig:
    """终止条件配置（RTD - Recursive Termination Design）"""
    # 成功终止
    success_threshold: float = 0.95
    consistency_threshold: float = 0.90
    
    # 强制终止
    max_generations: int = 50
    max_wall_time_minutes: int = 60
    stagnation_generations: int = 10
    goodhart_consecutive: int = 3
    
    # 人工干预
    human_abort: bool = False

@dataclass
class TerminationDecision:
    """终止决策"""
    should_terminate: bool
    reason: str
    is_success: bool  # True=成功终止, False=失败终止

class TerminationChecker:
    """
    终止条件检查器
    
    职责:
    - 检查各种终止条件
    - 检测停滞
    - 处理Goodhart暂停
    """
    
    def __init__(self, config: TerminationConfig = None):
        self.config = config or TerminationConfig()
        self.start_time = datetime.utcnow()
        self.score_history: List[float] = []
        self.goodhart_count: int = 0
    
    def check(
        self,
        current_gen: int,
        current_score: float,
        goodhart_flag: bool,
        human_abort: bool = False
    ) -> TerminationDecision:
        """
        检查是否应该终止
        
        Returns:
            TerminationDecision: 终止决策
        """
        self.score_history.append(current_score)
        
        # 1. 人工中止
        if human_abort or self.config.human_abort:
            return TerminationDecision(
                should_terminate=True,
                reason="人工中止",
                is_success=False
            )
        
        # 2. 成功终止条件
        if (current_score >= self.config.success_threshold):
            return TerminationDecision(
                should_terminate=True,
                reason=f"达到成功阈值: {current_score:.3f}",
                is_success=True
            )
        
        # 3. 最大代数
        if current_gen >= self.config.max_generations:
            return TerminationDecision(
                should_terminate=True,
                reason=f"达到最大代数: {current_gen}",
                is_success=False
            )
        
        # 4. 超时
        elapsed = datetime.utcnow() - self.start_time
        if elapsed > timedelta(minutes=self.config.max_wall_time_minutes):
            return TerminationDecision(
                should_terminate=True,
                reason=f"超时: {elapsed}",
                is_success=False
            )
        
        # 5. 停滞检测
        if len(self.score_history) >= self.config.stagnation_generations:
            recent_scores = self.score_history[-self.config.stagnation_generations:]
            if max(recent_scores) - min(recent_scores) < 0.01:  # 几乎无变化
                return TerminationDecision(
                    should_terminate=True,
                    reason=f"停滞 {self.config.stagnation_generations} 代",
                    is_success=False
                )
        
        # 6. Goodhart连续检测
        if goodhart_flag:
            self.goodhart_count += 1
            if self.goodhart_count >= self.config.goodhart_consecutive:
                return TerminationDecision(
                    should_terminate=True,
                    reason=f"连续 {self.goodhart_count} 代触发Goodhart",
                    is_success=False
                )
        else:
            self.goodhart_count = 0
        
        # 继续进化
        return TerminationDecision(
            should_terminate=False,
            reason="",
            is_success=False
        )
```

---

### 3.4 Git 自动版本控制

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P3-T15 | 实现 Git 提交功能 | 3h | - | AI |
| P3-T16 | 实现按代提交 | 2h | P3-T15 | AI |
| P3-T17 | 实现回滚功能 | 2h | P3-T16 | AI |
| P3-T18 | Git 功能单元测试 | 3h | P3-T15-P3-T17 | AI |

**详细规格**:
```python
# core/version_control.py

import subprocess
from pathlib import Path
from typing import Optional

class GitManager:
    """
    Git版本控制管理器
    
    职责:
    - 自动提交每代代码
    - 支持回滚到指定代
    """
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
    
    def commit_generation(
        self,
        task_id: str,
        gen_number: int,
        file_path: str,
        score: float
    ) -> str:
        """
        提交一代进化代码
        
        Args:
            task_id: 任务ID
            gen_number: 代数
            file_path: 代码文件路径
            score: 得分
            
        Returns:
            str: Git commit hash
        """
        # 添加文件
        self._run_git(["add", file_path])
        
        # 提交
        commit_msg = f"[{task_id}] gen{gen_number}: score={score:.3f}"
        self._run_git(["commit", "-m", commit_msg])
        
        # 获取commit hash
        result = self._run_git(["rev-parse", "HEAD"])
        return result.stdout.strip()
    
    def rollback_to_generation(self, file_path: str, commit_hash: str):
        """
        回滚到指定代
        
        Args:
            file_path: 代码文件路径
            commit_hash: Git commit hash
        """
        self._run_git(["checkout", commit_hash, "--", file_path])
    
    def _run_git(self, args: list) -> 'subprocess.CompletedProcess':
        """运行git命令"""
        cmd = ["git"] + args
        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git命令失败: {result.stderr}")
        return result
```

---

### 3.3b Skills Library 技能库（Layer 1）

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| **P3-T18a** | **创建 skills/ 目录结构** | **1h** | **-** | **AI** |
| **P3-T18b** | **实现代码生成模板（Jinja2）** | **3h** | **P3-T18a** | **AI** |
| **P3-T18c** | **实现策略注册表** | **2h** | **P3-T18a** | **AI** |
| **P3-T18d** | **实现已验证策略入库逻辑** | **2h** | **P3-T18c** | **AI** |
| **P3-T18e** | **技能库单元测试** | **2h** | **P3-T18b-P3-T18d** | **AI** |

**详细规格**:
```python
# skills/templates/python_function.j2
"""
你是一个Python专家，任务是实现以下函数规格。

## 任务描述
{{ task_description }}

## 目标函数签名
```python
{{ function_signature }}
```

## 需求列表
{{ requirements }}

## 前代实现（如有）
```python
{{ previous_code }}
```

## 前代得分
- 内生分（测试通过率）: {{ intrinsic_score }}
- 失败的测试用例: {{ failed_tests }}
- 外生分（一致性验证）: {{ extrinsic_score }}

## 本代进化策略
- 变异类型: {{ mutation_type }}
- 重点改进方向: {{ improvement_focus }}

## 要求
1. 只输出函数实现代码，不要包含测试代码
2. 不要使用任何外部库
3. 代码必须完整可执行
4. 不要添加任何解释文字

```python
"""

# skills/strategies/strategy_registry.json
{
  "version": "1.0",
  "verified_strategies": [
    {
      "strategy_key": "{...}",
      "task_type": "calculator",
      "success_rate": 0.95,
      "avg_generations": 8.5,
      "added_at": "2026-03-07T10:00:00Z"
    }
  ]
}

# skills/template_manager.py
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

class TemplateManager:
    """
    模板管理器
    
    管理代码生成模板，支持:
    - 加载Jinja2模板
    - 渲染生成Prompt
    - A/B测试不同模板效果
    """
    
    def __init__(self, templates_dir: str = "skills/templates"):
        self.env = Environment(loader=FileSystemLoader(templates_dir))
    
    def render_prompt(self, template_name: str, context: dict) -> str:
        """渲染Prompt模板"""
        template = self.env.get_template(f"{template_name}.j2")
        return template.render(**context)

# skills/strategy_registry.py
import json
from pathlib import Path
from typing import List, Dict, Optional

class StrategyRegistry:
    """
    策略注册表
    
    管理已验证的进化策略:
    - 记录成功策略
    - A/B测试不同策略效果
    - 策略版本管理
    """
    
    def __init__(self, registry_path: str = "skills/strategies/strategy_registry.json"):
        self.registry_path = Path(registry_path)
        self._load_registry()
    
    def _load_registry(self):
        """加载注册表"""
        if self.registry_path.exists():
            with open(self.registry_path) as f:
                self.registry = json.load(f)
        else:
            self.registry = {"version": "1.0", "verified_strategies": []}
    
    def add_verified_strategy(
        self,
        strategy: dict,
        task_type: str,
        success_rate: float,
        avg_generations: float
    ):
        """
        添加已验证的策略到注册表
        
        只有达到一定成功率的策略才入库（Goodhart检测通过后）
        """
        entry = {
            "strategy_key": json.dumps(strategy, sort_keys=True),
            "task_type": task_type,
            "success_rate": success_rate,
            "avg_generations": avg_generations,
            "added_at": datetime.utcnow().isoformat()
        }
        self.registry["verified_strategies"].append(entry)
        self._save_registry()
    
    def get_strategies_for_task_type(self, task_type: str) -> List[dict]:
        """获取适合特定任务类型的策略"""
        return [
            s for s in self.registry["verified_strategies"]
            if s["task_type"] == task_type
        ]
    
    def _save_registry(self):
        """保存注册表"""
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=2)
```

---

### 3.5 进化编排器（Orchestrator）

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P3-T19 | 实现 Orchestrator 主循环 | 5h | P3-T1-P3-T18e | AI |
| P3-T20 | 集成所有组件 | 4h | P3-T19 | AI |
| P3-T21 | 实现进化日志记录 | 2h | P3-T20 | AI |
| P3-T22 | 编排器单元测试 | 4h | P3-T19-P3-T21 | AI |

**详细规格**:
```python
# evolution/orchestrator.py

import uuid
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

class EvolutionOrchestrator:
    """
    进化编排器
    
    职责:
    - 管理完整进化循环
    - 协调各组件工作
    - 记录进化历史
    """
    
    def __init__(
        self,
        task: 'Task',
        code_generator: 'CodeGenerator',
        test_runner: 'TestRunner',
        dual_evaluator: 'DualEvaluator',
        strategy_optimizer: 'StrategyOptimizer',
        termination_checker: 'TerminationChecker',
        git_manager: 'GitManager',
        on_generation: Optional[Callable] = None
    ):
        self.task = task
        self.code_generator = code_generator
        self.test_runner = test_runner
        self.dual_evaluator = dual_evaluator
        self.strategy_optimizer = strategy_optimizer
        self.termination_checker = termination_checker
        self.git_manager = git_manager
        self.on_generation = on_generation
        
        self.current_gen = 0
        self.best_score = 0.0
        self.best_code = None
        self.best_gen = 0
    
    def run(self) -> 'EvolutionResult':
        """
        运行完整进化循环
        
        Returns:
            EvolutionResult: 进化结果
        """
        print(f"开始进化任务: {self.task.name}")
        print(f"最大代数: {self.termination_checker.config.max_generations}")
        
        while True:
            self.current_gen += 1
            print(f"\n{'='*60}")
            print(f"Generation {self.current_gen}")
            print('='*60)
            
            # 1. 选择策略
            strategy = self.strategy_optimizer.select_strategy()
            print(f"策略: {strategy}")
            
            # 2. 生成代码
            context = GenerationContext(
                task_description=self.task.description,
                function_signature=self.task.target_function_signature,
                requirements=[],  # 从task解析
                previous_code=self.best_code,
                mutation_type=strategy['mutation_type']
            )
            code = self.code_generator.generate(context)
            
            # 3. 保存代码
            solution_path = self._save_code(code)
            
            # 4. 运行测试
            test_report = self.test_runner.run_tests(
                solution_path=solution_path,
                test_file_path=self.task.test_file_path
            )
            
            # 5. 双轨评估
            eval_report = self.dual_evaluator.evaluate(
                code=code,
                test_report=test_report,
                function_signature=self.task.target_function_signature,
                requirements=[]
            )
            
            # 6. Git提交
            commit_hash = self.git_manager.commit_generation(
                task_id=self.task.id,
                gen_number=self.current_gen,
                file_path=solution_path,
                score=eval_report.final_score
            )
            
            # 7. 更新策略
            success = eval_report.final_score > self.best_score
            self.strategy_optimizer.report_result(
                strategy=strategy,
                success=success,
                score=eval_report.final_score
            )
            
            # 8. 更新最佳
            if eval_report.final_score > self.best_score:
                self.best_score = eval_report.final_score
                self.best_code = code
                self.best_gen = self.current_gen
                print(f"🎉 新最佳! 得分: {self.best_score:.3f}")
            
            # 9. 记录到数据库
            self._save_generation(
                gen_number=self.current_gen,
                code=code,
                strategy=strategy,
                eval_report=eval_report,
                commit_hash=commit_hash
            )
            
            # 10. 回调通知
            if self.on_generation:
                self.on_generation(self.current_gen, eval_report)
            
            # 11. 检查终止
            decision = self.termination_checker.check(
                current_gen=self.current_gen,
                current_score=eval_report.final_score,
                goodhart_flag=eval_report.goodhart_flag
            )
            
            if decision.should_terminate:
                print(f"\n{'='*60}")
                print(f"进化终止: {decision.reason}")
                print(f"最终最佳: Gen {self.best_gen}, 得分 {self.best_score:.3f}")
                print('='*60)
                return EvolutionResult(
                    success=decision.is_success,
                    reason=decision.reason,
                    best_gen=self.best_gen,
                    best_score=self.best_score,
                    best_code=self.best_code,
                    total_gens=self.current_gen
                )
    
    def _save_code(self, code: str) -> str:
        """保存代码到文件"""
        # 实现...
        pass
    
    def _save_generation(self, **kwargs):
        """保存进化代到数据库"""
        # 实现...
        pass

@dataclass
class EvolutionResult:
    """进化结果"""
    success: bool
    reason: str
    best_gen: int
    best_score: float
    best_code: str
    total_gens: int
```

---

## 📊 任务依赖图

```
P3-T1 (StrategyArm)
    └── P3-T2 (Thompson Sampling)
        ├── P3-T3 (策略更新)
        ├── P3-T4 (持久化)
        └── P3-T5 (测试)

P3-T7 (外生评估)
    └── P3-T6 (内生评估)
        ├── P3-T8 (Goodhart检测)
        ├── P3-T9 (综合评分)
        ├── P3-T10 (测试)
        └── P3-T10a (AI生成边界用例) ← 新增

P3-T11 (终止条件)
    ├── P3-T12 (停滞检测)
    ├── P3-T13 (Goodhart暂停)
    └── P3-T14 (测试)

P3-T15 (Git提交)
    ├── P3-T16 (按代提交)
    ├── P3-T17 (回滚)
    └── P3-T18 (测试)

P3-T18a (目录结构) ← 新增: Skills Library
    ├── P3-T18b (Jinja2模板)
    ├── P3-T18c (策略注册表)
    ├── P3-T18d (入库逻辑)
    └── P3-T18e (测试)

P3-T19 (Orchestrator) ← 依赖所有上游任务 (含P3-T18e)
    ├── P3-T20 (集成)
    ├── P3-T21 (日志)
    └── P3-T22 (测试)
```

---

## ✅ 验收标准

### 必须完成
- [ ] StrategyOptimizer 实现并通过测试
- [ ] DualEvaluator 实现并通过测试 (含AI生成边界用例P3-T10a)
- [ ] TerminationChecker 实现并通过测试
- [ ] GitManager 实现并通过测试
- [ ] EvolutionOrchestrator 实现并通过测试
- [ ] Skills Library 实现并通过测试 (P3-T18a-P3-T18e)

### 功能验收
```bash
# 运行计算器实验完整进化循环
python demo_phase3.py

# 期望输出:
# - 成功运行多代进化
# - 最终得分 >= 0.90
# - Thompson Sampling策略选择有效
# - Goodhart检测正常工作
# - 每代有Git提交
```

### 测试验收
```bash
# 所有测试通过
pytest tests/evolution/ -v

# 覆盖率
pytest tests/ --cov=evolution --cov-report=term-missing
```

---

**最后更新**: 2026-03-07  
**前置**: [Phase 2路线图](./PHASE2_ROADMAP.md)
