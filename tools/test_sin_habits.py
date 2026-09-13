"""WSL/Linux: make -C src -j4 && python3 tools/test_sin_habits.py.

Boots a disposable world; never writes live players, accounts, or areas.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
build = ROOT / 'src/.build-local/release-sanitize0'
with tempfile.TemporaryDirectory(prefix='haven-sin-habits-') as temporary:
    scratch = Path(temporary)
    for name in ('area', 'data', 'player', 'accounts', 'gods'):
        shutil.copytree(ROOT / name, scratch / name,
                        ignore=shutil.ignore_patterns('back[1-7]'))
    wilds = scratch / 'area/wildfor.are'
    if not wilds.read_bytes().rstrip().endswith(b'#$'):
        shutil.copy2(ROOT / 'area/back7/wildfor.are', wilds)
    (scratch / 'log').mkdir()
    (scratch / 'prp').mkdir()
    comm = scratch / 'comm.o'
    shutil.copy2(build / 'comm.o', comm)
    subprocess.run(['objcopy', '--redefine-sym', 'main=haven_game_main', str(comm)], check=True)
    objects_text = re.search(r'^O_FILES\s*=\s*(.*?)(?=\n\n)',
                             (ROOT / 'src/Makefile').read_text(), re.M | re.S)[1]
    objects = [str(build / name) for name in re.findall(r'[\w-]+\.o\b', objects_text)
               if name != 'comm.o']
    binary = scratch / 'test'
    subprocess.run(['g++', '-g', '-Wno-deprecated', '-Wno-write-strings',
                    '-I' + str(ROOT / 'src'), str(ROOT / 'tools/test_sin_habits.cpp'),
                    str(comm), *objects, '-rdynamic', '-ldl', '-lcrypt', '-lcurl',
                    '-o', str(binary)], check=True)
    result = subprocess.run([str(binary)], cwd=scratch / 'area',
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, errors='replace', timeout=120)
    (build.parent / 'sin-habits-test.log').write_text(result.stdout)
    print('\n'.join(result.stdout.splitlines()[-40:] if result.returncode else
                    [line for line in result.stdout.splitlines() if 'PASS:' in line]))
    raise SystemExit(result.returncode)
