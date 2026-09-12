#!/usr/bin/env python3
"""Link the real engine and test in a disposable copy of the world.

Run after make -C src; pass --sanitize after make -C src BUILD=debug SANITIZE=1.
"""
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sanitize = "--sanitize" in sys.argv
build = ROOT / ("src/.build-local/debug-sanitize1" if sanitize else
                "src/.build-local/release-sanitize0")
with tempfile.TemporaryDirectory(prefix="haven-world-changes-test-") as temporary:
    scratch = Path(temporary)
    for name in ("area", "data", "player", "accounts", "gods"):
        shutil.copytree(ROOT / name, scratch / name,
                        ignore=shutil.ignore_patterns("back[1-7]"))
    (scratch / "log").mkdir()
    comm = scratch / "comm-test.o"
    shutil.copy2(build / "comm.o", comm)
    subprocess.run(["objcopy", "--redefine-sym", "main=haven_game_main", str(comm)], check=True)
    makefile = (ROOT / "src/Makefile").read_text()
    objects_text = re.search(r"^O_FILES\s*=\s*(.*?)(?=\n\n)", makefile, re.M | re.S)[1]
    objects = [str(build / name) for name in re.findall(r"[\w-]+\.o\b", objects_text)
               if name != "comm.o"]
    binary = scratch / "world-changes-test"
    flags = ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"] if sanitize else []
    subprocess.run(["g++", "-g", "-Wno-deprecated", "-Wno-write-strings", *flags,
                    "-I" + str(ROOT / "src"), str(ROOT / "tools/test_world_changes.cpp"),
                    str(comm), *objects, "-rdynamic", "-ldl", "-lcrypt", "-lcurl",
                    "-o", str(binary)], check=True)
    env = dict(os.environ, ASAN_OPTIONS="detect_leaks=0:halt_on_error=1",
               UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1")
    arguments = ["--enforcers-only"] if "--enforcers-only" in sys.argv else []
    result = subprocess.run([str(binary), *arguments], cwd=scratch / "area", env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, errors="replace", timeout=120)
    (build.parent / "world-changes-test.log").write_text(result.stdout)
    lines = result.stdout.splitlines()
    print("\n".join(lines[-70:] if result.returncode else
                    [line for line in lines if "PASS:" in line]))
    raise SystemExit(result.returncode)

