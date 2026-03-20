"""
Dual Evaluator 模块 - 双轨评估器集成

整合：
1. IntrinsicEvaluator（内生评估）- 静态代码质量
2. ExtrinsicEvaluator（外生评估）- 行为一致性
3. GoodhartDetector（Goodhart检测）- 作弊模式检测

生成综合评估报告，用于代码进化的质量评估。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from evolution.extrinsic_evaluator import ExtrinsicEvaluator
from evolution.goodhart_detector import GoodhartDetectionResult, GoodhartDetector
from evolution.intrinsic_evaluator import IntrinsicEvaluator


@dataclass
class DualEvaluationReport:
    """双轨评估报告

    Attributes:
        intrinsic_score: 内生评估得分 (0-1)
        extrinsic_score: 外生评估得分 (0-1)
        goodhart_detected: 是否检测到Goodhart现象
        final_score: 最终综合得分 (0-1)
        intrinsic_details: 内生评估详情
        extrinsic_details: 外生评估详情
        goodhart_details: Goodhart检测详情（当检测到）
    """

    intrinsic_score: float
    extrinsic_score: float
    goodhart_detected: bool
    final_score: float
    intrinsic_details: Dict[str, Any] = field(default_factory=dict)
    extrinsic_details: Dict[str, Any] = field(default_factory=dict)
    goodhart_details: Optional[Dict[str, Any]] = None


class DualEvaluator:
    """双轨评估器

    整合内生评估、外生评估和Goodhart检测，生成综合评估报告。

    评分权重：
    - 内生评估：40%
    - 外生评估：40%
    - Goodhart惩罚：在范围内降低得分

    约束：
    - 最终得分必须在 [min(内生,外生), max(内生,外生)] 范围内

    Example:
        >>> evaluator = DualEvaluator()
        >>> report = evaluator.evaluate(
        ...     code="def add(a, b): return a + b",
        ...     function_signature="add(a, b)",
        ...     requirements=["Returns sum"]
        ... )
        >>> print(f"Final score: {report['final_score']:.2f}")
        >>> if report['goodhart_detected']:
        ...     print("Warning: Potential cheating detected!")
    """

    # 权重配置
    WEIGHT_INTRINSIC = 0.4
    WEIGHT_EXTRINSIC = 0.4
    WEIGHT_GOODHART_PENALTY = 0.2  # 当检测到Goodhart时应用的惩罚权重

    def __init__(
        self,
        intrinsic_evaluator: Optional[IntrinsicEvaluator] = None,
        extrinsic_evaluator: Optional[ExtrinsicEvaluator] = None,
        goodhart_detector: Optional[GoodhartDetector] = None,
    ) -> None:
        """初始化双轨评估器

        Args:
            intrinsic_evaluator: 内生评估器，默认创建新实例
            extrinsic_evaluator: 外生评估器，默认创建新实例
            goodhart_detector: Goodhart检测器，默认创建新实例
        """
        self.intrinsic_evaluator = intrinsic_evaluator or IntrinsicEvaluator()
        self.extrinsic_evaluator = extrinsic_evaluator or ExtrinsicEvaluator()
        self.goodhart_detector = goodhart_detector or GoodhartDetector()

    def evaluate(
        self,
        code: str,
        function_signature: str,
        requirements: List[str],
        test_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """执行双轨评估

        Args:
            code: 要评估的代码字符串
            function_signature: 函数签名
            requirements: 功能需求描述列表
            test_code: 可选的测试代码，用于计算真实测试通过率

        Returns:
            评估报告字典
        """
        # 处理空代码
        if not code or not code.strip():
            return self._create_zero_report("Empty code")

        # 检查语法
        try:
            import ast

            ast.parse(code)
        except SyntaxError:
            return self._create_zero_report("Syntax error")

        # 1. 内生评估（静态分析）
        intrinsic_result = self.intrinsic_evaluator.evaluate(code)
        intrinsic_score = intrinsic_result.total_score

        # 2. 外生评估（行为一致性）
        # 传入 test_code 启用增强评估（性能+鲁棒性测试）
        extrinsic_result = self.extrinsic_evaluator.evaluate(
            code=code,
            function_signature=function_signature,
            requirements=requirements,
            test_code=test_code,  # 启用增强模式
        )
        extrinsic_score = extrinsic_result["score"]

        # 3. 计算真实的测试通过率（如果提供了测试代码）
        pass_rate = intrinsic_score  # 默认使用内生得分作为近似
        if test_code:
            from evolution.test_runner import TestRunner

            test_result = TestRunner().run_tests_with_code(code, test_code)
            pass_rate = test_result.get("pass_rate", intrinsic_score)

        # 4. Goodhart检测
        # 使用真实测试通过率（如果有）或内生得分作为回退
        goodhart_result = self.goodhart_detector.detect(
            pass_rate=pass_rate, consistency_score=extrinsic_score
        )

        # 4. 计算最终得分
        final_score = self._calculate_final_score(
            intrinsic_score=intrinsic_score,
            extrinsic_score=extrinsic_score,
            goodhart_result=goodhart_result,
        )

        # 5. 构建报告
        report = {
            "intrinsic_score": round(intrinsic_score, 2),
            "extrinsic_score": round(extrinsic_score, 2),
            "goodhart_detected": goodhart_result.is_goodhart,
            "final_score": round(final_score, 2),
            "intrinsic_details": {
                "syntax_valid": intrinsic_result.syntax_valid,
                "static_score": intrinsic_result.static_score,
                "structure_score": intrinsic_result.structure_score,
                "doc_score": intrinsic_result.doc_score,
                "warnings": intrinsic_result.warnings,
            },
            "extrinsic_details": {
                "consistency_score": extrinsic_result.get("consistency_score"),
                "static_analysis_score": extrinsic_result.get("static_analysis_score"),
                "edge_case_results": extrinsic_result.get("edge_case_results", []),
            },
        }

        # 添加Goodhart详情（如果检测到）
        if goodhart_result.is_goodhart:
            report["goodhart_details"] = {
                "confidence": goodhart_result.confidence,
                "reason": goodhart_result.reason,
            }

        return report

    def _calculate_final_score(
        self,
        intrinsic_score: float,
        extrinsic_score: float,
        goodhart_result: GoodhartDetectionResult,
    ) -> float:
        """计算最终得分

        计算逻辑：
        1. 基础得分 = 加权平均（内生40% + 外生40%）/ 80%
        2. 如果检测到Goodhart，在有效范围内应用惩罚

        约束：最终得分必须在 [min(内生,外生), max(内生,外生)] 范围内

        Args:
            intrinsic_score: 内生评估得分
            extrinsic_score: 外生评估得分
            goodhart_result: Goodhart检测结果

        Returns:
            最终得分 (0-1)
        """
        # 计算有效范围
        score_min = min(intrinsic_score, extrinsic_score)
        score_max = max(intrinsic_score, extrinsic_score)

        # 基础加权得分（归一化到0-1）
        base_score = (
            self.WEIGHT_INTRINSIC * intrinsic_score
            + self.WEIGHT_EXTRINSIC * extrinsic_score
        ) / (self.WEIGHT_INTRINSIC + self.WEIGHT_EXTRINSIC)

        if not goodhart_result.is_goodhart:
            # 无Goodhart，直接返回加权得分（限制在范围内）
            return max(score_min, min(score_max, base_score))

        # 检测到Goodhart，应用惩罚（在范围内降低）
        # 惩罚程度基于置信度
        penalty_factor = 1.0 - (
            goodhart_result.confidence * self.WEIGHT_GOODHART_PENALTY
        )
        penalized_score = base_score * penalty_factor

        # 确保惩罚后的得分在有效范围内
        return max(score_min, min(score_max, penalized_score))

    def _create_zero_report(self, reason: str) -> Dict[str, Any]:
        """创建零分报告

        Args:
            reason: 零分原因

        Returns:
            零分报告字典
        """
        return {
            "intrinsic_score": 0.0,
            "extrinsic_score": 0.0,
            "goodhart_detected": False,
            "final_score": 0.0,
            "intrinsic_details": {
                "syntax_valid": False,
                "static_score": 0.0,
                "structure_score": 0.0,
                "doc_score": 0.0,
                "warnings": [reason],
            },
            "extrinsic_details": {
                "consistency_score": 0.0,
                "static_analysis_score": 0.0,
                "edge_case_results": [],
            },
        }
