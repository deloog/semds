"""
SEMDS Storage Models

SQLAlchemy数据模型定义，对应规格文档第六章。

本模块提供：
- Task: 任务模型
- Generation: 进化代模型
- StrategyState: 策略状态模型（Phase 3使用）
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid() -> str:
    """生成UUID字符串。"""
    return str(uuid.uuid4())


def get_current_timestamp() -> datetime:
    """获取当前UTC时间。"""
    return datetime.now(timezone.utc)


class Task(Base):  # type: ignore[misc, valid-type]
    """
    任务模型，存储进化任务的元信息。

    对应规格文档6.1节。

    Attributes:
        id: UUID主键
        name: 任务名称（如"calculator_evolution"）
        description: 自然语言描述
        target_function_signature: 目标函数签名
        test_file_path: 测试文件路径
        status: 任务状态
        current_generation: 当前代数
        best_score: 历史最高分
        best_generation_id: 最高分对应的代ID
        owner_id: 任务所有者用户ID
        created_at: 创建时间
        updated_at: 更新时间
    """

    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    target_function_signature = Column(String(500), nullable=True)
    test_file_path = Column(String(500), nullable=True)
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="pending | running | paused | success | failed | aborted",
    )
    current_generation = Column(Integer, nullable=False, default=0)
    best_score = Column(Float, nullable=True)
    best_generation_id = Column(String(36), nullable=True)
    owner_id = Column(String(36), nullable=True, index=True, comment="任务所有者用户ID")
    created_at = Column(DateTime, nullable=False, default=get_current_timestamp)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=get_current_timestamp,
        onupdate=get_current_timestamp,
    )

    # 关系
    generations = relationship(
        "Generation", back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, name={self.name}, status={self.status})>"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典表示。"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "target_function_signature": self.target_function_signature,
            "test_file_path": self.test_file_path,
            "status": self.status,
            "current_generation": self.current_generation,
            "best_score": self.best_score,
            "best_generation_id": self.best_generation_id,
            "owner_id": self.owner_id,
            "created_at": (self.created_at.isoformat() if self.created_at else None),
            "updated_at": (self.updated_at.isoformat() if self.updated_at else None),
        }


class Generation(Base):  # type: ignore[misc, valid-type]
    """
    进化代模型，存储每一代进化的详细结果。

    对应规格文档6.2节。

    Attributes:
        id: UUID主键
        task_id: 外键，关联Task
        gen_number: 代数编号（0, 1, 2...）
        code: 生成的代码
        strategy_used: 使用的策略配置（JSON）
        intrinsic_score: 内生分（测试通过率）
        extrinsic_score: 外生分（一致性验证）
        final_score: 综合分
        test_pass_rate: 测试通过率
        test_results: 各测试用例结果（JSON）
        execution_time_ms: 执行时间（毫秒）
        sandbox_logs: 沙盒输出日志
        goodhart_flag: 是否触发Goodhart检测
        human_reviewed: 是否经过人类审查
        git_commit_hash: Git提交哈希
        created_at: 创建时间
    """

    __tablename__ = "generations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gen_number = Column(Integer, nullable=False)
    code = Column(Text, nullable=True)
    strategy_used = Column(JSON, nullable=True)

    # 双轨评分
    intrinsic_score = Column(Float, nullable=True, comment="内生分（测试通过率）")
    extrinsic_score = Column(Float, nullable=True, comment="外生分（一致性验证）")
    final_score = Column(Float, nullable=True, comment="综合分")

    # 执行细节
    test_pass_rate = Column(Float, nullable=True)
    test_results = Column(JSON, nullable=True, comment="各测试用例结果")
    execution_time_ms = Column(Float, nullable=True)
    sandbox_logs = Column(Text, nullable=True)

    # 状态标记
    goodhart_flag = Column(Boolean, nullable=False, default=False)
    human_reviewed = Column(Boolean, nullable=False, default=False)

    # 版本控制
    git_commit_hash = Column(String(40), nullable=True)

    created_at = Column(DateTime, nullable=False, default=get_current_timestamp)

    # 关系
    task = relationship("Task", back_populates="generations")

    # 唯一约束：每个任务的代数唯一
    __table_args__ = (
        # 注意：这里使用字符串方式避免某些SQLAlchemy版本的兼容问题
        {"sqlite_autoincrement": False},
    )

    def __repr__(self) -> str:
        return (
            f"<Generation(id={self.id}, "
            f"task_id={self.task_id}, "
            f"gen={self.gen_number})>"
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典表示。"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "gen_number": self.gen_number,
            "code": self.code,
            "strategy_used": self.strategy_used,
            "intrinsic_score": self.intrinsic_score,
            "extrinsic_score": self.extrinsic_score,
            "final_score": self.final_score,
            "test_pass_rate": self.test_pass_rate,
            "test_results": self.test_results,
            "execution_time_ms": self.execution_time_ms,
            "sandbox_logs": self.sandbox_logs,
            "goodhart_flag": self.goodhart_flag,
            "human_reviewed": self.human_reviewed,
            "git_commit_hash": self.git_commit_hash,
            "created_at": (self.created_at.isoformat() if self.created_at else None),
        }


class ApprovalRequest(Base):  # type: ignore[misc, valid-type]
    """
    审批请求模型，存储需要人工审批的代码进化请求。

    对应规格文档审批流程章节。

    Attributes:
        id: UUID主键
        task_id: 关联的任务ID
        generation_id: 关联的进化代ID
        code: 需要审批的代码
        reason: 需要审批的原因
        status: 审批状态
        created_at: 创建时间
        reviewed_at: 审核时间
        reviewer_comment: 审核意见
    """

    __tablename__ = "approval_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), nullable=False, index=True)
    generation_id = Column(String(36), nullable=False, index=True)
    code = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="pending | approved | rejected",
    )
    created_at = Column(DateTime, nullable=False, default=get_current_timestamp)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_comment = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ApprovalRequest(id={self.id}, "
            f"task_id={self.task_id}, "
            f"status={self.status})>"
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典表示。"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "generation_id": self.generation_id,
            "code": self.code,
            "reason": self.reason,
            "status": self.status,
            "created_at": (self.created_at.isoformat() if self.created_at else None),
            "reviewed_at": (self.reviewed_at.isoformat() if self.reviewed_at else None),
            "reviewer_comment": self.reviewer_comment,
        }


class StrategyState(Base):  # type: ignore[misc, valid-type]
    """
    策略状态模型，存储Thompson Sampling的状态。

    对应规格文档6.3节。

    Phase 3使用，Phase 1保留模型定义但不使用。

    Attributes:
        task_id: 任务ID（复合主键的一部分）
        strategy_key: 策略组合的唯一键（复合主键的一部分）
        alpha: Thompson Sampling成功计数
        beta: Thompson Sampling失败计数
        total_uses: 总使用次数
        last_used: 最后使用时间
    """

    __tablename__ = "strategy_states"

    task_id = Column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    strategy_key = Column(String(255), primary_key=True)
    alpha = Column(Float, nullable=False, default=1.0)
    beta = Column(Float, nullable=False, default=1.0)
    total_uses = Column(Integer, nullable=False, default=0)
    last_used = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<StrategyState(task_id={self.task_id}, " f"key={self.strategy_key})>"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典表示。"""
        return {
            "task_id": self.task_id,
            "strategy_key": self.strategy_key,
            "alpha": self.alpha,
            "beta": self.beta,
            "total_uses": self.total_uses,
            "last_used": (self.last_used.isoformat() if self.last_used else None),
        }


if __name__ == "__main__":
    # 简单测试
    from storage.database import init_database
    from storage.database import get_session as _get_session

    # 初始化数据库
    init_database()

    # 获取会话
    with _get_session() as session:  # type: ignore
        # 创建测试任务
        task = Task(
            name="test_task",
            description="A test task",
            target_function_signature="def test():",
            status="pending",
        )

        session.add(task)
        session.commit()

        print(f"Created task: {task.id}")

    # 创建测试代
    gen = Generation(
        task_id=task.id,
        gen_number=0,
        code="def test(): pass",
        intrinsic_score=0.8,
        test_pass_rate=0.8,
    )

    session.add(gen)
    session.commit()

    print(f"Created generation: {gen.id}")

    # 查询
    tasks = session.query(Task).all()
    print(f"Total tasks: {len(tasks)}")

    session.close()
