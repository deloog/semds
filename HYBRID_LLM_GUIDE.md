# Hybrid LLM 配置指南

## 概述

SEMDS 现在支持**混合 LLM 策略**，结合 DeepSeek API（高质量）和本地 Qwen 3.5 4B（免费）来大幅降低进化成本。

## 成本对比

| 模式 | 1000代费用 | 质量 |
|------|-----------|------|
| 纯 DeepSeek | ~¥50 | ⭐⭐⭐⭐⭐ |
| 纯 Ollama (本地) | 免费 | ⭐⭐⭐ |
| **混合策略** | **~¥5** | **⭐⭐⭐⭐** |

**节省 90% 成本！**

## 快速开始

### 1. 安装 Ollama 和 Qwen 3.5

```bash
# 运行自动安装脚本
python setup_ollama.py
```

或手动安装：
1. 下载 Ollama: https://ollama.com/download
2. 拉取模型: `ollama pull qwen3.5:4b`
3. 启动服务: `ollama serve`

### 2. 启用混合模式

```bash
# 在 .env 文件中设置
ENABLE_HYBRID_LLM=true
```

或运行：
```bash
python setup_ollama.py  # 会自动配置
```

### 3. 运行进化

```bash
python experiments/challenge_3_sorting/run_challenge.py
```

## 工作原理

```
Generation 1-19:  Ollama (本地)     - 微优化，免费
Generation 20:    DeepSeek (API)    - 架构级改进
Generation 21-39: Ollama (本地)     - 继续微优化
Generation 40:    DeepSeek (API)    - 再次架构改进
...
```

如果 Ollama 连续失败 3 次，自动切换到 DeepSeek 救场。

## 配置选项

在 `.env` 文件中：

```env
# 混合策略开关
ENABLE_HYBRID_LLM=true

# 每 N 代使用一次 DeepSeek
HYBRID_STRATEGIC_INTERVAL=20

# 连续失败 N 次后切换到 DeepSeek
HYBRID_FALLBACK_THRESHOLD=3

# Ollama 配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:4b
```

## 显存优化（6GB 显卡）

如果显存不足，强制使用 CPU：

```bash
# Windows PowerShell
$env:OLLAMA_GPU_OVERHEAD="1"
ollama serve
```

或使用更小的模型：
```bash
ollama pull qwen3.5:2b  # 仅需 ~1.5GB
```

## 验证安装

```bash
# 测试 Ollama 连接
python test_local_llm.py

# 查看混合策略演示
python evolution/hybrid_llm.py
```

## 故障排除

### Ollama 连接失败
```bash
# 检查服务是否运行
curl http://localhost:11434

# 手动启动
ollama serve
```

### 模型下载失败
```bash
# 检查网络
ollama pull qwen3.5:4b

# 使用国内镜像（如有）
export OLLAMA_HOST=0.0.0.0
ollama serve
```

### 代码生成质量差
- 增加 `HYBRID_FALLBACK_THRESHOLD=1` - 更快切换到 DeepSeek
- 降低 `HYBRID_STRATEGIC_INTERVAL=10` - 更频繁使用 DeepSeek

## 性能参考

在 RTX 3060 12GB + i5-12400F 上：

| 模型 | 生成速度 | 显存占用 |
|------|---------|---------|
| qwen3.5:4b | ~5-10s/代 | ~4GB |
| qwen3.5:2b | ~3-5s/代 | ~2GB |

## 建议

- **开发测试**: 纯 Ollama 模式（免费）
- **生产进化**: 混合模式（90% 成本节省）
- **关键任务**: 纯 DeepSeek 模式（最高质量）

---

有问题？检查 `setup_ollama_qwen35.md` 详细安装指南。
