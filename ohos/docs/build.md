# Build the toolchain

Run commands from the `go-ohos` repository root. Use Git, Python 3.11+, and a separate official Go 1.27.3 installation. The source checkout must not be inside that bootstrap installation.

## Bootstrap on Windows

```powershell
git clone https://github.com/flypigJ/go-ohos.git
cd go-ohos
$bootstrap = go env GOROOT
python ohos/scripts/manage.py verify
python ohos/scripts/manage.py bootstrap --bootstrap $bootstrap
./bin/go.exe version
python ohos/scripts/manage.py test
```

The first `go` is the official bootstrap compiler on PATH; the resulting `bin/go.exe` is the downstream compiler. Installation does not replace the system `go`, run `go env -w`, or persistently change PATH. Use the absolute path to the downstream compiler when needed.

`bootstrap` isolates inherited GO/CGO/compiler configuration, disables automatic toolchain switching and limits bootstrap concurrency. The source manifest is verified before and after compilation. `ohos/out/bootstrap.json` records the result and compiler hashes; `ohos/out/host-tests.json` records focused host test results.

## Host bootstrap on Linux

```bash
python3 ohos/scripts/manage.py verify
python3 ohos/scripts/manage.py bootstrap --bootstrap "$(go env GOROOT)"
./bin/go version
python3 ohos/scripts/manage.py test
```

This runs `src/make.bash` rather than `make.bat`. Linux CI is a host-toolchain check. It is not a target-device test. macOS native bootstrap and cross-compilation need their own validation before being advertised as supported.

## Build a target library and loader

Install the complete Huawei API 26 native SDK separately. For the standard Windows DevEco Studio installation:

```powershell
$nativeSdk = 'C:/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/native'
python ohos/scripts/manage.py sdk-smoke --sdk $nativeSdk
```

This compiles `ohos/examples/cshared`, its C header and `ohos/examples/loader.c`. Output is under `ohos/out/arm64`. The script requires AArch64 ELF, a TLS descriptor relocation and no initial-exec TLS relocation in the example library. It writes a receipt with library and loader hashes.

On a compatible target where execution is authorized, run the loader with the library's absolute path. Its successful output is `PASS: 400 callbacks on four pthreads`. Loading inside a signed HAP/N-API application requires the consumer's own DevEco project and signing; neither SDK nor signing material is bundled here.

## Build another CGO library

Use the downstream compiler with `GOOS=openharmony`, `GOARCH=arm64`, `CGO_ENABLED=1`, `GOTOOLCHAIN=local`, and a `CC` command supplying `--target=aarch64-linux-ohos`, the matching SDK sysroot and `-D__MUSL__`. See `target_env` in [common.py](../scripts/common.py) for the tested command quoting, including paths containing spaces.

Build caches must stay separate from official Go. Copying an old compiler into a new source tree does not constitute a valid bootstrap; the scripts verify the exact compiler binaries produced by this checkout.

## Troubleshooting

| Failure | Meaning / next step |
| --- | --- |
| Source digest or file-set mismatch | Inspect your change against the port manifest; preserve edits and use a fresh checkout for a known baseline |
| Wrong bootstrap version | Supply the official Go 1.27.3 installation, separate from this checkout |
| SDK missing / wrong API | Select the `native` directory containing `llvm`, `sysroot` and SDK metadata |
| Windows MSYS/DLL sandbox error | Run the bootstrap in a normal supported host environment; do not count the interrupted run as a pass |
| Library compiles but cannot load | Check ELF dependencies/relocations and app packaging; collect a minimal redacted target log |

Read [platform limits](platform.md) before treating a successful build as support for an arbitrary device or Go package.
