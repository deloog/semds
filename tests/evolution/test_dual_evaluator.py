"""
Dual Evaluator 集成测试模块 - TDD Red Phase

测试 DualEvaluator 类 - 整合内生评估、外生评估和Goodhart检测

职责：
1. 整合 IntrinsicEvaluator 和 ExtrinsicEvaluator 的结果
2. 使用 GoodhartDetector 检测作弊模式
3. 生成最终的综合评估报告
"""

# Import will be added after implementation exists
# from evolution.dual_evaluator import DualEvaluator, DualEvaluationReport


# =============================================================================
# Test DualEvaluationResult Dataclass
# =============================================================================


class TestDualEvaluationReport:
    """DualEvaluationReport 数据类测试"""

    def test_report_has_intrinsic_score_field(self):
        """测试报告包含内生得分字段"""
        from evolution.dual_evaluator import DualEvaluationReport

        report = DualEvaluationReport(
            intrinsic_score=0.85,
            extrinsic_score=0.75,
            goodhart_detected=False,
            final_score=0.80,
        )
        assert report.intrinsic_score == 0.85

    def test_report_has_extrinsic_score_field(self):
        """测试报告包含外生得分字段"""
        from evolution.dual_evaluator import DualEvaluationReport

        report = DualEvaluationReport(
            intrinsic_score=0.85,
            extrinsic_score=0.75,
            goodhart_detected=False,
            final_score=0.80,
        )
        assert report.extrinsic_score == 0.75

    def test_report_has_goodhart_flag_field(self):
        """测试报告包含Goodhart检测标志"""
        from evolution.dual_evaluator import DualEvaluationReport

        report = DualEvaluationReport(
            intrinsic_score=0.95,
            extrinsic_score=0.30,
            goodhart_detected=True,
            final_score=0.40,
        )
        assert report.goodhart_detected is True

    def test_report_has_final_score_field(self):
        """测试报告包含最终得分字段"""
        from evolution.dual_evaluator import DualEvaluationReport

        report = DualEvaluationReport(
            intrinsic_score=0.85,
            extrinsic_score=0.75,
            goodhart_detected=False,
            final_score=0.80,
        )
        assert report.final_score == 0.80

    def test_report_has_optional_details(self):
        """测试报告包含可选详细信息"""
        from evolution.dual_evaluator import DualEvaluationReport

        report = DualEvaluationReport(
            intrinsic_score=0.85,
            extrinsic_score=0.75,
            goodhart_detected=False,
            final_score=0.80,
            intrinsic_details={"syntax_valid": True},
            extrinsic_details={"consistency_score": 0.75},
        )
        assert report.intrinsic_details == {"syntax_valid": True}


# =============================================================================
# Test DualEvaluator - Initialization
# =============================================================================


class TestDualEvaluatorInitialization:
    """DualEvaluator 初始化测试"""

    def test_initializes_with_default_evaluators(self):
        """测试使用默认评估器初始化"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        assert evaluator.intrinsic_evaluator is not None
        assert evaluator.extrinsic_evaluator is not None
        assert evaluator.goodhart_detector is not None

    def test_can_accept_custom_evaluators(self):
        """测试可接受自定义评估器"""
        from evolution.dual_evaluator import DualEvaluator
        from evolution.intrinsic_evaluator import IntrinsicEvaluator
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator
        from evolution.goodhart_detector import GoodhartDetector

        custom_intrinsic = IntrinsicEvaluator()
        custom_extrinsic = ExtrinsicEvaluator()
        custom_goodhart = GoodhartDetector()

        evaluator = DualEvaluator(
            intrinsic_evaluator=custom_intrinsic,
            extrinsic_evaluator=custom_extrinsic,
            goodhart_detector=custom_goodhart,
        )

        assert evaluator.intrinsic_evaluator is custom_intrinsic
        assert evaluator.extrinsic_evaluator is custom_extrinsic
        assert evaluator.goodhart_detector is custom_goodhart


# =============================================================================
# Test DualEvaluator - Full Evaluation Integration
# =============================================================================


class TestDualEvaluatorFullEvaluation:
    """完整评估集成测试（P0优先级）"""

    def test_evaluate_returns_complete_report(self):
        """测试评估返回完整报告"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        code = """
