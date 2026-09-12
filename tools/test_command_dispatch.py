#!/usr/bin/env python3
"""WSL/Linux: make -C src -j4 && python3 tools/test_command_dispatch.py.

Links the actual engine, boots a disposable world, and never writes live saves.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "src/.build-local/release-sanitize0"

with tempfile.TemporaryDirectory(prefix="haven-command-test-") as temporary:
    scratch = Path(temporary)
    for name in ("area", "data", "player", "accounts", "gods"):
        shutil.copytree(ROOT / name, scratch / name,
                        ignore=shutil.ignore_patterns("back[1-7]"))
    (scratch / "log").mkdir()
    comm = scratch / "comm-test.o"
    shutil.copy2(BUILD / "comm.o", comm)
    subprocess.run(["objcopy", "--redefine-sym", "main=haven_game_main", str(comm)], check=True)
    makefile = (ROOT / "src/Makefile").read_text()
    objects_text = re.search(r"^O_FILES\s*=\s*(.*?)(?=\n\n)", makefile, re.M | re.S)[1]
    objects = [str(BUILD / name) for name in re.findall(r"[\w-]+\.o\b", objects_text)
               if name != "comm.o"]
    binary = scratch / "command-test"
    subprocess.run(["g++", "-g", "-Wno-deprecated", "-Wno-write-strings",
                    "-I" + str(ROOT / "src"),
                    str(ROOT / "tools/test_command_dispatch.cpp"), str(comm), *objects,
                    "-rdynamic", "-ldl", "-lcrypt", "-lcurl", "-o", str(binary)], check=True)
    result = subprocess.run([str(binary)], cwd=scratch / "area", stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, errors="replace", timeout=120)
    lines = result.stdout.splitlines()
    print("\n".join(lines[-30:] if result.returncode else [line for line in lines if "PASS:" in line]))
    raise SystemExit(result.returncode)
