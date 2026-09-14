#!/usr/bin/env python3
"""Exercise the production wake command's warfare protection (WSL/Linux)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
movement = (ROOT / "src/act_move.c").read_text()
start = movement.index("  _DOFUN(do_wake) {")
command = movement[start:movement.index("  _DOFUN(do_visible)", start)]
source = r'''
#include "merc.h"
#include <cassert>
#include <cstring>
#undef PERS
#define PERS(ch, looker) "someone"
time_t current_time = 1000;
CHAR_DATA *room_target = nullptr;
int awakenings = 0;
bool dream_slave(CHAR_DATA *) { return false; }
bool is_dreaming(CHAR_DATA *) { return false; }
bool physical_dreamer(CHAR_DATA *) { return false; }
bool is_helpless(CHAR_DATA *) { return false; }
bool in_fight(CHAR_DATA *ch) { return ch->in_fight; }
bool is_gm(CHAR_DATA *) { return false; }
int get_trust(CHAR_DATA *) { return 0; }
bool room_hostile(ROOM_INDEX_DATA *) { return false; }
void start_hostilefight(CHAR_DATA *) {}
void send_to_char(const char *, CHAR_DATA *) {}
void printf_to_char(CHAR_DATA *, const char *, ...) {}
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
char *dream_name(CHAR_DATA *) { static char name[] = "someone"; return name; }
void dreamscape_message(CHAR_DATA *, int, char *) {}
void to_spectre(CHAR_DATA *, bool) {}
void wake_char(CHAR_DATA *ch) { ++awakenings; ch->pcdata->spectre = 0; }
void do_stand(CHAR_DATA *, char *) {}
void do_function(CHAR_DATA *ch, DO_FUN *fn, char *argument) { fn(ch, argument); }
char *one_argument(char *argument, char *arg) { strcpy(arg, argument); return argument + strlen(argument); }
CHAR_DATA *get_char_room(CHAR_DATA *, ROOM_INDEX_DATA *, char *) { return room_target; }
''' + command + r'''
int main() {
  CHAR_DATA outsider = {}, target = {};
  PC_DATA outside_pc = {}, target_pc = {};
  DESCRIPTOR_DATA descriptor = {};
  outsider.pcdata = &outside_pc;
  target.pcdata = &target_pc;
  target.desc = &descriptor;
  room_target = &target;
  char named[] = "target", self[] = "";
  // An ordinary outsider must not pull either side out before combat starts,
  // including during search pauses or while followers wait for their leader.
  for (int state : {PATROL_ATTACKSEARCHING, PATROL_ATTACKWAITING,
                    PATROL_ATTACKASSISTING, PATROL_DEFENDASSISTING,
                    PATROL_DEFENDHIDING, PATROL_WAGINGWAR}) {
    target_pc.patrol_status = state;
    target_pc.spectre = 1;
    target.in_fight = false;
    awakenings = 0;
    do_wake(&outsider, named);
    assert(awakenings == 0 && target_pc.spectre == 1);
    // The existing self-wake protection must continue to hold too.
    do_wake(&target, self);
    assert(awakenings == 0 && target_pc.spectre == 1);
  }
  // Ending the event restores normal wake behavior.
  target_pc.patrol_status = 0;
  do_wake(&outsider, named);
  assert(awakenings == 1 && target_pc.spectre == 0);
  // Normal sleepers and idle patrollers also remain wakeable.
  target_pc.patrol_status = PATROL_PATROL;
  target_pc.sleeping = 20;
  do_wake(&outsider, named);
  assert(target_pc.sleeping == 0);
  puts("PASS: outsiders cannot wake warfare participants; normal wake still works");
}
'''
with tempfile.TemporaryDirectory(prefix="warfare-wake-") as temporary:
    path = Path(temporary)
    cpp, executable = path / "test.cc", path / "test"
    cpp.write_text(source)
    subprocess.run(["g++", "-std=gnu++17", "-w", "-fsanitize=address,undefined", "-no-pie",
                    "-I", str(ROOT / "src"), str(cpp), "-o", str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
