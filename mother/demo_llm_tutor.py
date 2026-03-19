"""
SEMDS LLM Tutor - Demo
SEMDS 提升本地模型编程能力演示
"""

import sys

sys.path.insert(0, "D:\\semds")

from dotenv import load_dotenv

load_dotenv("D:\\semds\\.env")

from mother.llm_tutor.code_tutor import CodeTutor
from mother.llm_tutor.few_shot_optimizer import FewShotOptimizer
from mother.llm_tutor.iterative_trainer import IterativeTrainer


def demo_code_tutor():
    """演示编程教练"""
    print("=" * 70)
    print("DEMO 1: Code Tutor - SEMDS as Teacher")
    print("=" * 70)
    print()
    print("Strategy:")
    print("  1. Local model generates code (simulated)")
    print("  2. SEMDS evaluates and gives feedback")
    print("  3. DeepSeek (strong model) generates improved version")
    print("  4. Lesson recorded for future learning")
    print()

    tutor = CodeTutor()

    # 模拟本地模型生成的有问题的代码
    local_model_code = """
def fetch_url(url):
    import requests
    return requests.get(url).text
"""

    print("[Local Model Output]")
    print(local_model_code)
    print()

    # SEMDS 教学
    session = tutor.teach(
        task="Fetch data from URL with proper error handling and validation",
        student_code=local_model_code,
        max_iterations=2,
    )

    print("\n" + "=" * 70)
    print("Teaching Results:")
    print("=" * 70)
    print(f"Final score: {session.final_score}/100")
    print(f"Lessons learned: {session.lessons_learned}")

    print("\nFinal improved code:")
    print("-" * 70)
    print(session.final_code[:800])

    tutor.print_summary()


def demo_few_shot_optimizer():
    """演示 Few-shot 优化"""
    print("\n\n" + "=" * 70)
    print("DEMO 2: Few-shot Optimizer")
    print("=" * 70)
    print()
    print("Strategy:")
    print("  1. Collect good vs bad code examples")
    print("  2. Build few-shot prompt library")
    print("  3. Local model learns from examples")
    print()

    optimizer = FewShotOptimizer()

    # 添加几个学习示例
    examples = [
        {
            "type": "http_client",
            "task": "Fetch JSON from API",
            "bad": """def get_json(url):
    return requests.get(url).json()""",
            "good": '''def get_json(url: str) -> dict:
    """Fetch JSON from API safely."""
    if not isinstance(url, str):
        raise ValueError("URL must be string")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}''',
            "improvements": [
                "Type hints",
                "Input validation",
                "Error handling",
                "Timeout",
            ],
        },
        {
            "type": "parser",
            "task": "Parse CSV data",
            "bad": """def parse_csv(data):
    lines = data.split("\\n")
    return [line.split(",") for line in lines]""",
            "good": '''def parse_csv(data: str) -> list:
    """Parse CSV string to list of lists."""
    import csv
    from io import StringIO
    
    if not isinstance(data, str):
        return []
    
    try:
        reader = csv.reader(StringIO(data))
        return list(reader)
    except csv.Error as e:
        return []''',
            "improvements": [
                "Type hints",
                "Input validation",
                "Proper CSV parsing",
                "Error handling",
            ],
        },
    ]

    for ex in examples:
        optimizer.add_example(
            task_type=ex["type"],
            task_description=ex["task"],
            bad_code=ex["bad"],
            good_code=ex["good"],
            improvements=ex["improvements"],
        )

    # 生成优化后的提示
    print("[Generating optimized prompt for new task...]")

    prompt = optimizer.get_prompt_for_ollama(
        task_type="http_client", new_task="Download image from URL and save to file"
    )

    print("\nOptimized prompt for local LLM:")
    print("-" * 70)
    print(prompt[:1000])
    print("...")

    optimizer.print_examples_stats()


def demo_iterative_trainer():
    """演示迭代训练"""
    print("\n\n" + "=" * 70)
    print("DEMO 3: Iterative Trainer")
    print("=" * 70)
    print()
    print("Strategy:")
    print("  1. Local model generates code")
    print("  2. SEMDS evaluates quality")
    print("  3. If score < target, generate feedback")
    print("  4. Local model regenerates with feedback")
    print("  5. Loop until target reached")
    print()

    print("[This demo requires Ollama running with local model]")
    print("[Skipping actual training, showing structure...]")
    print()

    # 展示结构
    print("Training loop structure:")
    print("""
    for iteration in range(max_iterations):
        # 1. Local model generates
        code = local_model.generate(task)
        
        # 2. SEMDS evaluates
        score = code_optimizer.check(code)
        
        # 3. Check target
        if score >= target_score:
            break
        
        # 4. Generate feedback
        feedback = generate_feedback(code)
        
        # 5. Record example
        few_shot.add_example(bad=code, good=improved)
        
        # 6. Next iteration
        code = local_model.generate(task, feedback)
    """)

    # 加载已有训练记录
    trainer = IterativeTrainer()
    trainer.print_training_stats()


def print_architecture():
    """打印架构说明"""
    print("\n\n" + "=" * 70)
    print("SEMDS LLM Tutor Architecture")
    print("=" * 70)
    print("""
Goal: Improve local model's (Qwen) programming capability

Approach: Three-layer enhancement

┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Code Tutor                                         │
│  - DeepSeek (strong) generates golden standard              │
│  - Compare with local model output                          │
│  - Generate specific improvement suggestions                │
│  - Record lessons learned                                   │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Few-shot Optimizer                                 │
│  - Build library of good vs bad examples                    │
│  - Create optimized prompts for local model                 │
│  - Local model learns from examples                         │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Iterative Trainer                                  │
│  - Loop: Generate -> Check -> Feedback -> Improve           │
│  - Accumulate training data                                 │
│  - Measure improvement over time                            │
└─────────────────────────────────────────────────────────────┘

Key Insight:
  Instead of retraining the model (expensive),
  we improve the INPUT (prompt) and provide FEEDBACK.
  This is "prompt engineering" at scale with automation.

Data Flow:
  Local Model Output → SEMDS Evaluation → Feedback → 
  Improved Code → Few-shot Example → Better Prompt →
  Next Generation (hopefully better)
""")


def main():
    print("=" * 70)
    print("SEMDS LLM Tutor - Improving Local Model Programming")
    print("=" * 70)
    print()
    print("This system helps your local Qwen model write better code")
    print("by using SEMDS as a teacher and coach.")
    print()

    try:
        demo_code_tutor()
    except Exception as e:
        print(f"\n[Error in Code Tutor demo: {e}]")
        import traceback

        traceback.print_exc()

    try:
        demo_few_shot_optimizer()
    except Exception as e:
        print(f"\n[Error in Few-shot demo: {e}]")
        import traceback

        traceback.print_exc()

    try:
        demo_iterative_trainer()
    except Exception as e:
        print(f"\n[Error in Trainer demo: {e}]")
        import traceback

        traceback.print_exc()

    print_architecture()

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("  1. Run actual training: python mother/llm_tutor/iterative_trainer.py")
    print("  2. Check examples: mother/llm_tutor/few_shot_examples/")
    print("  3. Use in Mother System: Integrate with enhanced_mother.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
