# Platform behavior and limits

This is a downstream OpenHarmony port carried onto official Go 1.27.3. The initial integration target is a dynamically loaded arm64 shared library inside a HarmonyOS API 26 application.

## Build and runtime identity

Set `GOOS=openharmony`, `GOARCH=arm64` and `CGO_ENABLED=1`; use the matching SDK's Clang and sysroot. The compiler identifies itself as `go1.27.3-ohos-devel`, separating its cache identity from official Go. The `devel` suffix also lets Go account for compiler content build IDs.

The inherited port intentionally reports `runtime.GOOS == "linux"` and exposes `runtime.IsOpenharmony == true`. Build selection supports the OpenHarmony target and reuses Linux source. This differs from ports that give `runtime.GOOS` a separate string; do not assume compatibility with those forks or unmodified desktop Go.

An ordinary Go compiler cannot substitute for this compiler when producing the dynamic library. The port adds ARM64 general-dynamic TLS lowering and ELF TLS descriptors so the target loader can load the shared library. The source manifest includes the compiler/linker/runtime changes.

## Runtime assumptions

- CGO and external linking are required for the qualified shared-library path. Other build modes and architectures are not covered by this project's initial device evidence.
- The inherited arm64 heap address-space assumption is 39 bits. A different device ABI requires separate analysis and tests; this repository does not claim universal arm64 support.
- The runtime largely inherits Linux signal handling. HarmonyOS signal-chain interaction, asynchronous preemption, profiling and fault/unwinder behavior need dedicated target qualification. A callback/GC smoke test does not cover them.
- Interface enumeration uses the platform's `getifaddrs` with balanced cleanup. Enumeration success does not establish VPN routing, network-selection policy or system DNS behavior.
- Timezone data is read from the port's platform paths. System timezone changes and application/user trust policy are not fully integrated by this project.
- Linux-compatible syscalls may still be unavailable in an app sandbox. A library compiling does not prove process creation, executable memory, filesystem or network permissions.

## Lifecycle contract

Configure the process environment before loading the Go library. Do not race C environment mutation against runtime initialization. Do not unload a live Go runtime with `dlclose`. Use one runtime per tested integration path; loading multiple different Go runtimes is not qualified.

The SDK smoke example builds a library and loader, checks TLS relocations, and can exercise 400 calls from four pthreads when run on a compatible target. Building the loader is not running it. Full standard-library, long-running stress, battery and platform signal testing remain separate work.

## What is inherited and what changed

The underlying port comes from the OpenHarmony SIG Go work and the MeshArc forward-port. This extraction preserves the reviewed K1 runtime/compiler changes, gives the downstream compiler a distinct version identity, and adds independent build, test and maintenance tooling. It is not an independent reimplementation of Go.

See [provenance](../NOTICE.md) for source links and [validation](validation.md) for exact evidence boundaries.
