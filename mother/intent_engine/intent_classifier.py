"""
Intent Classifier - 意图识别器
本地模型负责理解用户意图，决定后续处理流程
"""
import os
import sys
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, 'D:\\semds')


class IntentType(Enum):
    """意图类型"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUG_HELP = "debug_help"
    EXPLANATION = "explanation"
    WEB_SEARCH = "web_search"
    SIMPLE_CHAT = "simple_chat"
    TASK_ORCHESTRATION = "task_orchestration"
    UNKNOWN = "unknown"


class ComplexityLevel(Enum):
    """复杂度级别"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


@dataclass
class UserIntent:
    """用户意图"""
    raw_input: str
    intent_type: IntentType
    complexity: ComplexityLevel
    entities: Dict[str, str]
    confidence: float
    suggested_model: str
    context_needed: bool


class IntentClassifier:
    """
    意图识别器
    
    使用本地模型（Qwen 3.5 4B）分析用户输入：
    1. 识别用户想做什么
    2. 评估任务复杂度
    3. 提取关键实体
    4. 决定使用哪个模型处理
    """
    
    def __init__(self, use_local_model: bool = False):
        self.use_local_model = use_local_model
        self.intent_patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict:
        """加载意图识别模式"""
        return {
            IntentType.CODE_GENERATION: {
                'keywords': ['write', 'create', 'generate', 'code', 'function',
                           'class', 'implement', 'build', 'script'],
                'patterns': [r'write\s+(?:a\s+)?function',
                           r'create\s+(?:a\s+)?class',
                           r'generate\s+code']
            },
            IntentType.CODE_REVIEW: {
                'keywords': ['review', 'check', 'improve', 'optimize', 'refactor'],
                'patterns': [r'review\s+(?:this\s+)?code',
                           r'improve\s+(?:this\s+)?']
            },
            IntentType.DEBUG_HELP: {
                'keywords': ['error', 'exception', 'bug', 'fail', 'debug', 'fix'],
                'patterns': [r'(?:getting|have)\s+(?:an?\s+)?error',
                           r'(?:code|it)\s+(?:is\s+)?not\s+working']
            },
            IntentType.EXPLANATION: {
                'keywords': ['explain', 'what is', 'how to', 'why'],
                'patterns': [r'what\s+is\s+\w+',
                           r'how\s+(?:does|do|to)\s+\w+']
            },
            IntentType.WEB_SEARCH: {
                'keywords': ['search', 'find', 'lookup', 'latest', 'current'],
                'patterns': [r'search\s+(?:for\s+)?',
                           r'find\s+(?:information\s+(?:about|on))?']
            },
            IntentType.TASK_ORCHESTRATION: {
                'keywords': ['and then', 'multiple', 'workflow', 'pipeline', 'steps'],
                'patterns': [r'(?:first|then|after|finally)',
                           r'(?:multiple|several)\s+steps']
            },
        }
    
    def classify(self, user_input: str) -> UserIntent:
        """分析用户输入，识别意图"""
        # 规则匹配
        intent, confidence = self._rule_based_classification(user_input)
        
        # 如果置信度低，用本地模型确认
        if confidence < 0.7 and self.use_local_model:
            intent, confidence = self._model_based_classification(user_input)
        
        # 评估复杂度和提取实体
        complexity = self._assess_complexity(user_input, intent)
        entities = self._extract_entities(user_input, intent)
        suggested_model = self._route_to_model(intent, complexity)
        context_needed = self._needs_context(user_input)
        
        return UserIntent(
            raw_input=user_input,
            intent_type=intent,
            complexity=complexity,
            entities=entities,
            confidence=confidence,
            suggested_model=suggested_model,
            context_needed=context_needed
        )
    
    def _rule_based_classification(self, text: str) -> Tuple[IntentType, float]:
        """基于规则的意图识别"""
        text_lower = text.lower()
        scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for kw in patterns['keywords']:
                if kw.lower() in text_lower:
                    score += 1
            for pattern in patterns['patterns']:
                if re.search(pattern, text_lower):
                    score += 2
            if score > 0:
                scores[intent] = score
        
        if scores:
            best_intent = max(scores, key=scores.get)
            confidence = min(0.5 + scores[best_intent] * 0.1, 0.9)
            return best_intent, confidence
        
        return IntentType.UNKNOWN, 0.3
    
    def _model_based_classification(self, text: str) -> Tuple[IntentType, float]:
        """使用本地模型进行意图识别"""
        # TODO: 接入 Ollama/Qwen
        return self._rule_based_classification(text)
    
    def _assess_complexity(self, text: str, intent: IntentType) -> ComplexityLevel:
        """评估任务复杂度"""
        if intent == IntentType.TASK_ORCHESTRATION:
            return ComplexityLevel.COMPLEX
        if intent == IntentType.SIMPLE_CHAT:
            return ComplexityLevel.SIMPLE
        
        score = 0
        if len(text) > 200:
            score += 1
        if text.count('.') + text.count('?') > 3:
            score += 1
        if text.lower().count(' and ') > 2:
            score += 1
        
        if score >= 2:
            return ComplexityLevel.COMPLEX
        elif score >= 1:
            return ComplexityLevel.MEDIUM
        return ComplexityLevel.SIMPLE
    
    def _extract_entities(self, text: str, intent: IntentType) -> Dict[str, str]:
        """提取关键实体"""
        entities = {}
        
        url_match = re.search(r'https?://[^\s<>"\']+', text)
        if url_match:
            entities['url'] = url_match.group(0)
        
        code_match = re.search(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL)
        if code_match:
            entities['code_block'] = code_match.group(1)
        
        if intent == IntentType.CODE_GENERATION:
            name_match = re.search(r'(?:called|named)\s+(\w+)', text, re.IGNORECASE)
            if name_match:
                entities['suggested_name'] = name_match.group(1)
        
        return entities
    
    def _route_to_model(self, intent: IntentType, complexity: ComplexityLevel) -> str:
        """决定使用哪个模型"""
        routing = {
            (IntentType.SIMPLE_CHAT, ComplexityLevel.SIMPLE): "local",
            (IntentType.EXPLANATION, ComplexityLevel.SIMPLE): "local",
            (IntentType.CODE_GENERATION, ComplexityLevel.SIMPLE): "template",
            (IntentType.CODE_GENERATION, ComplexityLevel.COMPLEX): "deepseek",
            (IntentType.DEBUG_HELP, ComplexityLevel.COMPLEX): "deepseek",
            (IntentType.TASK_ORCHESTRATION, ComplexityLevel.COMPLEX): "deepseek",
        }
        return routing.get((intent, complexity), "hybrid")
    
    def _needs_context(self, text: str) -> bool:
        """判断是否需要上下文"""
        context_signals = ['it', 'this', 'that', 'the above', 'the previous']
        text_lower = text.lower()
        return any(signal in text_lower for signal in context_signals)


# 便捷函数
def classify_intent(text: str) -> UserIntent:
    """快速分类意图"""
    classifier = IntentClassifier(use_local_model=False)
    return classifier.classify(text)


if __name__ == "__main__":
    classifier = IntentClassifier()
    
    test_inputs = [
        "Write a function to fetch data",
        "Review this code",
        "I'm getting an error",
        "What is Python asyncio?",
        "First download, then parse, finally save",
    ]
    
    print("Intent Classification Test")
    print("="*60)
    
    for text in test_inputs:
        intent = classifier.classify(text)
        print(f"\nInput: {text}")
        print(f"  Intent: {intent.intent_type.value}")
        print(f"  Complexity: {intent.complexity.value}")
        print(f"  Model: {intent.suggested_model}")
