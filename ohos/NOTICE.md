# Provenance and attribution

The source history starts from the genuine official Go 1.27.3 commit `2aae1000ea1d4b28923b96db28acf4e3b99d6aff`, obtained from `https://go.googlesource.com/go`. The local preparation initially used a shallow checkout; upstream parent identity is preserved rather than fabricating a new Go source commit. GitHub's fork relationship preserves access to upstream history.

The platform adaptation builds on [OpenHarmony SIG's Go port](https://gitcode.com/openharmony-sig/ohos_golang_go), carried forward through the MeshArc engineering work. The original Go/OpenHarmony copyright headers remain. The inherited K1 patch and official source-archive hashes are recorded in `source.json`; the canonical Git tree is verified separately from the distribution archive.

This extraction adds a distinct downstream compiler identity, standalone Python build/check scripts, focused tests, a small C/shared-library example, documentation and maintenance automation. It does not claim authorship of inherited Go, OpenHarmony or earlier MeshArc code.

The repository retains Go's [LICENSE](../LICENSE), [PATENTS](../PATENTS) and contributor records. Build tools added here use the same BSD-3-Clause license. Official Go downloads and Huawei/OpenHarmony SDKs are separate inputs with their own distribution terms; this repository does not redistribute the SDK.

Related community work, consulted for repository organization rather than silently imported as this implementation, includes [ZxillyFork/go-hmos](https://github.com/ZxillyFork/go-hmos), its build/installer projects, and [star4277/ohos-go](https://github.com/star4277/ohos-go).
