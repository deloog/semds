"""
Extrinsic Evaluator 模块 - 外生评估（行为一致性验证）

通过生成边界用例并执行来验证代码行为一致性。

评估维度（整合版）：
- 静态代码分析（危险模式检测）
- 边界用例生成与执行
- 行为一致性评分
- 运行时性能评估
- 鲁棒性测试（基于测试代码）

版本说明：
此文件已整合原 extrinsic_evaluator_enhanced.py 的功能。
禁止创建 V2/增强版/加强版 等分离文件，所有改进必须在此文件完成。
"""

import ast
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, cast


@dataclass
class EdgeCaseResult:
    """边界用例执行结果"""

    inputs: Dict[str, Any]
    expected: Any
    actual: Any
    passed: bool
    description: str = ""


@dataclass
class EvaluationResult:
    """外生评估结果"""

    score: float
    consistency_score: float
    static_analysis_score: float
    edge_case_results: List[EdgeCaseResult] = field(default_factory=list)


class ExtrinsicEvaluator:
    """外生评估器 - 行为一致性验证（整合增强版）

    通过以下方式评估代码：
    1. 静态分析检测危险模式
    2. 生成边界用例
    3. 执行用例验证行为一致性
    4. 运行时性能评估
    5. 鲁棒性测试（可选，需 test_code）

    Example:
        >>> evaluator = ExtrinsicEvaluator()
        >>> result = evaluator.evaluate(
        ...     code="def add(a, b): return a + b",
        ...     function_signature="add(a, b)",
        ...     requirements=["Returns sum"]
        ... )
        >>> print(f"Score: {result['score']:.2f}")

        >>> # 启用增强评估
        >>> result = evaluator.evaluate(
        ...     code=code,
        ...     function_signature=sig,
        ...     requirements=reqs,
        ...     test_code=test_code  # 传入测试代码以评估鲁棒性
        ... )
    """

    # 权重配置（可自定义）
    WEIGHT_STATIC = 0.4
    WEIGHT_CONSISTENCY = 0.6

    # 增强模式权重（当传入 test_code 时使用）
    WEIGHT_ENHANCED_BASE = 0.3
    WEIGHT_ENHANCED_PERF = 0.4
    WEIGHT_ENHANCED_ROBUST = 0.3

    # 危险模式
    DANGEROUS_PATTERNS = [
        (r"eval\s*\(", "Use of eval()"),
        (r"exec\s*\(", "Use of exec()"),
        (r'compile\s*\([^)]*,\s*[\'"]exec[\'"]', "Use of compile() with exec mode"),
        (r"os\.system\s*\(", "Use of os.system()"),
        (r"subprocess\.\w+.*shell\s*=\s*True", "Use of subprocess with shell=True"),
        (
            r"subprocess\.call.*shell\s*=\s*True",
            "Use of subprocess.call with shell=True",
        ),
        (r"__import__\s*\(", "Use of __import__()"),
        (r'\bopen\s*\([^)]*[\'"]w[\'"][^)]*\)', "File write operation"),
        (r"input\s*\(", "Use of input()"),
    ]

    # 密钥/令牌模式
    SECRET_PATTERNS = [
        (r"sk-[a-zA-Z0-9]{10,}", "Hardcoded API key (OpenAI format)"),
        (r"AKIA[0-9A-Z]{16}", "Hardcoded AWS access key"),
        (r'password\s*=\s*[\'"][^\'"]{3,}[\'"]', "Hardcoded password"),
        (r'secret\s*=\s*[\'"][^\'"]{3,}[\'"]', "Hardcoded secret"),
        (r'token\s*=\s*[\'"][^\'"]{3,}[\'"]', "Hardcoded token"),
    ]

    def __init__(self, timeout_seconds: float = 2.0) -> None:
        """
        初始化评估器。

        Args:
            timeout_seconds: 性能测试超时时间（秒）
        """
        self.timeout_seconds = timeout_seconds

    def evaluate(
        self,
        code: str,
        function_signature: str,
        requirements: List[str],
        test_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        执行完整外生评估（整合增强版）。

        Args:
            code: 要评估的代码字符串
            function_signature: 函数签名（如 "add(a: int, b: int) -> int"）
            requirements: 功能需求描述列表
            test_code: 可选的测试代码，用于鲁棒性评估

        Returns:
            包含以下字段的字典：
            - score: 总得分 (0-1)
            - consistency_score: 行为一致性得分
            - static_analysis_score: 静态分析得分
            - edge_case_results: 边界用例执行结果列表
            - performance_score: 性能得分（新增）
            - robustness_score: 鲁棒性得分（新增，需 test_code）
            - details: 详细得分构成
        """
        # 空代码或语法错误处理
        if not code or not code.strip():
            return self._create_empty_result()

        try:
            ast.parse(code)
        except SyntaxError:
            return self._create_empty_result()

        # 1. 基础评估（静态分析 + 边界用例）
        static_score = self._static_analysis(code)
        edge_cases = self._generate_edge_cases(function_signature)
        edge_results, consistency_score = self._execute_edge_cases(
            code, function_signature, edge_cases
        )

        # 基础模式：仅使用静态和一致性得分
        if test_code is None:
            total_score = (
                self.WEIGHT_STATIC * static_score
                + self.WEIGHT_CONSISTENCY * consistency_score
            )

            return {
                "score": round(total_score, 2),
                "consistency_score": round(consistency_score, 2),
                "static_analysis_score": round(static_score, 2),
                "edge_case_results": [
                    {
                        "inputs": r.inputs,
                        "expected": r.expected,
                        "actual": r.actual,
                        "passed": r.passed,
                        "description": r.description,
                    }
                    for r in edge_results
                ],
            }

        # 增强模式：添加性能和鲁棒性评估
        # 2. 性能评估
        perf_score = self._evaluate_performance(code, function_signature)

        # 3. 鲁棒性评估
        robust_score = self._evaluate_robustness(code, test_code)

        # 4. 综合得分（增强权重）
        # 基础质量 30% + 性能 40% + 鲁棒性 30%
        base_quality = (static_score + consistency_score) / 2
        total_score = (
            self.WEIGHT_ENHANCED_BASE * base_quality
            + self.WEIGHT_ENHANCED_PERF * perf_score
            + self.WEIGHT_ENHANCED_ROBUST * robust_score
        )

        return {
            "score": round(total_score, 2),
            "consistency_score": round(consistency_score, 2),
            "static_analysis_score": round(static_score, 2),
            "performance_score": round(perf_score, 2),
            "robustness_score": round(robust_score, 2),
            "edge_case_results": [
                {
                    "inputs": r.inputs,
                    "expected": r.expected,
                    "actual": r.actual,
                    "passed": r.passed,
                    "description": r.description,
                }
                for r in edge_results
            ],
            "details": {
                "base_quality": round(base_quality, 2),
                "performance": round(perf_score, 2),
                "robustness": round(robust_score, 2),
            },
        }

    def _create_empty_result(self) -> Dict[str, Any]:
        """创建空代码/语法错误的结果"""
        return {
            "score": 0.0,
            "consistency_score": 0.0,
            "static_analysis_score": 0.0,
            "edge_case_results": [],
        }

    def _evaluate_performance(self, code: str, function_signature: str) -> float:
        """
        评估代码执行性能（整合自原 enhanced 版本）。

        通过执行代码并测量运行时间来判断性能。

        Args:
            code: 代码字符串
            function_signature: 函数签名

        Returns:
            性能得分 (0-1)
        """
        try:
            namespace: Dict[str, Any] = {}
            exec(code, namespace)  # nosec B102

            func_name = function_signature.split("(")[0].strip()
            if func_name not in namespace:
                return 0.5

            func = namespace[func_name]
            test_inputs = self._generate_perf_test_inputs(function_signature)

            total_time = 0.0
            for test_input in test_inputs:
                start = time.perf_counter()
                try:
                    if isinstance(test_input, tuple):
                        func(*test_input)
                    else:
                        func(test_input)
                except:
                    pass
                elapsed = time.perf_counter() - start
                total_time += elapsed

            avg_time = total_time / len(test_inputs) if test_inputs else 0

            # 评分：越快越高分
            if avg_time < 0.001:  # 1ms
                return 1.0
            elif avg_time < 0.01:  # 10ms
                return 0.9
            elif avg_time < 0.1:  # 100ms
                return 0.8
            elif avg_time < self.timeout_seconds:
                return 0.6
            else:
                return 0.3

        except Exception:
            return 0.5

    def _generate_perf_test_inputs(self, function_signature: str) -> List[Any]:
        """
        生成性能测试输入（整合自原 enhanced 版本）。

        Args:
            function_signature: 函数签名

        Returns:
            测试输入列表
        """
        sig = function_signature.lower()

        if "sort" in sig or "list" in sig:
            return [
                list(range(10)),
                list(range(100)),
                list(range(500)),
            ]
        elif "fibonacci" in sig or "fib" in sig:
            return [5, 10, 20]
        elif "string" in sig or "str" in sig:
            return [
                "a" * 10,
                "a" * 100,
                "a" * 1000,
            ]
        else:
            return [1, 10, 100]

    def _evaluate_robustness(self, code: str, test_code: str) -> float:
        """
        评估代码鲁棒性（基于测试通过率）。

        直接运行测试代码，计算通过率。

        Args:
            code: 被测代码
            test_code: 测试代码

        Returns:
            鲁棒性得分 (0-1)
        """
        from evolution.test_runner import TestRunner

        try:
            result = TestRunner().run_tests_with_code(code, test_code)
            return float(result.get("pass_rate", 0.0))
        except:
            return 0.0

    def _static_analysis(self, code: str) -> float:
        """静态代码分析

        检查危险模式和奖励良好实践。

        Args:
            code: 代码字符串

        Returns:
            0-1之间的得分
        """
        score = 1.0

        # 检测危险模式
        has_dangerous = False
        for pattern, description in self.DANGEROUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                score -= 0.6  # 严重扣分
                has_dangerous = True

        # 检测硬编码密钥
        for pattern, description in self.SECRET_PATTERNS:
            if re.search(pattern, code):
                score -= 0.5
                has_dangerous = True

        # 如果有危险模式，限制最大得分
        if has_dangerous:
            # 检查是否包含特别危险的操作（os.system）
            if re.search(r"os\.system\s*\(", code, re.IGNORECASE):
                score = min(score, 0.2)  # 极其危险
            else:
                score = min(score, 0.4)

        # 检查良好实践
        try:
            tree = ast.parse(code)

            # 检查类型注解
            has_type_annotations = False
            has_error_handling = False
            has_docstrings = False

            for node in ast.walk(tree):
                # 检查函数定义
                if isinstance(node, ast.FunctionDef):
                    # 检查参数类型注解
                    if node.args.args:
                        for arg in node.args.args:
                            if arg.annotation:
                                has_type_annotations = True
                    # 检查返回类型注解
                    if node.returns:
                        has_type_annotations = True

                    # 检查文档字符串
                    if (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    ):
                        has_docstrings = True

                # 检查错误处理
                if isinstance(node, ast.Try):
                    has_error_handling = True

            # 奖励良好实践
            if has_type_annotations:
                score += 0.1
            if has_error_handling:
                score += 0.1
            if has_docstrings:
                score += 0.1

        except SyntaxError:
            return 0.0

        return max(0.0, min(1.0, score))

    def _generate_edge_cases(self, function_signature: str) -> List[Dict[str, Any]]:
        """生成边界用例

        基于函数签名生成边界测试用例。

        Args:
            function_signature: 函数签名字符串

        Returns:
            边界用例列表，每个用例包含inputs和description
        """
        # 解析参数类型
        param_types = self._parse_signature(function_signature)

        if not param_types:
            return []

        # 为每个参数生成边界值列表
        param_values: Dict[str, List[Any]] = {}
        for param_name, param_type in param_types.items():
            if "int" in param_type.lower():
                param_values[param_name] = [0, 1, -1, 10000, -10000]
            elif "float" in param_type.lower():
                param_values[param_name] = [0.0, 0.5, -0.5, 1e10]
            elif "str" in param_type.lower():
                param_values[param_name] = ["", "test", "a" * 1000]
            else:
                param_values[param_name] = [None, 0, 1]

        # 生成参数组合（笛卡尔积的子集）
        edge_cases: List[Dict[str, Any]] = []
        param_names = list(param_types.keys())

        # 策略：生成一些代表性的组合
        # 1. 所有参数为0/默认值
        case = {name: param_values[name][0] for name in param_names}
        case["description"] = "All params at boundary (0/None)"
        edge_cases.append(case)

        # 2. 所有参数为1
        case = {
            name: (
                param_values[name][1]
                if len(param_values[name]) > 1
                else param_values[name][0]
            )
            for name in param_names
        }
        case["description"] = "All params at normal value (1)"
        edge_cases.append(case)

        # 3. 混合：第一个参数为-1，其他为1
        if len(param_names) >= 2:
            case = {name: 1 for name in param_names}
            case[param_names[0]] = -1
            case["description"] = f"{param_names[0]}=-1, others=1"
            edge_cases.append(case)

        # 4. 大数值测试
        case = {
            name: 10000 if "int" in param_types[name].lower() else param_values[name][0]
            for name in param_names
        }
        case["description"] = "Large values"
        edge_cases.append(case)

        # 5. 更多边界组合
        for i, name in enumerate(param_names[:3]):  # 限制参数数量
            for j, val in enumerate(param_values[name][:3]):  # 限制值数量
                case = {n: param_values[n][0] for n in param_names}
                case[name] = val
                case["description"] = f"{name}={val}"
                edge_cases.append(case)

        return edge_cases[:15]  # 限制总数

    def _parse_signature(self, signature: str) -> Dict[str, str]:
        """解析函数签名提取参数

        Args:
            signature: 函数签名字符串

        Returns:
            参数字典 {name: type}
        """
        params: Dict[str, str] = {}

        # 提取括号内的参数部分
        match = re.search(r"\(([^)]*)\)", signature)
        if not match:
            return params

        params_str = match.group(1)
        if not params_str.strip():
            return params

        # 分割参数
        for param in params_str.split(","):
            param = param.strip()
            if not param:
                continue

            # 解析参数名和类型
            if ":" in param:
                name, type_hint = param.split(":", 1)
                name = name.strip()
                type_hint = type_hint.split("=")[0].strip()  # 移除默认值
                # 移除类型提示中的默认值部分
                if " " in type_hint:
                    type_hint = type_hint.split()[0]
                params[name] = type_hint
            else:
                # 无类型注解
                name = param.split("=")[0].strip()
                params[name] = "Any"

        return params

    def _execute_edge_cases(
        self, code: str, function_signature: str, edge_cases: List[Dict[str, Any]]
    ) -> Tuple[List[EdgeCaseResult], float]:
        """执行边界用例

        Args:
            code: 代码字符串
            function_signature: 函数签名
            edge_cases: 边界用例列表

        Returns:
            (结果列表, 通过率)
        """
        results = []
        passed_count = 0

        # 提取函数名
        func_name = function_signature.split("(")[0].strip()
        if "." in func_name:
            func_name = func_name.split(".")[-1]

        # 创建安全的执行环境
        safe_globals = {
            "__builtins__": {
                "abs": abs,
                "all": all,
                "any": any,
                "bool": bool,
                "dict": dict,
                "float": float,
                "int": int,
                "len": len,
                "list": list,
                "max": max,
                "min": min,
                "pow": pow,
                "range": range,
                "round": round,
                "str": str,
                "sum": sum,
                "tuple": tuple,
                "type": type,
                "zip": zip,
                "True": True,
                "False": False,
                "None": None,
            }
        }

        try:
            # 执行代码定义函数
            exec(code, safe_globals)  # nosec B102

            # 获取函数
            if func_name not in safe_globals:
                # 函数未定义
                for case in edge_cases:
                    results.append(
                        EdgeCaseResult(
                            inputs={
                                k: v for k, v in case.items() if k != "description"
                            },
                            expected="N/A",
                            actual="Function not found",
                            passed=False,
                            description=case.get("description", ""),
                        )
                    )
                return results, 0.0

            func = cast(Callable[..., Any], safe_globals[func_name])

            # 执行每个边界用例
            for case in edge_cases:
                description = case.get("description", "")
                inputs = {k: v for k, v in case.items() if k != "description"}

                try:
                    # 执行函数
                    actual = func(**inputs)

                    # 简单的预期值推断（实际应该基于需求）
                    expected = self._infer_expected(inputs, func_name)

                    # 检查结果
                    passed = self._compare_results(actual, expected)
                    if passed:
                        passed_count += 1

                    results.append(
                        EdgeCaseResult(
                            inputs=inputs,
                            expected=expected,
                            actual=actual,
                            passed=passed,
                            description=description,
                        )
                    )

                except Exception as e:
                    results.append(
                        EdgeCaseResult(
                            inputs=inputs,
                            expected="N/A",
                            actual=str(e),
                            passed=False,
                            description=description,
                        )
                    )

        except Exception as e:
            # 代码执行失败
            for case in edge_cases:
                inputs = {k: v for k, v in case.items() if k != "description"}
                results.append(
                    EdgeCaseResult(
                        inputs=inputs,
                        expected="N/A",
                        actual=str(e),
                        passed=False,
                        description=case.get("description", ""),
                    )
                )

        # 计算一致性得分
        if len(results) > 0:
            consistency_score = passed_count / len(results)
        else:
            consistency_score = 0.0

        return results, consistency_score

    def _infer_expected(self, inputs: Dict[str, Any], func_name: str) -> Any:
        """推断预期结果

        基于函数名和输入推断预期输出。
        这是一个启发式方法，实际应该基于需求。

        Args:
            inputs: 输入参数字典
            func_name: 函数名

        Returns:
            预期的输出值
        """
        func_name_lower = func_name.lower()

        # 基于函数名的启发式推断
        if "add" in func_name_lower or "sum" in func_name_lower:
            return sum(inputs.values())
        elif "multiply" in func_name_lower or "product" in func_name_lower:
            result = 1
            for v in inputs.values():
                result *= v if v is not None else 1
            return result
        elif "subtract" in func_name_lower or "minus" in func_name_lower:
            values = list(inputs.values())
            if len(values) >= 2:
                return values[0] - values[1]
            return values[0] if values else 0
        elif "divide" in func_name_lower:
            values = list(inputs.values())
            if len(values) >= 2 and values[1] != 0:
                return values[0] / values[1]
            return 0
        elif "double" in func_name_lower:
            for v in inputs.values():
                if isinstance(v, (int, float)):
                    return v * 2
            return 0
        elif "identity" in func_name_lower:
            for v in inputs.values():
                return v
            return None
        else:
            # 默认：返回第一个输入值
            for v in inputs.values():
                return v
            return None

    def _compare_results(self, actual: Any, expected: Any) -> bool:
        """比较实际结果和预期结果

        Args:
            actual: 实际结果
            expected: 预期结果

        Returns:
            是否匹配
        """
        if actual is None and expected is None:
            return True
        if actual is None or expected is None:
            return False

        # 数值比较（允许小误差）
        if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
            return abs(float(actual) - float(expected)) < 1e-9

        # 字符串比较
        if isinstance(actual, str) and isinstance(expected, str):
            return actual == expected

        # 默认相等比较
        try:
            return bool(actual == expected)
        except Exception:
            return False
