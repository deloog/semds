"""
SEMDS Code Generator - Layer 1

Code generator supporting multiple LLM backends including local Ollama.

Supported LLM:
- Deepseek (default, recommended)
- Anthropic Claude
- OpenAI GPT
- Ollama (local models like Qwen3.5)
"""

import os
import re
import json
from typing import Any, Dict, List, Optional, Type, Union

# Optional imports
Anthropic: Optional[Type[Any]] = None
OpenAI: Optional[Type[Any]] = None

try:
    from anthropic import Anthropic
except ImportError:
    pass

try:
    from openai import OpenAI
except ImportError:
    pass


# Code generation prompt template
GENERATION_PROMPT = """You are a Python expert. Implement the following function specification.

## Task Description
{task_description}

## Target Function Signature
```python
{function_signature}
```

## Requirements
{requirements}

## Previous Implementation (if any)
```python
{previous_code}
```

## Previous Score
- Intrinsic score (test pass rate): {intrinsic_score}
- Failed test cases: {failed_tests}
- Extrinsic score (consistency): {extrinsic_score}

## This Generation Strategy
- Mutation type: {mutation_type}
- Improvement focus: {improvement_focus}

## Requirements
1. Only output the function implementation, no test code
2. Do not use any external libraries
3. Code must be complete and executable
4. No explanatory text

```python
"""

CODE_EXTRACTION_PATTERN = r"```python\n(.*?)\n```"


