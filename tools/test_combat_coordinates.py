#!/usr/bin/env python3
"""Check production movement geometry and effect consumption under ASan/UBSan."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
fight = (ROOT / 'src/fight.c').read_text()


def section(start, end):
    offset = fight.index(start)
    return fight[offset:fight.index(end, offset)]


source = r'''
#include "merc.h"
#include <cassert>
#include <climits>
#include <cmath>
CHAR_DATA actor = {}, target = {};
PC_DATA pc = {};
ROOM_INDEX_DATA room = {};
CharList people;
int lower_calls = 0;
bool has_caff(CHAR_DATA *ch, int affect) {
  for (int i = 0; i < 30; ++i)
    if (ch->caff[i] == affect && ch->caff_duration[i] > 0) return true;
  return false;
}
void lower_caff(CHAR_DATA *ch, int affect) {
  ++lower_calls;
  for (int i = 0; i < 30; ++i)
    if (ch->caff[i] == affect && ch->caff_duration[i] > 0) --ch->caff_duration[i];
}
void remove_caff(CHAR_DATA *ch, int affect) {
  for (int i = 0; i < 30; ++i)
    if (ch->caff[i] == affect) ch->caff_duration[i] = 0;
}
void apply_caff(CHAR_DATA *, int, int) {}
bool same_fight(CHAR_DATA *, CHAR_DATA *) { return true; }
bool is_in_cover(CHAR_DATA *) { return false; }
CHAR_DATA *get_cover(CHAR_DATA *) { return nullptr; }
int relative_x(CHAR_DATA *ch, ROOM_INDEX_DATA *, int x) { return x - ch->x; }
int relative_y(CHAR_DATA *ch, ROOM_INDEX_DATA *, int y) { return y - ch->y; }
int get_speed(CHAR_DATA *) { return 20; }
int max_hp(CHAR_DATA *) { return 100; }
int fight_speed(CHAR_DATA *) { return 1; }
int temperature(ROOM_INDEX_DATA *) { return 70; }
bool has_gasmask(CHAR_DATA *) { return false; }
bool is_undead(CHAR_DATA *) { return false; }
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
void send_to_char(const char *, CHAR_DATA *) {}
void noattack(CHAR_DATA *) {}
void combat_damage(CHAR_DATA *, CHAR_DATA *, int, int) {}
void summon_cobj(ROOM_INDEX_DATA *, int, int, int, int, CHAR_DATA *) {}
void to_combat_room(CHAR_DATA *, ROOM_INDEX_DATA *, int) { assert(false); }
int move_caff_mod(CHAR_DATA *, int);
'''
source += section('  // Retreat vectors are extended', '  int get_speed(CHAR_DATA *ch) {')
source += section('  int get_dist(int xone,', '  void move_message(')
source += section('  int move_caff_mod(CHAR_DATA *ch, int dist) {', '  void nomove(')
source += section('  void move_relative(CHAR_DATA *ch, int x, int y, int z) {', '  CHAR_DATA *get_char_fight(')
source += r'''
void reset() {
  actor = {}; target = {}; pc = {}; room = {}; people.clear();
  actor.pcdata = &pc; actor.in_room = target.in_room = &room;
  actor.x = actor.y = 100; room.size = 1000; room.people = &people;
  lower_calls = 0;
}
void effect(int affect, int duration = 4) {
  for (int i = 0; i < 30; ++i) if (actor.caff_duration[i] == 0) {
    actor.caff[i] = affect; actor.caff_duration[i] = duration; return;
  }
  assert(false);
}
int main() {
  assert(get_dist(0, 0, 0, 0) == 1);
  assert(get_dist(0, 0, 3, 4) == 5);
  assert(get_dist(0, 0, 50000, 50000) == 70710);
  assert(get_dist(INT_MIN, INT_MIN, INT_MAX, INT_MAX) == INT_MAX);
  reset(); move_towards(&actor, 50000, 50000, 10, 0, true);
  assert(actor.x == 107 && actor.y == 107 && actor.moved == 10);
  assert(actor.facing == DIR_NORTHEAST && actor.move_timer == FIGHT_WAIT);
  reset(); move_towards(&actor, INT_MAX, INT_MIN, 100, 0, false);
  assert(actor.x == 170 && actor.y == 30 && actor.move_timer == 0);
  assert(actor.facing == DIR_SOUTHEAST);
  reset(); move_away(&actor, INT_MAX, INT_MIN, 100, 0, true);
  assert(actor.x == 30 && actor.y == 170 && actor.facing == DIR_NORTHWEST);
  // Large target vectors used to overflow or round their entire step to zero.
  for (int x : {INT_MIN, -50000, -100, 0, 100, 50000, INT_MAX})
    for (int y : {INT_MIN, -50000, -100, 0, 100, 50000, INT_MAX}) {
      reset(); actor.x = actor.y = 500;
      move_towards(&actor, x, y, 20, 0, true);
      assert(std::hypot(actor.x - 500, actor.y - 500) <= 21);
      if (x != 0 || y != 0) assert(actor.x != 500 || actor.y != 500);
      assert((long long)(actor.x - 500) * x >= 0);
      assert((long long)(actor.y - 500) * y >= 0);
    }
  // Retreat must slow once and consume one duration, just like approaching.
  reset(); effect(CAFF_SLOW);
  move_away(&actor, 100, 0, 20, 0, true);
  assert(actor.x == 90 && actor.y == 100 && actor.moved == 10);
  assert(lower_calls == 1 && actor.caff_duration[0] == 3);
  reset(); effect(CAFF_SPRINTING);
  move_away(&actor, 100, 0, 20, 0, true);
  assert(actor.x == 70 && actor.moved == 30 && lower_calls == 1);
  reset(); effect(CAFF_FEAR); effect(CAFF_SLOW); actor.afraid_of = &target;
  target.x = 200; target.y = 100;
  move_towards(&actor, 100, 0, 20, 0, true);
  assert(actor.x == 90 && actor.moved == 10 && lower_calls == 1);
  // Narrowing and sign reversal remain defined at the integer boundaries.
  reset(); move_towards(&actor, 100, 0, INT_MIN, 0, true);
  assert(actor.x == 0);
  reset(); move_away(&actor, 100, 0, INT_MIN, 0, true);
  assert(actor.x == 200);
  reset(); actor.moved = INT_MAX; move_towards(&actor, 10, 0, 10, 0, true);
  assert(actor.moved == INT_MAX);
  reset(); effect(CAFF_SPRINTING); effect(CAFF_AMESSENGER);
  pc.divine_focus = CAFF_AMESSENGER;
  assert(move_caff_mod(&actor, INT_MAX) == INT_MAX && lower_calls == 2);
  reset(); actor.x = actor.y = INT_MAX - 2;
  move_relative(&actor, 10, 10, 0);
  assert(actor.x == room.size && actor.y == room.size);
  puts("PASS: large movement vectors, bounded distances, retreat effects and integer limits");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-combat-coordinates-') as temporary:
    path = Path(temporary)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-fsanitize=address,undefined,float-cast-overflow',
                    '-fno-sanitize-recover=all', '-no-pie', '-I', str(ROOT / 'src'),
                    str(path / 'test.cc'), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
