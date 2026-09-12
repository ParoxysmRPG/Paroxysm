#!/usr/bin/env python3
"""Exercise production operation helpers with instrumented C++ engine stubs.

Run under Linux/WSL: python3 tools/test_operation_optimization.py (requires g++).
No game data is loaded or changed; ASan/UBSan check the disposable executable.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'src/clans.c').read_text()
fight = (ROOT / 'src/fight.c').read_text()
structs = (ROOT / 'src/structs.h').read_text()


def section(text, start, end):
    offset = text.index(start)
    return text[offset:text.index(end, offset)]


stubs = r'''
#include <algorithm>
#include <cassert>
#include <climits>
#include <cmath>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <list>
#include <string>
#include <vector>
#define TRUE true
#define FALSE false
#define MSL 4096
#define IS_NPC(c) ((c)->npc)
#define UMAX(a,b) std::max(a,b)
#define ADVERSARY_VALUE 65
enum { POI_EXTRACT = 1, POI_CAPTURE = 2, GOAL_PSYCHIC = 3,
       OPERATION_INTERCEPT = 4, OPERATION_EXTRACT = 5,
       OPERATION_CAPTURE = 6, OPERATION_MULTIPLE = 7 };
struct ROOM_INDEX_DATA { int x = 0, y = 0, size = 50, bg = 1; };
struct MOB_INDEX_DATA { int vnum = 0; };
struct CHAR_DATA {
  ROOM_INDEX_DATA *in_room = nullptr;
  MOB_INDEX_DATA *pIndexData = nullptr;
  bool npc = false, gm = false;
  int faction = 0, x = 0, y = 0, bagcarrier = 0;
};
struct OPERATION_TYPE {
  int poix[10] = {}, poiy[10] = {}, poitype[10] = {}, poifaction[10] = {}, poibg[10] = {};
  int battleground_number = 1, goal = 0, type = 0, timer = 0, waves = 5;
  int power = 100, size = 5, adversary_type = 0;
  char *elitestring = nullptr, *adversary_name = nullptr, *upload_name = nullptr;
  int enrolled[10] = {}, uploads[10] = {}, faction = 0, home_uploads = 0, upload = 100;
};
typedef std::list<CHAR_DATA*> CharList;
CharList char_list;
bool isactiveoperation = false;
OPERATION_TYPE *activeoperation = nullptr;
int battle_factions[6] = {};
int gm_calls = 0, room_calls = 0, wins = 0, losses = 0, ends = 0, spawns = 0;
bool antag_win = false;
bool is_gm(CHAR_DATA *c) { ++gm_calls; return c->gm; }
bool battleground(ROOM_INDEX_DATA *r) { return r && r->bg > 0; }
int bg_number(ROOM_INDEX_DATA *r) { return r->bg; }
ROOM_INDEX_DATA rooms[5][5];
ROOM_INDEX_DATA *battleroom_bycoord(int, int x, int y) {
  ++room_calls;
  if (x < 0 || y < 0 || x > 250 || y > 250) return nullptr;
  int rx = x > 0 ? (x - 1) / 50 : 0;
  int ry = y > 0 ? (y - 1) / 50 : 0;
  return &rooms[rx][ry];
}
int get_dist(int x, int y, int xx, int yy) {
  return static_cast<int>(std::sqrt((x-xx)*(x-xx) + (y-yy)*(y-yy)));
}
int map_translation[50];
std::string output;
void printf_to_char(CHAR_DATA *, const char *fmt, ...) {
  char buf[MSL]; va_list args; va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args); va_end(args); output += buf;
}
bool check_antag_win(int) { return antag_win; }
void lose_operation() { ++losses; }
void win_operation(int, OPERATION_TYPE *) { ++wins; }
void end_battle() { ++ends; isactiveoperation = false; activeoperation = nullptr; }
void battle_message(const char *, int) {}
void send_message_temp(int, const char *) {}
int pc_op_count() { return 2; }
void make_elite(int, int, int, int, char *, int, int) { ++spawns; }
void make_adversary(int, int, int, int, char *, int) { ++spawns; }
int safe_strlen(const char *s) { return s ? strlen(s) : 0; }
void free_string(char *s) { free(s); }
char *str_dup(const char *s) { return strdup(s); }
int poidistance(CHAR_DATA *, int, int);
'''

tests = r'''
// Original per-cell algorithm, retained as a behavior/performance reference.
int reference_poitype(CHAR_DATA *ch, int size, int mapy, int mapx) {
  if (!isactiveoperation || !activeoperation) return 0;
  int x = mapx / 2 - (size - 1) / 2, y = mapy - (size - 1) / 2;
  for (int i = 0; i < 10; ++i) {
    if (bg_number(ch->in_room) != activeoperation->poibg[i]) continue;
    int px = activeoperation->poix[i], py = activeoperation->poiy[i];
    int rx = relative_x(ch, battleroom_bycoord(1, px, py),
                        px % battleroom_bycoord(1, px, py)->size);
    int ry = relative_y(ch, battleroom_bycoord(1, px, py),
                        py % battleroom_bycoord(1, px, py)->size);
    if (rx >= map_expand(x) && rx < map_expand(x+1) &&
        ry >= map_expand(y) && ry < map_expand(y+1))
      return activeoperation->poitype[i];
  }
  return -1;
}

int main() {
  for (int i = 0; i < 50; ++i) map_translation[i] = i*i + i;
  for (int x = 0; x < 5; ++x) for (int y = 0; y < 5; ++y) {
    rooms[x][y].x = x; rooms[x][y].y = y;
  }
  OPERATION_TYPE op;
  CHAR_DATA viewer; viewer.in_room = &rooms[2][2]; viewer.faction = 10;
  isactiveoperation = true; activeoperation = &op;
  for (int i = 0; i < 10; ++i) {
    op.poibg[i] = 1; op.poix[i] = i * 23; op.poiy[i] = i * 19;
    op.poitype[i] = i % 3; // Preserve even zero-type points and first-match order.
    op.poifaction[i] = i % 2 ? 99 : 0; // Map visibility has no faction filter.
  }
  int old_calls = 0, new_calls = 0;
  for (int size : {11, 21, 31}) for (int position : {0, 25, 49}) {
    viewer.x = position; viewer.y = 49-position;
    OperationPoiPosition points[10];
    room_calls = 0;
    int count = operation_poi_positions(&viewer, points);
    assert(count == 10 && room_calls == 10);
    new_calls += room_calls;
    room_calls = 0;
    for (int y = 0; y < size; ++y) for (int x = 0; x < size*2; ++x)
      assert(operation_poi_type(points, count, size, y, x) == reference_poitype(&viewer, size, y, x));
    old_calls += room_calls;
  }
  printf("PASS: identical objective map cells; room lookups %d -> %d across 9 draws.\n", old_calls, new_calls);
  op.poix[0] = op.poix[1]; op.poiy[0] = op.poiy[1];
  OperationPoiPosition points[10];
  operation_poi_positions(&viewer, points);
  assert(points[0].type == 0 && points[0].x == points[1].x);
  op.poibg[0] = 2;
  assert(operation_poi_positions(&viewer, points) == 9);
  op.poix[1] = 999;
  assert(operation_poi_positions(&viewer, points) == 8);
  assert(poidistance(&viewer, 999, 0) == INT_MAX);
  assert(poidistance(nullptr, 0, 0) == INT_MAX);
  isactiveoperation = false;
  room_calls = 0;
  assert(operation_poi_positions(&viewer, points) == 0 && room_calls == 0);
  assert(!poidisplay(&viewer, 21, 0, 0));
  isactiveoperation = true;

  // Equal-distance objectives prefer the first; targets refresh after movement.
  op = OPERATION_TYPE(); viewer.in_room = &rooms[0][0]; viewer.x = viewer.y = 25;
  for (int i = 0; i < 4; ++i) { op.poibg[i] = 1; op.poitype[i] = POI_CAPTURE; }
  op.poix[0] = 20; op.poiy[0] = 25;
  op.poix[1] = 30; op.poiy[1] = 25;
  op.poix[2] = op.poiy[2] = 25; op.poifaction[2] = 99;
  op.poix[3] = op.poiy[3] = 25; op.poibg[3] = 2;
  int x, y; room_calls = 0;
  assert(get_poi_target(&viewer, POI_CAPTURE, &x, &y) && x == -5 && y == 0);
  assert(room_calls == 2);
  viewer.x = 29;
  assert(get_poi_target(&viewer, POI_CAPTURE, &x, &y) && x == 1 && y == 0);
  assert(!get_poi_target(&viewer, POI_EXTRACT, &x, &y) && x == 0 && y == 0);
  assert(get_poix(&viewer, POI_EXTRACT) == 0 && get_poiy(&viewer, POI_EXTRACT) == 0);
  room_calls = 0; output.clear(); displaypois(&viewer);
  assert(room_calls == 2 && output.find("Capture Point (X:1 Y:0 D:1)") != std::string::npos);
  rooms[0][0].size = 0;
  assert(poidistance(&viewer, 20, 25) == INT_MAX);
  rooms[0][0].size = 50;
  puts("PASS: objective filtering, ties, movement refresh, display and missing-room safety.");

  // Compare combined counts with the original helpers over mixed populations.
  ROOM_INDEX_DATA elsewhere; elsewhere.bg = 2;
  ROOM_INDEX_DATA outside; outside.bg = 0;
  MOB_INDEX_DATA cover, adversary, ordinary;
  cover.vnum = 110; adversary.vnum = 115; ordinary.vnum = 1;
  std::vector<CHAR_DATA> people(1000);
  for (int i = 0; i < 1000; ++i) {
    auto &c = people[i];
    c.in_room = i%7 == 0 ? nullptr : i%5 == 0 ? &elsewhere : i%3 == 0 ? &outside : viewer.in_room;
    c.npc = i%2; c.gm = i%11 == 0;
    c.pIndexData = i%3 == 0 ? &cover : i%3 == 1 ? &adversary : &ordinary;
    c.faction = i%3 == 0 ? 200000 : i%3 == 1 ? 300000 : 10;
    char_list.push_back(&c);
  }
  auto pop = operation_population(1);
  assert(pop.players == battle_pc_pop(1));
  assert(pop.defenders == battle_defend_pop(1));
  assert(pop.attackers == battle_attack_pop(1));
  assert(pop.cover == op_cover_count());
  assert(pop.adversaries == adver_count());
  assert(pop.battle_adversaries == advercount(1));
  char_list.push_back(nullptr);
  assert(operation_population(1).players == pop.players);
  isactiveoperation = false; gm_calls = 0; operations_update(); assert(gm_calls == 0);
  isactiveoperation = true; activeoperation = nullptr; operations_update(); assert(gm_calls == 0);
  puts("PASS: combined counts match all 6 original population helpers; idle update does no scan.");

  // Exercise real update control flow, including a carrier on overlapping exits.
  char_list.clear(); char_list.push_back(&viewer); viewer.bagcarrier = 1;
  activeoperation = &op; op = OPERATION_TYPE(); op.type = OPERATION_EXTRACT;
  op.waves = 0; op.timer = -1;
  for (int i = 0; i < 2; ++i) {
    op.poibg[i] = 1; op.poitype[i] = POI_EXTRACT;
    op.poix[i] = viewer.x; op.poiy[i] = viewer.y;
  }
  operations_update(); assert(wins == 1 && ends == 1 && spawns == 0);
  // An empty battleground loses once, or respects an antagonist victory.
  activeoperation = &op; isactiveoperation = true; char_list.clear();
  operations_update(); assert(losses == 1 && ends == 2);
  activeoperation = &op; isactiveoperation = true; antag_win = true;
  operations_update(); assert(losses == 1 && ends == 3);
  // Psychic attacker/defender handling is unchanged.
  activeoperation = &op; isactiveoperation = true; op.goal = GOAL_PSYCHIC;
  char_list.push_back(&viewer); viewer.faction = 300000;
  operations_update(); assert(wins == 2);
  viewer.faction = 200000;
  operations_update(); assert(losses == 2 && ends == 4);
  // Wave growth and spawn budget still work with the shared population.
  activeoperation = &op; isactiveoperation = true; op = OPERATION_TYPE();
  op.type = OPERATION_INTERCEPT; op.timer = 6; op.power = 1000;
  CHAR_DATA obstacle; obstacle.npc = true; obstacle.pIndexData = &cover;
  char_list.push_back(&obstacle);
  operations_update(); assert(op.timer == 5 && op.power == 1300 && spawns == 19);
  puts("PASS: extraction concludes once; zero waves, loss, psychic goals and reinforcement budget.");
}
'''

production = (
    section(structs, '    struct OperationPoiPosition', '    struct operation_type')
    + section(fight, '  int relative_x(CHAR_DATA *ch,', '  int relative_z(CHAR_DATA *ch,')
    + section(fight, '  int map_expand(int number)', '  int map_contract(int number)')
    + section(source, '  CHAR_DATA *get_carrier(int battleground_number)', '  // A fresh snapshot per update:')
    + section(source, '  int advercount(int bg_num)', '  void assign_pc_carrier(')
    + section(source, '  // A fresh snapshot per update:', '  /*\nbool poi(')
    + section(source, '  // Resolve each objective once', '  bool capture_attack(CHAR_DATA *ch)')
)

with tempfile.TemporaryDirectory(prefix='haven-operation-test-') as directory:
    cpp = Path(directory) / 'operations.cpp'
    binary = Path(directory) / 'operations-test'
    cpp.write_text(stubs + production + tests)
    subprocess.run(['g++', '-std=c++11', '-O1', '-g', '-Wall', '-Wextra',
                    '-Wno-unused-parameter', '-fsanitize=address,undefined',
                    '-fno-omit-frame-pointer', str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
