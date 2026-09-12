#!/usr/bin/env python3
"""Run production progression, sanctuary, Civil Servant and breach policies in WSL."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
def section(file, start, end):
    text = (ROOT / 'src' / file).read_text()
    a = text.index(start)
    return text[a:text.index(end, a)]

source = r'''
#include "merc.h"
#include <cassert>
#include <cstring>
#include <cstdlib>
#include <cstdarg>
#include <climits>
time_t current_time = 100;
int tier = 3, focus = 3, legends = 0, percent = 1, spawned = 0;
bool full_sanctuary = false, limited_sanctuary = false;
CHAR_DATA monster = {};
MOB_INDEX_DATA index_data = {};
FACTION_TYPE cortex = {};
LOCATION_TYPE site = {};
int battle_factions[6] = {};
char *str_dup(const char *s) { return strdup(s); }
void free_string(char *s) { free(s); }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a,b) != 0; }
void send_to_char(const char *, CHAR_DATA *) {}
void printf_to_char(CHAR_DATA *, const char *, ...) {}
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
bool higher_power(CHAR_DATA *) { return false; }
bool guestmonster(CHAR_DATA *) { return false; }
bool is_super(CHAR_DATA *) { return true; }
bool seems_super(CHAR_DATA *) { return true; }
bool is_undead(CHAR_DATA *) { return false; }
bool is_gm(CHAR_DATA *) { return false; }
bool is_ghost(CHAR_DATA *) { return false; }
bool is_helpless(CHAR_DATA *ch) { return ch->wounds > 3; }
bool in_fight(CHAR_DATA *ch) { return ch->in_fight; }
bool battleground(ROOM_INDEX_DATA *) { return false; }
bool in_haven(ROOM_INDEX_DATA *) { return true; }
int in_world(CHAR_DATA *ch) { return ch->in_room->area->world; }
int combat_focus(CHAR_DATA *) { return focus; }
int get_skill(CHAR_DATA *, int) { return 0; }
int get_tier(CHAR_DATA *) { return tier; }
int skilltype(int) { return STYPE_ABOMINATION; }
int skillbase_count(CHAR_DATA *, int) { return legends; }
bool under_understanding(CHAR_DATA *, CHAR_DATA *) { return full_sanctuary; }
bool under_limited(CHAR_DATA *, CHAR_DATA *) { return limited_sanctuary; }
bool society_has_room(CHAR_DATA *ch) { return !ch->fcore && !ch->fsociety && !ch->legacy_society; }
FACTION_TYPE *clan_lookup(int n) { return n == FACTION_CORTEX ? &cortex : nullptr; }
LOCATION_TYPE *territory_by_number(int) { return &site; }
int number_percent() { return percent; }
int number_range(int low, int) { return low; }
int get_demon_lvl(int) { return 10; }
MOB_INDEX_DATA *get_mob_index(int n) { index_data.vnum = n; return &index_data; }
CHAR_DATA *create_mobile(MOB_INDEX_DATA *p) { ++spawned; monster.pIndexData = p; SET_FLAG(monster.act, ACT_IS_NPC); return &monster; }
void char_to_room(CHAR_DATA *ch, ROOM_INDEX_DATA *room) { ch->in_room = room; }
int max_hp(CHAR_DATA *) { return 10000; }
void start_fight(CHAR_DATA *, CHAR_DATA *) {}
'''
source += section('skills.c', '  bool can_train_disc(', '  int train_disc_cost(')
source += 'bool legendary_allowed(CHAR_DATA *ch) { int skill = 1; bool show = false;\n'
source += section('skills.c', '    if (skilltype(skill) == STYPE_ABOMINATION &&', '    if (skilltype(skill) == STYPE_SABILITIES)')
source += 'return true; }\n'
source += section('skills.c', '  static bool sanctuary_blocks_imprint_lock(', '  _DOFUN(do_imprint)')
source += section('lookup.c', '  bool pact_holder(', '  bool in_wilds(')
source += section('clans.c', '  bool cortex_loyalty_brainwashed(', '  int cortex_lifeforce_bonus(')
source += section('clans.c', '  bool is_containment_priority(', '  void normalize_society_record(')
source += section('clans.c', '  void enforce_civil_servant_membership(', '  void normalize_society_memberships(')
source += section('clans.c', '  bool player_faction_join_allowed(', '  /*Local Functions */')
source += 'void leave_cortex(CHAR_DATA *ch, int number) {\n'
source += section('clans.c', '      if (number == FACTION_CORTEX &&', '      if (ch->fcore == number) {')
source += 'ch->fcore = 0; }\n'
source += section('fight.c', '  int difficulty_mod(', '  char *const crystal_levels')
source += section('fight.c', '  bool cortex_breach_monster(', '  void populate_warren(')
source += 'void victory_breach(bool active, FACTION_TYPE *fac, OPERATION_TYPE *op) {\n'
source += section('clans.c', '    if (active && fac && fac->antagonist == 1)', '    if(fac->antagonist == 1)')
source += '}\n'
source += r'''
int main() {
  CHAR_DATA ch = {}, author = {};
  PC_DATA pc = {}; ch.pcdata = &pc;
  for (tier = 1; tier <= 5; ++tier) {
    for (legends = 0; legends <= 4; ++legends)
      assert(legendary_allowed(&ch) == (tier >= 3 && legends < tier-2));
  }
  for (tier = 3; tier <= 5; ++tier) {
    focus = tier;
    int melee = tier == 3 ? 40 : tier == 4 ? 96 : 144;
    int ranged = tier == 3 ? 70 : tier == 4 ? 96 : 120;
    int defense = tier == 3 ? 20 : tier == 4 ? 60 : 120;
    int armor = tier == 3 ? 40 : tier == 4 ? 54 : 60;
    int unarmed = tier == 3 ? 25 : tier == 4 ? 36 : 42;
    for (int disc : {DIS_KNIFE, DIS_LONGBLADE, DIS_BLUNT, DIS_SPEAR,
        DIS_PISTOLS, DIS_RIFLES, DIS_BOWS, DIS_THROWN, DIS_SHOTGUNS, DIS_CARBINES,
        DIS_SPEARGUN, DIS_TOUGHNESS, DIS_BONES, DIS_FORCES, DIS_FATE, DIS_PUSH,
        DIS_MARMOR, DIS_BARMOR, DIS_MSHIELD, DIS_BSHIELD, DIS_STRIKING, DIS_GRAPPLE}) {
      memset(ch.disciplines, 0, sizeof(ch.disciplines));
      int cap = melee;
      if (disc == DIS_PISTOLS || disc == DIS_RIFLES || disc == DIS_BOWS || disc == DIS_THROWN || disc == DIS_SHOTGUNS || disc == DIS_CARBINES || disc == DIS_SPEARGUN) cap = ranged;
      if (disc == DIS_TOUGHNESS || disc == DIS_BONES || disc == DIS_FORCES || disc == DIS_FATE || disc == DIS_PUSH) cap = defense;
      if (disc == DIS_MARMOR || disc == DIS_BARMOR || disc == DIS_MSHIELD || disc == DIS_BSHIELD) cap = armor;
      if (disc == DIS_STRIKING || disc == DIS_GRAPPLE) cap = unarmed;
      ch.disciplines[disc] = cap-1; assert(can_train_disc(&ch,disc));
      ch.disciplines[disc] = cap; assert(!can_train_disc(&ch,disc));
    }
    memset(ch.disciplines, 0, sizeof(ch.disciplines));
    ch.disciplines[DIS_TOUGHNESS] = defense/2;
    ch.disciplines[DIS_BONES] = defense-defense/2;
    assert(!can_train_disc(&ch,DIS_FORCES));
  }
  assert(!sanctuary_blocks_imprint_lock(&ch,&author));
  full_sanctuary = true; assert(sanctuary_blocks_imprint_lock(&ch,&author));
  full_sanctuary = false; limited_sanctuary = true;
  assert(sanctuary_blocks_imprint_lock(&ch,&author));
  assert(sanctuary_blocks_imprint_lock(&ch,nullptr));
  limited_sanctuary = false;
  SET_FLAG(ch.affected_by,AFF_UNDERSTANDING);
  assert(sanctuary_blocks_imprint_lock(&ch,&author));
  REMOVE_FLAG(ch.affected_by,AFF_UNDERSTANDING);
  ch.race = RACE_CIVIL_SERVANT; ch.fcore = FACTION_SCUM;
  ch.name = str_dup("Clerk");
  enforce_civil_servant_membership(&ch);
  assert(ch.fcore == FACTION_CORTEX && ch.faction == FACTION_CORTEX);
  assert(!str_cmp(cortex.member_names[0], "Clerk"));
  enforce_civil_servant_membership(&ch); assert(cortex.member_names[1] == nullptr);
  FACTION_TYPE scum = {}; scum.vnum = FACTION_SCUM; scum.type = FACTION_CORE;
  assert(!player_faction_join_allowed(&ch,&scum,false));
  leave_cortex(&ch,FACTION_CORTEX); assert(ch.fcore == FACTION_CORTEX);
  ROOM_INDEX_DATA room = {}; AREA_DATA area = {}; DESCRIPTOR_DATA desc = {};
  room.vnum = 1000; room.area = &area; area.world = WORLD_EARTH;
  ch.in_room = &room; ch.desc = &desc; tier = 3;
  FACTION_TYPE npc = {}; npc.antagonist = 1;
  OPERATION_TYPE op = {};
  site.continent = CONTINENT_OTHER;
  victory_breach(true, &npc, &op);
  assert(cortex_breach_until == 0); // Cortex did not participate.
  battle_factions[0] = FACTION_CORTEX;
  victory_breach(false, &npc, &op);
  assert(cortex_breach_until == 0); // Scheduled/unplayed results do not count.
  site.continent = CONTINENT_NA;
  victory_breach(true, &npc, &op);
  assert(cortex_breach_until == 0); // Earth operation.
  site.continent = CONTINENT_OTHER;
  percent = 26; victory_breach(true, &npc, &op);
  assert(cortex_breach_until == 0);
  percent = 25; victory_breach(true, &npc, &op);
  assert(cortex_breach_until == current_time + 3600 && cortex_breach_origin == WORLD_OTHER);
  cortex_breach_until = 0;
  for (int sector : {SECT_STREET, SECT_HOUSE}) {
    room.sector_type = sector;
    pc.spawned_monsters = 0;
    cortex_breach(WORLD_OTHER);
    percent = 6; assert(!cortex_monster_ambush(&ch));
    percent = 1; assert(cortex_monster_ambush(&ch));
    assert(monster.in_room == &room && cortex_breach_monster(&monster));
    pc.spawned_monsters = 0;
    assert(!cortex_monster_ambush(&ch)); // One encounter per breach.
    free_string(monster.aggression); monster.aggression = nullptr;
  }
  cortex_breach(WORLD_OTHER); current_time += 3600;
  assert(!cortex_monster_ambush(&ch));
  assert(spawned == 2);
  free_string(ch.name); free_string(cortex.member_names[0]);
  puts("Progression boundaries, sanctuary, Civil Servants, and road/building breaches passed.");
}
'''
with tempfile.TemporaryDirectory(prefix='haven-balance-') as tmp:
    path = Path(tmp)
    (path/'test.cc').write_text(source)
    subprocess.run(['g++','-std=gnu++17','-w','-ffunction-sections','-fdata-sections',
                    '-Wl,--gc-sections','-fsanitize=address,undefined','-no-pie','-I',str(ROOT/'src'),
                    str(path/'test.cc'),str(ROOT/'src/tables.c'),'-o',str(path/'test')],check=True)
    subprocess.run([str(path/'test')],check=True)
