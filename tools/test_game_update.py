#!/usr/bin/env python3
"""Linux/WSL integration tests; all servers and Git remotes are disposable."""
import fcntl
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import game_update


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.remote = self.base / "remote"
        self.root = self.base / "live"
        self.remote.mkdir()
        self.root.mkdir()
        for directory in ("src", "area", "tools", "player", "accounts", "data", "gods", "bin"):
            (self.root / directory).mkdir()
        self.saved = {}
        for name in ("player/Alice", "player/GroundObjects", "accounts/Alice", "area/houses.are",
                     "area/world.are", "data/houses.txt", "data/commands.txt", "gods/Alice", "bin/startup",
                     "src/local.c"):
            (self.root / name).write_text("LIVE custom data: " + name)
            self.saved[name] = (self.root / name).read_bytes()
        (self.root / "src/haven").write_bytes(b"previous working executable")
        (self.root / "src/haven").chmod(0o700)
        shutil.copyfile(Path(game_update.__file__), self.root / "tools/game_update.py")
        (self.remote / "src").mkdir()
        (self.remote / "src/main.c").write_text('void do_gameupdate(void) {}\nint main(void) { return 0; }\n')
        (self.remote / "src/Makefile").write_text('haven:\n\tcc -rdynamic main.c -o haven\n')
        # Tracked build products and world files must not be installed.
        (self.remote / "src/haven").write_text("bogus tracked executable")
        (self.remote / "src/main.o").write_text("bogus tracked object")
        for name in self.saved:
            target = self.remote / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("UPSTREAM overwrite")
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Updater tests")
        self.git("config", "user.email", "tests@example.invalid")
        self.commit()
        (self.root / "game-update.json").write_text(json.dumps({"repository": str(self.remote)}))
        self.updater = game_update.Updater(self.root)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.remote), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-m", "fixture")

    def assert_data_unchanged(self):
        for name, expected in self.saved.items():
            self.assertEqual((self.root / name).read_bytes(), expected, name)
        self.assertFalse((self.root / ".git").exists())

    def test_build_install_rollback_preserves_data(self):
        self.updater.build()
        self.assertEqual(self.updater.live.read_bytes(), b"previous working executable")
        self.assert_data_unchanged()
        self.updater.install()
        self.assertEqual(subprocess.run([str(self.updater.live)]).returncode, 0)
        self.assert_data_unchanged()
        self.updater.rollback()
        self.assertEqual(self.updater.live.read_bytes(), b"previous working executable")
        self.assert_data_unchanged()

    def test_failed_build_invalidates_old_candidate(self):
        self.updater.build()
        (self.remote / "src/Makefile").write_text("haven:\n\tfalse\n")
        self.commit()
        with self.assertRaises(RuntimeError):
            self.updater.build()
        self.assertFalse((self.updater.state / "ready.json").exists())
        self.assertEqual(self.updater.live.read_bytes(), b"previous working executable")
        self.assert_data_unchanged()

    def test_failed_fetch_leaves_executable_and_data(self):
        (self.root / "game-update.json").write_text(json.dumps({"repository": str(self.base / "missing")}))
        with self.assertRaises(RuntimeError):
            self.updater.build()
        self.assertEqual(self.updater.live.read_bytes(), b"previous working executable")
        self.assert_data_unchanged()

    def test_candidate_tampering_refused(self):
        self.updater.build()
        (self.updater.state / "candidate-haven").write_bytes(b"tampered")
        with self.assertRaisesRegex(RuntimeError, "checksum"):
            self.updater.install()
        self.assertEqual(self.updater.live.read_bytes(), b"previous working executable")

    def test_manual_binary_change_refused(self):
        self.updater.build()
        self.updater.live.write_bytes(b"manual upgrade")
        with self.assertRaisesRegex(RuntimeError, "changed since build"):
            self.updater.install()
        self.assertEqual(self.updater.live.read_bytes(), b"manual upgrade")

    def test_failed_atomic_install_keeps_live_and_backup(self):
        self.updater.build()
        replace = game_update.os.replace
        def fail_live(source, destination):
            if destination == self.updater.live:
                raise OSError("simulated install failure")
            replace(source, destination)
        with patch.object(game_update.os, "replace", side_effect=fail_live):
            with self.assertRaises(OSError):
                self.updater.install()
        self.assertEqual(self.updater.live.read_bytes(), b"previous working executable")
        self.assertEqual((self.updater.state / "previous-haven").read_bytes(), self.updater.live.read_bytes())
        self.assert_data_unchanged()

    def test_missing_updater_symbol_refused(self):
        (self.remote / "src/main.c").write_text("int main(void) { return 0; }\n")
        self.commit()
        with self.assertRaisesRegex(RuntimeError, "lacks gameupdate"):
            self.updater.build()
        self.assertFalse((self.updater.state / "ready.json").exists())

    def test_unsafe_archives_refused(self):
        for name, kind in (("src/../../player/Alice", tarfile.REGTYPE),
                           ("/src/absolute", tarfile.REGTYPE),
                           ("player/Alice", tarfile.REGTYPE),
                           ("src/link", tarfile.SYMTYPE),
                           ("src/hardlink", tarfile.LNKTYPE)):
            with self.subTest(name=name):
                archive = self.base / "unsafe.tar"
                with tarfile.open(archive, "w") as output:
                    member = tarfile.TarInfo(name)
                    member.type = kind
                    member.linkname = "../../player/Alice" if kind != tarfile.REGTYPE else ""
                    output.addfile(member, io.BytesIO())
                with self.assertRaises(RuntimeError):
                    self.updater.extract_source(archive, self.base / "extract")
        self.assert_data_unchanged()

    def test_live_symlink_refused(self):
        self.updater.live.unlink()
        self.updater.live.symlink_to(self.root / "player/Alice")
        with self.assertRaisesRegex(RuntimeError, "symlink"):
            self.updater.build()
        self.assert_data_unchanged()

    def test_corrupt_rollback_refused(self):
        self.updater.build()
        self.updater.install()
        installed = self.updater.live.read_bytes()
        (self.updater.state / "previous-haven").write_bytes(b"bad backup")
        with self.assertRaisesRegex(RuntimeError, "checksum"):
            self.updater.rollback()
        self.assertEqual(self.updater.live.read_bytes(), installed)

    def test_concurrent_cli_operation_refused(self):
        with (self.updater.state / "lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = subprocess.run(["python3", str(self.root / "tools/game_update.py"), "build"],
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Another update operation", result.stdout)
        self.assert_data_unchanged()


if __name__ == "__main__":
    unittest.main()
