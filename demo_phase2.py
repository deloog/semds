"""Phase 2 演示脚本

演示 Docker 沙盒执行环境功能
包括:
- SandboxConfig 配置
- ExecutionResult 结果
- DockerManager 代码执行（降级模式）
"""

import sys

sys.path.insert(0, ".")

from core.docker_manager import DockerManager, SandboxConfig, ExecutionResult


def demo_config():
    """演示配置类"""
    print("=" * 60)
    print("演示 1: SandboxConfig 配置")
    print("=" * 60)

    # 默认配置
    config = SandboxConfig()
    print(f"默认配置:")
    print(f"  镜像: {config.image}")
    print(f"  内存限制: {config.memory_limit}")
    print(f"  CPU限制: {config.cpu_limit}")
    print(f"  网络禁用: {config.network_disabled}")
    print(f"  超时: {config.timeout}秒")

    # 自定义配置
    custom = SandboxConfig(
        image="custom-sandbox:latest",
        memory_limit="512m",
        cpu_limit=2.0,
        network_disabled=False,
        timeout=120,
    )
    print(f"\n自定义配置:")
    print(f"  镜像: {custom.image}")
    print(f"  内存限制: {custom.memory_limit}")
    print(f"  CPU限制: {custom.cpu_limit}")
    print(f"  网络禁用: {custom.network_disabled}")
    print(f"  超时: {custom.timeout}秒")

    # 转换为字典
    print(f"\n配置字典: {config.to_dict()}")
    print()


def demo_execution_result():
    """演示执行结果类"""
    print("=" * 60)
    print("演示 2: ExecutionResult 执行结果")
    print("=" * 60)

    # 成功结果
    success_result = ExecutionResult(
        success=True,
        stdout="Hello, World!\n42",
        stderr="",
        exit_code=0,
        duration=0.5,
    )
    print(f"成功结果:")
    print(f"  成功: {success_result.success}")
    print(f"  标准输出: {success_result.stdout.strip()}")
    print(f"  退出码: {success_result.exit_code}")
    print(f"  执行时间: {success_result.duration}秒")

    # 失败结果
    failure_result = ExecutionResult(
        success=False,
        stdout="",
        stderr="NameError: name 'x' is not defined",
        exit_code=1,
        duration=0.1,
    )
    print(f"\n失败结果:")
    print(f"  成功: {failure_result.success}")
    print(f"  标准错误: {failure_result.stderr}")
    print(f"  退出码: {failure_result.exit_code}")

    # 转换为字典
    print(f"\n结果字典: {success_result.to_dict()}")
    print()


def demo_execute_code():
    """演示代码执行"""
    print("=" * 60)
    print("演示 3: DockerManager 代码执行")
    print("=" * 60)

    # 创建管理器
    manager = DockerManager()
    print(f"Docker 可用: {manager._docker_available}")

    # 执行简单代码
    code1 = "print('Hello from sandbox!'); result = 1 + 2; print(f'1 + 2 = {result}')"
    print(f"\n执行代码: {code1}")
    result1 = manager.execute_code(code1)
    print(f"  成功: {result1.success}")
    print(f"  输出: {result1.stdout.strip()}")
    print(f"  退出码: {result1.exit_code}")
    print(f"  执行时间: {result1.duration:.4f}秒")

    # 执行有错误的代码
    code2 = "print(x)"
    print(f"\n执行代码: {code2}")
    result2 = manager.execute_code(code2)
    print(f"  成功: {result2.success}")
    print(f"  标准错误: {result2.stderr.strip()}")
    print(f"  退出码: {result2.exit_code}")

    # 执行超时测试
    code3 = "import time; time.sleep(0.1)"
    print(f"\n执行代码: {code3}")
    result3 = manager.execute_code(code3, timeout=1)
    print(f"  成功: {result3.success}")
    print(f"  输出: {result3.stdout.strip()}")
    print(f"  退出码: {result3.exit_code}")
    print()


def demo_isolation():
    """演示隔离验证"""
    print("=" * 60)
    print("演示 4: 隔离验证")
    print("=" * 60)

    manager = DockerManager()

    # 验证隔离性
    print(f"当前配置网络禁用: {manager.config.network_disabled}")

    # 由于没有Docker连接，降级模式返回True
    result = manager.verify_isolation("test-container")
    print(f"隔离验证结果: {result} (降级模式)")
    print()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("SEMDS Phase 2 - Docker 沙盒执行环境演示")
    print("=" * 60)
    print()

    # 运行所有演示
    demo_config()
    demo_execution_result()
    demo_execute_code()
    demo_isolation()

    print("=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
