# 矩阵乘法挑战 - 快速启动指南

## 步骤 1: 部署 Qwen 3.5 4B 到 D 盘

打开 **PowerShell (管理员)**，运行：

```powershell
# 方式 1: 自动部署（推荐）
powershell -ExecutionPolicy Bypass -File D:\setup_qwen35.ps1

# 方式 2: 手动步骤
$env:OLLAMA_MODELS = "D:\ollama_models"
$ollama = "$env:USERPROFILE\AppData\Local\Programs\Ollama\ollama.exe"
& $ollama pull qwen3.5:4b
```

下载时间：10-30 分钟（取决于网速，模型大小 3.4GB）

## 步骤 2: 启动 Ollama 服务

下载完成后，打开 **新终端**，运行：

```batch
D:\start_ollama.bat
```

保持此窗口运行！API 将在 http://localhost:11434 可用

## 步骤 3: 启动矩阵乘法挑战

在 **另一个终端** 中运行：

```bash
cd D:\semds
python start_matrix_challenge.py
```

## 步骤 4: 监控进度

打开浏览器访问：http://localhost:8000/monitor/

## 实验目标

| 目标 | 说明 | 难度 |
|------|------|------|
| 🥉 青铜 | 发现 cache 友好的实现 | 容易 |
| 🥈 白银 | 代码比标准实现简洁且等效 | 中等 |
| 🥇 黄金 | 使用 <8 次乘法（突破） | 困难 |
| 🏆 王者 | 使用 7 次（匹配 Strassen）| 极难 |

## 费用预估

- **500 代进化**:
  - DeepSeek API: ~25 次调用 ≈ ¥2-3
  - Qwen 3.5 本地: ~475 次调用 ≈ 免费
  - **总计**: ~¥3 （vs 纯 DeepSeek ¥25）

## 可能的结果

### 成功场景 A：实用优化
```python
# 发现 cache 友好的内存访问模式
# 比标准实现快 2-3 倍，但仍用 8 次乘法
```

### 成功场景 B：简洁实现
```python
# 发现与标准算法等价但代码更清晰的实现
# 便于理解和维护
```

### 突破场景 C：算法改进
```python
# 发现使用 <8 次乘法的实现
# 或发现 Strassen 算法的简洁表达
```

## 故障排除

### Ollama 启动失败
```powershell
# 检查模型是否存在
$env:OLLAMA_MODELS = "D:\ollama_models"
ollama list

# 重新拉取
ollama pull qwen3.5:4b
```

### 显存不足（6GB 显卡）
```powershell
# 强制使用 CPU
$env:OLLAMA_GPU_OVERHEAD = "1"
ollama serve
```

### SEMDS 连接失败
```bash
# 检查 API 是否运行
curl http://localhost:11434/api/tags

# 检查 SEMDS 服务
curl http://localhost:8000/health
```

## 相关文件

- `D:\setup_qwen35.ps1` - 自动部署脚本
- `D:\start_ollama.bat` - Ollama 启动脚本
- `D:\semds\start_matrix_challenge.py` - 挑战启动器
- `D:\semds\experiments\challenge_matrix_mul\` - 实验目录

---

**准备好了吗？先运行步骤 1 的部署脚本！** 🚀
