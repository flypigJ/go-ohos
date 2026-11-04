# Go for OpenHarmony

A community OpenHarmony port of Go 1.27.3, maintained alongside MeshArc.

[中文说明](README.zh-CN.md) · [Build](ohos/docs/build.md) · [Platform limits](ohos/docs/platform.md) · [Validation](ohos/docs/validation.md) · [Maintenance](ohos/docs/maintenance.md)

**Developer preview, not an official Go or Huawei release.** The initial integration target is **HarmonyOS API 26 / arm64 / CGO shared libraries**. The compiler uses the distinct identity `go1.27.3-ohos-devel`. Read the platform limits before adopting it: the inherited runtime exposes Linux identity, assumes a 39-bit arm64 heap address space, and has not completed full target standard-library or signal/lifecycle qualification.

## Build your own toolchain

Install Git, Python 3.11+ and official Go 1.27.3. On Windows PowerShell:

```powershell
git clone https://github.com/flypigJ/go-ohos.git
cd go-ohos
$bootstrap = go env GOROOT
python ohos/scripts/manage.py verify
python ohos/scripts/manage.py bootstrap --bootstrap $bootstrap
./bin/go.exe version
python ohos/scripts/manage.py test
```

The official bootstrap installation must be separate from this checkout. Nothing replaces your system Go installation or changes persistent Go configuration. Linux commands and native SDK preparation are in [Build the toolchain](ohos/docs/build.md).

## Build a HarmonyOS library

With the complete API 26 native SDK installed at DevEco Studio's default Windows location:

```powershell
python ohos/scripts/manage.py sdk-smoke --sdk 'C:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/native'
```

This produces a small shared library, a pthread loader and a hash receipt in `ohos/out/arm64`. ELF/TLS checks are performed during the build. Running the loader on a compatible device is a separate step, and loading inside a signed HAP needs the application's own project/signing.

For a real consumer, see [tailscale-ohos-core](https://github.com/flypigJ/tailscale-ohos-core) and [MeshArc](https://github.com/flypigJ/Tailscale-OHOS). Their device results apply to their recorded source and packages; they are not blanket certification of every binary produced by this compiler.

## What is in this fork

The repository keeps upstream Go source history, the OpenHarmony platform adaptation, focused regressions and a separate `ohos/` directory for project-specific tools/documentation. `ohos/source.json` pins the upstream commit/tree and modified runtime/compiler file hashes.

The port includes ARM64 dynamic TLS lowering, CGO/runtime initialization adaptation, interface enumeration cleanup and platform source selection. The complete scope and known gaps are described in [Platform behavior](ohos/docs/platform.md). A successful bootstrap or cross-compile is never reported as a device test.

## Updating and contributing

Daily monitoring checks upstream stable tags and `master`, opening/updating one tracking issue when drift is detected. It does not silently switch the compiler to a moving branch. Runtime changes need fresh validation before a new qualified revision is published. See [Maintenance](ohos/docs/maintenance.md) and [Contributing](ohos/CONTRIBUTING.md).

This project builds on Go, OpenHarmony SIG and prior MeshArc work. Original copyright, LICENSE and PATENTS are retained; see [Provenance](ohos/NOTICE.md). The unmodified upstream README is retained at [ohos/README.upstream.md](ohos/README.upstream.md).
