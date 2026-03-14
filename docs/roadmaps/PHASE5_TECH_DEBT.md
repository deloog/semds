# Phase 5 技术债务清单

**文档版本**: v1.0  
**创建时间**: 2026-03-12  
**关联文档**: PHASE4_TDD_ROADMAP.md, SEMDS_v1.1_SPEC.md

---

## 🔐 认证与授权

### 1. 用户认证机制

**优先级**: P0  
**来源**: Phase 4 代码审查

**当前状态**: ❌ 未实现

**需求描述**:
- 实现JWT Token认证或Session认证
- 登录/登出API端点
- Token刷新机制

**涉及文件**:
- `api/routers/auth.py` (新增)
- `api/middleware.py` (添加认证中间件)
- `api/dependencies.py` (添加get_current_user依赖)

**实现建议**:
```python
# 示例：认证依赖
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_session)
) -> User:
    """从JWT token获取当前用户"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
```

---

### 2. 任务级用户隔离

**优先级**: P0  
**来源**: Phase 4 代码审查

**当前状态**: ❌ 未实现（所有用户可访问所有任务）

**需求描述**:
- `Task` 模型添加 `user_id` 外键
- 所有任务查询添加 `user_id` 过滤
- 管理员角色可访问所有任务

**涉及文件**:
- `storage/models.py` (修改Task模型)
- `api/routers/tasks.py` (添加用户过滤)
- `api/routers/evolution.py` (添加权限检查)

**数据库变更**:
```python
# storage/models.py
class Task(Base):
    # ... 现有字段 ...
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="tasks")
```

**代码变更示例**:
```python
# api/routers/tasks.py
@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    status: TaskStatus = None,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)  # 新增
):
    """列出当前用户的所有任务"""
    query = db.query(Task).filter(Task.user_id == current_user.id)  # 添加过滤
    if status:
        query = query.filter(Task.status == status)
    return query.all()
```

---

### 3. 操作权限控制

**优先级**: P1  
**来源**: Phase 4 代码审查

**当前状态**: ❌ 未实现

**需求描述**:
- 定义角色：普通用户、管理员
- 普通用户只能操作自己的任务
- 管理员可操作所有任务
- 敏感操作（删除、中止）需要二次确认或更高权限

**涉及文件**:
- `storage/models.py` (添加User模型和角色枚举)
- `api/dependencies.py` (添加role_required依赖)

**实现建议**:
```python
# api/dependencies.py
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

def require_admin(current_user: User = Depends(get_current_user)):
    """要求管理员权限"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user

# 使用示例
@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_admin)  # 仅管理员可删除
):
    # ...
```

---

## 🔧 架构改进

### 4. 活跃进化状态持久化

**优先级**: P1  
**来源**: Phase 4 代码审查 (api/routers/evolution.py)

**当前状态**: ⚠️ 内存存储 (重启丢失)

**当前代码**:
```python
# 内存状态，重启丢失
active_evolutions: Set[str] = set()
```

**改进方案**:
- 使用Redis存储活跃进化任务状态
- 或使用数据库字段 `is_running`
- 应用启动时从数据库恢复状态

**涉及文件**:
- `storage/models.py` (添加is_running字段)
- `api/routers/evolution.py` (替换为Redis/DB)
- 新增 `core/redis_client.py` (如果使用Redis)

---

### 5. 分布式锁（多Worker支持）

**优先级**: P2  
**来源**: Phase 4 代码审查

**当前状态**: ❌ 不支持多Worker部署

**需求描述**:
- 当部署多个API Worker时，`active_evolutions` 需要在实例间同步
- 防止同一任务在多个Worker上同时运行

**解决方案**:
- 使用Redis分布式锁
- 或使用数据库乐观锁

---

## 📊 监控与审计

### 6. 操作日志记录

**优先级**: P1  
**来源**: Phase 4 代码审查

**当前状态**: ❌ 未记录谁执行了操作

**需求描述**:
- 记录所有进化控制操作（启动、暂停、中止）
- 记录操作人、时间、结果
- 支持审计查询

**涉及文件**:
- `storage/models.py` (新增AuditLog模型)
- `api/routers/evolution.py` (添加日志记录)

**模型设计**:
```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str]  # start/pause/resume/abort
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"))
    timestamp: Mapped[datetime]
    details: Mapped[Optional[dict]]  # 额外信息
```

---

### 7. 速率限制（Rate Limiting）

**优先级**: P2  
**来源**: 最佳实践

**当前状态**: ❌ 未实现

**需求描述**:
- 限制API调用频率，防止滥用
- 进化控制操作（start/pause/abort）限制更严格
- 查询接口限制较宽松

**实现建议**:
- 使用 `slowapi` 库集成FastAPI
- 或使用Nginx/网关层限流

---

## 📝 数据完整性

### 8. 级联删除确认

**优先级**: P2  
**来源**: Phase 4 代码审查 (test_tasks.py)

**当前状态**: ⚠️ 数据库模型有级联配置，但需验证

**验证项**:
- 删除任务时，关联的Generations是否正确级联删除
- 删除任务时，关联的AuditLogs如何处理
- 软删除 vs 硬删除策略

---

## ✅ 完成标准

Phase 5 完成时需满足：

```markdown
- [ ] 用户注册/登录/登出API可用
- [ ] JWT认证中间件生效
- [ ] 所有任务API带用户隔离
- [ ] 管理员可访问所有任务
- [ ] 操作日志记录完整
- [ ] 活跃进化状态持久化（Redis/DB）
- [ ] 多Worker部署测试通过
```

---

## 📅 建议排期

| 任务 | 优先级 | 估算工时 | 依赖 |
|------|--------|----------|------|
| 用户认证机制 | P0 | 4h | - |
| 任务级用户隔离 | P0 | 4h | 用户认证 |
| 操作权限控制 | P1 | 3h | 用户认证 |
| 活跃状态持久化 | P1 | 4h | - |
| 操作日志记录 | P1 | 3h | 用户认证 |
| 分布式锁 | P2 | 4h | Redis |
| 速率限制 | P2 | 2h | - |

---

**最后更新**: 2026-03-12  
**维护者**: SEMDS AI开发团队
