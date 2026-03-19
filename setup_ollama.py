"""
Ollama + Qwen 3.5 4B Setup Script

Automates the installation and configuration of local LLM for SEMDS.
Usage: python setup_ollama.py
"""

import os
import sys
import subprocess
import time


def run_command(cmd, shell=True):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_ollama_installed():
    """Check if Ollama is installed"""
    success, stdout, stderr = run_command("ollama --version")
    if success:
        print(f"[OK] Ollama installed: {stdout.strip()}")
        return True
    print("[X] Ollama not found")
    return False


def install_ollama():
    """Install Ollama"""
    print("\nInstalling Ollama...")
    print("Please download and install from: https://ollama.com/download")
    print("After installation, press Enter to continue...")
    input()
    return check_ollama_installed()


def check_ollama_running():
    """Check if Ollama service is running"""
    import urllib.request

    try:
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        print("[OK] Ollama service is running")
        return True
    except:
        print("[X] Ollama service not running")
        return False


def start_ollama():
    """Start Ollama service"""
    print("\nStarting Ollama service...")
    print("Run this command in a separate terminal:")
    print("  ollama serve")
    print("\nThen press Enter to continue...")
    input()
    return check_ollama_running()


def pull_model(model_name="qwen3.5:4b"):
    """Pull Qwen 3.5 4B model"""
    print(f"\nPulling {model_name}...")
    print("This may take several minutes depending on your internet speed.")
    print("Model size: ~3GB")

    success, stdout, stderr = run_command(f"ollama pull {model_name}")
    if success:
        print(f"[OK] {model_name} pulled successfully")
        return True
    print(f"[X] Failed to pull {model_name}")
    print(f"Error: {stderr}")
    return False


def test_model(model_name="qwen3.5:4b"):
    """Test the model with a simple prompt"""
    print(f"\nTesting {model_name}...")

    import urllib.request
    import json

    data = json.dumps(
        {
            "model": model_name,
            "prompt": "Write a Python function to add two numbers. Only output the code.",
            "stream": False,
        }
    ).encode()

    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode())
            code = result.get("response", "")

            if "def " in code:
                print("[OK] Model test passed")
                print("\nGenerated code sample:")
                print("-" * 40)
                print(code[:500])
                print("-" * 40)
                return True
            else:
                print("[X] Model did not generate valid code")
                return False

    except Exception as e:
        print(f"[X] Test failed: {e}")
        return False


def update_env_file():
    """Update .env file to enable hybrid LLM"""
    print("\nUpdating .env configuration...")

    env_path = ".env"
    if not os.path.exists(env_path):
        print("[X] .env file not found")
        return False

    with open(env_path, "r") as f:
        content = f.read()

    # Enable hybrid mode
    if "ENABLE_HYBRID_LLM=false" in content:
        content = content.replace("ENABLE_HYBRID_LLM=false", "ENABLE_HYBRID_LLM=true")
        with open(env_path, "w") as f:
            f.write(content)
        print("[OK] Hybrid LLM mode enabled in .env")
    else:
        print("[INFO] Hybrid LLM already enabled or not found")

    return True


def main():
    print("=" * 60)
    print("SEMDS Ollama + Qwen 3.5 4B Setup")
    print("=" * 60)
    print("\nSystem Requirements:")
    print("- 6GB+ VRAM or 32GB+ RAM")
    print("- ~3GB disk space for model")
    print("- Internet connection for download")
    print()

    # Step 1: Check Ollama installation
    if not check_ollama_installed():
        if not install_ollama():
            print("\n[X] Ollama installation failed")
            return 1

    # Step 2: Check Ollama service
    if not check_ollama_running():
        if not start_ollama():
            print("\n[X] Could not start Ollama service")
            return 1

    # Step 3: Pull model
    model = "qwen3.5:4b"
    success, stdout, _ = run_command(f"ollama list | findstr {model}")
    if not success:
        if not pull_model(model):
            print("\n[X] Model download failed")
            return 1
    else:
        print(f"[OK] Model {model} already available")

    # Step 4: Test model
    if not test_model(model):
        print("\n[X] Model test failed")
        return 1

    # Step 5: Update configuration
    update_env_file()

    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Keep 'ollama serve' running in a terminal")
    print("2. Run SEMDS evolution - it will now use Qwen 3.5 4B")
    print("3. DeepSeek will be used every 20 generations for major changes")
    print("\nEstimated cost savings: ~90% vs pure DeepSeek")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