def add(a: int, b: int) -> int:
    \"\"\"Add two integers.\"\"\"
    return a + b
"""
        report = evaluator.evaluate(
            code=code,
            function_signature="add(a: int, b: int) -> int",
            requirements=["Returns sum of two integers"],
        )

        assert isinstance(report, dict)
        assert "intrinsic_score" in report
        assert "extrinsic_score" in report
        assert "goodhart_detected" in report
        assert "final_score" in report

    def test_evaluate_good_code_gets_high_scores(self):
        """测试评估好代码获得高分"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        code = """
def calculate(x: int, y: int) -> int:
    \"\"\"Calculate something.\"\"\"
    try:
        return x + y
    except Exception:
        return 0
"""
        report = evaluator.evaluate(
            code=code,
            function_signature="calculate(x: int, y: int) -> int",
            requirements=["Returns sum of x and y"],
        )

        # 好代码应该在各方面都得分较高
        assert report["intrinsic_score"] > 0.6
        assert report["extrinsic_score"] > 0.6
        assert report["final_score"] > 0.6

    def test_evaluate_bad_code_gets_low_scores(self):
        """测试评估差代码获得低分"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        code = """
def bad_func(x, y):
    return x - y  # Wrong operation
"""
        report = evaluator.evaluate(
            code=code,
            function_signature="add(x, y)",
            requirements=["Should return x + y"],
        )

        # 差代码应该得分较低
        assert report["final_score"] < 0.8

    def test_detects_goodhart_in_evaluation(self):
        """测试在评估中检测Goodhart现象"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        # 高静态质量（类型注解+文档）但错误行为
        code = '''
"""Calculator module.\"\"\"


def calculate(a: int, b: int) -> int:
    \"\"\"Calculate sum of two integers.\"\"\"
    # Cheating: always returns 10
    return 10
'''
        report = evaluator.evaluate(
            code=code,
            function_signature="calculate(a: int, b: int) -> int",
            requirements=["Returns a + b"],
        )

        # 应该检测到Goodhart现象（高静态分+低一致性）
        assert report["goodhart_detected"] is True


# =============================================================================
# Test DualEvaluator - Score Calculation
# =============================================================================


class TestDualEvaluatorScoreCalculation:
    """得分计算测试（P0优先级）"""

    def test_final_score_is_weighted_average(self):
        """测试最终得分是加权平均"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        code = """
def func(x):
    return x
"""
        report = evaluator.evaluate(
            code=code,
            function_signature="func(x: int) -> int",
            requirements=["Returns input"],
        )

        intrinsic = report["intrinsic_score"]
        extrinsic = report["extrinsic_score"]
        final = report["final_score"]

        # 最终得分应该在两者之间（即使考虑Goodhart惩罚）
        assert min(intrinsic, extrinsic) <= final <= max(intrinsic, extrinsic)

    def test_goodhart_penalty_reduces_final_score(self):
        """测试Goodhart惩罚降低最终得分"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        # 硬编码答案代码
        code = """
def add(a, b):
    if a == 1 and b == 2:
        return 3  # Hardcoded for test case
    return 0
"""
        report = evaluator.evaluate(
            code=code,
            function_signature="add(a, b)",
            requirements=["Returns a + b for any inputs"],
        )

        # 如果检测到Goodhart，最终得分应该被惩罚
        if report["goodhart_detected"]:
            assert report["final_score"] < report["intrinsic_score"]

    def test_no_goodhart_no_extra_penalty(self):
        """测试无Goodhart无额外惩罚"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        # 正确的代码
        code = """
def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b
"""
        report = evaluator.evaluate(
            code=code,
            function_signature="add(a: int, b: int) -> int",
            requirements=["Returns sum of a and b"],
        )

        if not report["goodhart_detected"]:
            # 无Goodhart时，最终得分应该是正常加权
            assert report["final_score"] > 0.5

    def test_extreme_goodhart_gets_minimum_score(self):
        """测试极端Goodhart获得最低分"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        # 完美的静态代码但完全错误的行为
        code = """
\"\"\"Perfectly documented module.\"\"\"

def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\":return: a + b\"\"\"
    # Always returns 0 - completely wrong
    return 0
"""
        report = evaluator.evaluate(
            code=code,
            function_signature="add(a: int, b: int) -> int",
            requirements=["Returns a + b"],
        )

        if report["goodhart_detected"]:
            assert report["final_score"] < 0.5


