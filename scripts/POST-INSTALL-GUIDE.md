# SEMDS 项目 - Windows 重装后配置指南

## 📋 重装前备份（重要！）

### 必须备份的项目

| 项目 | 位置 | 备份到哪里 |
|------|------|-----------|
| SEMDS 项目代码 | `D:\semds\` | 已安全（D盘）✅ |
| Docker 数据 | `D:\docker-data\` | 可删除（重装后重建） |
| API Keys | `.env` 文件 | 拍照/密码管理器记录 |
| Git 配置 | `.gitconfig` | 记录用户名邮箱 |
| SSH Keys | `%USERPROFILE%\.ssh\` | 可选备份 |

### API Keys 记录（拍照保存）
```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
# 其他 Keys...
```

---

## 🖥️ Windows 安装建议

### 版本选择
- **Windows 11 Pro** 或 **Windows 10 Pro**
- **必须包含**：Hyper-V 功能（家庭版没有）

### 安装选项
- ✅ 使用本地账户（避免微软服务依赖）
- ✅ 关闭"增强的隐私设置"（减少后台活动）
- ✅ 暂时不安装第三方杀毒（Windows Defender 足够）

---

## 🚀 重装后软件安装清单

### 第 1 步：系统更新
```powershell
# 设置 Windows 更新
设置 → Windows 更新 → 检查更新
# 安装所有更新，可能需要重启 2-3 次
```

### 第 2 步：启用 WSL2 和 Hyper-V
**以管理员运行 PowerShell：**
```powershell
# 启用 WSL
wsl --install

# 启用 Hyper-V
dism /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart

# 重启电脑
Restart-Computer
```

### 第 3 步：安装 Python
**方式 A - Microsoft Store（推荐）：**
- 打开 Microsoft Store
- 搜索 "Python 3.11"
- 安装

**方式 B - 官网下载：**
- https://www.python.org/downloads/
- 下载 Python 3.11.x
- **安装时勾选**："Add Python to PATH"

验证：
```powershell
python --version
pip --version
```

### 第 4 步：安装 Git
- 官网：https://git-scm.com/download/win
- 使用默认设置安装

配置：
```powershell
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

### 第 5 步：安装 VS Code（可选）
- 官网：https://code.visualstudio.com/
- 安装 Python 扩展

---

## 🐳 Docker Desktop 安装（可选）

**⚠️ 注意**: SEMDS 已使用 **subprocess + tempfile** 方案替代 Docker（见 DD-001），Docker 不再是必需依赖。

如需安装 Docker 作为可选后端使用，请参考以下步骤：

### 安装前准备
1. 确保 Windows 更新完成
2. 确保 Hyper-V 已启用（见第 2 步）
3. 确保有 10GB+ 磁盘空间

### 安装步骤
1. 下载 Docker Desktop：
   - https://www.docker.com/products/docker-desktop
   - 或从 `D:\semds\scripts` 备份的安装程序

2. **安装时注意**：
   - ✅ 勾选 "Use WSL 2 instead of Hyper-V"（这次试试 WSL2，系统干净应该没问题）
   - 或 ❌ 取消勾选使用 Hyper-V（如果之前有问题）

3. 安装完成后**重启电脑**

4. 验证安装：
```powershell
docker --version
docker-compose --version
```

### 配置 D 盘数据目录
创建文件 `%USERPROFILE%\.docker\daemon.json`：
```json
{
  "data-root": "D:\\docker-data\\docker",
  "storage-driver": "overlay2"
}
```

然后重启 Docker Desktop。

---

## 🧪 SEMDS 项目环境配置

### 第 1 步：创建项目目录
```powershell
# 创建目录（如果重装后 D 盘数据丢失）
mkdir D:\semds
cd D:\semds

# 如果之前备份了代码，复制回来
# 或重新克隆
git clone https://github.com/your-repo/semds.git .
```

### 第 2 步：创建 Python 虚拟环境
```powershell
cd D:\semds
python -m venv venv

# 激活环境
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### 第 3 步：配置环境变量
创建 `.env` 文件（从备份恢复或重新创建）：
```
DEEPSEEK_API_KEY=sk-your-key-here
# 其他配置...
```

### 第 4 步：验证环境
```powershell
# 测试 Python 环境
python -c "import docker; print('docker-py OK')"

# 测试 Docker
docker run hello-world

# 构建 SEMDS 沙盒
docker build -f docker/Dockerfile.sandbox -t semds-sandbox:latest .

# 运行测试
cd D:\semds
python -m pytest tests/core/test_docker_manager.py -v
```

---

## 📦 完整安装顺序总结

```
1. Windows 重装 → 系统更新
        ↓
2. 启用 WSL2 + Hyper-V → 重启
        ↓
3. 安装 Python 3.11
        ↓
4. 安装 Git
        ↓
5. 安装 Docker Desktop → 重启
        ↓
6. 配置 Docker D 盘数据目录
        ↓
7. 恢复 SEMDS 项目
        ↓
8. 创建 Python 虚拟环境
        ↓
9. 安装依赖
        ↓
10. 配置 API Keys
        ↓
11. 构建沙盒镜像 → 运行测试
        ↓
✅ DONE!
```

**预计总时间**：2-3 小时（大部分时间是下载和更新）

---

## ⚡ 加速技巧

### 软件下载加速
- Python：使用国内镜像 https://npm.taobao.org/mirrors/python/
- Docker：使用阿里云镜像加速器

### pip 换国内源
创建 `%APPDATA%\pip\pip.ini`：
```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

---

## 🔧 重装后首次启动 SEMDS

```powershell
# 1. 激活环境
cd D:\semds
.\venv\Scripts\Activate.ps1

# 2. 验证 Docker
docker info

# 3. 构建沙盒（如果需要）
docker build -f docker/Dockerfile.sandbox -t semds-sandbox:latest .

# 4. 运行测试
python -m pytest tests/core/test_docker_manager.py -v

# 5. 运行演示
python demo_phase2.py
```

---

## 📞 重装后遇到问题？

如果重装后仍有问题，可能是：
1. BIOS 中未启用虚拟化（VT-x/AMD-V）
2. Windows 版本不支持 Hyper-V（需要 Pro 版）
3. 硬件兼容性问题

**检查虚拟化：**
```powershell
systeminfo | findstr "Hyper-V"
# 应该显示：Hyper-V 要求:      虚拟机监视器模式扩展：是
```

---

**祝重装顺利！完成后告诉我，我帮您验证 SEMDS 环境！** 🎉
