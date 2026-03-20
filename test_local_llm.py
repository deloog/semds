"""Test local Qwen 3.5 4B model via Ollama"""

import time

import requests

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen3.5:4b"


def test_ollama_connection():
    """Test if Ollama is running"""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json()
            print("Ollama is running!")
            print("Available models:")
            for m in models.get("models", []):
                print(f"  - {m['name']}")
            return True
        else:
            print(f"Ollama returned status {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to Ollama")
        print("Please run: ollama serve")
        return False


def test_qwen_generation():
    """Test code generation"""
    prompt = """You are a Python expert. Write a function to sort a list using quicksort.

Requirements:
- Function name: solution
- Parameter: arr (list of integers)
- Return: sorted list
- Use in-place partition for efficiency

Write only the function, no explanation:"""

    print(f"\nTesting {MODEL}...")
    start = time.time()

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 500},
            },
            timeout=60,
        )

        elapsed = time.time() - start

        if resp.status_code == 200:
            result = resp.json()
            code = result.get("response", "")
            print(f"Generated code ({elapsed:.2f}s):")
            print("-" * 60)
            print(code[:1000])
            print("-" * 60)

            # Try to validate the code
            try:
                compile(code, "<string>", "exec")
                print("Syntax: OK")
            except SyntaxError as e:
                print(f"Syntax Error: {e}")

            return True
        else:
            print(f"Error: {resp.status_code}")
            print(resp.text[:500])
            return False

    except Exception as e:
        print(f"Request failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Local LLM (Qwen 3.5 4B)")
    print("=" * 60)

    if test_ollama_connection():
        test_qwen_generation()
    else:
        print("\nPlease install and start Ollama first:")
        print("1. Download from https://ollama.com/download/windows")
        print("2. Run: ollama pull qwen3.5:4b")
        print("3. Run: ollama serve")
