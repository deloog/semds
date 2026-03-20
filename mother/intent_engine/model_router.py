"""
Model Router - 模型路由器
根据意图和上下文，智能路由到合适的模型
"""

from enum import Enum
from typing import Dict, Optional

from mother.intent_engine.intent_classifier import (
    ComplexityLevel,
    IntentType,
    UserIntent,
)


class ModelType(Enum):
    """模型类型"""

    LOCAL = "local"  # 本地 Qwen 3.5 4B
    TEMPLATE = "template"  # 模板填充（无模型）
    HYBRID = "hybrid"  # 本地 + DeepSeek
    DEEPSEEK = "deepseek"  # DeepSeek API
    OLLAMA = "ollama"  # Ollama 本地模型


class ModelRouter:
    """
    模型路由器

    核心逻辑：
    1. 根据意图选择模型类型
    2. 根据上下文调整（如用户明确要求用某个模型）
    3. 平衡成本和质量

    路由策略：
    - 简单任务 → 本地模型（免费、快速）
    - 模板任务 → 模板填充（确定性好）
    - 中等任务 → Hybrid（本地预处理 + DeepSeek 生成）
    - 复杂任务 → DeepSeek（高质量）
    """

    def __init__(self):
        self.cost_tracker = {
            "local_calls": 0,
            "deepseek_calls": 0,
            "deepseek_cost": 0.0,
        }

    def route(
        self, intent: UserIntent, user_preference: Optional[str] = None
    ) -> ModelType:
        """
        决定使用哪个模型

        Args:
            intent: 用户意图
            user_preference: 用户明确要求（如 "use deepseek"）

        Returns:
            模型类型
        """
        # 1. 尊重用户偏好
        if user_preference:
            preference = user_preference.lower()
            if "deepseek" in preference or "strong" in preference:
                return ModelType.DEEPSEEK
            if "local" in preference or "fast" in preference:
                return ModelType.LOCAL

        # 2. 根据意图路由
        route_map = {
            # (intent, complexity) -> model
            (IntentType.SIMPLE_CHAT, ComplexityLevel.SIMPLE): ModelType.LOCAL,
            (IntentType.SIMPLE_CHAT, ComplexityLevel.MEDIUM): ModelType.LOCAL,
            (IntentType.EXPLANATION, ComplexityLevel.SIMPLE): ModelType.LOCAL,
            (IntentType.EXPLANATION, ComplexityLevel.MEDIUM): ModelType.HYBRID,
            (IntentType.EXPLANATION, ComplexityLevel.COMPLEX): ModelType.DEEPSEEK,
            (IntentType.CODE_GENERATION, ComplexityLevel.SIMPLE): ModelType.TEMPLATE,
            (IntentType.CODE_GENERATION, ComplexityLevel.MEDIUM): ModelType.HYBRID,
            (IntentType.CODE_GENERATION, ComplexityLevel.COMPLEX): ModelType.DEEPSEEK,
            (IntentType.CODE_REVIEW, ComplexityLevel.SIMPLE): ModelType.LOCAL,
            (IntentType.CODE_REVIEW, ComplexityLevel.MEDIUM): ModelType.HYBRID,
            (IntentType.CODE_REVIEW, ComplexityLevel.COMPLEX): ModelType.DEEPSEEK,
            (IntentType.DEBUG_HELP, ComplexityLevel.SIMPLE): ModelType.HYBRID,
            (IntentType.DEBUG_HELP, ComplexityLevel.MEDIUM): ModelType.HYBRID,
            (IntentType.DEBUG_HELP, ComplexityLevel.COMPLEX): ModelType.DEEPSEEK,
            (IntentType.WEB_SEARCH, ComplexityLevel.SIMPLE): ModelType.LOCAL,
            (IntentType.WEB_SEARCH, ComplexityLevel.MEDIUM): ModelType.HYBRID,
            (IntentType.TASK_ORCHESTRATION, ComplexityLevel.SIMPLE): ModelType.HYBRID,
            (
                IntentType.TASK_ORCHESTRATION,
                ComplexityLevel.COMPLEX,
            ): ModelType.DEEPSEEK,
            (IntentType.UNKNOWN, ComplexityLevel.SIMPLE): ModelType.LOCAL,
            (IntentType.UNKNOWN, ComplexityLevel.COMPLEX): ModelType.DEEPSEEK,
        }

        model = route_map.get(
            (intent.intent_type, intent.complexity), ModelType.HYBRID  # 默认
        )

        # 3. 根据置信度调整
        if intent.confidence < 0.5 and model == ModelType.LOCAL:
            # 意图不确定，用更强的模型
            model = ModelType.HYBRID

        return model

    def execute_with_model(
        self, model_type: ModelType, intent: UserIntent, context: str = ""
    ) -> Dict:
        """
        使用指定的模型执行

        Returns:
            {'success': bool, 'content': str, 'model_used': str, 'cost': float}
        """
        if model_type == ModelType.LOCAL:
            return self._execute_local(intent, context)

        elif model_type == ModelType.TEMPLATE:
            return self._execute_template(intent, context)

        elif model_type == ModelType.HYBRID:
            return self._execute_hybrid(intent, context)

        elif model_type == ModelType.DEEPSEEK:
            return self._execute_deepseek(intent, context)

        else:
            return {
                "success": False,
                "content": "Unknown model type",
                "model_used": "none",
                "cost": 0,
            }

    def _execute_local(self, intent: UserIntent, context: str) -> Dict:
        """执行本地模型"""
        self.cost_tracker["local_calls"] += 1

        # TODO: 接入 Ollama
        # 本地模型处理简单响应

        return {
            "success": True,
            "content": f"[Local model response for {intent.intent_type.value}]",
            "model_used": "local",
            "cost": 0,
        }

    def _execute_template(self, intent: UserIntent, context: str) -> Dict:
        """执行模板填充"""
        from mother.llm_tutor.template_router import quick_generate

        try:
            code = quick_generate(intent.raw_input)
            return {
                "success": True,
                "content": code,
                "model_used": "template",
                "cost": 0,
            }
        except Exception as e:
            return {
                "success": False,
                "content": f"Template error: {e}",
                "model_used": "template",
                "cost": 0,
            }

    def _execute_hybrid(self, intent: UserIntent, context: str) -> Dict:
        """执行混合模式（本地预处理 + DeepSeek 生成）"""
        # 1. 本地模型做预处理
        preprocessed = self._local_preprocess(intent, context)

        # 2. DeepSeek 生成
        result = self._execute_deepseek(
            intent,
            context=preprocessed.get("enhanced_context", context),
            task_hint=preprocessed.get("task_hint", ""),
        )

        result["model_used"] = "hybrid"
        return result

    def _local_preprocess(self, intent: UserIntent, context: str) -> Dict:
        """本地模型预处理"""
        # 本地模型可以：
        # - 提取关键信息
        # - 格式化请求
        # - 生成提示模板

        return {
            "enhanced_context": context,
            "task_hint": f"Task type: {intent.intent_type.value}",
        }

    def _execute_deepseek(
        self, intent: UserIntent, context: str = "", task_hint: str = ""
    ) -> Dict:
        """执行 DeepSeek"""
        from evolution.code_generator import CodeGenerator

        try:
            generator = CodeGenerator(backend="deepseek")

            # 构建提示
            full_prompt = intent.raw_input
            if context:
                full_prompt = f"Context:\n{context}\n\nTask:\n{full_prompt}"
            if task_hint:
                full_prompt = f"{task_hint}\n\n{full_prompt}"

            task_spec = {
                "description": full_prompt,
                "requirements": ["Write clean, well-documented code"],
            }

            result = generator.generate(task_spec)

            if result["success"]:
                self.cost_tracker["deepseek_calls"] += 1
                # 估算成本（假设 0.001$/1K tokens）
                estimated_cost = 0.002
                self.cost_tracker["deepseek_cost"] += estimated_cost

                return {
                    "success": True,
                    "content": result["code"],
                    "model_used": "deepseek",
                    "cost": estimated_cost,
                }
            else:
                return {
                    "success": False,
                    "content": result.get("error", "Generation failed"),
                    "model_used": "deepseek",
                    "cost": 0,
                }

        except Exception as e:
            return {
                "success": False,
                "content": f"DeepSeek error: {e}",
                "model_used": "deepseek",
                "cost": 0,
            }

    def get_cost_report(self) -> Dict:
        """获取成本报告"""
        return {
            "local_calls": self.cost_tracker["local_calls"],
            "deepseek_calls": self.cost_tracker["deepseek_calls"],
            "total_cost_usd": self.cost_tracker["deepseek_cost"],
            "cost_per_call": (
                self.cost_tracker["deepseek_cost"]
                / max(self.cost_tracker["deepseek_calls"], 1)
            ),
        }


