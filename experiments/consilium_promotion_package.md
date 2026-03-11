# Consilium 多平台推广内容包

---

## 1. Twitter/X 系列推文 (3条)

### 推文 1 - 问题引入
```
🚨 AI Agent 失控问题：

"帮我自动回复所有邮件"
→ AI 回复了垃圾邮件 + 老板的严肃邮件 + 泄露了隐私

问题：AI 缺乏"深思熟虑"的能力

Consilium = 给 AI 加上多方审议机制
PM + 技术负责人 + 成本专家 + 用户代表 共同决策

#AISafety #OpenClaw #MultiAgent
```

### 推文 2 - 产品介绍
```
🧠 Consilium 智议决策引擎

把"直接执行"变成"先审议后执行"

Before:
用户: "删除临时文件"
AI: 直接删除 → 误删重要文件

After:
AI: 审议后只删7天前的缓存文件，其他需确认 ✅

给 OpenClaw 装上安全刹车

→ github.com/deloog/consilium

#OpenSource #AI
```

### 推文 3 - 技术亮点
```
Consilium 核心设计：

六重流程控制
├─ 需求澄清 (PM)
├─ 技术可行性 (Tech Lead)
├─ 成本分析 (Cost Expert)
├─ 用户体验 (User Rep)
├─ 价值守护者检查
└─ 决策清单输出

不是让 AI 变慢，是让 AI 变可靠

已上架 OpenClaw 技能市场 🎉

#Consilium #AgentSkills
```

---

## 2. 知乎回答

### 问题：如何让 AI Agent 更安全可靠？

```markdown
作为一个长期折腾 AI Agent 的开发者，分享一个我们最近开源的方案。

## 核心问题：AI 太"果断"了

现在的 AI Agent（如 AutoGPT、OpenClaw）接到指令后直接执行：
- "删除临时文件" → 可能误删重要数据
- "自动回复邮件" → 可能泄露隐私
- "生成代码" → 可能有安全漏洞

问题本质：AI 缺乏人类的"深思熟虑"过程。

## 解决方案：Consilium 多方审议

我们设计了一个**多 Agent 审议框架**，模拟真实团队协作：

| 角色 | 职责 |
|------|------|
| 产品经理 | 确保需求理解准确 |
| 技术负责人 | 评估可行性、识别风险 |
| 成本专家 | 分析资源消耗 |
| 用户代表 | 从终端用户视角审视 |
| 价值守护者 | 安全检查、防危险操作 |

### 实际效果

**场景：自动回复邮件**

❌ 传统方式：
```
用户：自动回复所有邮件
AI：好的（回复了所有邮件，包括垃圾邮件和老板邮件）
```

✅ Consilium 方式：
```
[PM] 用户核心需求是减少邮件处理时间
[技术] 可以按规则过滤：仅回复订阅邮件
[成本] API调用约50次/天
[用户代表] 担心误回复重要邮件
[守护者] ⚠️ 高风险，建议：
  - 仅自动回复订阅类邮件
  - VIP发件人排除
  - 每日生成操作摘要
```

## 技术实现

- Python / TypeScript / Go / Rust 四语言支持
- 支持 DeepSeek / OpenAI / Anthropic
- 已作为 OpenClaw 官方技能发布

安装：
```bash
openclaw skill install consilium
```

## 开源地址

GitHub: https://github.com/deloog/consilium

MIT 协议，欢迎试用和贡献！
```

---

## 3. Reddit r/MachineLearning

### 帖子标题：Consilium - A Multi-Agent Deliberation Framework for Safer AI Operations

```markdown
Hi r/MachineLearning,

We just open-sourced **Consilium**, a deliberation framework that adds "thinking before acting" to AI agents.

## The Problem

Current AI agents (AutoGPT, OpenClaw, etc.) execute user commands immediately:
- "Delete temp files" → might delete important data
- "Auto-reply to emails" → might leak privacy
- "Generate code" → might have security bugs

The issue: AI lacks human-like deliberation.

## Our Approach

Consilium simulates a team review process with distinct roles:
- **PM**: Clarifies requirements
- **Tech Lead**: Assesses feasibility
- **Cost Expert**: Analyzes resource usage
- **User Rep**: UX perspective
- **Guardian**: Safety checks

## Example

**User**: "Auto-reply to all my emails"

**Without Consilium**: AI sets up blanket auto-reply → replies to spam, leaks info

**With Consilium**:
```
[PM] Core need: reduce email handling time
[Tech] Can filter by domain and content patterns
[Cost] ~50 API calls/day
[User Rep] Worried about important emails
[Guardian] ⚠️ High privacy risk

Decision:
✅ Auto-reply ONLY newsletters
✅ VIP senders excluded
✅ Daily summary for review
❌ Blanket auto-reply rejected
```

## Technical Details

- Multi-language: Python, TypeScript, Go, Rust
- LLM backends: DeepSeek, OpenAI, Anthropic
- Integration: OpenClaw skill (official)

GitHub: https://github.com/deloog/consilium

Would love your feedback!
```

---

## 4. HackerNews

### 标题：Show HN: Consilium – Multi-Agent Deliberation for Safer AI Operations

```
Consilium adds "thinking before acting" to AI agents through multi-party deliberation.

Problem: Current AI agents execute immediately without deliberation, leading to accidents (deleting wrong files, leaking data, etc.)

Solution: Simulate a team review with PM, Tech Lead, Cost Expert, User Rep, and Guardian roles before executing sensitive operations.

Open source (MIT): https://github.com/deloog/consilium

Also available as an OpenClaw skill.
```

---

## 5. Moltbook 帖子

参考 `consilium-moltbook-post.md`（已创建）

---

## 6. 发布检查清单

- [ ] Twitter/X - 3条推文
- [ ] 知乎 - 1个回答
- [ ] Reddit r/MachineLearning
- [ ] HackerNews Show HN
- [ ] Moltbook
- [ ] GitHub README 更新
- [ ] OpenClaw 技能市场上架
- [ ] Discord 社区分享

---

## 7. 发布时机建议

**第一波**（技能上架当天）：
- Twitter/X 推文 1
- Moltbook 帖子
- Discord 公告

**第二波**（3天后，有初步反馈）：
- Twitter/X 推文 2-3
- 知乎回答

**第三波**（1周后）：
- Reddit
- HackerNews
- 根据反馈更新内容
