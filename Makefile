.PHONY: help install install-dev test test-unit test-integration test-cov lint format check docker-up docker-down clean demo demo-phase1 demo-phase2 demo-phase3 demo-phase4 demo-phase5 docs

PYTHON := python
PIP := pip
DOCKER_COMPOSE := docker-compose

# ============================================================================
# 帮助
# ============================================================================
help:
	@echo "SEMDS - Self-Evolving Meta-Development System"
	@echo ""
	@echo "可用命令:"
	@echo "  make install         - 安装依赖"
	@echo "  make install-dev     - 安装开发依赖"
	@echo "  make test            - 运行所有测试"
	@echo "  make test-unit       - 运行单元测试"
	@echo "  make test-integration - 运行集成测试"
	@echo "  make test-cov        - 运行测试并生成覆盖率报告"
	@echo "  make lint            - 运行代码检查 (black, isort, mypy, flake8)"
	@echo "  make format          - 自动格式化代码"
	@echo "  make check           - 运行所有检查 (lint + test)"
	@echo "  make docker-up       - 启动 Docker 服务"
	@echo "  make docker-down     - 停止 Docker 服务"
	@echo "  make clean           - 清理临时文件"
	@echo "  make demo-phase1     - 运行 Phase 1 演示"
	@echo "  make demo-phase2     - 运行 Phase 2 演示 (需要 Docker)"
	@echo "  make demo-phase3     - 运行 Phase 3 演示 (完整进化循环)"
	@echo "  make demo-phase4     - 运行 Phase 4 演示 (API + 监控)"
	@echo "  make demo-phase5     - 运行 Phase 5 演示 (多任务并发)"
	@echo "  make docs            - 生成文档"

# ============================================================================
# 安装
# ============================================================================
install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"
	pre-commit install

# ============================================================================
# 测试
# ============================================================================
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v -m "not integration and not docker"

test-integration:
	pytest tests/integration/ -v -m integration

test-cov:
	pytest --cov=semds --cov-report=html --cov-report=term-missing

test-fast:
	pytest -x -n auto

# ============================================================================
# 代码质量
# ============================================================================
lint:
	@echo "Running black check..."
	black --check .
	@echo "Running isort check..."
	isort --check-only .
	@echo "Running mypy..."
	mypy core/ evolution/ storage/
	@echo "Running flake8..."
	flake8 core/ evolution/ storage/
	@echo "Running pylint..."
	pylint core/ evolution/ storage/ --exit-zero

format:
	@echo "Formatting with black..."
	black .
	@echo "Formatting with isort..."
	isort .

check: lint test
	@echo "All checks passed!"

# ============================================================================
# Docker
# ============================================================================
docker-up:
	$(DOCKER_COMPOSE) up -d

docker-down:
	$(DOCKER_COMPOSE) down

docker-build:
	$(DOCKER_COMPOSE) build

docker-logs:
	$(DOCKER_COMPOSE) logs -f

# ============================================================================
# 演示
# ============================================================================
demo-phase1:
	@echo "Running Phase 1 Demo: Core Skeleton"
	$(PYTHON) demo_phase1.py

demo-phase2:
	@echo "Running Phase 2 Demo: Docker Sandbox"
	$(PYTHON) demo_phase2.py

demo-phase3:
	@echo "Running Phase 3 Demo: Evolution Loop"
	$(PYTHON) demo_phase3.py

demo-phase4:
	@echo "Running Phase 4 Demo: API + Monitor"
	@echo "Starting FastAPI server..."
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

demo-phase5:
	@echo "Running Phase 5 Demo: Multi-task Concurrency"
	$(PYTHON) demo_phase5.py

# ============================================================================
# 清理
# ============================================================================
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ build/ dist/ .tox/

clean-all: clean
	rm -rf .venv/
	rm -rf semds.db

# ============================================================================
# 文档
# ============================================================================
docs:
	mkdocs serve

docs-build:
	mkdocs build

# ============================================================================
# 数据库
# ============================================================================
db-init:
	alembic init migrations

db-migrate:
	alembic revision --autogenerate -m "$(message)"

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

# ============================================================================
# 实用工具
# ============================================================================
shell:
	ipython

env:
	@echo "Checking environment..."
	@$(PYTHON) --version
	@$(PYTHON) -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
	@$(PYTHON) -c "import docker; print(f'Docker SDK: {docker.__version__}')"
	@$(DOCKER_COMPOSE) --version || echo "Docker Compose not found"

update-deps:
	$(PIP) install --upgrade -e ".[dev]"
