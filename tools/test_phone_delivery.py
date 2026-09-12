#!/usr/bin/env python3
"""WSL/Linux: make -C src -j4 && python3 tools/test_phone_delivery.py.

Exercises phone delivery using the actual engine in a disposable world; never writes live saves.
"""
from pathlib import Path
import os
import sys
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sanitize = '--sanitize' in sys.argv
BUILD = ROOT / ('src/.build-local/debug-sanitize1' if sanitize else 'src/.build-local/release-sanitize0')
flags = ['-fsanitize=address,undefined', '-fno-omit-frame-pointer'] if sanitize else []

with tempfile.TemporaryDirectory(prefix="haven-phone-delivery-") as temporary:
    scratch = Path(temporary)
    for name in ("area", "data", "player", "accounts", "gods"):
        shutil.copytree(ROOT / name, scratch / name,
                        ignore=shutil.ignore_patterns("back[1-7]"))
    # Match test_full_moon: repair only the disposable, truncated Wilds fixture.
    wilds = scratch / "area/wildfor.are"
    if not wilds.read_bytes().rstrip().endswith(b"#$"):
        shutil.copy2(ROOT / "area/back7/wildfor.are", wilds)
    (scratch / "log").mkdir()
    (scratch / "prp").mkdir()
    comm = scratch / "comm-test.o"
    shutil.copy2(BUILD / "comm.o", comm)
    subprocess.run(["objcopy", "--redefine-sym", "main=haven_game_main", str(comm)], check=True)
    makefile = (ROOT / "src/Makefile").read_text()
    objects_text = re.search(r"^O_FILES\s*=\s*(.*?)(?=\n\n)", makefile, re.M | re.S)[1]
    objects = [str(BUILD / name) for name in re.findall(r"[\w-]+\.o\b", objects_text)
               if name != "comm.o"]
    binary = scratch / "phone-delivery-test"
    subprocess.run(["g++", *flags, "-g", "-Wno-deprecated", "-Wno-write-strings",
                    "-I" + str(ROOT / "src"),
                    str(ROOT / "tools/test_phone_delivery.cpp"), str(comm), *objects,
                    "-rdynamic", "-ldl", "-lcrypt", "-lcurl", "-o", str(binary)], check=True)
    result = subprocess.run([str(binary)], cwd=scratch / "area",
                            env=dict(os.environ, ASAN_OPTIONS="detect_leaks=0:halt_on_error=1",
                                     UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1"), stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, errors="replace", timeout=120)
    lines = result.stdout.splitlines()
    print("\n".join(lines[-30:] if result.returncode else [line for line in lines if "PASS:" in line]))
    raise SystemExit(result.returncode)
