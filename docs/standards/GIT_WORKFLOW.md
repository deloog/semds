# SEMDS Git 工作流规范

**版本**: v1.0  
**分支模型**: Git Flow (简化版)  
**强制**: 是

---

## 🌿 分支策略

```
main (保护分支，永远可部署)
  ↑
develop (开发分支，集成测试)
  ↑
feature/* (功能分支，来自develop)
  ↑
hotfix/* (热修分支，来自main)
```

### 分支说明

| 分支 | 来源 | 合并到 | 用途 |
|------|------|--------|------|
| `main` | - | - | 生产代码，永远稳定 |
| `develop` | main | main | 开发集成，日常开发 |
| `feature/*` | develop | develop | 新功能开发 |
| `hotfix/*` | main | main+develop | 紧急修复 |
| `experiment/*` | develop | - | 实验性代码（不合并） |

---

## 📝 提交信息规范

### 格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型
```
feat:     新功能
fix:      修复bug
docs:     文档更新
style:    代码格式（不影响功能）
refactor: 重构（既不是feat也不是fix）
test:     测试相关
chore:    构建/工具/依赖更新
perf:     性能优化
security: 安全相关
```

### 示例
```bash
# ✅ 好的提交信息
git commit -m "feat(evolution): add Thompson Sampling strategy selector"

git commit -m "fix(core): handle timeout in sandbox execution

- Add timeout parameter to sandbox_execute()
- Raise SandboxTimeoutError on timeout
- Add test for timeout handling

Closes #123"

git commit -m "docs: update API reference for CodeGenerator"

# ❌ 坏的提交信息
git commit -m "update"
git commit -m "fix bug"
git commit -m "changes"
```

---

## 🔒 保护分支规则

### main 分支
- [x] 禁止直接推送
- [x] 需要PR审查
- [x] 需要CI通过
- [x] 需要至少1个批准

### develop 分支
- [x] 禁止直接推送
- [x] 需要PR审查
- [x] 建议CI通过

---

## 🔄 工作流程

### 开发新功能
```bash
# 1. 从develop创建分支
git checkout develop
git pull origin develop
git checkout -b feature/thompson-sampling

# 2. 开发...
git add .
git commit -m "feat(evolution): implement Thompson Sampling"

# 3. 推送到远程
git push origin feature/thompson-sampling

# 4. 创建PR（通过GitHub/GitLab）
# Base: develop
# Review required

# 5. 合并后清理
git checkout develop
git pull origin develop
git branch -d feature/thompson-sampling
```

### 紧急修复
```bash
# 1. 从main创建热修分支
git checkout main
git pull origin main
git checkout -b hotfix/fix-security-issue

# 2. 修复...
git commit -m "security(core): fix path traversal vulnerability"

# 3. 合并到main和develop
git checkout main
git merge hotfix/fix-security-issue
git push origin main

git checkout develop
git merge hotfix/fix-security-issue
git push origin develop

# 4. 打标签
git tag -a v1.0.1 -m "Fix security issue"
git push origin v1.0.1
```

---

## 🏷️ 版本标签

### 版本号格式
遵循 [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH

MAJOR: 不兼容的API变更
MINOR: 向后兼容的功能添加
PATCH: 向后兼容的问题修复
```

### 标签示例
```bash
# 发布 v1.0.0
git tag -a v1.0.0 -m "Initial stable release"

# 发布补丁 v1.0.1
git tag -a v1.0.1 -m "Fix sandbox timeout issue"

# 发布新功能 v1.1.0
git tag -a v1.1.0 -m "Add subprocess sandbox support"
```

---

## ✅ 提交前检查

```bash
# 1. 运行测试
pytest

# 2. 检查代码格式
black --check semds/
isort --check-only semds/

# 3. 类型检查
mypy semds/

# 4. 安全扫描
bandit -r semds/

# 5. 提交
```

---

**未经审查的代码不得合并到 develop 或 main**
