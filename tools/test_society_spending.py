#!/usr/bin/env python3
"""Exercise real society affordability, resupply, setup and upkeep code."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
clans = (ROOT / 'src/clans.c').read_text()


def section(start, end):
    a = clans.index(start)
    return clans[a:clans.index(end, a)]


stubs = r'''
#include "merc.h"
#include <cassert>
#include <cstring>
#include <cstdarg>
FACTION_TYPE society = {};
OBJ_INDEX_DATA item_index = {};
OBJ_DATA *received = nullptr;
bool trusted = true;
int paid = 0, members = 2, item_price = 50000;
std::string output;
FACTION_TYPE *clan_lookup(int) { return &society; }
bool has_trust(CHAR_DATA *, int, int) { return trusted; }
bool is_leader(CHAR_DATA *, int) { return trusted; }
int get_trust(CHAR_DATA *) { return 0; }
int member_count(FACTION_TYPE *) { return members; }
bool generic_faction_vnum(int id) { return id == FACTION_CORTEX; }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
bool goblin_market(ROOM_INDEX_DATA *) { return true; }
bool is_helpless(CHAR_DATA *) { return false; }
bool in_fight(CHAR_DATA *) { return false; }
bool is_pinned(CHAR_DATA *) { return false; }
bool is_ghost(CHAR_DATA *) { return false; }
bool room_hostile(ROOM_INDEX_DATA *) { return false; }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void printf_to_char(CHAR_DATA *, const char *fmt, ...) {
  char buf[4096]; va_list args; va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args); va_end(args); output += buf;
}
OBJ_INDEX_DATA *get_obj_index(int id) { item_index.vnum = id; return &item_index; }
OBJ_DATA *create_object(OBJ_INDEX_DATA *index, int) {
  auto *obj = new OBJ_DATA{}; obj->pIndexData = index; obj->cost = item_price;
  return obj;
}
void obj_to_char(OBJ_DATA *obj, CHAR_DATA *) { assert(!received); received = obj; }
void extract_obj_silent(OBJ_DATA *obj) { delete obj; }
void use_resources(int cost, int, CHAR_DATA *, char *) { paid += cost; society.resource -= cost; }
'''

develop = section('    else if (!str_cmp(arg, "develop")) {', '    else\n    printf_to_char(ch, "Syntax: %s info/news')
develop_body = develop[develop.index('{') + 1:develop.rfind('}')]
production = '\n'.join([
    section('  bool can_afford_faction_spending(', '  bool can_spend_resources('),
    section('  static int society_service_cost(', '  void win_battle args'),
    section('  static void resupply_item(', '  _DOFUN(do_minioncommand)'),
    'void test_develop(CHAR_DATA *ch, FACTION_TYPE *fac, char *argument) {' + develop_body + '}',
    'int test_upkeep(FACTION_TYPE *fac) { int cost = 0;\n' +
    section('    // All factions and societies pay the same upkeep', '    for (int i = 0; i < 5; i++) {') +
    'return cost; }',
])

tests = r'''
int main() {
  society.vnum = 100; society.type = FACTION_SOCIETY;
  for (int minimum : {5000, 6500, 8000, 8500, 9500, 10000, 10250, 11000, 12000}) {
    society.resource = 50;
    assert(can_afford_faction_spending(&society, 50, minimum));
    assert(!can_afford_faction_spending(&society, 51, minimum));
    society.resource = 0;
    assert(can_afford_faction_spending(&society, 0, minimum));
    assert(!can_afford_faction_spending(&society, 1, minimum));
    for (int type : {FACTION_CORE, FACTION_NPC}) {
      FACTION_TYPE legacy = {}; legacy.type = type;
      legacy.resource = minimum - 1;
      assert(!can_afford_faction_spending(&legacy, 50, minimum));
      ++legacy.resource; assert(can_afford_faction_spending(&legacy, 50, minimum));
    }
  }
  assert(!can_afford_faction_spending(nullptr, 0, 0));
  assert(!can_afford_faction_spending(&society, -1, 0));
  CHAR_DATA player = {}; player.faction = society.vnum;
  society.resource = 49;
  do_resupply(&player, const_cast<char *>("bandage"));
  assert(!received && paid == 0 && society.resource == 49);
  society.resource = 50;
  do_resupply(&player, const_cast<char *>("bandage"));
  assert(received && paid == 50 && society.resource == 0);
  delete received; received = nullptr;
  society.resource = 500;
  trusted = false; do_resupply(&player, const_cast<char *>("bandage"));
  assert(!received && society.resource == 500); trusted = true;
  for (const char *item : {"pepper spray", "bandage", "compass", "taser", "taserdart",
       "taser dart", "tranquilizer gun", "tranquilizer dart", "caltrops", "landmine",
       "bola", "gasmask", "smoke grenade", "tear gas", "frag grenade", "naturalizer",
       "neutralizer grenade", "neutralizer collar", "spy camera", "police scanner", "dream charm"}) {
    society.resource = 50;
    do_resupply(&player, const_cast<char *>(item));
    assert(received && society.resource == 0); delete received; received = nullptr;
  }
  // Setup charges only the price scaled to membership, not the former reserve.
  society.resource = 199;
  test_develop(&player, &society, const_cast<char *>("sanctuary"));
  assert(!society.attributes[FACTION_UNDERSTANDING] && society.resource == 199);
  society.resource = 200;
  test_develop(&player, &society, const_cast<char *>("sanctuary"));
  assert(society.attributes[FACTION_UNDERSTANDING] && society.resource == 0);
  test_develop(&player, &society, const_cast<char *>("sanctuary"));
  assert(!society.attributes[FACTION_UNDERSTANDING] && society.resource == 0);
  society.resource = 500; trusted = false;
  test_develop(&player, &society, const_cast<char *>("sanctuary"));
  assert(!society.attributes[FACTION_UNDERSTANDING]); trusted = true;
  // Ongoing services share the available balance, at their actual scaled costs.
  society.attributes[FACTION_UNDERSTANDING] = 1;
  society.attributes[FACTION_SCOUTS] = 1;
  society.attributes[FACTION_911] = 1;
  society.attributes[FACTION_COMMS] = 1;
  society.attributes[FACTION_CORPSE] = 1;
  society.resource = 480;
  assert(test_upkeep(&society) == 480);
  assert(society.attributes[FACTION_UNDERSTANDING] && society.attributes[FACTION_COMMS]);
  assert(!society.attributes[FACTION_CORPSE]);
  society.resource = 399;
  assert(test_upkeep(&society) == 80);
  assert(!society.attributes[FACTION_UNDERSTANDING]);
  // Core and NPC factions follow exactly the same upkeep as societies.
  for (int type : {FACTION_SOCIETY, FACTION_CORE, FACTION_NPC}) {
    FACTION_TYPE fac = {}; fac.type = type; fac.vnum = FACTION_CORTEX;
    const int services[] = {FACTION_UNDERSTANDING, FACTION_SCOUTS,
                           FACTION_911, FACTION_COMMS, FACTION_CORPSE};
    for (int count : {0, 1, 2, 100}) {
      members = count;
      for (int service : services) fac.attributes[service] = 1;
      fac.resource = 340 * UMAX(1, count);
      assert(test_upkeep(&fac) == fac.resource);
      for (int service : services) assert(fac.attributes[service] == 1);
      fac.resource = 0;
      assert(test_upkeep(&fac) == 0);
      for (int service : services) assert(fac.attributes[service] == 0);
    }
    members = 2;
    for (int service : services) fac.attributes[service] = 1;
    fac.resource = 479;
    assert(test_upkeep(&fac) == 460);
    assert(!fac.attributes[FACTION_COMMS] && !fac.attributes[FACTION_CORPSE]);
    fac.college = 1; fac.resource = 0;
    fac.attributes[FACTION_UNDERSTANDING] = 1;
    assert(test_upkeep(&fac) == 0 && fac.attributes[FACTION_UNDERSTANDING] == 1);
  }
  puts("Society spending: exact-cost purchases, reserve removal, permissions, setup and faction/society upkeep parity passed.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-spending-') as temp:
    path = Path(temp)
    source = path / 'test.cc'
    source.write_text(stubs + production + tests)
    subprocess.run(['g++', '-std=gnu++17', '-g', '-O1', '-Wno-write-strings',
                    '-Wno-deprecated', '-fsanitize=address,undefined', '-no-pie',
                    '-I', str(ROOT / 'src'), str(source), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
