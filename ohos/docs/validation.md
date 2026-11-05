# Validation record

This record describes the initial public developer preview, tested on 2026-11-05 (Asia/Shanghai). It is a bounded qualification, not a claim of complete Go support on HarmonyOS.

## Source and environment

The upstream source is Go 1.27.3 at `2aae1000ea1d4b28923b96db28acf4e3b99d6aff`. The downstream compiler/runtime contents are identified by [source.json](../source.json), whose SHA-256 is `cf367683c42392d7f8092d6fc8e60bc6a2857232d62840bde648ca8e10ed2363`. The initial port commit is `e0c4a7f95f3bf9c8480f50d918f19a14b6848374`; later documentation and build-tool corrections do not change those compiler/runtime hashes.

The local host was Windows/amd64. Bootstrap used a separate official Go 1.27.3 installation. Cross-compilation used Huawei's API 26 Release native SDK, version `26.0.0.105`.

## Executed checks

Commands below run from the repository root; substitute the separately installed bootstrap and SDK paths as described in [Build](build.md).

| Command | Result | What it establishes |
| --- | --- | --- |
| `python ohos/scripts/manage.py verify` | Passed | Upstream tree identity and recorded port source contents |
| `python -m unittest discover -s ohos/tests -p "test_*.py" -v` | Passed | Build-helper isolation, path/hash validation and upstream version comparison |
| `python ohos/scripts/manage.py bootstrap --bootstrap <official-go-root>` | Passed on Windows | Fresh downstream compiler with identity `go1.27.3-ohos-devel` |
| `python ohos/scripts/manage.py test` | Passed on Windows | Selected compiler/arm64/platform and certificate regressions |
| `python ohos/scripts/manage.py sdk-smoke --sdk <native-sdk>` | Passed on Windows | ARM64 CGO shared library, dynamic TLS relocation checks and C/pthread loader compilation |

The SDK test was run with spaces in the SDK path. It caught and verified a correction to the compiler argument quoting. See the committed [bootstrap receipt](evidence/windows-bootstrap.json), [host receipt](evidence/windows-host-tests.json) and [SDK receipt](evidence/windows-sdk-smoke.json). Fresh runs write separate receipts under ignored `ohos/out/`.

GitHub Actions independently repeats the host checks on Linux and Windows. Consult [the workflow runs](https://github.com/flypigJ/go-ohos/actions/workflows/port.yml) for the actual result of a particular commit; a local receipt is not evidence that a remote run passed.

## Target execution attempt

A connected arm64 device reported API 26 and `OpenHarmony-7.0.0.111`. All four transferred files matched their host SHA-256 values. The loader was owned by `shell` with mode `0755`, but direct execution from the HDC temporary directory was denied with exit code **126** before library entrypoints ran. The core smoke program was therefore not attempted in that run. Temporary files were removed. See [the blocked attempt receipt](evidence/device-shell-attempt.json).

This is an execution-environment restriction observed in that attempt, not a runtime-test pass or evidence of a Go crash. The subsequent signed-HAP check below executes the libraries in application context.

## Signed HAP execution

On 2026-11-05, the same example library produced by `sdk-smoke` executed in a signed Debug feature HAP on that API 26 arm64 device. Three cold-process runs each completed 400 callbacks from four native threads, with zero failures. Each callback verified `go1.27.3-ohos-devel` and `openharmony=true`; `OhosHello` also invokes GC. The Tailscale core built with the same compiler separately passed three cold-process runs and its 41-export/version/engine/media checks.

The [receipt](evidence/device-hap-probe.json) binds the compiler, input library, stripped packaged library and signed HAP hashes to individual results and distinct process IDs. [The log excerpt](evidence/device-hap-probe.log) contains the six probe runs. The temporary test feature was removed, the original entry metadata and selected app identity/state fields were preserved, and the normal application was reopened. This is not an audit of all application data.

The shared [probe source and reproduction guide](https://github.com/flypigJ/tailscale-ohos-core/tree/main/examples/hap-probe) live in the consumer repository; file hashes are included in the receipt. It requires your own development application and signing profile. No signed package or signing material is distributed.

## Not established by this preview

- The complete Go standard-library suite has not been run on a HarmonyOS device.
- Signal chaining, asynchronous preemption, profiling, lifecycle stress, different address-space configurations and other architectures remain separate qualification work.
- Neither macOS native builds nor all HarmonyOS/OpenHarmony versions are certified by these results.
- Earlier MeshArc K1–K7 device evidence belongs to its exact recorded compiler, libraries and application packages. It does not automatically transfer to these standalone outputs.

See [Platform limits](platform.md) before selecting this toolchain for a new application.
