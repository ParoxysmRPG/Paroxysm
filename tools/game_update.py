#!/usr/bin/env python3
"""Stage source updates and atomically replace ONLY src/haven (Linux)."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import signal
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def regular(path):
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"Expected a regular file, not a symlink: {path}")


def atomic_write(path, data, mode=0o600):
    fd, name = tempfile.mkstemp(prefix=".update-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fchmod(stream.fileno(), mode)
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class Updater:
    def __init__(self, root):
        self.root = root.resolve()
        self.state = self.root / ".updates"
        for directory in (self.root / "src", self.root / "area", self.root / "tools"):
            if directory.is_symlink() or not directory.is_dir():
                raise RuntimeError(f"Expected a real server directory: {directory}")
        if self.state.is_symlink():
            raise RuntimeError(".updates must not be a symlink")
        self.state.mkdir(mode=0o700, exist_ok=True)
        self.live = self.root / "src/haven"
        self.env = os.environ.copy()
        # Unattended fetches must fail instead of waiting for credentials.
        self.env.update(GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="Never",
                        GIT_SSH_COMMAND="ssh -oBatchMode=yes")
        # The server's shell must not redirect our private git/build operations.
        for key in list(self.env):
            if key.startswith("GIT_") and key not in ("GIT_TERMINAL_PROMPT", "GIT_SSH_COMMAND"):
                del self.env[key]
        for key in ("MAKEFLAGS", "MFLAGS", "MAKEFILES"):
            self.env.pop(key, None)

    def status(self, message):
        text = f"{datetime.now(timezone.utc).isoformat()} {message}\n"
        atomic_write(self.state / "status.txt", text.encode())
        print(text, end="", flush=True)

    def run(self, args, cwd=None, timeout=300, output=None):
        print("Running: " + " ".join(map(str, args)), flush=True)
        # Own process group lets timeouts kill make AND its compiler children.
        process = subprocess.Popen(args, cwd=cwd or self.state, env=self.env,
                                   stdin=subprocess.DEVNULL, stdout=output,
                                   start_new_session=True)
        try:
            result = process.wait(timeout=timeout)
        except BaseException:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise
        if result:
            raise RuntimeError(f"{args[0]} exited with status {result}; see gameupdate log")

    def extract_source(self, archive, target):
        # Never extract world/player files, links, devices or traversing paths.
        with tarfile.open(archive) as source:
            for member in source:
                path = PurePosixPath(member.name)
                if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "src":
                    raise RuntimeError(f"Unsafe archive path: {member.name}")
                if not (member.isdir() or member.isfile()):
                    raise RuntimeError(f"Source archive contains a link/special file: {member.name}")
                if ".build" in path.parts or path.suffix in (".o", ".d") or str(path) == "src/haven":
                    continue
                destination = target.joinpath(*path.parts)
                if member.isdir():
                    destination.mkdir(parents=True, exist_ok=True)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with source.extractfile(member) as incoming, destination.open("wb") as outgoing:
                        shutil.copyfileobj(incoming, outgoing)
                    destination.chmod(0o700 if member.mode & 0o111 else 0o600)

    def build(self):
        # Invalidate any older candidate even if this build fails.
        (self.state / "ready.json").unlink(missing_ok=True)
        regular(self.live)
        base = digest(self.live)
        config_path = self.root / "game-update.json"
        config = json.loads(config_path.read_text()) if config_path.exists() else {}
        repository = config.get("repository", "https://github.com/ParoxysmRPG/Paroxysm.git")
        branch = config.get("branch", "main")
        jobs = config.get("jobs", 2)
        if not isinstance(repository, str) or not repository or repository.startswith("-"):
            raise RuntimeError("Invalid update repository")
        if not isinstance(branch, str) or not branch or branch.startswith("-"):
            raise RuntimeError("Invalid update branch")
        if type(jobs) is not int or not 1 <= jobs <= 8:
            raise RuntimeError("jobs must be an integer from 1 to 8")
        self.run(["git", "check-ref-format", "refs/heads/" + branch])
        with tempfile.TemporaryDirectory(prefix="build-", dir=self.state) as directory:
            workspace = Path(directory)
            repo = workspace / "repo.git"
            self.run(["git", "init", "--bare", str(repo)])
            git = ["git", "--git-dir", str(repo)]
            self.status(f"RUNNING: fetching branch {branch}")
            self.run(git + ["fetch", "--depth=1", "--no-tags", "--", repository, "refs/heads/" + branch])
            commit_file = workspace / "commit.txt"
            with commit_file.open("wb") as output:
                self.run(git + ["rev-parse", "FETCH_HEAD"], output=output)
            commit = commit_file.read_text().strip()
            archive = workspace / "source.tar"
            self.run(git + ["archive", "--format=tar", "--output=" + str(archive), commit, "src"])
            source = workspace / "source"
            self.extract_source(archive, source)
            self.status(f"RUNNING: compiling {commit} with {jobs} jobs")
            self.run(["make", "-j" + str(jobs), "BUILD=release", "SANITIZE=0", "haven"],
                     cwd=source / "src", timeout=3600)
            candidate = source / "src/haven"
            regular(candidate)
            with candidate.open("rb") as stream:
                if stream.read(4) != b"\x7fELF":
                    raise RuntimeError("Build did not produce a Linux ELF executable")
            symbols = workspace / "symbols.txt"
            with symbols.open("wb") as output:
                self.run(["nm", "-D", "--defined-only", str(candidate)], output=output)
            if not any(line.split()[-1:] == ["do_gameupdate"] for line in symbols.read_text().splitlines()):
                raise RuntimeError("Fetched source lacks gameupdate. Push the updater changes to this branch first.")
            atomic_write(self.state / "candidate-haven", candidate.read_bytes(), 0o700)
            metadata = {"commit": commit, "sha256": digest(self.state / "candidate-haven"), "base": base}
            atomic_write(self.state / "ready.json", json.dumps(metadata).encode())
            self.status(f"READY: {commit}. Use gameupdate install, then copyover now when ready.")

    def install(self):
        metadata = json.loads((self.state / "ready.json").read_text())
        candidate = self.state / "candidate-haven"
        regular(candidate)
        regular(self.live)
        if digest(candidate) != metadata["sha256"]:
            raise RuntimeError("Candidate checksum mismatch; build again")
        if digest(self.live) != metadata["base"]:
            raise RuntimeError("Live executable changed since build; build again")
        # Finish a durable backup BEFORE changing the executable used at restart.
        atomic_write(self.state / "previous-haven", self.live.read_bytes(), 0o700)
        atomic_write(self.state / "previous.sha256", digest(self.state / "previous-haven").encode())
        atomic_write(self.live, candidate.read_bytes(), 0o700)
        (self.state / "ready.json").unlink()
        self.status(f"INSTALLED: {metadata['commit']}. Running game is unchanged until copyover/restart. "
                    "Use copyover now when ready. Previous executable saved for gameupdate rollback.")

    def rollback(self):
        previous = self.state / "previous-haven"
        regular(previous)
        regular(self.live)
        if digest(previous) != (self.state / "previous.sha256").read_text().strip():
            raise RuntimeError("Previous executable checksum mismatch; rollback refused")
        atomic_write(self.live, previous.read_bytes(), 0o700)
        (self.state / "ready.json").unlink(missing_ok=True)
        self.status("ROLLED BACK: previous executable restored. Use copyover now, or restart if the game is down.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "install", "rollback", "status"))
    args = parser.parse_args()
    updater = Updater(Path(__file__).resolve().parents[1])
    lockfd = os.open(updater.state / "lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lockfd, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Another update operation is running. Try gameupdate status later.", flush=True)
            return 1
        if args.action == "status":
            path = updater.state / "status.txt"
            print("Updater idle. " + (path.read_text() if path.exists() else "No updates yet."))
            return 0
        try:
            updater.status("RUNNING: " + args.action)
            getattr(updater, args.action)()
            return 0
        except Exception as error:
            updater.status(f"FAILED ({args.action}): {error}. Check gameupdate log. No restart was requested.")
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
