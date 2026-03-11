# 路线图与SEMDS_v1.1_SPEC.md对齐报告

## 审查日期
2026-03-07

## 发现的出入及修正

### 1. Phase 1 修正

| 问题 | 修正措施 |
|------|---------|
| StrategyState模型缺失 | 在storage/models.py中新增StrategyState类，支持Thompson Sampling状态持久化 |

### 2. Phase 2 状态
✅ 与规格一致，无需修改

### 3. Phase 3 增补

| 新增/修改 | 内容 | 规格依据 |
|-----------|------|---------|
| **新增章节 3.3b** | Skills Library (技能库层) | 规格第3.1节、第5章 |
| 新增任务P3-T18a-e | 实现skills/目录、Jinja2模板、策略注册表 | 规格5.2节 |
| 新增任务P3-T10a | AI生成边界用例 | 规格4.2节、9.2节 |
| 更新依赖图 | 包含P3-T18a-e和P3-T10a | - |
| 更新验收标准 | 包含Skills Library验收 | - |

**关键修正**：
- 双轨评估器必须使用AI生成边界用例，而非硬编码用例
- 这是防止Goodhart现象的核心机制

### 4. Phase 4 增补

| 新增/修改 | 内容 | 规格依据 |
|-----------|------|---------|
| **新增章节 4.6** | Human Gate (人类监督闸口) | 规格4.7节 |
| 新增任务P4-T25-29 | HumanGateMonitor、审批API、审批UI | 规格4.7节、7.3节 |
| 扩充任务P4-T9 | 增补7.2节API端点(generations/best/rollback) | 规格7.2节 |
| 更新验收标准 | 包含Human Gate和API路径对齐 | - |

**关键修正**：
- API路由路径必须与规格7.1-7.4节完全一致
- WebSocket路径: /ws/tasks/{task_id}
- 审批API: /api/approvals/*

### 5. Phase 5 状态
✅ 与规格一致，无需修改

## 增补文件清单

1. `docs/roadmaps/PHASE3_ADDENDUM.md` - Phase 3增补说明
2. `docs/roadmaps/PHASE4_ADDENDUM.md` - Phase 4增补说明
3. `docs/roadmaps/ROADMAP_SPEC_ALIGNMENT.md` - 本对齐报告

## 文件修改清单

1. `docs/roadmaps/PHASE1_ROADMAP.md`
   - 添加StrategyState模型

2. `docs/roadmaps/PHASE3_ROADMAP.md`
   - 添加3.3b章节 (Skills Library)
   - 添加P3-T10a任务 (AI生成边界用例)
   - 更新依赖图
   - 更新验收标准

3. `docs/roadmaps/PHASE4_ROADMAP.md`
   - 扩充4.3章节 (增补API端点)
   - 更新验收标准

## 后续建议

1. **实施时注意**：Phase 3的AI生成边界用例(P3-T10a)是关键防Goodhart机制，不可省略

2. **架构完整性**：Skills Library层(P3-T18a-e)是Layer 1的核心组成，与core/和factory/并列

3. **监督机制**：Human Gate(P4-T25-29)是L2级决策的关键保障，必须实现审查质量监测

4. **API兼容性**：确保所有API路径与规格文档完全一致，避免前端集成问题

---
*对齐工作完成，路线图现已与SEMDS_v1.1_SPEC.md完全一致*
