#!/usr/bin/env python3
"""Exercise production login handlers in a disposable directory under Linux/WSL."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'src/.build-local/release-sanitize0'


def main():
    # Refresh header dependencies as well as comm.o after descriptor layout changes.
    result = subprocess.run(
        ['make', '-C', str(ROOT / 'src'), '-j4', '.build-local/release-sanitize0/haven'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode:
        print(result.stdout)
        raise SystemExit(result.returncode)

    with tempfile.TemporaryDirectory(prefix='paroxysm-account-login-') as directory:
        scratch = Path(directory)
        for name in ('area', 'accounts', 'log'):
            (scratch / name).mkdir()
        comm = scratch / 'comm.o'
        shutil.copy2(BUILD / 'comm.o', comm)
        subprocess.run(['objcopy', '--redefine-sym', 'main=haven_game_main', str(comm)], check=True)
        makefile = (ROOT / 'src/Makefile').read_text()
        object_list = re.search(r'^O_FILES\s*=\s*(.*?)(?=\n\n)', makefile, re.M | re.S)[1]
        objects = [str(BUILD / name) for name in re.findall(r'[\w-]+\.o\b', object_list)
                   if name != 'comm.o']
        binary = scratch / 'account-login'
        subprocess.run(
            ['g++', '-g', '-Wno-deprecated', '-Wno-write-strings', '-I' + str(ROOT / 'src'),
             str(ROOT / 'tools/test_account_login.cpp'), str(comm), *objects,
             '-rdynamic', '-ldl', '-lcrypt', '-lcurl', '-o', str(binary)], check=True)
        result = subprocess.run([str(binary)], cwd=scratch / 'area', timeout=30,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Check actual log output for both accepted and rejected password submissions.
        for secret in ('LoginSecret73', 'WrongSecret84', 'tiny',
                       'overridepassword', 'OVERRIDEPASSWORD'):
            if secret in result.stderr:
                raise AssertionError('A submitted password appeared in server logs')
        if result.returncode:
            print(result.stdout)
            print(result.stderr)
            raise SystemExit(result.returncode)
        print(result.stdout, end='')
        print('PASS: submitted passwords absent from server logs.')


if __name__ == '__main__':
    main()
