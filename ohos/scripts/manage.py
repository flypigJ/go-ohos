"""Build and validate this OpenHarmony Go source checkout. Python 3.11+."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess

from common import clean_env, digest, go_binary, go_env, native_sdk, read, run, target_env, verify_files, write

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ohos/out"


def verify():
    lock = read(ROOT / "ohos/source.json")
    if run(["git", "rev-parse", lock["upstream_commit"] + "^{tree}"], cwd=ROOT, capture=True) != lock["upstream_tree"]:
        raise ValueError("upstream source tree does not match provenance")
    expected = {f["path"] for f in lock["files"] if f["path"].startswith("src/")}
    actual = set(run(["git", "diff", "--name-only", lock["upstream_commit"], "--", "src"], cwd=ROOT, capture=True).splitlines())
    if actual != expected:
        raise ValueError("unrecorded runtime/compiler source changes")
    generated = {"src/cmd/cgo/zdefaultcc.go", "src/cmd/dist/dist.exe", "src/cmd/go/internal/cfg/zdefaultcc.go",
                 "src/cmd/internal/objabi/zbootstrap.go", "src/internal/buildcfg/zbootstrap.go",
                 "src/internal/runtime/sys/zversion.go", "src/time/tzdata/zzipdata.go"}
    added = set(run(["git", "ls-files", "--others", "--exclude-standard", "--", "src"], cwd=ROOT, capture=True).splitlines())
    if added - generated:
        raise ValueError("unrecorded source files")
    verify_files(ROOT, lock["files"])
    return lock


def bootstrap(bootstrap_root):
    lock = verify()
    bootstrap_root = Path(bootstrap_root).resolve()
    if bootstrap_root == ROOT or bootstrap_root.is_relative_to(ROOT):
        raise ValueError("bootstrap Go must be outside the source checkout")
    bootstrap_go = go_binary(bootstrap_root)
    version = run([bootstrap_go, "version"], env=go_env(bootstrap_root), capture=True)
    if not version.startswith("go version go1.27.3 "):
        raise ValueError("this reproducible bootstrap requires official Go 1.27.3")
    env = clean_env()
    env.update(GOROOT_BOOTSTRAP=str(bootstrap_root), GOCACHE=str(OUT / "bootstrap-cache"),
               GOPATH=str(OUT / "bootstrap-gopath"), GOPROXY="off", GOSUMDB="off", GOMAXPROCS="2")
    OUT.mkdir(parents=True, exist_ok=True)
    command = [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", "make.bat"] if os.name == "nt" else ["bash", "make.bash"]
    receipt = {"schema": 1, "status": "building", "identity": lock["identity"], "source_commit": run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture=True),
               "source_manifest_sha256": digest(ROOT / "ohos/source.json"), "device_tested": False}
    try:
        run(command, cwd=ROOT / "src", env=env)
        verify()
        built = run([go_binary(ROOT), "version"], env=go_env(ROOT), capture=True)
        if not built.startswith("go version " + lock["identity"] + " "):
            raise ValueError("built compiler identity differs")
        host = built.split()[-1].replace("/", "_")
        suffix = ".exe" if os.name == "nt" else ""
        names = ["bin/go" + suffix, "bin/gofmt" + suffix]
        names += ["pkg/tool/" + host + "/" + n + suffix for n in ("compile", "asm", "link", "cgo")]
        receipt.update(status="passed", version=built, binaries=[{"path": n, "sha256": digest(ROOT / n)} for n in names])
    except Exception:
        receipt["status"] = "failed"
        raise
    finally:
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
        write(OUT / "bootstrap.json", receipt)


def compiler_ready():
    lock = verify()
    receipt = read(OUT / "bootstrap.json")
    if receipt["status"] != "passed" or receipt["source_manifest_sha256"] != digest(ROOT / "ohos/source.json"):
        raise ValueError("bootstrap this exact source before testing")
    verify_files(ROOT, receipt["binaries"])
    return lock


def test_checked():
    compiler_ready()
    env = go_env(ROOT)
    env.update(GOCACHE=str(OUT / "host-cache"), GOPROXY="off", GOSUMDB="off")
    run([go_binary(ROOT), "test", "-p", "2", "-count=1", "cmd/internal/objabi", "cmd/internal/obj/arm64", "internal/platform"], cwd=ROOT, env=env)
    overlay = OUT / "x509-overlay.json"
    write(overlay, {"Replace": {str(ROOT / "src/crypto/x509/ohos_distrust_test.go"): str(ROOT / "ohos/tests/x509_distrust_test.go")}})
    run([go_binary(ROOT), "test", "-p", "2", "-count=1", "-short", "-overlay", overlay, "crypto/x509", "-run", "TestMeshArcDistrust|TestGoVerify", "-v"], cwd=ROOT, env=env)
    compiler_ready()
    write(OUT / "host-tests.json", {"status": "passed", "scope": "selected compiler/platform and x509 tests", "full_stdlib": False, "device_tested": False})


def test():
    write(OUT / "host-tests.json", {"status": "running", "device_tested": False})
    try:
        test_checked()
    except Exception:
        write(OUT / "host-tests.json", {"status": "failed", "device_tested": False})
        raise


def sdk_smoke_checked(sdk_root):
    lock = compiler_ready()
    sdk, info = native_sdk(sdk_root)
    env = target_env(ROOT, sdk, OUT / "target-cache")
    out = OUT / "arm64"
    out.mkdir(parents=True, exist_ok=True)
    library = out / "libohos_example.so"
    run([go_binary(ROOT), "build", "-p", "2", "-trimpath", "-buildvcs=false", "-buildmode=c-shared",
         "-ldflags=-extldflags=-Wl,--build-id=sha1", "-o", library, "."], cwd=ROOT / "ohos/examples/cshared", env=env)
    readelf = sdk / "llvm/bin" / ("llvm-readelf.exe" if os.name == "nt" else "llvm-readelf")
    relocations = run([readelf, "-r", library], capture=True)
    header = run([readelf, "-h", library], capture=True)
    if "AArch64" not in header or "TLSDESC" not in relocations or "R_AARCH64_TLS_TPREL" in relocations:
        raise ValueError("unexpected architecture or unsafe dynamic-library TLS model")
    clang = sdk / "llvm/bin" / ("clang.exe" if os.name == "nt" else "clang")
    run([clang, "--target=aarch64-linux-ohos", "--sysroot=" + str(sdk / "sysroot"),
         ROOT / "ohos/examples/loader.c", "-ldl", "-pthread", "-o", out / "loader"])
    compiler_ready()
    write(out / "build.json", {"status": "passed", "identity": lock["identity"], "sdk_version": info["version"],
                              "library_sha256": digest(library), "loader_sha256": digest(out / "loader"), "device_executed": False})


def sdk_smoke(sdk_root):
    receipt_path = OUT / "arm64/build.json"
    write(receipt_path, {"status": "building", "device_executed": False})
    try:
        sdk_smoke_checked(sdk_root)
    except Exception:
        write(receipt_path, {"status": "failed", "device_executed": False})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("verify-compiler")
    p = sub.add_parser("bootstrap")
    p.add_argument("--bootstrap", required=True, help="official Go 1.27.3 installation")
    sub.add_parser("test")
    p = sub.add_parser("sdk-smoke")
    p.add_argument("--sdk", required=True, help="API 26 native SDK directory")
    args = parser.parse_args()
    if args.command == "verify": verify(); print("Pinned port source verified")
    elif args.command == "verify-compiler": compiler_ready(); print("Compiler receipt and source verified")
    elif args.command == "bootstrap": bootstrap(args.bootstrap)
    elif args.command == "test": test()
    else: sdk_smoke(args.sdk)


if __name__ == "__main__":
    main()
