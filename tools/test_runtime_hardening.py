#!/usr/bin/env python3
"""Test runtime hardening with the real engine in a disposable working directory."""
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
with tempfile.TemporaryDirectory(prefix='haven-hardening-') as directory:
    scratch = Path(directory)
    comm = scratch / 'comm.o'
    shutil.copy2(build / 'comm.o', comm)
    subprocess.run(['objcopy', '--redefine-sym', 'main=haven_game_main', str(comm)], check=True)
    makefile = (ROOT / 'src/Makefile').read_text()
    objects_text = re.search(r'^O_FILES\s*=\s*(.*?)(?=\n\n)', makefile, re.M | re.S)[1]
    objects = [str(build / name) for name in re.findall(r'[\w-]+\.o\b', objects_text)
               if name != 'comm.o']
    flags = ['-fsanitize=address,undefined', '-fno-omit-frame-pointer'] if sanitize else []
    binary = scratch / 'hardening'
    compiled = subprocess.run(['g++', '-g', '-Wno-deprecated', '-Wno-write-strings', *flags,
                    '-I' + str(ROOT / 'src'), str(ROOT / 'tools/test_runtime_hardening.cpp'),
                    str(comm), *objects, '-Wl,--wrap=number_percent,--wrap=send', '-rdynamic', '-ldl', '-lcrypt', '-lcurl',
                    '-o', str(binary)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if compiled.returncode:
        print(compiled.stdout)
        raise SystemExit(compiled.returncode)
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
               UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    result = subprocess.run([str(binary)], cwd=scratch, env=env, timeout=30,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    lines = result.stdout.splitlines()
    print('\n'.join(lines if result.returncode else [line for line in lines if 'PASS:' in line]))
    raise SystemExit(result.returncode)
