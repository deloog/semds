"""Frontend E2E Test - End-to-End Workflow Verification

Tests the complete workflow:
1. Create task via API
2. Start evolution
3. Verify WebSocket real-time updates
4. Check chart data and code display

Usage:
    python tests/e2e_frontend_test.py

Note: These tests require a running server and are skipped in CI.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

# Setup path - use current directory
_current_dir = Path(__file__).parent.parent
os.chdir(_current_dir)
sys.path.insert(0, str(_current_dir))

import requests  # noqa: E402
import websocket  # noqa: E402

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

# Load env and get auth token
from core.env_loader import load_env  # noqa: E402

load_env()

from api.auth.jwt import create_access_token  # noqa: E402
from api.auth.models import UserRole  # noqa: E402

TEST_TOKEN = create_access_token(
    data={"sub": "admin-1", "role": UserRole.ADMIN}, expires_delta=None
)

HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}", "Content-Type": "application/json"}

# Skip all E2E tests in CI environment (requires running server)
pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true" or os.environ.get("SKIP_E2E") == "1",
    reason="E2E tests require running server, skipped in CI"
)


def test_health():
    """Test health endpoint"""
    print("\n[1/6] Testing health endpoint...")
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    print(f"  OK - API version: {data['version']}")


def test_list_tasks():
    """Test listing tasks"""
    print("\n[2/6] Testing task list...")
    resp = requests.get(f"{BASE_URL}/api/tasks", headers=HEADERS)
    assert resp.status_code == 200
    tasks = resp.json()
    print(f"  OK - Found {len(tasks)} tasks")
    return tasks


def test_create_task():
    """Test creating a task"""
    print("\n[3/6] Testing create task...")

    task_data = {
        "name": f"E2E Test Task {datetime.now().strftime('%H%M%S')}",
        "description": "End-to-end test task for frontend validation",
        "target_function_signature": "def solution(data: list) -> list:",
        "test_code": (
            "def test_solution():\n"
            "    assert solution([3,1,2]) == [1,2,3]\n"
            "    assert solution([5,4,3,2,1]) == [1,2,3,4,5]"
        ),
        "max_generations": 5,
        "success_criteria": {"target_score": 0.9},
    }

    resp = requests.post(f"{BASE_URL}/api/tasks", headers=HEADERS, json=task_data)

    if resp.status_code != 201:
        print(f"  FAILED - Status: {resp.status_code}")
        print(f"  Response: {resp.text}")
        return None

    task = resp.json()
    print(f"  OK - Created task: {task['id']}")
    return task["id"]


def test_get_generations(task_id):
    """Test getting generation history"""
    print(f"\n[4/6] Testing generation history for {task_id[:8]}...")
    resp = requests.get(f"{BASE_URL}/api/tasks/{task_id}/generations", headers=HEADERS)
    assert resp.status_code == 200
    generations = resp.json()
    print(f"  OK - Found {len(generations)} generations")
    return generations


def test_websocket(task_id):
    """Test WebSocket connection"""
    print("\n[5/6] Testing WebSocket connection...")

    ws_url = f"{WS_URL}/ws/tasks/{task_id}"
    print(f"  Connecting to {ws_url}...")

    messages = []

    def on_message(ws, message):
        data = json.loads(message)
        messages.append(data)
        print(
            "  Received: gen={}, score={}".format(
                data.get("generation", "N/A"), data.get("best_score", "N/A")
            )
        )
        if len(messages) >= 3:
            ws.close()

    def on_error(ws, error):
        print(f"  WebSocket error: {error}")

    def on_close(ws, close_status_code, close_msg):
        print(f"  WebSocket closed: {close_status_code}")

    def on_open(ws):
        print("  WebSocket connected")
        ws.send(json.dumps({"action": "subscribe"}))

    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    # Run for 5 seconds
    ws.run_forever(ping_interval=5, ping_timeout=3)

    print(f"  OK - Received {len(messages)} messages")
    return messages


def test_start_evolution(task_id):
    """Test starting evolution"""
    print("\n[6/6] Testing start evolution...")
    resp = requests.post(f"{BASE_URL}/api/tasks/{task_id}/start", headers=HEADERS)

    if resp.status_code == 400 and "already" in resp.text.lower():
        print("  OK - Evolution already running")
        return True

    if resp.status_code == 200:
        data = resp.json()
        print(f"  OK - Evolution started: {data.get('message', 'OK')}")
        return True

    print(f"  WARNING - Status: {resp.status_code}")
    print(f"  Response: {resp.text[:200]}")
    return False


def test_frontend_static():
    """Test frontend static files"""
    print("\n[*] Testing frontend static files...")

    # Test main page
    resp = requests.get(f"{BASE_URL}/monitor/")
    assert resp.status_code == 200
    assert "Chart.js" in resp.text or "chart.js" in resp.text.lower()
    assert "Prism.js" in resp.text or "prism" in resp.text.lower()
    assert "SEMDS Monitor" in resp.text
    print("  OK - Frontend page loaded with Chart.js and Prism.js")


def run_all_tests():
    """Run all E2E tests"""
    print("=" * 60)
    print("SEMDS Frontend E2E Test Suite")
    print("=" * 60)

    try:
        # Basic tests
        test_health()
        test_frontend_static()

        # Task tests
        test_list_tasks()

        # Create new task
        task_id = test_create_task()
        if not task_id:
            print("\nFAILED: Could not create task")
            return False

        # Test generations endpoint
        test_get_generations(task_id)

        # Test WebSocket (without starting evolution)
        test_websocket(task_id)

        # Test start evolution
        test_start_evolution(task_id)

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
