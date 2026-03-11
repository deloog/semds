# SEMDS 环境配置指南

## 快速配置 (3步)

### 第 1 步: 获取 DeepSeek API Key

1. 访问 https://platform.deepseek.com/
2. 注册/登录账号
3. 进入「API Keys」页面
4. 点击「创建 API Key」
5. 复制生成的 Key (格式: `sk-xxxxxxxxxxxxxxxx`)

### 第 2 步: 配置环境变量

**方法 A: 直接编辑 .env 文件 (推荐)**

打开 `/mnt/d/semds/.env` 文件，修改：
```bash
DEEPSEEK_API_KEY=sk-your-actual-key-here
```

**方法 B: 系统环境变量**

Linux/Mac:
```bash
export DEEPSEEK_API_KEY="sk-your-actual-key-here"
```

Windows PowerShell:
```powershell
$env:DEEPSEEK_API_KEY="sk-your-actual-key-here"
```

Windows CMD:
```cmd
set DEEPSEEK_API_KEY=sk-your-actual-key-here
```

### 第 3 步: 验证配置

```bash
cd /mnt/d/semds
python3 core/env_loader.py
```

预期输出：
```
✓ 已从 /mnt/d/semds/.env 加载 5 个环境变量
✓ 已配置: DEEPSEEK_API_KEY

当前 LLM 配置:
  Backend: deepseek
  Model: deepseek-chat
  API Key: ********xxxx
```

## 运行实验

配置完成后，运行对比实验：

```bash
cd /mnt/d/semds
python3 experiments/run_comparison_experiment.py
```

## 配置选项说明

### LLM 后端选择

| 后端 | 配置项 | 适用场景 |
|------|--------|----------|
| DeepSeek | `DEEPSEEK_API_KEY` | 国内可用，性价比高 |
| Anthropic | `ANTHROPIC_API_KEY` | 代码能力强，需梯子 |
| OpenAI | `OPENAI_API_KEY` | GPT-4，需梯子 |

### Consilium 配置

```bash
# Consilium 使用的 LLM (deepseek/openai/anthropic)
CONSILIUM_BACKEND=deepseek

# 安全级别 (low/medium/high/critical)
CONSILIUM_SAFETY_LEVEL=medium
```

### 本地模型配置 (Qwen2.5 4B)

```bash
# Ollama 地址
OLLAMA_BASE_URL=http://localhost:11434

# 模型名称
OLLAMA_MODEL=qwen2.5:4b
```

## 故障排除

### 问题: "未找到 API Key"

**原因**: .env 文件不存在或未正确设置

**解决**:
1. 确认 `.env` 文件存在于 `/mnt/d/semds/.env`
2. 确认文件中有 `DEEPSEEK_API_KEY=sk-xxxx`
3. 确认没有多余的空格或引号

### 问题: "API Error 401"

**原因**: API Key 无效或过期

**解决**:
1. 检查 Key 是否完整复制
2. 在 DeepSeek 平台确认 Key 状态
3. 重新生成 Key

### 问题: "Connection timeout"

**原因**: 网络问题

**解决**:
- 检查网络连接
- 国内用户 DeepSeek 通常可直接访问
- 如使用 Anthropic/OpenAI 需要梯子

## 费用参考

DeepSeek API 价格 (截至 2024):
- deepseek-chat: ~¥1-2 / 百万 tokens
- deepseek-reasoner: ~¥4-8 / 百万 tokens

一次完整实验 (6 次调用) 约消耗 ¥0.1-0.3

---

**配置完成后即可开始实验！**
