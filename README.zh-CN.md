# OpenHarmony Go 工具链

基于官方 Go 1.27.3 的社区 OpenHarmony 移植，与 MeshArc 配套维护。

这是**开发者预览**，不是 Go 或华为官方发行版。初始目标是 **HarmonyOS API 26、arm64、CGO 共享库**。独立工具链身份为 `go1.27.3-ohos-devel`，不会覆盖系统 Go。

2026-11-05 已完成新工具链产物的真机 Debug HAP 测试：示例库和 Tailscale 核心各通过 3 次冷启动、1,200 次跨线程 CGO 回调。完整哈希、测试源码入口和逐次结果见[验证记录](ohos/docs/validation.md)；完整标准库与生命周期仍未完成资格验证。

## 使用顺序

1. 阅读 [构建说明](ohos/docs/build.md)，使用独立的官方 Go 1.27.3 自举本仓库。
2. 运行源码校验和主机测试，再用 API 26 native SDK 编译最小共享库。
3. 在自己的目标环境验证库加载、线程回调、权限和生命周期，再用于实际应用。

英文首页提供可直接执行的 PowerShell 命令；Linux 步骤也在构建文档中。

## 支持范围

继承的移植使用 OpenHarmony 构建目标，但 `runtime.GOOS` 仍为 `linux`，并通过 `runtime.IsOpenharmony` 区分平台。ARM64 堆地址空间继承 39 位假设。信号链、profiling、完整标准库、其他设备 ABI、长时间运行和 macOS 主机尚需独立资格验证，详见 [平台限制](ohos/docs/platform.md)。

我们分别记录源码校验、自举、主机测试、SDK 编译、目标执行和应用验证，不把它们合并成一个“全部支持”。具体结果见 [验证记录](ohos/docs/validation.md)。

## 仓库关系

- 本仓库：Go 编译器、运行时和平台移植，保留上游历史及来源。
- [tailscale-ohos-core](https://github.com/flypigJ/tailscale-ohos-core)：固定使用本工具链的 Tailscale C 接口与适配。
- [MeshArc](https://github.com/flypigJ/Tailscale-OHOS)：完整鸿蒙应用。

每天自动检查上游正式标签和主线，有变化时更新跟踪 issue；经过审查和验证后再升级固定版本。贡献与文档要求见 [维护规范](ohos/docs/maintenance.md)，继承关系见 [NOTICE](ohos/NOTICE.md)。
