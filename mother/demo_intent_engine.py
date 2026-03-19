"""
SEMDS Intent Engine Demo
本地模型作为意图识别器和上下文管理器演示
"""

import sys

sys.path.insert(0, "D:\\semds")

from mother.intent_engine.intent_classifier import IntentClassifier
from mother.intent_engine.context_manager import ContextManager
from mother.intent_engine.model_router import process_user_input


def demo_intent_classification():
    """演示意图识别"""
    print("=" * 70)
    print("DEMO 1: Intent Classification (Local Model/Rule Based)")
    print("=" * 70)
    print()
    print("Local model acts as: Intent Classifier")
    print("  - Analyzes user input")
    print("  - Identifies task type")
    print("  - Assesses complexity")
    print("  - Suggests which model to use")
    print()

    classifier = IntentClassifier()

    test_cases = [
        ("Write a function to fetch data from API", "Simple code generation"),
        ("Can you review this code and tell me what's wrong?", "Code review request"),
        ("I'm getting KeyError 'user' when running my script", "Debug help"),
        ("What is the difference between async and await?", "Explanation"),
        ("Search for latest Python 3.12 features", "Web search"),
        (
            "First download the data, then parse it, finally save to DB",
            "Multi-step task",
        ),
        ("Hello, how are you?", "Simple chat"),
        ("Optimize this sorting algorithm for large datasets", "Complex optimization"),
    ]

    for text, description in test_cases:
        intent = classifier.classify(text)

        print(f'Input: "{text}"')
        print(f"  Description: {description}")
        print(f"  Intent: {intent.intent_type.value}")
        print(f"  Complexity: {intent.complexity.value}")
        print(f"  Confidence: {intent.confidence:.0%}")
        print(f"  Suggested Model: {intent.suggested_model}")
        print(f"  Entities: {intent.entities}")
        print(f"  Needs Context: {intent.context_needed}")
        print()


def demo_context_management():
    """演示上下文管理"""
    print("\n" + "=" * 70)
    print("DEMO 2: Context Management (Local Model)")
    print("=" * 70)
    print()
    print("Local model acts as: Context Manager")
    print("  - Maintains conversation history")
    print("  - Resolves references (this, it, that)")
    print("  - Extracts and accumulates knowledge")
    print("  - Summarizes for external models")
    print()

    cm = ContextManager()
    session_id = "demo_session"

    # 模拟对话
    conversation = [
        ("user", "I want to write Python code to download images"),
        ("assistant", "Here's code to download images...", "deepseek"),
        ("user", "Can you make it async?"),
        ("assistant", "Here's the async version...", "deepseek"),
        ("user", "Add error handling to it"),
    ]

    print("Simulated conversation:")
    for i, (role, content, *model) in enumerate(conversation):
        print(f"\n{i+1}. [{role.upper()}]: {content}")

        cm.add_message(session_id, role, content, model[0] if model else None)

        if role == "user":
            # 提取知识
            knowledge = cm.extract_knowledge(session_id, content)
            if knowledge:
                print(f"   -> Extracted knowledge: {knowledge}")

            # 指代消解
            resolved = cm.resolve_references(session_id, content)
            if resolved != content:
                print(f'   -> Resolved: "{resolved}"')

    print("\n" + "-" * 70)
    print("Context summary for external model:")
    summary = cm.summarize_for_external_model(session_id, "Add error handling")
    print(summary)

    stats = cm.get_session_stats(session_id)
    print(f"\nSession stats: {stats}")


def demo_full_pipeline():
    """演示完整流程"""
    print("\n\n" + "=" * 70)
    print("DEMO 3: Full Processing Pipeline")
    print("=" * 70)
    print()
    print("Complete flow:")
    print("  User Input -> Intent Classification -> Context Resolution")
    print("       -> Model Routing -> Execution -> Response")
    print()

    session_id = "pipeline_demo"

    inputs = [
        "Write a function to fetch JSON from API",
        "Can you add timeout to it?",
        "What about error handling?",
    ]

    for text in inputs:
        print(f"\n{'='*70}")
        print(f'User: "{text}"')
        print(f"{'='*70}")

        result = process_user_input(text, session_id=session_id)

        print(f"Detected intent: {result['intent']}")
        print(f"Complexity: {result['complexity']}")
        print(f"Routed to: {result['model_used']}")
        print(f"Context used: {result['context_used']}")
        print(f"Cost: ${result['cost']:.4f}")


def print_architecture():
    """打印架构"""
    print("\n\n" + "=" * 70)
    print("Intent Engine Architecture")
    print("=" * 70)
    print("""
┌─────────────────────────────────────────────────────────────────────┐
│                        User Input                                  │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Intent Classifier (Local Model / Rules)                            │
│  • Classify intent type (code_gen, debug, explain...)              │
│  • Assess complexity (simple/medium/complex)                       │
│  • Extract entities (URLs, code blocks, function names)            │
│  • Estimate confidence                                             │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Context Manager (Local Model)                                      │
│  • Resolve references (this, it, that -> specific)                 │
│  • Maintain conversation history                                   │
│  • Extract and accumulate knowledge                                │
│  • Generate context summary for external models                    │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Model Router                                                        │
│  simple_chat  ────────► Local Model (fast, free)                   │
│  simple_code  ────────► Template (deterministic)                   │
│  medium_task  ────────► Hybrid (local + deepseek)                  │
│  complex_task ────────► DeepSeek (high quality, $)                 │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Response                                     │
└─────────────────────────────────────────────────────────────────────┘

Key Design:
  • Local model handles "intelligence" tasks it's good at:
    - Classification, entity extraction, summarization
  • Local model manages state (context) to reduce API costs
  • Complex generation tasks go to DeepSeek
  • Routing is transparent to user but optimizes for cost/quality
""")


def main():
    print("=" * 70)
    print("SEMDS Intent Engine - Local Model as Router & Context Manager")
    print("=" * 70)
    print()
    print("This demo shows how the local model (Qwen 3.5 4B) can be used")
    print("effectively as an intent classifier and context manager,")
    print("while delegating complex tasks to external models (DeepSeek).")
    print()

    demo_intent_classification()
    demo_context_management()
    demo_full_pipeline()
    print_architecture()

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("Key Takeaway:")
    print("  Local model is the 'brain' that decides what to do")
    print("  External models are the 'muscle' that does heavy lifting")
    print("  This maximizes the value of both models")
    print("=" * 70)


if __name__ == "__main__":
    main()
