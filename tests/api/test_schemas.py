"""测试Pydantic数据模型"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError


class TestTaskStatusEnum:
    """任务状态枚举测试"""

    def test_task_status_enum_values(self):
        """任务状态枚举应有正确的值"""
        from api.schemas import TaskStatus

        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.PAUSED == "paused"
        assert TaskStatus.SUCCESS == "success"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.ABORTED == "aborted"


class TestTaskCreateSchema:
    """任务创建模型测试"""

    def test_valid_task_create_parses_correctly(self):
        """有效数据应正确解析"""
        from api.schemas import TaskCreate

        data = {
            "name": "test_task",
            "description": "测试任务",
            "target_function_signature": "def calculate(a, b):",
            "test_code": "def test(): pass",
        }

        task = TaskCreate(**data)

        assert task.name == "test_task"
        assert task.description == "测试任务"
        assert task.target_function_signature == "def calculate(a, b):"
        assert task.test_code == "def test(): pass"
        assert task.success_criteria == {}
        assert task.max_generations == 50

    def test_empty_name_raises_validation_error(self):
        """空名称应触发验证错误"""
        from api.schemas import TaskCreate

        with pytest.raises(ValidationError):
            TaskCreate(name="", description="test", test_code="pass")

    def test_name_too_long_raises_validation_error(self):
        """名称过长应触发验证错误"""
        from api.schemas import TaskCreate

        with pytest.raises(ValidationError):
            TaskCreate(name="x" * 101, description="test", test_code="pass")

    def test_max_generations_boundary(self):
        """max_generations应在1-100范围内"""
        from api.schemas import TaskCreate

        base_data = {
            "name": "test",
            "description": "test",
            "target_function_signature": "def test():",
            "test_code": "pass",
        }

        # 有效边界
        task = TaskCreate(**{**base_data, "max_generations": 1})
        assert task.max_generations == 1

        task = TaskCreate(**{**base_data, "max_generations": 100})
        assert task.max_generations == 100

        # 无效边界
        with pytest.raises(ValidationError):
            TaskCreate(**{**base_data, "max_generations": 0})

        with pytest.raises(ValidationError):
            TaskCreate(**{**base_data, "max_generations": 101})

    def test_test_code_length_boundary(self):
        """test_code应在1-50000字符范围内"""
        from api.schemas import TaskCreate

        base_data = {
            "name": "test",
            "description": "test",
            "target_function_signature": "def test():",
        }

        # 空字符串应失败
        with pytest.raises(ValidationError):
            TaskCreate(**{**base_data, "test_code": ""})

        # 1字符应成功
        task = TaskCreate(**{**base_data, "test_code": "x"})
        assert len(task.test_code) == 1

        # 50000字符应成功
        long_code = "x" * 50000
        task = TaskCreate(**{**base_data, "test_code": long_code})
        assert len(task.test_code) == 50000

        # 50001字符应失败
        with pytest.raises(ValidationError):
            TaskCreate(**{**base_data, "test_code": "x" * 50001})


class TestTaskResponseSchema:
    """任务响应模型测试"""

    def test_task_response_serializes_correctly(self):
        """任务响应应正确序列化"""
        from api.schemas import TaskResponse, TaskStatus

        now = datetime.now(timezone.utc)
        task = TaskResponse(
            id="test-id-123",
            name="test",
            description="test desc",
            status=TaskStatus.PENDING,
            current_generation=0,
            best_score=0.0,
            created_at=now,
            updated_at=now,
        )

        data = task.model_dump()
        assert data["id"] == "test-id-123"
        assert data["name"] == "test"
        assert data["status"] == "pending"
        assert data["current_generation"] == 0
        assert data["best_score"] == 0.0


class TestEvolutionControlSchemas:
    """进化控制模型测试"""

    def test_evolution_start_requires_task_id(self):
        """启动进化请求必须包含task_id"""
        from api.schemas import EvolutionStart

        with pytest.raises(ValidationError):
            EvolutionStart()

        start = EvolutionStart(task_id="test-id")
        assert start.task_id == "test-id"

    def test_evolution_control_requires_task_id(self):
        """进化控制请求必须包含task_id"""
        from api.schemas import EvolutionControl

        with pytest.raises(ValidationError):
            EvolutionControl()

        control = EvolutionControl(task_id="test-id")
        assert control.task_id == "test-id"


class TestGenerationResponseSchema:
    """进化代响应模型测试"""

    def test_generation_response_serializes_correctly(self):
        """进化代响应应正确序列化"""
        from api.schemas import GenerationResponse

        now = datetime.now(timezone.utc)
        gen = GenerationResponse(
            id="gen-123",
            gen_number=5,
            intrinsic_score=0.85,
            extrinsic_score=0.90,
            final_score=0.87,
            goodhart_flag=False,
            created_at=now,
        )

        data = gen.model_dump()
        assert data["id"] == "gen-123"
        assert data["gen_number"] == 5
        assert data["intrinsic_score"] == 0.85
        assert data["extrinsic_score"] == 0.90
        assert data["final_score"] == 0.87
        assert data["goodhart_flag"] is False


class TestEvolutionProgressSchema:
    """进化进度模型测试"""

    def test_evolution_progress_serializes_correctly(self):
        """进化进度模型应正确序列化"""
        from api.schemas import EvolutionProgress, TaskStatus

        progress = EvolutionProgress(
            task_id="task-123",
            current_gen=10,
            max_gen=50,
            current_score=0.75,
            best_score=0.85,
            best_gen=8,
            status=TaskStatus.RUNNING,
            recent_generations=[],
        )

        data = progress.model_dump()
        assert data["task_id"] == "task-123"
        assert data["current_gen"] == 10
        assert data["max_gen"] == 50
        assert data["best_gen"] == 8
        assert data["status"] == "running"


class TestSystemStatsSchema:
    """系统统计模型测试"""

    def test_system_stats_serializes_correctly(self):
        """系统统计模型应正确序列化"""
        from api.schemas import SystemStats

        stats = SystemStats(
            total_tasks=10, active_tasks=2, completed_tasks=5, total_generations=100
        )

        data = stats.model_dump()
        assert data["total_tasks"] == 10
        assert data["active_tasks"] == 2
        assert data["completed_tasks"] == 5
        assert data["total_generations"] == 100


class TestApprovalSchemas:
    """审批相关模型测试"""

    def test_approval_response_serializes_correctly(self):
        """审批响应模型应正确序列化"""
        from api.schemas import ApprovalResponse

        now = datetime.now(timezone.utc)
        approval = ApprovalResponse(
            id="approval-123",
            task_id="task-123",
            generation_id="gen-123",
            status="pending",
            created_at=now,
        )

        data = approval.model_dump()
        assert data["id"] == "approval-123"
        assert data["status"] == "pending"

    def test_approval_create_requires_fields(self):
        """创建审批请求必须有必需字段"""
        from api.schemas import ApprovalCreate

        with pytest.raises(ValidationError):
            ApprovalCreate()

        approval = ApprovalCreate(
            task_id="task-123",
            generation_id="gen-123",
            code="def test(): pass",
            reason="需要审批",
        )
        assert approval.task_id == "task-123"

    def test_approval_review_requires_fields(self):
        """审批审核请求必须有approved字段"""
        from api.schemas import ApprovalReview

        with pytest.raises(ValidationError):
            ApprovalReview()

        review = ApprovalReview(approved=True, comment="LGTM")
        assert review.approved is True
        assert review.comment == "LGTM"

        # comment可为空
        review = ApprovalReview(approved=False)
        assert review.approved is False
        assert review.comment is None