class CodeGenerator:
    """
    Code generator supporting multiple LLM backends.

    Supported backends:
    - deepseek (default)
    - anthropic
    - openai
    - ollama (local models)

    Attributes:
        client: API client
        model: Model name
        default_temperature: Default temperature
        backend: LLM backend type
        base_url: Custom base URL for API
    """

    DEFAULT_MODEL = "deepseek-chat"
    DEFAULT_BACKEND = "deepseek"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        default_temperature: float = 0.5,
        backend: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        """
        Initialize code generator.

        Args:
            api_key: API key (from env var if not provided)
            model: Model name
            default_temperature: Temperature (0.0-1.0)
            backend: LLM backend (deepseek/anthropic/openai/ollama)
            base_url: Custom API base URL
        """
        self.backend = backend or os.environ.get("LLM_BACKEND", self.DEFAULT_BACKEND)
        self.model = model
        self.default_temperature = default_temperature
        self.base_url = base_url

        if self.backend == "deepseek":
            self._init_deepseek(api_key, base_url)
        elif self.backend == "anthropic":
            self._init_anthropic(api_key)
        elif self.backend == "openai":
            self._init_openai(api_key, base_url)
        elif self.backend == "ollama":
            self._init_ollama(base_url)
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

    def _init_deepseek(self, api_key: Optional[str], base_url: Optional[str]) -> None:
        """Initialize Deepseek client"""
        if OpenAI is None:
            raise ImportError("openai library required. Install: pip install openai")

        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("Deepseek API key required via DEEPSEEK_API_KEY")

        base_url = base_url or os.environ.get(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
        )
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)

    def _init_anthropic(self, api_key: Optional[str]) -> None:
        """Initialize Anthropic client"""
        if Anthropic is None:
            raise ImportError(
                "anthropic library required. Install: pip install anthropic"
            )

        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required via ANTHROPIC_API_KEY")

        self.client = Anthropic(api_key=self.api_key)

    def _init_openai(self, api_key: Optional[str], base_url: Optional[str]) -> None:
        """Initialize OpenAI client"""
        if OpenAI is None:
            raise ImportError("openai library required. Install: pip install openai")

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required via OPENAI_API_KEY")

        kwargs = {"api_key": self.api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)

    def _init_ollama(self, base_url: Optional[str]) -> None:
        """Initialize Ollama (local model) - no API key needed"""
        self.base_url = base_url or os.environ.get(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        self.model = os.environ.get("OLLAMA_MODEL", self.model)
        self.client = None  # Use requests directly for Ollama

    def generate(
        self,
        task_spec: Dict[str, Any],
        previous_code: Optional[str] = None,
        previous_score: Optional[Dict[str, Any]] = None,
        failed_tests: Optional[List[str]] = None,
        strategy: Optional[Dict[str, Any]] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate code implementation.

        Args:
            task_spec: Task specification with description, function_signature, requirements
            previous_code: Previous generation code
            previous_score: Previous scores
            failed_tests: List of failed tests
            strategy: Mutation strategy
            temperature: Override default temperature

        Returns:
            Dict with success, code, raw_response, error
        """
        prompt_params = {
            "task_description": task_spec.get("description", ""),
            "function_signature": task_spec.get("function_signature", ""),
            "requirements": self._format_requirements(
                task_spec.get("requirements", [])
            ),
            "previous_code": previous_code or "# First generation, no previous code",
            "intrinsic_score": (
                previous_score.get("intrinsic_score", "N/A")
                if previous_score
                else "N/A"
            ),
            "extrinsic_score": (
                previous_score.get("extrinsic_score", "N/A")
                if previous_score
                else "N/A"
            ),
            "failed_tests": ", ".join(failed_tests) if failed_tests else "None",
            "mutation_type": (
                strategy.get("mutation_type", "conservative")
                if strategy
                else "conservative"
            ),
            "improvement_focus": (
                strategy.get("improvement_focus", "Improve test pass rate")
                if strategy
                else "Implement basic functionality"
            ),
        }

        prompt = GENERATION_PROMPT.format(**prompt_params)

        try:
            if self.backend == "ollama":
                raw_response = self._call_ollama(prompt, temperature)
            elif self.backend in ["deepseek", "openai"]:
                raw_response = self._call_openai_compatible(prompt, temperature)
            else:
                raw_response = self._call_anthropic(prompt, temperature)

            extracted_code = self.extract_code(raw_response)

            if extracted_code:
                return {
                    "success": True,
                    "code": extracted_code,
                    "raw_response": raw_response,
                    "error": None,
                }
            else:
                return {
                    "success": False,
                    "code": None,
                    "raw_response": raw_response,
                    "error": "Failed to extract code from response",
                }

        except Exception as e:
            return {
                "success": False,
                "code": None,
                "raw_response": None,
                "error": f"API call failed: {str(e)}",
            }

    def _call_ollama(self, prompt: str, temperature: Optional[float]) -> str:
        """Call Ollama API"""
        import requests  # type: ignore[import-untyped]

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature or self.default_temperature,
                "num_predict": 2048,  # Limit output for small models
            },
        }

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return str(response.json().get("response", ""))

    def _call_openai_compatible(self, prompt: str, temperature: Optional[float]) -> str:
        """Call OpenAI/Deepseek API"""
        messages = [
            {
                "role": "system",
                "content": "You are a professional Python programmer. Only output code, no explanations. Code must be in ```python block.",
            },
            {"role": "user", "content": prompt},
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or self.default_temperature,
            max_tokens=4096,
        )
        return str(response.choices[0].message.content)

    def _call_anthropic(self, prompt: str, temperature: Optional[float]) -> str:
        """Call Anthropic API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=temperature or self.default_temperature,
            system="You are a professional Python programmer. Only output code, no explanations. Code must be in ```python block.",
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0]
        return content.text if hasattr(content, "text") else str(content)

    def extract_code(self, response: str) -> Optional[str]:
        """Extract Python code from response"""
        matches = re.findall(CODE_EXTRACTION_PATTERN, response, re.DOTALL)

        if matches:
            code = str(matches[0]).strip()
            if code.endswith("```"):
                code = code[:-3].strip()
            return code

        # Fallback: try generic code block
        fallback_pattern = r"```\n(.*?)\n```"
        fallback_matches = re.findall(fallback_pattern, response, re.DOTALL)
        if fallback_matches:
            code = str(fallback_matches[0]).strip()
            if code.endswith("```"):
                code = code[:-3].strip()
            return code

        # Last resort: check if response contains code-like content
        if "def " in response or "class " in response:
            lines = response.split("\n")
            code_lines = []
            in_code = False
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("def ") or stripped.startswith("class "):
                    in_code = True
                if in_code:
                    code_lines.append(line)
            if code_lines:
                return "\n".join(code_lines).strip()

        return None

    def _format_requirements(self, requirements: Union[str, List[Any]]) -> str:
        """Format requirements list"""
        if isinstance(requirements, str):
            return requirements
        # isinstance(requirements, list)
        return "\n".join(f"- {req}" for req in requirements)


if __name__ == "__main__":
    # Test with Ollama
    import os

    os.environ["LLM_BACKEND"] = "ollama"
    os.environ["OLLAMA_MODEL"] = "qwen3.5:4b"

    generator = CodeGenerator()

    task_spec = {
        "description": "Implement a simple addition function",
        "function_signature": "def add(a: float, b: float) -> float:",
        "requirements": ["Return sum of two numbers", "Support floats"],
    }

    result = generator.generate(task_spec)

    if result["success"]:
        print("Generated code:")
        print(result["code"])
    else:
        print(f"Generation failed: {result['error']}")
        print(f"Raw response: {result['raw_response']}")