# =============================================================================
# Test DualEvaluator - Report Details
# =============================================================================


class TestDualEvaluatorReportDetails:
    """报告详情测试（P1优先级）"""

    def test_report_includes_intrinsic_details(self):
        """测试报告包含内生评估详情"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        code = "def func(): pass"
        report = evaluator.evaluate(
            code=code,
            function_signature="func()",
            requirements=[],
        )

        assert "intrinsic_details" in report
        assert isinstance(report["intrinsic_details"], dict)

    def test_report_includes_extrinsic_details(self):
        """测试报告包含外生评估详情"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        code = "def func(): pass"
        report = evaluator.evaluate(
            code=code,
            function_signature="func()",
            requirements=[],
        )

        assert "extrinsic_details" in report
        assert isinstance(report["extrinsic_details"], dict)

    def test_report_includes_goodhart_details_when_detected(self):
        """测试报告在检测到Goodhart时包含详情"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        code = """
def func():
    return 42  # Hardcoded
"""
        report = evaluator.evaluate(
            code=code,
            function_signature="func() -> int",
            requirements=["Returns dynamic value"],
        )

        if report["goodhart_detected"]:
            assert "goodhart_details" in report
            assert "confidence" in report["goodhart_details"]
            assert "reason" in report["goodhart_details"]

    def test_all_scores_bounded_between_0_and_1(self):
        """测试所有得分都在0-1之间"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()

        test_codes = [
            ("def f(): pass", "f()", []),
            ("def g(x): return x", "g(x)", ["identity"]),
            ("", "empty()", []),  # Empty code
        ]

        for code, sig, reqs in test_codes:
            report = evaluator.evaluate(
                code=code, function_signature=sig, requirements=reqs
            )
            assert 0.0 <= report["intrinsic_score"] <= 1.0
            assert 0.0 <= report["extrinsic_score"] <= 1.0
            assert 0.0 <= report["final_score"] <= 1.0


# =============================================================================
# Test DualEvaluator - Edge Cases
# =============================================================================


class TestDualEvaluatorEdgeCases:
    """边界情况测试"""

    def test_handles_empty_code(self):
        """测试处理空代码"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        report = evaluator.evaluate(
            code="",
            function_signature="func()",
            requirements=[],
        )

        assert report["final_score"] == 0.0

    def test_handles_syntax_error_code(self):
        """测试处理语法错误代码"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        report = evaluator.evaluate(
            code="def broken(",
            function_signature="broken()",
            requirements=[],
        )

        assert report["intrinsic_score"] == 0.0
        assert report["final_score"] == 0.0

    def test_handles_eval_in_code_safely(self):
        """测试安全处理代码中的eval"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        code = "result = eval('1 + 1')"
        report = evaluator.evaluate(
            code=code,
            function_signature="run()",
            requirements=[],
        )

        # 应该检测危险模式
        assert report["extrinsic_score"] < 1.0

    def test_handles_complex_evaluation_scenario(self):
        """测试处理复杂评估场景"""
        from evolution.dual_evaluator import DualEvaluator

        evaluator = DualEvaluator()
        code = """
\"\"\"Complex calculator module.\"\"\"

from typing import Union


def calculate(
    a: Union[int, float], b: Union[int, float], op: str
) -> Union[int, float]:
    \"\"\"Perform calculation.\":param op: Operation (+, -, *, /)\":return: Result\"\"\"
    if op == "+":
        return a + b
    elif op == "-":
        return a - b
    elif op == "*":
        return a * b
    elif op == "/":
        try:
            return a / b
        except ZeroDivisionError:
            raise ValueError("Cannot divide by zero")
    else:
        raise ValueError(f"Unknown operation: {op}")
"""
        report = evaluator.evaluate(
            code=code,
            function_signature="calculate(a, b, op)",
            requirements=["Performs arithmetic operations", "Handles division by zero"],
        )

        # 复杂但正确的代码应该得分较高
        assert report["intrinsic_score"] > 0.7
        assert isinstance(report["goodhart_detected"], bool)
