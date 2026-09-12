#!/usr/bin/env python3
"""Run the production walking deadline under ASan/UBSan (WSL/Linux)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
movement = (ROOT / 'src/act_move.c').read_text()
start = movement.index('  bool finish_overdue_walk(')
helper = movement[start:movement.index('  _DOFUN(do_walk)', start)]
source = r'''
#include "merc.h"
#include <cassert>
time_t current_time = 1000;
int looks = 0;
void char_from_room(CHAR_DATA *ch) { ch->in_room = nullptr; }
void char_to_room(CHAR_DATA *ch, ROOM_INDEX_DATA *room) { ch->in_room = room; }
void send_to_char(const char *, CHAR_DATA *) {}
void do_look(CHAR_DATA *, char *) { ++looks; }
void do_function(CHAR_DATA *ch, DO_FUN *function, char *argument) { function(ch, argument); }
''' + helper + r'''
int main() {
  CHAR_DATA ch = {};
  PC_DATA pc = {};
  AREA_DATA area = {};
  ROOM_INDEX_DATA a = {}, b = {}, destination = {};
  a.area = b.area = destination.area = &area;
  ch.pcdata = &pc; ch.walking = 1; ch.walk_started_at = 1000;
  ch.destination = &destination;
  for (int elapsed = 0; elapsed <= 600; ++elapsed) {
    current_time = 1000 + elapsed;
    ch.in_room = elapsed % 2 ? &a : &b; // A looping route never resets the clock.
    assert(!finish_overdue_walk(&ch));
    assert(ch.in_room != &destination && ch.walk_started_at == 1000);
  }
  current_time = 1601; ch.wait = 100;
  assert(finish_overdue_walk(&ch) && ch.in_room == &destination && looks == 1);
  assert(ch.walking == 0 && !ch.destination && ch.walk_started_at == 0);
  assert(!finish_overdue_walk(&ch) && looks == 1);
  ch.walking = 1; ch.destination = &destination; ch.in_room = &a;
  assert(!finish_overdue_walk(&ch) && ch.walk_started_at == current_time);
  ch.walking = 0; current_time += 601;
  assert(!finish_overdue_walk(&ch) && ch.in_room == &a && ch.walk_started_at == 0);
  ch.walking = 1; ch.destination = nullptr;
  assert(!finish_overdue_walk(&ch));
  assert(!finish_overdue_walk(nullptr));
  puts("PASS: looping walks, exact ten-minute boundary, one-time teleport, wait states and cancellation");
}
'''
with tempfile.TemporaryDirectory(prefix='haven-walk-test-') as temporary:
    path = Path(temporary)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-fsanitize=address,undefined', '-no-pie',
                    '-I', str(ROOT / 'src'), str(path / 'test.cc'), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
