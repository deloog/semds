# Qwen 3.5 4B 本地部署指南

## 系统要求
- 显存: 6GB (你的配置 ✓)
- 内存: 32GB (你的配置 ✓)
- 模型大小: ~3GB

## 安装步骤

### 1. 下载 Ollama
访问: https://ollama.com/download/windows
下载安装包并运行

### 2. 拉取 Qwen 3.5 4B 模型
打开 PowerShell，执行:
```powershell
ollama pull qwen3.5:4b
```

### 3. 测试模型
```powershell
ollama run qwen3.5:4b
# 输入: 用 Python 写一个快速排序
# 按 Ctrl+D 退出
```

### 4. 启动 API 服务
```powershell
ollama serve
```

保持这个窗口运行，API 将在 http://localhost:11434 可用

## SEMDS 配置

已自动配置 `.env` 使用本地模型：

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:4b
```

## 显存优化（6GB 显存专用）

如果显存不足，可以强制使用 CPU：

```powershell
# 设置环境变量，让 Ollama 只用 CPU
$env:OLLAMA_GPU_OVERHEAD = "1"
ollama serve
```

或者修改模型加载参数：

```powershell
# 创建自定义 Modelfile
@"
FROM qwen3.5:4b
PARAMETER num_gpu 0
PARAMETER num_thread 8
"@ | Set-Content qwen35-cpu.modelfile

ollama create qwen35-cpu -f qwen35-cpu.modelfile
```

## 验证安装

运行测试脚本:
```powershell
python test_local_llm.py
```

成功后会显示:
```
[Qwen3.5-4B] Response: 这是一个测试响应
Time: 2.34s
Status: OK
```
