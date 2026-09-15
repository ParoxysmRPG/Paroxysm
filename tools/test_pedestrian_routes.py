#!/usr/bin/env python3
"""Exercise production pedestrian paths/following under ASan/UBSan (WSL/Linux)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = r'''
#include "merc.h"
#include "global.h"
#include <cassert>
#include <map>
std::map<int, ROOM_INDEX_DATA *> world;
int lookups = 0;
time_t current_time = 1000;
const int trolly_stops[] = {100, 102, 103, 100};
const int trolly_stop_count = 4;
const sh_int rev_dir[] = {2, 3, 0, 1, 5, 4, 9, 8, 7, 6};
const char *dir_name[10][2] = {};
ROOM_INDEX_DATA *get_room_index(int vnum) {
  ++lookups;
  auto found = world.find(vnum);
  return found == world.end() ? nullptr : found->second;
}
bool pedestrian(CHAR_DATA *ch) { return ch && IS_NPC(ch) && ch->level == 1; }
bool in_fight(CHAR_DATA *ch) { return ch->in_fight; }
bool is_helpless(CHAR_DATA *ch) {
  return ch->position <= POS_SLEEPING || IS_FLAG(ch->act, PLR_BOUND)
      || IS_FLAG(ch->act, PLR_BOUNDFEET);
}
bool room_hostile(ROOM_INDEX_DATA *room) { return room->vnum == 999; }
int number_range(int low, int high) { assert(high >= low); return low; }
void char_from_room(CHAR_DATA *ch) { ch->in_room->people->remove(ch); ch->in_room = nullptr; }
void char_to_room(CHAR_DATA *ch, ROOM_INDEX_DATA *room) { ch->in_room = room; room->people->push_front(ch); }
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
int get_exit_x(int, ROOM_INDEX_DATA *) { return 2; }
int get_exit_y(int, ROOM_INDEX_DATA *) { return 3; }
#include "pedestrian_routes.c"

int main() {
  AREA_DATA town = {}, otherworld = {};
  town.vnum = 13; town.world = WORLD_EARTH;
  otherworld.vnum = 14; otherworld.world = WORLD_OTHER;
  ROOM_INDEX_DATA rooms[10] = {};
  CharList people[10];
  for (int i = 0; i < 10; ++i) {
    rooms[i].vnum = 100 + i; rooms[i].area = &town;
    rooms[i].sector_type = SECT_STREET; rooms[i].people = &people[i];
    world[100 + i] = &rooms[i];
  }
  rooms[4].sector_type = SECT_HOUSE;
  rooms[4].room_flags = ROOM_INDOORS | ROOM_PRIVATE;
  rooms[5].room_flags = ROOM_PRIVATE;
  rooms[6].area = &otherworld;
  EXIT_DATA exits[20] = {};
  int used = 0;
  auto link = [&](int a, int door, int b) {
    EXIT_DATA *exit = &exits[used++]; exit->u1.to_room = &rooms[b];
    rooms[a].exit[door] = exit;
  };
  // Main A-B-C corridor and longer A-H-I-C detour, plus an isolated stop.
  link(0, 1, 1); link(1, 3, 0); link(1, 1, 2); link(2, 3, 1);
  link(0, 0, 7); link(7, 2, 0); link(7, 1, 8); link(8, 3, 7);
  link(8, 2, 2); link(2, 0, 8);
  link(1, 0, 4); link(0, 2, 5); link(0, 6, 6);
  assert(pedestrian_route_ready());
  assert(stops.size() == 3 && spawn_stops.size() == 2);
  assert(!street_index.count(104) && !street_index.count(105) && !street_index.count(106));
  for (int i = 0; i < 30; ++i) {
    int vnum = pedestrian_spawn_room(i)->vnum;
    assert(vnum == 100 || vnum == 102);
  }
  CHAR_DATA mob = {}, player = {}, shop = {};
  SET_FLAG(mob.act, ACT_IS_NPC); mob.level = 1; mob.position = POS_STANDING;
  SET_FLAG(shop.act, ACT_IS_NPC); shop.level = 2; shop.position = POS_STANDING;
  player.position = POS_STANDING;
  char_to_room(&mob, &rooms[0]);
  assert(pedestrian_walk_step(&mob) && mob.in_room == &rooms[1]);
  const int before_steps = lookups;
  // A closure is checked live; it cannot teleport through the cached path.
  SET_BIT(rooms[1].exit[1]->exit_info, EX_CLOSED);
  assert(!pedestrian_walk_step(&mob) && mob.in_room == &rooms[1]);
  assert(lookups == before_steps);
  current_time += 59;
  assert(!pedestrian_walk_step(&mob) && lookups == before_steps);
  ++current_time;
  assert(pedestrian_walk_step(&mob) && mob.in_room == &rooms[0]);
  assert(pedestrian_walk_step(&mob) && mob.in_room == &rooms[7]);
  assert(pedestrian_walk_step(&mob) && mob.in_room == &rooms[8]);
  assert(pedestrian_walk_step(&mob) && mob.in_room == &rooms[2]);
  REMOVE_BIT(rooms[1].exit[1]->exit_info, EX_CLOSED);
  const int cached_lookups = lookups;
  for (int i = 0; i < 100; ++i) assert(pedestrian_walk_step(&mob));
  assert(lookups == cached_lookups); // No per-pedestrian world/path search.

  char_from_room(&mob); char_to_room(&mob, &rooms[1]);
  char_to_room(&player, &rooms[4]); mob.master = &player;
  assert(!pedestrian_walk_step(&mob));
  SET_BIT(rooms[1].exit[0]->exit_info, EX_LOCKED);
  assert(!pedestrian_move(&mob, 0, true));
  REMOVE_BIT(rooms[1].exit[0]->exit_info, EX_LOCKED);
  assert(pedestrian_move(&mob, 0, true) && mob.in_room == &rooms[4]);
  assert(!destinations.count(&mob));
  char_from_room(&mob); char_to_room(&mob, &rooms[1]);
  SET_FLAG(mob.act, PLR_BOUND);
  assert(!pedestrian_move(&mob, 0, true));
  player.lifting = &mob; player.x = 7; player.y = 9;
  assert(pedestrian_move(&mob, 0, true) && mob.x == 7 && mob.y == 9);
  char_from_room(&mob); char_to_room(&mob, &rooms[1]);
  mob.position = POS_SLEEPING; player.lifting = nullptr;
  assert(!pedestrian_move(&mob, 0, true));
  player.dragging = &mob;
  assert(pedestrian_move(&mob, 0, true));
  char_from_room(&mob); char_to_room(&mob, &rooms[1]);
  player.in_fight = true;
  assert(!pedestrian_move(&mob, 0, true));
  char_to_room(&shop, &rooms[0]);
  assert(!pedestrian_walk_step(&shop) && !pedestrian_move(&shop, 1, false));
  assert(!pedestrian_walk_step(nullptr));
  pedestrian_forget_route(&mob);
  char_from_room(&mob); char_from_room(&shop); char_from_room(&player);
  puts("PASS: shared routes, isolated/public/world guards, live doors, bounded retry, hypnosis follow, binding, KO, carried/dragged movement, and shop exclusion");
}
'''
with tempfile.TemporaryDirectory(prefix='haven-pedestrian-routes-') as temporary:
    path = Path(temporary)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-fsanitize=address,undefined', '-no-pie',
                    '-I', str(ROOT / 'src'), str(path / 'test.cc'), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
