#!/usr/bin/env python3
"""Test real NPC/report engine helpers without booting or changing world data."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sanitize = '--sanitize' in sys.argv
build = ROOT / ('src/.build-local/debug-sanitize1' if sanitize else
                'src/.build-local/release-sanitize0')
with tempfile.TemporaryDirectory(prefix='haven-npc-engine-') as directory:
    scratch = Path(directory)
    comm = scratch / 'comm.o'
    shutil.copy2(build / 'comm.o', comm)
    subprocess.run(['objcopy', '--redefine-sym', 'main=haven_game_main', str(comm)], check=True)
    makefile = (ROOT / 'src/Makefile').read_text()
    objects_text = re.search(r'^O_FILES\s*=\s*(.*?)(?=\n\n)', makefile, re.M | re.S)[1]
    objects = [str(build / name) for name in re.findall(r'[\w-]+\.o\b', objects_text)
               if name != 'comm.o']
    flags = ['-fsanitize=address,undefined', '-fno-omit-frame-pointer'] if sanitize else []
    binary = scratch / 'npc-engine'
    subprocess.run(['g++', '-g', '-Wno-deprecated', '-Wno-write-strings', *flags,
                    '-I' + str(ROOT / 'src'), str(ROOT / 'tools/test_npc_engine.cpp'),
                    str(comm), *objects, '-rdynamic', '-ldl', '-lcrypt', '-lcurl',
                    '-o', str(binary)], check=True)
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
               UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    subprocess.run([str(binary)], cwd=scratch, env=env, check=True, timeout=30)
