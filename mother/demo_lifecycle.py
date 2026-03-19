"""
SEMDS Lifecycle Demo - Full闭环 demonstration.

This demo shows the complete lifecycle:
1. Generate a simple API
2. Deploy it to container
3. Monitor its health
4. Simulate failure and auto-heal
5. Clean up
"""

import sys
import time

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pathlib import Path

from mother.lifecycle import LifecycleManager, DeploymentConfig, HealthStatus

# Sample FastAPI application
SAMPLE_APP = """
from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="Demo API")

@app.get("/")
def root():
    return {"message": "Hello from SEMDS!", "time": datetime.now().isoformat()}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id, "name": f"Item {item_id}"}
"""

# App with bug (for healing demo)
BUGGY_APP = """
from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="Demo API - Buggy")

counter = 0

@app.get("/")
def root():
    global counter
    counter += 1
    # Simulate failure after 5 requests
    if counter > 5:
        raise RuntimeError("Simulated failure!")
    return {"message": "Hello!", "count": counter}

@app.get("/health")
def health():
    global counter
    if counter > 5:
        return {"status": "unhealthy"}, 500
    return {"status": "healthy"}
"""


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print("=" * 60)


def demo_basic_deployment():
    """Demo 1: Basic deployment and monitoring."""
    print_section("DEMO 1: Basic Deployment")

    with LifecycleManager() as manager:
        # Deploy service
        print("Deploying sample API...")
        result = manager.deploy_service(
            name="demo-api",
            app_code=SAMPLE_APP,
            config=DeploymentConfig(name="demo-api", port=8081),
        )

        if result.status.value == "running":
            print(f"[OK] Deployed at: {result.service_url}")
            print(f"[INFO] Build time: {result.build_time_ms}ms")
        else:
            print(f"[FAIL] Deployment failed: {result.error}")
            return

        # Check status
        print("\nChecking service status...")
        for i in range(3):
            time.sleep(2)
            status = manager.get_service_status("demo-api")
            print(f"  Health: {status.health.value}")

            if status.health == HealthStatus.HEALTHY:
                print(f"\n[OK] Service is healthy!")
                print(f"  URL: {status.url}")
                break

        # List all services
        print("\nAll deployed services:")
        services = manager.list_services()
        for name, status in services.items():
            print(f"  - {name}: {status.health.value} at {status.url}")

        # Stop service
        print("\nStopping service...")
        manager.stop_service("demo-api")
        print("[OK] Service stopped")


def demo_auto_healing():
    """Demo 2: Auto-healing on failure."""
    print_section("DEMO 2: Auto-Healing")

    with LifecycleManager(enable_auto_healing=True) as manager:
        # Deploy buggy app
        print("Deploying app with intentional bug...")
        print("(App will fail after 5 requests)")

        result = manager.deploy_service(
            name="buggy-api",
            app_code=BUGGY_APP,
            config=DeploymentConfig(name="buggy-api", port=8082),
            wait_for_healthy=False,
        )

        print(f"[OK] Deployed at: {result.service_url}")

        # Wait and watch for failure/healing
        print("\nMonitoring for 30 seconds...")
        print("(Making requests to trigger failure)")

        import requests

        url = result.service_url

        for i in range(15):
            time.sleep(2)

            try:
                resp = requests.get(f"{url}/", timeout=5)
                print(f"  Request {i+1}: HTTP {resp.status_code}")
            except Exception as e:
                print(f"  Request {i+1}: Error - {e}")

            status = manager.get_service_status("buggy-api")

            # Check healing history
            history = manager.get_healing_history("buggy-api")
            if history:
                print(f"\n[HEALING] Auto-healing triggered!")
                for h in history:
                    print(f"  Action: {h.action.value}, Success: {h.success}")
                break

        # Final status
        print("\nFinal status:")
        status = manager.get_service_status("buggy-api")
        print(f"  Health: {status.health.value}")

        # Show logs
        print("\nRecent logs:")
        logs = manager.get_service_logs("buggy-api", tail=10)
        for log in logs[-5:]:
            if log.strip():
                print(f"  {log}")

        # Clean up
        manager.stop_service("buggy-api")
        print("\n[OK] Service stopped")


def main():
    """Run all demos."""
    print("=" * 60)
    print("SEMDS Lifecycle Management Demo")
    print("Full闭环: Code → Deploy → Monitor → Heal")
    print("=" * 60)

    print("\nThis demo requires Docker to be running.")
    print("Make sure Docker Desktop is started.")

    input("\nPress Enter to continue...")

    try:
        demo_basic_deployment()

        print("\n" + "-" * 60)
        input("\nPress Enter to continue to healing demo...")

        demo_auto_healing()

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Demo failed: {e}")
        import traceback

        traceback.print_exc()

    print_section("Demo Complete")
    print("The lifecycle management system provides:")
    print("  1. One-command deployment")
    print("  2. Automatic health monitoring")
    print("  3. Self-healing on failures")
    print("  4. Complete闭环 from code to running service")


if __name__ == "__main__":
    main()
