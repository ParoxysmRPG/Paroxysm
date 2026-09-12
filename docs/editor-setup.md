# C++ IntelliSense on Windows

The game compiles as C++ with Linux g++, including files ending in `.c`.
Windows SDK headers cannot supply Linux headers such as `sys/time.h` and
`unistd.h`.

For a Windows VS Code window with Ubuntu installed in WSL, run this from the
repository root in PowerShell:

```powershell
wsl --exec python3 tools/configure_intellisense.py
```

This discovers g++'s actual include directories and copies their headers into
`.vscode/linux-headers/`, which Git ignores. It updates the `Win32` IntelliSense
configuration to use those local paths and Linux GCC mode. No game sources or
build settings change. It also copies GCC's integer-limit macro definitions,
which the cached headers need for `INT_MAX` and related constants when Windows
IntelliSense has no compiler to query. Repeat the command after upgrading the WSL
compiler or system development packages, or when setting up another checkout.

If existing diagnostics remain, run **C/C++: Select a Configuration** and choose
**Win32**, then run **C/C++: Reset IntelliSense Database** and
**Developer: Reload Window** from the command palette.

Alternatively, use **WSL: Reopen Folder in WSL** and install the C/C++ extension
in WSL. The `Linux` configuration uses `/usr/bin/g++` directly and does not need
the copied headers. See Microsoft's [C++ with WSL guide](https://code.visualstudio.com/docs/cpp/config-wsl).
