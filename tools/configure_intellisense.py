#!/usr/bin/env python3
"""Run in WSL to give Windows IntelliSense a local copy of Linux headers.

From PowerShell: wsl --exec python3 tools/configure_intellisense.py
The Linux configuration continues to query /usr/bin/g++ directly.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess


def compiler_integer_limits(compiler):
    # With compilerPath="", IntelliSense cannot query GCC's builtins. The
    # copied limits.h uses these macros to define INT_MAX and related limits.
    probe = subprocess.run(
        [compiler, "-std=gnu++17", "-dM", "-E", "-x", "c++", "/dev/null"],
        check=True, capture_output=True, text=True,
    )
    macros = {}
    for line in probe.stdout.splitlines():
        parts = line.split(maxsplit=2)
        if len(parts) == 3 and parts[0] == "#define":
            macros[parts[1]] = parts[2]
    names = ("__CHAR_BIT__", "__SCHAR_MAX__", "__SHRT_MAX__", "__INT_MAX__",
             "__LONG_MAX__", "__LONG_LONG_MAX__")
    return {name: macros[name] for name in names}


def main():
    root = Path(__file__).resolve().parents[1]
    compiler = shutil.which("g++")
    if not compiler:
        raise SystemExit("Run this script in Linux/WSL with g++ installed.")
    probe = subprocess.run(
        [compiler, "-std=gnu++17", "-E", "-x", "c++", "-v", "/dev/null"],
        check=True, capture_output=True, text=True, env={**os.environ, "LC_ALL": "C"},
    )
    includes = []
    collecting = False
    for line in probe.stderr.splitlines():
        if line == "#include <...> search starts here:":
            collecting = True
        elif line == "End of search list.":
            break
        elif collecting:
            path = Path(line.strip())
            if not path.is_absolute() or not path.is_dir():
                raise SystemExit("Unexpected compiler include directory: " + line)
            includes.append(path)
    if not includes:
        raise SystemExit("Could not discover g++ system header directories.")

    cache = root / ".vscode/linux-headers"
    if cache.is_symlink():
        raise SystemExit("The local header cache must not be a symlink.")
    cache.mkdir(parents=True, exist_ok=True)
    # Parent include directories already contain several of the compiler paths.
    parents = [p for p in includes if not any(other in p.parents for other in includes)]
    for source in parents:
        destination = cache / source.relative_to("/")
        print("Copying headers from " + str(source), flush=True)
        # Dereference Linux links so Windows doesn't need WSL to read the cache.
        shutil.copytree(source, destination, symlinks=False, dirs_exist_ok=True)

    settings_path = root / ".vscode/c_cpp_properties.json"
    settings = (json.loads(settings_path.read_text()) if settings_path.exists()
                else {"configurations": [], "version": 4})
    configurations = settings.setdefault("configurations", [])
    windows = next((c for c in configurations if c["name"] == "Win32"), None)
    if windows is None:
        windows = {"name": "Win32"}
        configurations.append(windows)
    if not any(c["name"] == "Linux" for c in configurations):
        configurations.append({
            "name": "Linux",
            "compilerPath": compiler,
            "intelliSenseMode": "linux-gcc-x64",
            "includePath": ["${workspaceFolder}/src", "${workspaceFolder}/src/rapidjson"],
            "cppStandard": "gnu++17",
        })
    limits = compiler_integer_limits(compiler)
    defines = [d for d in windows.get("defines", []) if d.split("=", 1)[0] not in limits]
    defines.extend(name + "=" + value for name, value in limits.items())
    windows.update(
        compilerPath="",
        intelliSenseMode="linux-gcc-x64",
        includePath=["${workspaceFolder}/src", "${workspaceFolder}/src/rapidjson"] + [
            "${workspaceFolder}/.vscode/linux-headers/" + p.relative_to("/").as_posix()
            for p in includes
        ],
        cppStandard="gnu++17",
        defines=defines,
    )
    temporary = settings_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(settings, indent=4) + "\n")
    temporary.replace(settings_path)

    # The Makefile uses g++ even for .c files; VS Code otherwise treats them as C.
    editor_path = root / ".vscode/settings.json"
    editor = json.loads(editor_path.read_text()) if editor_path.exists() else {}
    editor.setdefault("files.associations", {}).update({"*.c": "cpp", "*.h": "cpp"})
    temporary = editor_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(editor, indent=4) + "\n")
    temporary.replace(editor_path)
    print("Windows IntelliSense now uses local Linux headers. Reload VS Code if diagnostics persist.")


if __name__ == "__main__":
    main()
