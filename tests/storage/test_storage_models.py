"""Tests for storage/models.py

测试Task, Generation, StrategyState模型。
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import inspect

from storage.models import (
    Base,
    Generation,
    StrategyState,
    Task,
    generate_uuid,
    get_current_timestamp,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class TestUUIDAndTimestamp:
    """测试UUID和时间戳生成函数"""

    def test_generate_uuid_returns_valid_uuid(self):
        """测试generate_uuid返回有效的UUID字符串"""
        uuid_str = generate_uuid()

        # 验证格式: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        assert isinstance(uuid_str, str)
        assert len(uuid_str) == 36
        parts = uuid_str.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

    def test_generate_uuid_returns_unique_values(self):
        """测试generate_uuid返回唯一值"""
        uuids = {generate_uuid() for _ in range(100)}
        assert len(uuids) == 100

    def test_get_current_timestamp_returns_datetime(self):
        """测试get_current_timestamp返回datetime对象"""
        ts = get_current_timestamp()
        assert isinstance(ts, datetime)

    def test_get_current_timestamp_is_utc(self):
        """测试get_current_timestamp返回UTC时间"""
        from datetime import timezone

        ts = get_current_timestamp()
        assert ts.tzinfo == timezone.utc  # 返回带时区的datetime


class TestTaskModel:
    """测试Task模型"""

    def test_task_creation_with_defaults(self, db_session: "Session"):
        """测试使用默认值创建Task"""
        task = Task(name="test_task")
        db_session.add(task)
        db_session.commit()

        assert task.id is not None
        assert len(task.id) == 36  # UUID格式
        assert task.name == "test_task"
        assert task.status == "pending"
        assert task.current_generation == 0
        assert task.best_score is None
        assert task.best_generation_id is None
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_task_creation_with_all_fields(self, db_session: "Session"):
        """测试使用所有字段创建Task"""
        task = Task(
            name="calculator_evolution",
            description="Evolve a calculator function",
            target_function_signature=(
                "def calculate(a: float, b: float, op: str) -> float"
            ),
            test_file_path="tests/test_calculator.py",
            status="running",
            current_generation=5,
            best_score=0.95,
            best_generation_id="gen-uuid-123",
        )
        db_session.add(task)
        db_session.commit()

        # 重新查询验证持久化
        result = db_session.query(Task).filter_by(name="calculator_evolution").first()
        assert result is not None
        assert result.description == "Evolve a calculator function"
        assert (
            result.target_function_signature
            == "def calculate(a: float, b: float, op: str) -> float"
        )
        assert result.test_file_path == "tests/test_calculator.py"
        assert result.status == "running"
        assert result.current_generation == 5
        assert result.best_score == 0.95
        assert result.best_generation_id == "gen-uuid-123"

    def test_task_status_values(self, db_session: "Session"):
        """测试Task支持的各种状态值"""
        statuses = ["pending", "running", "paused", "success", "failed", "aborted"]

        for status in statuses:
            task = Task(name=f"task_{status}", status=status)
            db_session.add(task)

        db_session.commit()

        for status in statuses:
            task = db_session.query(Task).filter_by(name=f"task_{status}").first()
            assert task is not None
            assert task.status == status

    def test_task_repr(self, db_session: "Session"):
        """测试Task的__repr__方法"""
        task = Task(name="test_task", status="running")
        db_session.add(task)
        db_session.commit()

        repr_str = repr(task)
        assert "Task" in repr_str
        assert task.id in repr_str
        assert "test_task" in repr_str
        assert "running" in repr_str

    def test_task_to_dict(self, db_session: "Session"):
        """测试Task的to_dict方法"""
        task = Task(
            name="test_task",
            description="Test description",
            status="success",
            current_generation=10,
            best_score=0.99,
        )
        db_session.add(task)
        db_session.commit()

        task_dict = task.to_dict()

        assert isinstance(task_dict, dict)
        assert task_dict["id"] == task.id
        assert task_dict["name"] == "test_task"
        assert task_dict["description"] == "Test description"
        assert task_dict["target_function_signature"] is None
        assert task_dict["test_file_path"] is None
        assert task_dict["status"] == "success"
        assert task_dict["current_generation"] == 10
        assert task_dict["best_score"] == 0.99
        assert task_dict["best_generation_id"] is None
        assert isinstance(task_dict["created_at"], str)
        assert isinstance(task_dict["updated_at"], str)

    def test_task_to_dict_datetime_format(self, db_session: "Session"):
        """测试Task的to_dict方法中datetime的ISO格式"""
        task = Task(name="test_task")
        db_session.add(task)
        db_session.commit()

        task_dict = task.to_dict()

        # 验证ISO格式: 2024-01-01T00:00:00
        created_at = task_dict["created_at"]
        assert "T" in created_at
        # 解析验证
        parsed = datetime.fromisoformat(created_at)
        assert isinstance(parsed, datetime)

    def test_task_name_not_nullable(self, db_session: "Session"):
        """测试Task的name字段不能为null"""
        task = Task(name=None)  # type: ignore[arg-type]
        db_session.add(task)

        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()


class TestGenerationModel:
    """测试Generation模型"""

    @pytest.fixture
    def sample_task(self, db_session: "Session") -> Task:
        """创建示例Task用于测试"""
        task = Task(name="test_task", description="For generation tests")
        db_session.add(task)
        db_session.commit()
        return task

    def test_generation_creation_with_defaults(
        self, db_session: "Session", sample_task: Task
    ):
        """测试使用默认值创建Generation"""
        gen = Generation(
            task_id=sample_task.id,
            gen_number=0,
        )
        db_session.add(gen)
        db_session.commit()

        assert gen.id is not None
        assert len(gen.id) == 36
        assert gen.task_id == sample_task.id
        assert gen.gen_number == 0
        assert gen.code is None
        assert gen.strategy_used is None
        assert gen.intrinsic_score is None
        assert gen.extrinsic_score is None
        assert gen.final_score is None
        assert gen.goodhart_flag is False
        assert gen.human_reviewed is False
        assert gen.created_at is not None

    def test_generation_creation_with_all_fields(
        self, db_session: "Session", sample_task: Task
    ):
        """测试使用所有字段创建Generation"""
        gen = Generation(
            task_id=sample_task.id,
            gen_number=1,
            code="def calculate(a, b, op): return a + b",
            strategy_used={"temperature": 0.7, "model": "claude"},
            intrinsic_score=0.85,
            extrinsic_score=0.90,
            final_score=0.87,
            test_pass_rate=0.85,
            test_results={"test_add": True, "test_sub": False},
            execution_time_ms=150.5,
            sandbox_logs="Test execution log",
            goodhart_flag=True,
            human_reviewed=True,
            git_commit_hash="abc123def456",
        )
        db_session.add(gen)
        db_session.commit()

        # 重新查询验证
        result = (
            db_session.query(Generation)
            .filter_by(task_id=sample_task.id, gen_number=1)
            .first()
        )
        assert result is not None
        assert result.code == "def calculate(a, b, op): return a + b"
        assert result.strategy_used == {"temperature": 0.7, "model": "claude"}
        assert result.intrinsic_score == 0.85
        assert result.extrinsic_score == 0.90
        assert result.final_score == 0.87
        assert result.test_pass_rate == 0.85
        assert result.test_results == {"test_add": True, "test_sub": False}
        assert result.execution_time_ms == 150.5
        assert result.sandbox_logs == "Test execution log"
        assert result.goodhart_flag is True
        assert result.human_reviewed is True
        assert result.git_commit_hash == "abc123def456"

    def test_generation_repr(self, db_session: "Session", sample_task: Task):
        """测试Generation的__repr__方法"""
        gen = Generation(
            task_id=sample_task.id,
            gen_number=5,
        )
        db_session.add(gen)
        db_session.commit()

        repr_str = repr(gen)
        assert "Generation" in repr_str
        assert gen.id in repr_str
        assert sample_task.id in repr_str
        assert "gen=5" in repr_str

    def test_generation_to_dict(self, db_session: "Session", sample_task: Task):
        """测试Generation的to_dict方法"""
        gen = Generation(
            task_id=sample_task.id,
            gen_number=2,
            code="def test(): pass",
            intrinsic_score=1.0,
            strategy_used={"temp": 0.5},
            test_results={"passed": 10, "failed": 0},
        )
        db_session.add(gen)
        db_session.commit()

        gen_dict = gen.to_dict()

        assert isinstance(gen_dict, dict)
        assert gen_dict["id"] == gen.id
        assert gen_dict["task_id"] == sample_task.id
        assert gen_dict["gen_number"] == 2
        assert gen_dict["code"] == "def test(): pass"
        assert gen_dict["intrinsic_score"] == 1.0
        assert gen_dict["strategy_used"] == {"temp": 0.5}
        assert gen_dict["test_results"] == {"passed": 10, "failed": 0}
        assert gen_dict["goodhart_flag"] is False
        assert gen_dict["human_reviewed"] is False
        assert isinstance(gen_dict["created_at"], str)

    def test_generation_multiple_per_task(
        self, db_session: "Session", sample_task: Task
    ):
        """测试一个Task可以有多个Generation"""
        for i in range(5):
            gen = Generation(
                task_id=sample_task.id,
                gen_number=i,
                code=f"# Generation {i}",
            )
            db_session.add(gen)
        db_session.commit()

        gens = db_session.query(Generation).filter_by(task_id=sample_task.id).all()
        assert len(gens) == 5

    def test_generation_task_id_not_nullable(self, db_session: "Session"):
        """测试Generation的task_id字段不能为null"""
        gen = Generation(task_id=None, gen_number=0)  # type: ignore[arg-type]
        db_session.add(gen)

        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()


class TestStrategyStateModel:
    """测试StrategyState模型"""

    @pytest.fixture
    def sample_task(self, db_session: "Session") -> Task:
        """创建示例Task用于测试"""
        task = Task(name="test_task")
        db_session.add(task)
        db_session.commit()
        return task

    def test_strategy_state_creation_with_defaults(
        self, db_session: "Session", sample_task: Task
    ):
        """测试使用默认值创建StrategyState"""
        state = StrategyState(
            task_id=sample_task.id,
            strategy_key="temperature_0.7",
        )
        db_session.add(state)
        db_session.commit()

        assert state.task_id == sample_task.id
        assert state.strategy_key == "temperature_0.7"
        assert state.alpha == 1.0
        assert state.beta == 1.0
        assert state.total_uses == 0
        assert state.last_used is None

    def test_strategy_state_creation_with_all_fields(
        self, db_session: "Session", sample_task: Task
    ):
        """测试使用所有字段创建StrategyState"""
        now = datetime.now(timezone.utc)
        state = StrategyState(
            task_id=sample_task.id,
            strategy_key="model_claude_temp_0.5",
            alpha=5.0,
            beta=2.0,
            total_uses=10,
            last_used=now,
        )
        db_session.add(state)
        db_session.commit()

        # 重新查询验证
        result = (
            db_session.query(StrategyState)
            .filter_by(task_id=sample_task.id, strategy_key="model_claude_temp_0.5")
            .first()
        )
        assert result is not None
        assert result.alpha == 5.0
        assert result.beta == 2.0
        assert result.total_uses == 10
        # 数据库可能丢失微秒精度
        assert result.last_used is not None

    def test_strategy_state_repr(self, db_session: "Session", sample_task: Task):
        """测试StrategyState的__repr__方法"""
        state = StrategyState(
            task_id=sample_task.id,
            strategy_key="test_strategy",
        )
        db_session.add(state)
        db_session.commit()

        repr_str = repr(state)
        assert "StrategyState" in repr_str
        assert sample_task.id in repr_str
        assert "test_strategy" in repr_str

    def test_strategy_state_to_dict(self, db_session: "Session", sample_task: Task):
        """测试StrategyState的to_dict方法"""
        state = StrategyState(
            task_id=sample_task.id,
            strategy_key="my_strategy",
            alpha=3.0,
            beta=1.0,
            total_uses=5,
        )
        db_session.add(state)
        db_session.commit()

        state_dict = state.to_dict()

        assert isinstance(state_dict, dict)
        assert state_dict["task_id"] == sample_task.id
        assert state_dict["strategy_key"] == "my_strategy"
        assert state_dict["alpha"] == 3.0
        assert state_dict["beta"] == 1.0
        assert state_dict["total_uses"] == 5
        assert state_dict["last_used"] is None

    def test_strategy_state_to_dict_with_last_used(
        self, db_session: "Session", sample_task: Task
    ):
        """测试StrategyState的to_dict方法包含last_used"""
        from datetime import datetime

        now = datetime(2024, 1, 15, 10, 30, 0)

        state = StrategyState(
            task_id=sample_task.id,
            strategy_key="timed_strategy",
            last_used=now,
        )
        db_session.add(state)
        db_session.commit()

        state_dict = state.to_dict()

        assert state_dict["last_used"] == "2024-01-15T10:30:00"

    def test_strategy_state_composite_key(
        self, db_session: "Session", sample_task: Task
    ):
        """测试StrategyState的复合主键"""
        # 同一个task_id可以有多个不同的strategy_key
        state1 = StrategyState(task_id=sample_task.id, strategy_key="key1")
        state2 = StrategyState(task_id=sample_task.id, strategy_key="key2")
        db_session.add(state1)
        db_session.add(state2)
        db_session.commit()

        states = db_session.query(StrategyState).filter_by(task_id=sample_task.id).all()
        assert len(states) == 2

    def test_strategy_state_same_key_different_task(self, db_session: "Session"):
        """测试不同task可以使用相同的strategy_key"""
        task1 = Task(name="task1")
        task2 = Task(name="task2")
        db_session.add(task1)
        db_session.add(task2)
        db_session.commit()

        state1 = StrategyState(task_id=task1.id, strategy_key="shared_key")
        state2 = StrategyState(task_id=task2.id, strategy_key="shared_key")
        db_session.add(state1)
        db_session.add(state2)
        db_session.commit()

        states = (
            db_session.query(StrategyState).filter_by(strategy_key="shared_key").all()
        )
        assert len(states) == 2

    def test_strategy_state_duplicate_key_raises(
        self, db_session: "Session", sample_task: Task
    ):
        """测试重复的复合主键会报错"""
        state1 = StrategyState(task_id=sample_task.id, strategy_key="duplicate_key")
        state2 = StrategyState(task_id=sample_task.id, strategy_key="duplicate_key")
        db_session.add(state1)
        db_session.commit()

        db_session.add(state2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()


class TestModelRelationships:
    """测试模型间的关系"""

    def test_task_generations_relationship(self, db_session: "Session"):
        """测试Task和Generation的关系"""
        task = Task(name="test_task")
        db_session.add(task)
        db_session.commit()

        # 创建关联的generations
        for i in range(3):
            gen = Generation(
                task_id=task.id,
                gen_number=i,
                code=f"# Gen {i}",
            )
            db_session.add(gen)
        db_session.commit()

        # 通过关系访问
        task = db_session.query(Task).filter_by(id=task.id).first()
        assert len(task.generations) == 3
        for i, gen in enumerate(sorted(task.generations, key=lambda g: g.gen_number)):
            assert gen.gen_number == i
            assert gen.code == f"# Gen {i}"

    def test_generation_task_relationship(self, db_session: "Session"):
        """测试Generation的task关系"""
        task = Task(name="test_task")
        db_session.add(task)
        db_session.commit()

        gen = Generation(
            task_id=task.id,
            gen_number=0,
        )
        db_session.add(gen)
        db_session.commit()

        # 通过关系访问
        gen = db_session.query(Generation).filter_by(id=gen.id).first()
        assert gen.task is not None
        assert gen.task.id == task.id
        assert gen.task.name == "test_task"

    def test_task_cascade_delete_generations(self, db_session: "Session"):
        """测试删除Task时级联删除Generations"""
        task = Task(name="test_task")
        db_session.add(task)
        db_session.commit()

        # 创建generations
        for i in range(3):
            gen = Generation(task_id=task.id, gen_number=i)
            db_session.add(gen)
        db_session.commit()

        # 验证generations存在
        gens_before = db_session.query(Generation).filter_by(task_id=task.id).all()
        assert len(gens_before) == 3

        # 删除task
        db_session.delete(task)
        db_session.commit()

        # 验证generations被级联删除
        gens_after = db_session.query(Generation).filter_by(task_id=task.id).all()
        assert len(gens_after) == 0

    def test_task_delete_with_strategy_states(self, db_session: "Session"):
        """测试删除Task时手动清理StrategyStates（模型未定义级联关系）"""
        task = Task(name="test_task")
        db_session.add(task)
        db_session.commit()

        # 创建strategy states
        for i in range(2):
            state = StrategyState(
                task_id=task.id,
                strategy_key=f"key_{i}",
            )
            db_session.add(state)
        db_session.commit()

        # 验证states存在
        states_before = db_session.query(StrategyState).filter_by(task_id=task.id).all()
        assert len(states_before) == 2

        # 手动删除关联的StrategyStates（因为Task模型没有定义relationship）
        for state in states_before:
            db_session.delete(state)
        db_session.flush()

        # 删除task
        db_session.delete(task)
        db_session.commit()

        # 验证task和states都被删除
        task_after = db_session.query(Task).filter_by(id=task.id).first()
        states_after = db_session.query(StrategyState).filter_by(task_id=task.id).all()
        assert task_after is None
        assert len(states_after) == 0


class TestModelBase:
    """测试模型的基础功能"""

    def test_base_metadata_tables(self):
        """测试Base.metadata包含所有表"""
        tables = Base.metadata.tables

        assert "tasks" in tables
        assert "generations" in tables
        assert "strategy_states" in tables

    def test_tables_have_columns(self):
        """测试各表有正确的列"""
        # Task表
        task_columns = {c.name for c in Base.metadata.tables["tasks"].columns}
        expected_task_cols = {
            "id",
            "name",
            "description",
            "target_function_signature",
            "test_file_path",
            "status",
            "current_generation",
            "best_score",
            "best_generation_id",
            "owner_id",
            "created_at",
            "updated_at",
        }
        assert task_columns == expected_task_cols

        # Generation表
        gen_columns = {c.name for c in Base.metadata.tables["generations"].columns}
        expected_gen_cols = {
            "id",
            "task_id",
            "gen_number",
            "code",
            "strategy_used",
            "intrinsic_score",
            "extrinsic_score",
            "final_score",
            "test_pass_rate",
            "test_results",
            "execution_time_ms",
            "sandbox_logs",
            "goodhart_flag",
            "human_reviewed",
            "git_commit_hash",
            "created_at",
        }
        assert gen_columns == expected_gen_cols

        # StrategyState表
        state_columns = {
            c.name for c in Base.metadata.tables["strategy_states"].columns
        }
        expected_state_cols = {
            "task_id",
            "strategy_key",
            "alpha",
            "beta",
            "total_uses",
            "last_used",
        }
        assert state_columns == expected_state_cols

    def test_task_table_indexes(self, db_session: "Session"):
        """测试Task表的索引"""
        inspector = inspect(db_session.bind)
        indexes = inspector.get_indexes("tasks")
        # 应该有name字段的索引
        assert any("name" in idx["column_names"] for idx in indexes if idx["name"])

    def test_generation_table_indexes(self, db_session: "Session"):
        """测试Generation表的索引"""
        inspector = inspect(db_session.bind)
        indexes = inspector.get_indexes("generations")

        # 应该有task_id字段的索引
        assert any("task_id" in idx["column_names"] for idx in indexes if idx["name"])

    def test_generation_foreign_key(self):
        """测试Generation的外键约束"""
        table = Base.metadata.tables["generations"]
        fks = list(table.foreign_keys)

        assert len(fks) == 1
        fk = fks[0]
        assert fk.column.table.name == "tasks"
        assert fk.column.name == "id"
        assert fk.ondelete == "CASCADE"

    def test_strategy_state_foreign_key(self):
        """测试StrategyState的外键约束"""
        table = Base.metadata.tables["strategy_states"]
        fks = list(table.foreign_keys)

        assert len(fks) == 1
        fk = fks[0]
        assert fk.column.table.name == "tasks"
        assert fk.column.name == "id"
        assert fk.ondelete == "CASCADE"

    def test_task_primary_key(self):
        """测试Task的主键"""
        table = Base.metadata.tables["tasks"]
        pk = table.primary_key

        assert len(pk.columns) == 1
        assert pk.columns.keys()[0] == "id"

    def test_generation_primary_key(self):
        """测试Generation的主键"""
        table = Base.metadata.tables["generations"]
        pk = table.primary_key

        assert len(pk.columns) == 1
        assert pk.columns.keys()[0] == "id"

    def test_strategy_state_primary_key(self):
        """测试StrategyState的复合主键"""
        table = Base.metadata.tables["strategy_states"]
        pk = table.primary_key

        assert len(pk.columns) == 2
        col_names = {c.name for c in pk.columns}
        assert col_names == {"task_id", "strategy_key"}
