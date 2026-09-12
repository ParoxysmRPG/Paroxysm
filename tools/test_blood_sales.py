#!/usr/bin/env python3
"""Exercise production blood sales and Cortex encounter generation in Linux/WSL."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
fight = (ROOT / 'src/fight.c').read_text()
clans = (ROOT / 'src/clans.c').read_text()


def section(text, start, end):
    a = text.index(start)
    return text[a:text.index(end, a)]


stubs = r'''
#include "merc.h"
#include "global.h"
#include <cassert>
#include <cstring>
#include <cstdlib>
#include <cstdarg>
#include <climits>
CharList char_list;
time_t current_time = 2000000000;
int event_cleanse = 0, tier = 3, percent = 51, range_mode = 0;
int extracted = 0, saves = 0, fights = 0;
bool emergency = false, available = true, allowed = true;
FACTION_TYPE society = {};
OBJ_INDEX_DATA glass_index = {};
OBJ_DATA glass = {};
MOB_INDEX_DATA soldier_index = {}, creature_index = {};
std::string output;
const struct discipline_type discipline_table[] = {
  {DIS_TOUGHNESS, "toughness", 0, 0}, {DIS_STRIKING, "striking", 0, 0}
};
const int discipline_table_count = 2;
const struct monster_type monster_table[] = {
  {901, WORLD_OTHER, 0, 0, ""}, {902, WORLD_HELL, 0, 0, ""}, {-1, -1, 0, 0, ""}
};
int get_tier(CHAR_DATA *) { return tier; }
int number_percent() { return percent; }
int number_range(int low, int high) { return range_mode ? high : low; }
int in_world(CHAR_DATA *ch) { return ch->in_room->area->world; }
int room_level(ROOM_INDEX_DATA *room) { return room->level; }
bool in_haven(ROOM_INDEX_DATA *room) { return room->area->world == WORLD_EARTH; }
bool state_of_emergency() { return emergency; }
bool is_gm(CHAR_DATA *) { return false; }
bool is_ghost(CHAR_DATA *) { return false; }
bool higher_power(CHAR_DATA *) { return false; }
bool guestmonster(CHAR_DATA *) { return false; }
bool is_helpless(CHAR_DATA *) { return false; }
bool in_fight(CHAR_DATA *ch) { return ch->in_fight; }
bool battleground(ROOM_INDEX_DATA *) { return false; }
bool dissent_in_room(ROOM_INDEX_DATA *) { return false; }
bool free_to_act(CHAR_DATA *ch) { return allowed && !in_fight(ch); }
int selected_society(CHAR_DATA *ch) { return ch->faction; }
FACTION_TYPE *clan_lookup(int id) { return id == society.vnum ? &society : nullptr; }
char *str_dup(const char *s) { return strdup(s); }
void free_string(char *s) { free(s); }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void printf_to_char(CHAR_DATA *, const char *fmt, ...) {
  char buf[4096]; va_list args; va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args); va_end(args); output += buf;
}
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
void send_log(int, char *) {}
void save_char_obj(CHAR_DATA *, bool, bool) { ++saves; }
bool save_clans(bool) { return true; }
OBJ_DATA *get_obj_carry(CHAR_DATA *, char *arg, CHAR_DATA *) {
  return !strcmp(arg, "glass") && !extracted ? &glass : nullptr;
}
void extract_obj(OBJ_DATA *obj) { assert(obj == &glass); ++extracted; }
MOB_INDEX_DATA *get_mob_index(int id) {
  if (!available) return nullptr;
  if (id == CORTEX_SOLDIER) return &soldier_index;
  if (id == 901 || id == 902) return &creature_index;
  return nullptr;
}
int get_demon_lvl(int) { return 10; }
CHAR_DATA *create_mobile(MOB_INDEX_DATA *index) {
  auto *mob = new CHAR_DATA{}; SET_FLAG(mob->act, ACT_IS_NPC);
  SET_FLAG(mob->act, ACT_SENTINEL);
  mob->pIndexData = index;
  mob->disciplines[DIS_TOUGHNESS] = 100; mob->disciplines[DIS_STRIKING] = 100;
  char_list.push_back(mob); return mob;
}
void char_to_room(CHAR_DATA *ch, ROOM_INDEX_DATA *room) { ch->in_room = room; }
int max_hp(CHAR_DATA *ch) { return ch->disciplines[DIS_TOUGHNESS] * 5; }
void start_fight(CHAR_DATA *ch, CHAR_DATA *victim) {
  assert(!IS_FLAG(ch->act, ACT_SENTINEL));
  ch->in_fight = victim->in_fight = true; ++fights;
}
void cleanup(CHAR_DATA *ch) {
  for (auto *mob : char_list) {
    free_string(mob->name); free_string(mob->short_descr); free_string(mob->long_descr);
    free_string(mob->description); free_string(mob->aggression); delete mob;
  }
  char_list.clear(); ch->in_fight = false; ch->pcdata->spawned_monsters = 0;
}
'''

production = '\n'.join([
    section(fight, '  int difficulty_mod(', '  char *const crystal_levels'),
    section(fight, '  bool cortex_enforcer(', '  bool cortex_alarm('),
    section(fight, '  bool cortex_send_enforcers(', '  void cortex_enforcer_defeat('),
    section(fight, '  bool cortex_offworld_ambush(', '  void populate_warren('),
    section(clans, '  static void society_sell_blood(', '  _DOFUN(do_society)'),
])

tests = r'''
int main() {
  CHAR_DATA ch = {}; PC_DATA pc = {}; AREA_DATA area = {}; ROOM_INDEX_DATA room = {};
  DESCRIPTOR_DATA desc = {}; ch.pcdata = &pc; ch.in_room = &room; room.area = &area;
  ch.desc = &desc; ch.name = const_cast<char *>("Seller"); room.vnum = 16068;
  society.vnum = ch.faction = ch.fsociety = 100; society.type = FACTION_SOCIETY;
  society.name = const_cast<char *>("Society");
  glass.pIndexData = &glass_index; glass_index.vnum = 33; glass.item_type = ITEM_DRINK_CON;
  glass.value[1] = 1; SET_BIT(glass.extra_flags, ITEM_VBLOOD);
  char arg[] = "glass";
  // Validation consumes neither blood nor opportunity.
  for (int invalid = 0; invalid < 7; ++invalid) {
    if (invalid == 0) ch.fsociety = 0;
    if (invalid == 1) society.stasis = 1;
    if (invalid == 2) allowed = false;
    if (invalid == 3) glass.value[1] = 0;
    if (invalid == 4) glass_index.vnum = 34;
    if (invalid == 5) emergency = true;
    if (invalid == 6) available = false;
    society_sell_blood(&ch, arg);
    assert(!extracted && !pc.last_blood_sale && !society.resource && !saves);
    ch.fsociety = 100; society.stasis = 0; allowed = true; glass.value[1] = 1;
    glass_index.vnum = 33; emergency = false; available = true;
  }
  // Every percentile 1-50 ambushes; 51-100 pays, with no overlapping outcomes.
  for (percent = 1; percent <= 100; ++percent) {
    pc.last_blood_sale = 0; extracted = 0; society.resource = 0;
    society_sell_blood(&ch, arg);
    assert(extracted == 1 && pc.last_blood_sale == current_time);
    assert((percent <= 50) == in_fight(&ch));
    assert(society.resource == (percent <= 50 ? 0 : 1000));
    cleanup(&ch);
  }
  // Reconnect-equivalent restored timestamp, society switching, and exact week boundary.
  percent = 51; extracted = 0; society.resource = 0;
  society.vnum = ch.faction = ch.fsociety = 101;
  current_time += 7 * 86400 - 1;
  society_sell_blood(&ch, arg); assert(!extracted && !society.resource);
  ++current_time; society_sell_blood(&ch, arg); assert(extracted == 1 && society.resource == 1000);
  // Successful payouts double at each lower tier, capped at $20,000 ($10 per resource).
  const int payouts[] = {0, 2000, 2000, 1000, 500, 250};
  for (tier = 1; tier <= 5; ++tier) {
    for (range_mode = 0; range_mode <= 1; ++range_mode) {
      pc.last_blood_sale = 0; extracted = 0; society.resource = 0;
      society_sell_blood(&ch, arg);
      assert(extracted == 1 && society.resource == payouts[tier]);
    }
  }
  // Low/high rolls and tier actually change combat disciplines and squad size.
  for (tier = 1; tier <= 5; ++tier) {
    for (range_mode = 0; range_mode <= 1; ++range_mode) {
      assert(cortex_send_enforcers(&ch));
      assert(char_list.size() == (range_mode ? UMIN(6, tier + 2) : 1));
      const int expected = (40 + 20 * tier) * (range_mode ? 249 : 41) / 100
          * (range_mode ? 125 : 75) / 100;
      for (auto *mob : char_list) {
        assert(mob->disciplines[DIS_STRIKING] == expected);
        assert(mob->disciplines[DIS_TOUGHNESS] == expected);
        assert(mob->disciplines[DIS_FATE] == 0);
      }
      assert(!cortex_send_enforcers(&ch)); cleanup(&ch);
    }
  }
  tier = 3; range_mode = 1; percent = 5; room.level = 100;
  ch.fcore = FACTION_CORTEX; area.world = WORLD_OTHER;
  assert(cortex_offworld_ambush(&ch)); assert(char_list.size() == 4);
  for (auto *mob : char_list) {
    assert(mob->pIndexData == &creature_index && mob->ttl == 12);
    assert(mob->disciplines[DIS_STRIKING] == 311);
    assert(IS_FLAG(mob->act, ACT_CORTEX_BREACH) && !strcmp(mob->aggression, ch.name));
  }
  assert(!cortex_offworld_ambush(&ch)); cleanup(&ch);
  pc.spawned_monsters = 1; assert(!cortex_offworld_ambush(&ch)); pc.spawned_monsters = 0;
  percent = 6; assert(!cortex_offworld_ambush(&ch)); percent = 5;
  ch.fcore = FACTION_SCUM; assert(!cortex_offworld_ambush(&ch)); ch.fcore = FACTION_CORTEX;
  area.world = WORLD_EARTH; assert(!cortex_offworld_ambush(&ch));
  area.world = WORLD_WILDS; assert(!cortex_offworld_ambush(&ch)); // No local template.
  area.world = WORLD_HELL; range_mode = 0; assert(cortex_offworld_ambush(&ch));
  assert(char_list.size() == 1); cleanup(&ch);
  puts("PASS: blood-sale validation, all 100 outcome rolls, weekly boundary, tier/count/discipline scaling and off-world ambushes.");
}
'''

# Ensure old saves start eligible and the character timestamp is written/read.
save = (ROOT / 'src/save.c').read_text()
assert '"LastBloodSale %d\\n", ch->pcdata->last_blood_sale' in save
assert 'KEY("LastBloodSale", ch->pcdata->last_blood_sale, fread_number(fp));' in save
assert (ROOT / 'src/recycle.c').read_text().count('pcdata->last_blood_sale = 0;') == 2
assert 'cortex_offworld_ambush(ch) || cortex_monster_ambush(ch)' in (ROOT / 'src/act_move.c').read_text()

with tempfile.TemporaryDirectory(prefix='haven-blood-sale-') as temporary:
    path = Path(temporary)
    source = path / 'test.cc'
    source.write_text(stubs + production + tests)
    subprocess.run(['g++', '-std=gnu++17', '-g', '-O1', '-Wno-write-strings',
                    '-Wno-deprecated', '-fsanitize=address,undefined', '-no-pie',
                    '-I', str(ROOT / 'src'), str(source), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