# 便捷函数
_router = None


def get_router() -> ModelRouter:
    """获取全局路由器"""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router


def process_user_input(
    text: str, session_id: str = "default", user_preference: Optional[str] = None
) -> Dict:
    """
    处理用户输入的完整流程

    Args:
        text: 用户输入
        session_id: 会话ID
        user_preference: 用户偏好

    Returns:
        处理结果
    """
    from mother.intent_engine.context_manager import get_context_manager
    from mother.intent_engine.intent_classifier import classify_intent

    # 1. 识别意图（本地模型/规则）
    intent = classify_intent(text)

    # 2. 获取上下文
    cm = get_context_manager()

    # 指代消解
    resolved_text = cm.resolve_references(session_id, text)
    intent.raw_input = resolved_text

    # 获取上下文摘要
    context = cm.summarize_for_external_model(session_id, resolved_text)

    # 3. 路由到模型
    router = get_router()
    model_type = router.route(intent, user_preference)

    # 4. 执行
    result = router.execute_with_model(model_type, intent, context)

    # 5. 记录到上下文
    cm.add_message(session_id, "user", text)
    cm.add_message(session_id, "assistant", result["content"], result["model_used"])

    # 6. 提取知识
    cm.extract_knowledge(session_id, text)

    return {
        "intent": intent.intent_type.value,
        "complexity": intent.complexity.value,
        "model_used": result["model_used"],
        "content": result["content"],
        "cost": result["cost"],
        "context_used": bool(context),
    }


if __name__ == "__main__":
    # 测试完整流程
    print("=" * 70)
    print("Model Router Test")
    print("=" * 70)

    test_inputs = [
        "Write a function to fetch data",
        "Review this code",
        "What is Python asyncio?",
        "Fix this bug: KeyError 'name'",
    ]

    for text in test_inputs:
        print(f"\nInput: {text}")
        result = process_user_input(text, session_id="test")
        print(f"  Intent: {result['intent']}")
        print(f"  Complexity: {result['complexity']}")
        print(f"  Model: {result['model_used']}")
        print(f"  Cost: ${result['cost']:.4f}")
        print(f"  Context: {'Yes' if result['context_used'] else 'No'}")

    # 成本报告
    router = get_router()
    report = router.get_cost_report()
    print(f"\n{'='*70}")
    print("Cost Report:")
    print(f"  Local calls: {report['local_calls']}")
    print(f"  DeepSeek calls: {report['deepseek_calls']}")
    print(f"  Total cost: ${report['total_cost_usd']:.4f}")
