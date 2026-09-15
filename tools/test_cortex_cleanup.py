#!/usr/bin/env python3
"""Sanitizer regression for Cortex retirement and critical-wound recovery."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def section(filename, start, end):
    text = (ROOT / 'src' / filename).read_text()
    begin = text.index(start)
    return text[begin:text.index(end, begin)]


source = r'''
#include "merc.h"
#include "runtime_indexes.cc"
#include <cassert>
#include <cstdlib>
#include <cstring>

CharList char_list;
time_t current_time = 2000000000;
int fight_problem = 0, extracted = 0, auctions = 0;
bool emergency = false, dissent = false, reachable = true, coverage = true;
CHAR_DATA victim = {}, bystander = {};
PC_DATA victim_pc = {}, bystander_pc = {};
RecoveryState recovery;
ROOM_INDEX_DATA room = {}, nearby = {}, escaped = {};
AREA_DATA area = {};
MOB_INDEX_DATA cortex_index = {}, forest_index = {};
FACTION_TYPE society = {};
char *str_dup(const char *s) { return strdup(s ? s : ""); }
void free_string(char *s) { free(s); }
bool str_cmp(const char *a, const char *b) { return strcmp(a ? a : "", b ? b : "") != 0; }
bool state_of_emergency() { return emergency; }
bool dissent_crowd(CHAR_DATA *) { return false; }
bool dissent_in_room(ROOM_INDEX_DATA *) { return dissent; }
bool full_moon_pack(CHAR_DATA *) { return false; }
bool sin_vigilante_target(CHAR_DATA *, CHAR_DATA *) { return false; }
bool pedestrian(CHAR_DATA *ch) { return ch && IS_NPC(ch) && IS_FLAG(ch->act, ACT_PEDESTRIAN); }
bool pedestrian_helpless(CHAR_DATA *ch) { return ch->position <= POS_STUNNED || IS_FLAG(ch->act, PLR_BOUND); }
bool is_gm(CHAR_DATA *) { return false; }
bool is_ghost(CHAR_DATA *ch) { return IS_FLAG(ch->act, PLR_DEAD); }
bool is_vampire(CHAR_DATA *) { return false; }
bool is_undead(CHAR_DATA *) { return false; }
bool higher_power(CHAR_DATA *) { return false; }
bool guestmonster(CHAR_DATA *) { return false; }
int pc_pop(ROOM_INDEX_DATA *) { return 1; }
bool in_fight(CHAR_DATA *ch) { return ch->in_fight; }
bool can_get_to(CHAR_DATA *, ROOM_INDEX_DATA *) { return reachable; }
int in_world(CHAR_DATA *ch) { return ch->in_room->area->world; }
int mist_level(ROOM_INDEX_DATA *) { return 0; }
int init_combat_distance(CHAR_DATA *a, CHAR_DATA *b, bool) {
  return abs(a->in_room->x - b->in_room->x) * 10 + abs(a->x - b->x);
}
int get_agg(CHAR_DATA *a, CHAR_DATA *b) {
  return a->aggression && !str_cmp(a->aggression, b->name) ? 50 : 0;
}
int get_disc(CHAR_DATA *, int, bool) { return 0; }
int default_ranged(CHAR_DATA *) { return 0; }
bool can_see_char_distance(CHAR_DATA *, CHAR_DATA *, int) { return true; }
void send_to_char(const char *, CHAR_DATA *) {}
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
CHAR_DATA *get_char_world_pc(char *name) {
  if (!str_cmp(name, victim.name)) return &victim;
  if (!str_cmp(name, bystander.name)) return &bystander;
  return nullptr;
}
void extract_char(CHAR_DATA *ch, bool pull) {
  assert(pull && IS_NPC(ch));
  ++extracted;
  unregister_live_character(ch);
  char_list.remove(ch);
  free_string(ch->aggression);
  delete ch;
}
bool start_syndicate_auction(CHAR_DATA *ch, CHAR_DATA *) {
  ++auctions;
  ch->pcdata->patrol_status = PATROL_KIDNAPPED;
  ch->in_room = &escaped;
  return true;
}
int get_hour(ROOM_INDEX_DATA *) { return 12; }
bool personal_sanctuary(CHAR_DATA *) { return false; }
FACTION_TYPE *clan_lookup(int id) { return id == society.vnum ? &society : nullptr; }
bool sanctuary_population_blocked() { return false; }
bool under_black(CHAR_DATA *, CHAR_DATA *) { return false; }
bool under_sanctuary(CHAR_DATA *, CHAR_DATA *) { return coverage; }
'''
source += section('lookup.c', '  bool is_forcibly_helpless(', '  bool is_pinned(')
source += section('fight.c', '  bool forest_monster(', '  CHAR_DATA *find_prey(')
source += section('public_combat.c', 'bool public_target_excluded(', 'void cortex_public_response(')
source += section('fight.c', '  bool cortex_breach_monster(', '  int cortex_encounter_count(')
source += section('fight.c', '  void cortex_enforcer_defeat(', '  static time_t cortex_breach_until')
source += section('fight.c', '  bool is_enemy(', '  static bool pedestrian_has_enemy(')
source += section('public_combat.c', 'void cortex_public_update(', '} // extern "C"')
source += section('recovery.c', 'long next_sanctuary_recovery(', 'static std::string maim_description(')
source += r'''
CHAR_DATA *enforcer(bool public_response = false, CHAR_DATA *target = &victim) {
  CHAR_DATA *mob = new CHAR_DATA{};
  SET_FLAG(mob->act, ACT_IS_NPC);
  SET_FLAG(mob->act, ACT_CORTEX_ENFORCER);
  if (public_response) SET_FLAG(mob->act, ACT_CORTEX_PUBLIC);
  mob->pIndexData = &cortex_index;
  mob->in_room = &room; mob->ttl = 12; mob->attacking = 1;
  mob->aggression = str_dup(target->name);
  char_list.push_back(mob); register_live_character(mob); set_combat_state(mob, true);
  return mob;
}
void reset() {
  while (!char_list.empty()) extract_char(char_list.front(), true);
  victim = {}; bystander = {}; victim_pc = {}; bystander_pc = {};
  recovery = {}; area = {}; room = {}; nearby = {}; escaped = {};
  victim.name = "victim"; bystander.name = "bystander";
  victim.pcdata = &victim_pc; bystander.pcdata = &bystander_pc;
  victim_pc.recovery = &recovery; victim_pc.title = bystander_pc.title = "";
  victim.in_room = bystander.in_room = &room;
  room.area = nearby.area = escaped.area = &area;
  room.vnum = 1234; nearby.vnum = 1235; escaped.vnum = 1236;
  nearby.x = 2; escaped.x = 100;
  victim.hit = 25; victim.attacking = 1; victim.in_fight = bystander.in_fight = true;
  cortex_index.vnum = CORTEX_SOLDIER; forest_index.vnum = 15;
  society.vnum = 123; society.valid = true; victim.fsociety = society.vnum;
  emergency = dissent = false; reachable = coverage = true;
  extracted = auctions = 0;
}
int main() {
  reset();
  CHAR_DATA *regular = enforcer(), *public_mob = enforcer(true);
  assert(cortex_enforcer_target(regular, &victim));
  assert(!cortex_enforcer_target(regular, &bystander));
  assert(!cortex_enforcer_target(regular, nullptr));
  assert(!forest_monster(regular) && cortex_breach_monster(regular));
  // Adjacent, reachable combat movement stays in the encounter.
  victim.in_room = &nearby; cortex_public_update();
  assert(extracted == 0 && char_list.size() == 2);
  // A true escape must not leave either public or alarm soldiers behind.
  victim.in_room = &escaped; cortex_public_update();
  assert(extracted == 2 && char_list.empty());
  reset(); enforcer(); victim.in_fight = false; cortex_public_update();
  assert(extracted == 1);
  reset(); enforcer(); reachable = false; victim.in_room = &nearby;
  cortex_public_update(); assert(extracted == 1);
  puts("PASS: active pursuit survives nearby movement; escaped and ended fights retire public and alarm squads.");

  reset(); regular = enforcer(); public_mob = enforcer();
  CHAR_DATA *unrelated = enforcer(false, &bystander);
  cortex_enforcer_defeat(regular, &victim);
  assert(auctions == 1 && victim_pc.patrol_status == PATROL_KIDNAPPED);
  assert(!regular->in_fight && regular->ttl == 0 && public_mob->ttl == 0);
  assert(unrelated->ttl == 12 && extracted == 0);
  assert(!cortex_enforcer_target(regular, &bystander));
  cortex_public_update(); assert(extracted == 2 && char_list.size() == 1);
  reset(); regular = enforcer(); public_mob = enforcer(true);
  cortex_enforcer_defeat(regular, &victim);
  assert(auctions == 0 && victim_pc.sleeping == 240 && victim.hit == 0);
  cortex_public_update(); assert(extracted == 2 && char_list.empty());
  reset(); enforcer(); victim_pc.patrol_status = PATROL_KIDNAPPED;
  cortex_public_update(); assert(extracted == 1);
  puts("PASS: auction and public-subdual outcomes retire the whole matching squad without extracting during combat.");

  reset(); regular = enforcer(); enforcer(true);
  victim.wounds = 2;
  record_critical_injury(&victim, regular);
  assert(recovery.critical.source == RECOVERY_SANCTUARY && !recovery.critical.forest);
  assert(recovery.critical.payer == society.vnum);
  victim.wounds = 3;
  assert(!cortex_enforcer_target(regular, &victim));
  cortex_public_update(); assert(extracted == 2 && char_list.empty());
  // Bleeding out after the attacker has despawned retains captured coverage.
  coverage = false; current_time += 3600;
  record_death_recovery(&victim, &victim, true, false);
  assert(recovery.death.source == RECOVERY_SANCTUARY && !recovery.death.forest);
  assert(recovery.death.payer == society.vnum && recovery.death.due > current_time);
  assert(recovery.critical.source == RECOVERY_NONE);
  reset(); regular = enforcer(); regular->pIndexData = &forest_index;
  // Ordinary forest injuries keep the existing exclusion.
  record_critical_injury(&victim, regular);
  assert(recovery.critical.forest && recovery.critical.source == RECOVERY_NONE);
  puts("PASS: Cortex critical injuries preserve ordinary Sanctuary recovery after later bleed-out and attacker despawn.");

  reset(); regular = enforcer(); public_mob = enforcer(true);
  SET_FLAG(victim.act, PLR_SHROUD); cortex_public_update();
  assert(extracted == 2);
  reset(); regular = enforcer(); regular->ttl = 0; cortex_public_update();
  assert(extracted == 1);
  reset(); enforcer(true); emergency = true; cortex_public_update();
  assert(extracted == 1);
  reset(); enforcer(); victim.in_room = nullptr; cortex_public_update();
  assert(extracted == 1);
  reset();
}
'''

with tempfile.TemporaryDirectory(prefix='haven-cortex-cleanup-') as tmp:
    path = Path(tmp)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-fsanitize=address,undefined',
                    '-fno-sanitize-recover=all', '-fno-omit-frame-pointer', '-no-pie',
                    '-I', str(ROOT / 'src'), str(path / 'test.cc'),
                    '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
