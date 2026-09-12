#!/usr/bin/env python3
"""Run under Linux/WSL after a release make. Boot only a disposable copy."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import re

ROOT = Path(__file__).resolve().parents[1]
OBJECT_DIR = ROOT/'src'/'.build-local'/'release-sanitize0'
if not (OBJECT_DIR/'comm.o').exists():
    raise SystemExit('Build the release engine first: make -C src release')
scratch = Path(tempfile.mkdtemp(prefix='haven-room-audit-'))
for name in ('area', 'data', 'player', 'accounts', 'gods'):
    shutil.copytree(ROOT/name, scratch/name)
(scratch/'log').mkdir()
comm = scratch/'comm-test.o'
shutil.copy2(OBJECT_DIR/'comm.o', comm)
subprocess.run(['objcopy', '--redefine-sym', 'main=haven_game_main', str(comm)], check=True)
object_list = re.search(r'^O_FILES\s*=\s*(.*?)(?=\n\n)', (ROOT/'src'/'Makefile').read_text(), re.M | re.S)[1]
objects = [str(OBJECT_DIR/name) for name in re.findall(r'[\w-]+\.o\b', object_list) if name != 'comm.o']
binary = scratch/'room-test'
subprocess.run(['g++', '-g', '-Wno-deprecated', '-Wno-write-strings', '-I'+str(ROOT/'src'), str(ROOT/'tools'/'test_room_descriptions.cpp'), str(comm), *objects, '-ldl', '-lcrypt', '-lcurl', '-o', str(binary)], check=True)
log = ROOT/'docs'/'room-description-integration.log'
with log.open('w') as output:
    result = subprocess.run([str(binary)], cwd=scratch/'area', stdout=output, stderr=subprocess.STDOUT, timeout=120)
print('Disposable test world:', scratch)
print('Integration exit:', result.returncode)
print('\n'.join(log.read_text(errors='replace').splitlines()[-12:]))
raise SystemExit(result.returncode)
