"""
Context Manager - 上下文管理器
管理 SEMDS 调用外部模型时的状态和上下文
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    """对话消息"""

    role: str  # user, assistant, system
    content: str
    timestamp: float
    model_used: Optional[str] = None  # 记录哪个模型生成的


@dataclass
class ConversationContext:
    """对话上下文"""

    session_id: str
    messages: deque  # 使用 deque 自动限制长度
    user_preferences: Dict[str, Any]
    accumulated_knowledge: Dict[str, str]  # 累积的知识
    task_history: List[Dict]  # 任务执行历史

    def __init__(self, session_id: str, max_history: int = 10):
        self.session_id = session_id
        self.messages = deque(maxlen=max_history)
        self.user_preferences = {}
        self.accumulated_knowledge = {}
        self.task_history = []


class ContextManager:
    """
    上下文管理器

    本地模型的职责：
    1. 维护对话历史（短期记忆）
    2. 提取和总结关键信息（知识积累）
    3. 管理外部模型调用的上下文窗口
    4. 指代消解（this, it, that -> 具体指什么）

    为什么用本地模型：
    - 上下文管理是"信息整理"任务（4B 模型可以胜任）
    - 减少外部模型调用的 token 消耗（省钱）
    - 本地访问速度快（用户体验好）
    """

    def __init__(self, max_sessions: int = 100):
        self.sessions: Dict[str, ConversationContext] = {}
        self.max_sessions = max_sessions

    def get_or_create_session(self, session_id: str) -> ConversationContext:
        """获取或创建会话"""
        if session_id not in self.sessions:
            # 清理旧会话
            if len(self.sessions) >= self.max_sessions:
                oldest = min(
                    self.sessions,
                    key=lambda k: (
                        self.sessions[k].messages[-1].timestamp
                        if self.sessions[k].messages
                        else 0
                    ),
                )
                del self.sessions[oldest]

            self.sessions[session_id] = ConversationContext(session_id)

        return self.sessions[session_id]

    def add_message(
        self, session_id: str, role: str, content: str, model_used: Optional[str] = None
    ):
        """添加消息到上下文"""
        session = self.get_or_create_session(session_id)

        message = Message(
            role=role, content=content, timestamp=time.time(), model_used=model_used
        )

        session.messages.append(message)

    def get_context_for_model(self, session_id: str, max_tokens: int = 2000) -> str:
        """
        为外部模型生成上下文摘要

        不是简单拼接所有历史，而是用本地模型生成摘要
        这样可以减少 token 消耗
        """
        session = self.get_or_create_session(session_id)

        if not session.messages:
            return ""

        # 简单的上下文格式化（可以用本地模型改进）
        context_parts = []

        # 添加累积的知识
        if session.accumulated_knowledge:
            context_parts.append("Previous knowledge:")
            for key, value in session.accumulated_knowledge.items():
                context_parts.append(f"  {key}: {value}")

        # 添加最近的对话
        recent_messages = list(session.messages)[-5:]  # 最近5轮
        context_parts.append("\nRecent conversation:")
        for msg in recent_messages:
            role = "User" if msg.role == "user" else "Assistant"
            context_parts.append(f"{role}: {msg.content[:100]}...")

        return "\n".join(context_parts)

    def resolve_references(self, session_id: str, text: str) -> str:
        """
        指代消解

        将 "it", "this", "that" 替换为具体指代的内容
        这是本地模型能做的简单任务
        """
        session = self.get_or_create_session(session_id)

        # 简单的规则替换（可以用本地模型改进）
        reference_signals = ["it", "this", "that", "the above"]

        text_lower = text.lower()
        has_reference = any(sig in text_lower for sig in reference_signals)

        if not has_reference:
            return text

        # 找到最近的话题/实体
        recent_topics = self._extract_recent_topics(session)

        if recent_topics:
            # 替换指代
            resolved = text
            for signal in reference_signals:
                if signal in resolved.lower():
                    # 用最相关的话题替换
                    resolved = resolved.replace(signal, f"'{recent_topics[0]}'", 1)
                    break
            return resolved

        return text

    def _extract_recent_topics(self, session: ConversationContext) -> List[str]:
        """提取最近对话中的主题"""
        topics = []

        # 从最近的用户消息中提取关键词
        for msg in reversed(session.messages):
            if msg.role == "user":
                # 简单提取（可以用本地模型做 NER）
                words = msg.content.split()
                # 取较长的词作为主题
                topics.extend([w for w in words if len(w) > 4])

        return list(set(topics))[:5]  # 去重，最多5个

    def extract_knowledge(self, session_id: str, text: str) -> Dict[str, str]:
        """
        从对话中提取知识

        例如：
        "I want Python code" -> 记住用户偏好 Python
        "Use timeout of 30s" -> 记住配置 timeout=30
        """
        session = self.get_or_create_session(session_id)

        knowledge = {}

        # 简单的规则提取（可以用本地模型改进）
        text_lower = text.lower()

        # 提取语言偏好
        if "python" in text_lower:
            knowledge["preferred_language"] = "Python"
        elif "javascript" in text_lower or "js" in text_lower:
            knowledge["preferred_language"] = "JavaScript"

        # 提取超时设置
        timeout_match = __import__("re").search(r"(\d+)\s*(?:second|sec|s)", text_lower)
        if timeout_match:
            knowledge["default_timeout"] = timeout_match.group(1)

        # 保存到会话
        session.accumulated_knowledge.update(knowledge)

        return knowledge

    def summarize_for_external_model(self, session_id: str, current_task: str) -> str:
        """
        为外部模型生成上下文摘要

        这是关键功能：本地模型将长对话摘要成关键信息
        减少发送给 DeepSeek 的 token 数
        """
        session = self.get_or_create_session(session_id)

        summary_parts = []

        # 1. 用户偏好
        if session.user_preferences:
            summary_parts.append("User preferences:")
            for k, v in session.user_preferences.items():
                summary_parts.append(f"- {k}: {v}")

        # 2. 累积知识
        if session.accumulated_knowledge:
            summary_parts.append("\nRelevant knowledge:")
            for k, v in session.accumulated_knowledge.items():
                summary_parts.append(f"- {k}: {v}")

        # 3. 当前任务相关的历史
        relevant_history = self._get_relevant_history(session, current_task)
        if relevant_history:
            summary_parts.append("\nRelevant previous actions:")
            for action in relevant_history:
                summary_parts.append(f"- {action}")

        return "\n".join(summary_parts)

    def _get_relevant_history(
        self, session: ConversationContext, current_task: str
    ) -> List[str]:
        """获取与当前任务相关的历史"""
        # 简单实现：找关键词匹配的历史
        relevant = []
        task_keywords = set(current_task.lower().split())

        for msg in reversed(session.messages):
            if msg.role == "user":
                msg_keywords = set(msg.content.lower().split())
                overlap = task_keywords & msg_keywords
                if len(overlap) >= 2:  # 有关键词重叠
                    relevant.append(msg.content[:80] + "...")

        return relevant[:3]  # 最多3条

    def clear_session(self, session_id: str):
        """清理会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def get_session_stats(self, session_id: str) -> Dict:
        """获取会话统计"""
        session = self.sessions.get(session_id)
        if not session:
            return {}

        return {
            "message_count": len(session.messages),
            "knowledge_items": len(session.accumulated_knowledge),
            "task_count": len(session.task_history),
            "models_used": list(
                set(msg.model_used for msg in session.messages if msg.model_used)
            ),
        }


# 便捷函数
_context_manager = None


def get_context_manager() -> ContextManager:
    """获取全局上下文管理器"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


if __name__ == "__main__":
    # 测试
    cm = ContextManager()
    session_id = "test_session"

    # 添加一些消息
    cm.add_message(session_id, "user", "I need Python code to fetch data")
    cm.add_message(session_id, "assistant", "Here's the code...", "deepseek")
    cm.add_message(session_id, "user", "Can you make it async?")

    # 提取知识
    cm.extract_knowledge(session_id, "I prefer Python with aiohttp")

    # 获取上下文
    context = cm.get_context_for_model(session_id)
    print("Context for model:")
    print(context)

    # 指代消解
    resolved = cm.resolve_references(session_id, "Make it faster")
    print(f"\nResolved: {resolved}")

    # 统计
    stats = cm.get_session_stats(session_id)
    print(f"\nStats: {stats}")
