#!/usr/bin/env python3
"""Run with Linux/WSL after make -C src; never boots the live world."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OBJECT_DIR = ROOT / 'src' / '.build-local' / 'release-sanitize0'


def run_test(source='test_student_dorms.cpp', label='dorm'):
    if not (OBJECT_DIR / 'comm.o').exists():
        raise SystemExit('Build the release engine first: make -C src')
    with tempfile.TemporaryDirectory(prefix=f'paroxysm-{label}-test-') as directory:
        scratch = Path(directory)
        for name in ('area', 'data', 'player', 'accounts', 'gods'):
            shutil.copytree(ROOT / name, scratch / name)
        (scratch / 'log').mkdir()
        comm = scratch / 'comm-test.o'
        shutil.copy2(OBJECT_DIR / 'comm.o', comm)
        subprocess.run(['objcopy', '--redefine-sym', 'main=haven_game_main', str(comm)], check=True)
        object_list = re.search(r'^O_FILES\s*=\s*(.*?)(?=\n\n)',
                                (ROOT / 'src' / 'Makefile').read_text(), re.M | re.S)[1]
        objects = [str(OBJECT_DIR / name) for name in re.findall(r'[\w-]+\.o\b', object_list)
                   if name != 'comm.o']
        binary = scratch / f'{label}-test'
        subprocess.run(['g++', '-g', '-Wno-deprecated', '-Wno-write-strings', '-I' + str(ROOT / 'src'),
                        str(ROOT / 'tools' / source), str(comm), *objects,
                        '-rdynamic', '-ldl', '-lcrypt', '-lcurl', '-o', str(binary)], check=True)
        log = Path(tempfile.gettempdir()) / f'paroxysm-{label}-integration.log'
        with log.open('w') as output:
            result = subprocess.run([str(binary)], cwd=scratch / 'area', stdout=output,
                                    stderr=subprocess.STDOUT, timeout=120)
        print('Integration log:', log)
        print('\n'.join(log.read_text(errors='replace').splitlines()[-25:]))
        raise SystemExit(result.returncode)


if __name__ == '__main__':
    run_test()
