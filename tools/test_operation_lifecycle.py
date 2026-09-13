#!/usr/bin/env python3
"""Test real operation resolution in a disposable world after make -C src.

The full engine is linked so command-test stubs cannot hide completion bugs.
Run under Linux/WSL; live world and player files are never changed.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "src/.build-local/release-sanitize0"
SOURCE = r'''
#include "merc.h"
#include "recycle.h"
#include <cassert>
#include <cstring>
#include <ctime>
extern "C" {
extern char str_boot_time[];
extern bool isactiveoperation;
void win_operation(int, OPERATION_TYPE *);
void do_operation(CHAR_DATA *, char *);
}
static OPERATION_TYPE *operation(FACTION_TYPE *host) {
  auto *op = new_operation();
  op->faction = host->vnum; op->territoryvnum = 1;
  op->hour = 12; op->day = 2; op->goal = GOAL_CONTROL;
  op->competition = COMPETE_OPEN; op->max_pcs = 5; op->speed = 3;
  return op;
}
int main() {
  setvbuf(stdout, nullptr, _IONBF, 0);
  current_time = time(nullptr); strcpy(str_boot_time, ctime(&current_time));
  boot_db();
  auto *host = new_faction();
  host->vnum = 990121; host->type = FACTION_SOCIETY;
  host->alliance = ALLIANCE_SIDELEFT; host->resource = 100000;
  host->manpower = 20;
  free_string(host->name); host->name = str_dup("Operationtesters");
  FacVect.push_back(host);
  auto *actor = new_char(); actor->pcdata = new_pcdata();
  free_string(actor->name); actor->name = str_dup("Operationtester");
  actor->level = MAX_LEVEL; actor->faction = host->vnum;
  auto *op = operation(host); op->home_soldiers = 4;
  OpVect.clear(); OpVect.push_back(op);
  activeoperation = nullptr; isactiveoperation = false;
  char bribe[] = "bribe 1";
  do_operation(actor, bribe);
  assert(op->hour == 0 && host->manpower == 24 && host->operation_wins == 1);
  const auto resources = host->resource;
  assert(resources < 100000);
  char repeat[] = "bribe 1";
  do_operation(actor, repeat);
  assert(host->resource == resources && host->manpower == 24 && host->operation_wins == 1);
  puts("PASS: a bribed operation retires; repeated commands cannot charge or refund it again.");

  auto *unrelated = operation(host); unrelated->hour = 15;
  activeoperation = unrelated; isactiveoperation = false;
  auto *pending = operation(host);
  win_operation(host->vnum, pending);
  assert(pending->hour == 0 && unrelated->hour == 15);
  assert(activeoperation == unrelated && !isactiveoperation);
  isactiveoperation = true;
  pending = operation(host);
  win_operation(host->vnum, pending);
  assert(pending->hour == 0 && unrelated->hour == 15 && isactiveoperation);
  puts("PASS: explicit operation resolution retires its argument without altering another operation.");

  activeoperation = operation(host); isactiveoperation = true;
  win_operation(host->vnum, nullptr);
  assert(activeoperation->hour == 0 && !isactiveoperation);
  puts("PASS: battlefield victory still retires the active operation and clears battle state.");

  activeoperation = operation(host); activeoperation->goal = GOAL_PSYCHIC;
  isactiveoperation = true;
  win_operation(200000, nullptr);
  assert(activeoperation->hour == 0 && !isactiveoperation);
  puts("PASS: psychic defense victory retires its operation and clears battle state.");

  activeoperation = operation(host); activeoperation->goal = GOAL_PSYCHIC;
  free_string(activeoperation->target);
  activeoperation->target = str_dup("Absentpsychictarget");
  isactiveoperation = true;
  win_operation(300000, nullptr);
  assert(activeoperation->hour == 0 && !isactiveoperation);
  puts("PASS: psychic attack victory retires even if the offline target no longer exists.");
}
'''

with tempfile.TemporaryDirectory(prefix="operation-lifecycle-") as temporary:
    scratch = Path(temporary)
    for name in ("area", "data", "accounts", "gods"):
        shutil.copytree(ROOT / name, scratch / name,
                        ignore=shutil.ignore_patterns("back[1-7]"))
    (scratch / "log").mkdir()
    (scratch / "player").mkdir()
    comm = scratch / "comm-test.o"
    shutil.copy2(BUILD / "comm.o", comm)
    subprocess.run(["objcopy", "--redefine-sym", "main=operation_game_main", str(comm)], check=True)
    makefile = (ROOT / "src/Makefile").read_text()
    objects_text = re.search(r"^O_FILES\s*=\s*(.*?)(?=\n\n)", makefile, re.M | re.S)[1]
    objects = [str(BUILD / name) for name in re.findall(r"[\w-]+\.o\b", objects_text)
               if name != "comm.o"]
    cpp, binary = scratch / "test.cpp", scratch / "test"
    cpp.write_text(SOURCE)
    subprocess.run(["g++", "-g", "-Wno-deprecated", "-Wno-write-strings",
                    "-I" + str(ROOT / "src"), str(cpp), str(comm), *objects,
                    "-rdynamic", "-ldl", "-lcrypt", "-lcurl", "-o", str(binary)], check=True)
    result = subprocess.run([str(binary)], cwd=scratch / "area", stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, errors="replace", timeout=120)
    (BUILD.parent / "operation-lifecycle-test.log").write_text(result.stdout)
    lines = result.stdout.splitlines()
    print("\n".join(lines[-50:] if result.returncode else
                    [line for line in lines if "PASS:" in line]))
    raise SystemExit(result.returncode)
