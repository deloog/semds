# SEMDS Docker 安装指南 (D盘数据配置) [DEPRECATED]

**⚠️ 注意**: 本项目已改用 **subprocess + tempfile** 方案（DD-001），不再需要 Docker。

本文档保留供参考，如需使用 Docker 作为可选后端时参考。

## 📋 安装前检查

确保满足以下条件：
- ✅ Windows 10/11 64位
- ✅ WSL2 已启用（您已满足）
- ✅ D盘有足够空间（建议预留20GB+）
- ✅ 管理员权限

## 🚀 快速安装步骤

### 步骤 1: 运行安装脚本

**方法A - 双击运行（推荐）:**
1. 打开文件资源管理器
2. 进入 `d:\semds\scripts`
3. **右键** `install-docker.bat` → **"以管理员身份运行"**

**方法B - PowerShell:**
```powershell
# 以管理员身份打开PowerShell
# Win+X, 选择 "Windows PowerShell (管理员)" 或 "终端(管理员)"

cd d:\semds\scripts
powershell -ExecutionPolicy Bypass -File .\install-docker-d-drive.ps1
```

### 步骤 2: 安装过程

脚本会自动执行：
1. ✅ 创建D盘数据目录 (`D:\docker-data`)
2. ✅ 配置WSL2数据到D盘
3. ✅ 下载Docker Desktop
4. ✅ 安装Docker Desktop
5. ✅ 配置Docker数据根目录到D盘

**注意:** 安装过程中可能会有几次弹窗，请允许。

### 步骤 3: 重启电脑

**必须重启**，否则WSL2配置不生效。

### 步骤 4: 启动Docker Desktop

1. 从开始菜单启动 "Docker Desktop"
2. 等待系统托盘出现鲸鱼图标
3. 首次启动可能需要3-5分钟初始化

### 步骤 5: 配置SEMDS环境

重启并启动Docker后，运行：

```powershell
# 以管理员身份运行PowerShell
cd d:\semds\scripts
powershell -ExecutionPolicy Bypass -File .\setup-semds-docker.ps1
```

此脚本会：
- ✅ 构建SEMDS沙盒镜像
- ✅ 验证Docker环境
- ✅ 运行Phase 2测试

## 📁 目录结构

安装后数据分布：

```
C:\Program Files\Docker\          # 程序文件 (~500MB)
C:\ProgramData\DockerDesktop\     # 配置数据 (~100MB)

D:\docker-data\                   # 所有大数据
├── docker\                        # Docker镜像和容器数据
├── docker-desktop\                # Docker Desktop WSL
├── docker-desktop-data\           # Docker数据卷WSL
└── wsl\                           # WSL2交换文件
```

## ✅ 验证安装

运行以下命令验证：

```powershell
# 检查Docker版本
docker --version
docker-compose --version

# 检查WSL位置（应该在D盘）
wsl --list -v
wsl --manage docker-desktop --show-location

# 测试SEMDS沙盒
docker run --rm semds-sandbox:latest python -c "print('OK')"

# 运行测试
cd d:\semds
python -m pytest tests/core/test_docker_manager.py -v
```

## 🔧 故障排除

### 问题: "Docker Desktop无法启动"

**解决:**
```powershell
# 重置WSL
wsl --shutdown
wsl --unregister docker-desktop
wsl --unregister docker-desktop-data

# 然后重新运行 setup-semds-docker.ps1
```

### 问题: "磁盘空间不足"

**检查空间使用:**
```powershell
# 查看D盘空间
cd D:\docker-data
du -sh .  # 或使用属性查看
```

### 问题: "权限拒绝"

**解决:** 确保以**管理员身份**运行所有脚本。

### 问题: "SEMDS测试失败"

**解决:**
```powershell
# 手动构建镜像
cd d:\semds
docker build -f docker/Dockerfile.sandbox -t semds-sandbox:latest .

# 检查镜像
docker images | findstr semds

# 运行测试
python -m pytest tests/core/test_docker_manager.py -v
```

## 📊 存储占用预估

| 位置 | 初始大小 | 增长 |
|------|---------|------|
| C盘程序 | ~600MB | 固定 |
| D盘数据 | ~2GB | 随镜像增长 |
| SEMDS沙盒 | ~150MB | 固定 |

## 🔄 卸载

如需卸载：

```powershell
# 1. 卸载Docker Desktop (控制面板)
# 2. 清理WSL
wsl --unregister docker-desktop
wsl --unregister docker-desktop-data

# 3. 删除数据目录 (D盘空间释放)
Remove-Item -Recurse -Force D:\docker-data
```

## 📞 需要帮助?

查看Docker官方文档: https://docs.docker.com/desktop/install/windows-install/
