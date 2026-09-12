#!/usr/bin/env python3
"""Run production dissent/public-response policies with a small world in WSL/Linux."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
fight = (ROOT / 'src/fight.c').read_text()


def section(start, end):
    a = fight.index(start)
    return fight[a:fight.index(end, a)]


stubs = r'''
#include "merc.h"
#include "global.h"
#include <cassert>
#include <cstring>
#include <cstdlib>
#include <cstdarg>
#include <map>
CharList char_list;
DescList descriptor_list;
std::vector<FACTION_TYPE *> FacVect;
ROOM_INDEX_DATA *room_index_hash[MAX_KEY_HASH] = {};
time_t current_time = 2000000000;
int event_cleanse = 0, fight_problem = 0;
bool full_moon_pack(CHAR_DATA *) { return false; }
CHAR_DATA *full_moon_pack_prey(CHAR_DATA *) { return nullptr; }
bool emergency = false;
bool state_of_emergency(void) { return emergency; }
const struct discipline_type discipline_table[] = {};
const int discipline_table_count = 0;
ROOM_INDEX_DATA limbo = {};
ROOM_INDEX_DATA meeting_west = {}, meeting_east = {}, prison_west = {}, prison_east = {};
bool auction_rooms_available = true;
MOB_INDEX_DATA crowd_index = {}, enforcer_index = {};
int saves = 0, ambushes = 0, fights = 0, aggro_attacker = 20;
bool save_ok = true;
std::map<CHAR_DATA *, std::string> output_messages;
FACTION_TYPE *clan_lookup(int id) {
  for (auto *f : FacVect) if (f->vnum == id) return f;
  return nullptr;
}
char *str_dup(const char *s) { return strdup(s); }
void free_string(char *s) { free(s); }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
void send_to_char(const char *s, CHAR_DATA *ch) { output_messages[ch] += s; }
void save_char_obj(CHAR_DATA *, bool, bool) {}
void send_message(int, char *) {}
void printf_to_char(CHAR_DATA *ch, const char *fmt, ...) {
  char buf[8192]; va_list args; va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args); va_end(args); output_messages[ch] += buf;
}
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
void send_log(int, char *) {}
bool save_clans(bool) { ++saves; return save_ok; }
bool is_gm(CHAR_DATA *) { return false; }
bool is_ghost(CHAR_DATA *) { return false; }
bool higher_power(CHAR_DATA *) { return false; }
bool free_to_act(CHAR_DATA *ch) { return ch->in_room && !ch->in_fight; }
bool is_helpless(CHAR_DATA *ch) { return !IS_NPC(ch) && ch->pcdata->sleeping > 0; }
int number_range(int a, int) { return a; }
int max_hp(CHAR_DATA *ch) { return ch->disciplines[DIS_TOUGHNESS] * 5 + 25; }
void set_combat_state(CHAR_DATA *ch, bool state) { ch->in_fight = state; }
bool in_fight(CHAR_DATA *ch) { return ch->in_fight; }
void start_fight(CHAR_DATA *ch, CHAR_DATA *victim) {
  ++fights; set_combat_state(ch, true); set_combat_state(victim, true);
}
MOB_INDEX_DATA *get_mob_index(int id) { return id == 115 ? &crowd_index : &enforcer_index; }
ROOM_INDEX_DATA *get_room_index(int id) {
  if (!auction_rooms_available && (id == ROOM_MEETING_WEST || id == ROOM_MEETING_EAST)) return nullptr;
  if (id == ROOM_MEETING_WEST) return &meeting_west;
  if (id == ROOM_MEETING_EAST) return &meeting_east;
  if (id == ROOM_PRISON_WEST) return &prison_west;
  if (id == ROOM_PRISON_EAST) return &prison_east;
  return &limbo;
}
int pc_pop(ROOM_INDEX_DATA *room) {
  int count = 0;
  for (auto *ch : char_list) if (!IS_NPC(ch) && ch->in_room == room) ++count;
  return count;
}
bool in_haven(ROOM_INDEX_DATA *) { return true; }
CHAR_DATA *get_gm(ROOM_INDEX_DATA *, bool) { return nullptr; }
bool same_faction(CHAR_DATA *, CHAR_DATA *) { return false; }
int prof_focus(CHAR_DATA *) { return 0; }
CHAR_DATA *create_mobile(MOB_INDEX_DATA *index) {
  auto *ch = new CHAR_DATA{}; ch->pIndexData = index;
  ch->race = RACE_SOLDIER; SET_FLAG(ch->act, ACT_IS_NPC);
  SET_FLAG(ch->act, ACT_SENTINEL); // Ensure production explicitly removes this.
  ch->name = str_dup(""); ch->short_descr = str_dup("");
  ch->long_descr = str_dup(""); ch->description = str_dup("");
  ch->protecting = str_dup(""); ch->aggression = str_dup("");
  char_list.push_back(ch); return ch;
}
void char_to_room(CHAR_DATA *ch, ROOM_INDEX_DATA *room) { ch->in_room = room; }
void char_from_room(CHAR_DATA *ch) { ch->in_room = nullptr; }
char *roomtitle(ROOM_INDEX_DATA *room, bool) { return room->name; }
CHAR_DATA *get_char_world_pc(char *name) {
  for (auto *ch : char_list) if (!IS_NPC(ch) && !str_cmp(name, ch->name)) return ch;
  return nullptr;
}
bool cortex_monster_ambush(CHAR_DATA *, bool) { ++ambushes; return true; }
bool cortex_breach_monster(CHAR_DATA *ch) { return cortex_enforcer(ch); }
int in_world(CHAR_DATA *) { return WORLD_EARTH; }
bool can_get_to(CHAR_DATA *, ROOM_INDEX_DATA *) { return true; }
bool forest_monster(CHAR_DATA *) { return false; }
bool is_invader(CHAR_DATA *) { return false; }
int get_trust(CHAR_DATA *) { return 0; }
int mist_level(ROOM_INDEX_DATA *) { return 0; }
int init_combat_distance(CHAR_DATA *, CHAR_DATA *, bool) { return 1; }
int combat_distance(CHAR_DATA *, CHAR_DATA *, bool) { return 1; }
int get_agg(CHAR_DATA *, CHAR_DATA *victim) {
  return !strcmp(victim->name, "Attacker") ? aggro_attacker : 1000;
}
struct AggressionAttackProfile {};
int aggression_score(CHAR_DATA *ch, CHAR_DATA *victim, AggressionAttackProfile &) {
  return get_agg(ch, victim);
}
bool in_public(CHAR_DATA *, CHAR_DATA *) { return true; }
bool will_agg(CHAR_DATA *, CHAR_DATA *) { return true; }
CHAR_DATA *get_cover(CHAR_DATA *) { return nullptr; }
bool can_see_char_distance(CHAR_DATA *, CHAR_DATA *, int) { return true; }
'''

patrols = (ROOT / 'src/patrols.c').read_text()
production = '\n'.join([
    patrols[patrols.index('  bool start_syndicate_auction('):patrols.index('  bool free_to_act(')],
    section('  bool cortex_enforcer(', '  bool cortex_alarm('),
    section('  void cortex_enforcer_defeat(', '  static time_t cortex_breach_until'),
    section('  int difficulty_mod(', '  char *const crystal_levels'),
    section('  bool is_enemy(CHAR_DATA *ch, CHAR_DATA *victim) {', '  bool has_enemy('),
    section('  CHAR_DATA *get_npc_target(CHAR_DATA *ch) {', '  int process_npc_special('),
    (ROOT / 'src/dissent.c').read_text(),
    (ROOT / 'src/public_combat.c').read_text(),
])

tests = r'''
void cleanup_mobs() {
  for (auto it = char_list.begin(); it != char_list.end();) {
    CHAR_DATA *ch = *it;
    if (!IS_NPC(ch)) { ++it; continue; }
    it = char_list.erase(it);
    free_string(ch->name); free_string(ch->short_descr); free_string(ch->long_descr);
    free_string(ch->description); free_string(ch->protecting); free_string(ch->aggression);
    delete ch;
  }
}
int main() {
  crowd_index.vnum = 115; enforcer_index.vnum = CORTEX_SOLDIER;
  FACTION_TYPE cortex = {}, society = {}, offline = {}, scum = {}, npc = {}, deleted = {};
  cortex.vnum = FACTION_CORTEX; cortex.type = FACTION_CORE; cortex.valid = true;
  society.vnum = 100; society.type = FACTION_SOCIETY; society.valid = true;
  offline = society; offline.vnum = 101; offline.closed = 1;
  scum = cortex; scum.vnum = FACTION_SCUM;
  npc = society; npc.vnum = 102; npc.type = FACTION_NPC;
  deleted = society; deleted.vnum = 103; deleted.valid = false;
  FacVect = {&cortex, &society, &offline, &scum, &npc, &deleted};
  AREA_DATA town = {}; town.vnum = HAVEN_TOWN_VNUM; town.name = const_cast<char *>("Gravesend Township");
  ROOM_INDEX_DATA street = {}, other = {}; EXIT_DATA exit = {};
  street.area = other.area = &town; street.name = const_cast<char *>("Actual protest street");
  other.name = const_cast<char *>("Another street");
  street.room_flags = ROOM_PUBLIC; street.sector_type = SECT_STREET;
  street.x = 12; street.y = 34; street.size = 50;
  exit.u1.to_room = &other; exit.wall = WALL_NONE; street.exit[0] = &exit;
  room_index_hash[0] = &street;
  CHAR_DATA attacker = {}, defender = {}, outsider = {}; PC_DATA apc = {}, dpc = {}, opc = {};
  attacker.name = const_cast<char *>("Attacker"); defender.name = const_cast<char *>("Defender");
  outsider.name = const_cast<char *>("Outsider");
  attacker.pcdata = &apc; defender.pcdata = &dpc; outsider.pcdata = &opc;
  attacker.in_room = defender.in_room = outsider.in_room = &street;
  attacker.fcore = FACTION_CORTEX; defender.fsociety = society.vnum; outsider.fcore = FACTION_SCUM;
  attacker.hit = defender.hit = 200;
  char_list = {&attacker, &defender, &outsider};
  DESCRIPTOR_DATA ad = {}, defender_desc = {}, od = {};
  ad.character = &attacker; defender_desc.character = &defender; od.character = &outsider;
  ad.connected = defender_desc.connected = od.connected = CON_PLAYING;
  descriptor_list = {&ad, &defender_desc, &od};

  // Only eligible waking players can trigger dissent, with both sides available.
  assert(!dissent_launch(&outsider));
  SET_FLAG(attacker.act, PLR_SHROUD); assert(!dissent_launch(&attacker));
  REMOVE_FLAG(attacker.act, PLR_SHROUD);
  SET_FLAG(defender.act, PLR_DEEPSHROUD); assert(!dissent_launch(&attacker));
  REMOVE_FLAG(defender.act, PLR_DEEPSHROUD);
  street.room_flags |= ROOM_PRIVATE; assert(!dissent_launch(&attacker));
  street.room_flags = ROOM_PUBLIC;
  save_ok = false; assert(!dissent_launch(&attacker));
  assert(cortex.last_dissent == 0 && char_list.size() == 3);
  save_ok = true;
  assert(dissent_launch(&attacker));
  CHAR_DATA *mob = dissent_mob(); assert(mob && mob->in_room == &street);
  assert(!IS_FLAG(mob->act, ACT_SENTINEL) && mob->ttl > 0);
  assert(!strcmp(mob->short_descr, "a crowd") && strstr(mob->description, "dissenting mob"));
  assert(output_messages[&outsider].empty());
  assert(output_messages[&attacker].find("Actual protest street") != std::string::npos);
  assert(output_messages[&attacker].find("map 12, 34") != std::string::npos);
  attacker.attacking = 1;
  assert(public_target_excluded(&attacker, &defender));
  assert(!is_enemy(&attacker, &defender));
  assert(!public_target_excluded(&attacker, mob));
  assert(is_enemy(&attacker, mob)); // Public, stationary NPC remains a combat target.
  assert(get_npc_target(mob) == nullptr);
  assert(dissent_in_room(&street) && !dissent_in_room(&other));
  int count = char_list.size(); cortex_public_response(&attacker, &defender);
  assert((int)char_list.size() == count); // Dissent suppresses reinforcements.
  assert(!dissent_launch(&attacker));
  current_time += 1799; dissent_update(); assert(society.resource == 0);
  dissent_status(&defender); assert(output_messages[&defender].find("1 minute(s)") != std::string::npos);
  current_time += 1; dissent_update();
  assert(society.resource == 1000 && offline.resource == 1000 && cortex.resource == 0);
  assert(output_messages[&defender].find("$10000 in resources") != std::string::npos);
  assert(scum.resource == 0 && npc.resource == 0 && deleted.resource == 0);
  assert(mob->in_room == &limbo && mob->wounds == 4 && !in_fight(mob));
  dissent_update(); dissent_defeated(mob); assert(society.resource == 1000 && cortex.resource == 0);
  cleanup_mobs();
  current_time = cortex.last_dissent + 7 * 86400 - 1;
  assert(!dissent_launch(&attacker)); // Also covers a restart: only saved cooldown remains.
  ++current_time; assert(dissent_launch(&attacker));
  mob = dissent_mob(); current_time += 900;
  mob->hit = 0; dissent_defeated(mob); dissent_defeated(mob); dissent_update();
  assert(cortex.resource == 10000 && society.resource == 1000);
  assert(output_messages[&attacker].find("$100000 in resources") != std::string::npos);
  cleanup_mobs();
  current_time = cortex.last_dissent + 7 * 86400;
  assert(dissent_launch(&attacker)); cleanup_mobs(); dissent_update();
  assert(cortex.resource == 10000 && society.resource == 1000); // Purges don't pay out.
  assert(!dissent_launch(&attacker));

  // Public squads target only the aggressor, even when another target has more aggro.
  street.room_flags = 0; // A public street without the explicit ROOM_PUBLIC exclusion.
  assert(!public_target_excluded(&attacker, &defender));
  cortex_public_response(&attacker, &defender);
  assert(char_list.size() == 5 && fights == 2);
  CHAR_DATA *enforcer = nullptr;
  for (auto *ch : char_list) if (cortex_public_enforcer(ch)) {
    enforcer = ch; assert(!IS_FLAG(ch->act, ACT_SENTINEL));
    assert(get_npc_target(ch) == &attacker);
    assert(!strcmp(ch->protecting, defender.name));
  }
  assert(enforcer);
  cortex_public_response(&attacker, &defender); assert(char_list.size() == 5);
  attacker.wounds = 2; attacker.hit = 0;
  cortex_enforcer_defeat(enforcer, &attacker);
  assert(apc.sleeping >= 240 && attacker.hit == 0 && attacker.wounds == 2);
  assert(attacker.in_room == &street && !in_fight(&attacker) && ambushes == 0);
  assert(defender.hit == 200 && dpc.sleeping == 0);
  for (auto *ch : char_list) if (cortex_public_enforcer(ch))
    assert(ch->ttl == 0 && !in_fight(ch) && !get_npc_target(ch));
  cleanup_mobs(); apc.sleeping = 0; attacker.wounds = 0;

  for (int flag : {PLR_SHROUD, PLR_DEEPSHROUD}) {
    SET_FLAG(attacker.act, flag); cortex_public_response(&attacker, &defender);
    assert(char_list.size() == 3); REMOVE_FLAG(attacker.act, flag);
    SET_FLAG(defender.act, flag); cortex_public_response(&attacker, &defender);
    assert(char_list.size() == 3); REMOVE_FLAG(defender.act, flag);
  }
  cortex_public_response(&attacker, &defender);
  emergency = true;
  assert(!public_target_excluded(&attacker, &defender));
  cortex_public_update();
  for (auto *ch : char_list) if (cortex_public_enforcer(ch)) assert(ch->ttl == 0 && !in_fight(ch));
  cleanup_mobs();
  cortex_public_response(&attacker, &defender); assert(char_list.size() == 3);
  emergency = false;
  cortex_public_response(&attacker, &defender);
  apc.sleeping = 100; cortex_public_update();
  for (auto *ch : char_list) if (cortex_public_enforcer(ch)) assert(ch->ttl == 0);
  assert(apc.sleeping == 100 && attacker.in_room == &street);
  cleanup_mobs();

  // Alarm defeat auctions this exact character, with no monster or defense restoration.
  apc.sleeping = 0; attacker.in_room = &street; attacker.hit = 0; attacker.wounds = 2;
  dpc.patrol_habits[PATROL_DIPLOMATICHABIT] = 1; dpc.patrol_amount = 999;
  opc.patrol_habits[PATROL_DIPLOMATICHABIT] = 1;
  SET_FLAG(outsider.act, PLR_SHROUD);
  meeting_west.name = const_cast<char *>("West auction");
  meeting_east.name = const_cast<char *>("East auction");
  auto *alarm = create_mobile(&enforcer_index);
  SET_FLAG(alarm->act, ACT_CORTEX_ENFORCER); alarm->ttl = 12;
  free_string(alarm->aggression); alarm->aggression = str_dup(attacker.name);
  alarm->in_room = &street;
  cortex_enforcer_defeat(alarm, &attacker);
  assert(attacker.in_room == &prison_west && !IS_FLAG(attacker.act, PLR_BOUND));
  assert(apc.patrol_status == PATROL_KIDNAPPED && apc.patrol_timer == 24 * 60);
  assert(apc.syndicate_release_at == current_time + 24 * 60 * 60);
  assert(apc.sleeping == 0 && attacker.hit == 0 && attacker.wounds == 2 && ambushes == 0);
  assert(!in_fight(&attacker) && alarm->ttl == 0 && !in_fight(alarm));
  assert(dpc.patrol_status == PATROL_BIDDING && dpc.patrol_target == &attacker);
  assert(dpc.patrol_timer == 15 && dpc.patrol_room == &meeting_west && dpc.patrol_amount == 0);
  assert(opc.patrol_status == 0);
  apc.patrol_timer = 20; cortex_enforcer_defeat(alarm, &attacker);
  assert(apc.patrol_timer == 20); // Retired squad cannot capture a second time.
  assert(!start_syndicate_auction(&attacker));
  cleanup_mobs();

  // Occupied cells force the other venue; full venues leave the victim in place.
  REMOVE_FLAG(outsider.act, PLR_SHROUD);
  assert(start_syndicate_auction(&outsider) && outsider.in_room == &prison_east);
  dpc.patrol_status = 0;
  alarm = create_mobile(&enforcer_index);
  SET_FLAG(alarm->act, ACT_CORTEX_ENFORCER); alarm->ttl = 12;
  free_string(alarm->aggression); alarm->aggression = str_dup(defender.name);
  cortex_enforcer_defeat(alarm, &defender);
  assert(defender.in_room == &street && dpc.sleeping >= 240 && defender.hit == 0);
  assert(dpc.patrol_status == 0 && ambushes == 0);
  cleanup_mobs();
  auction_rooms_available = false;
  assert(!start_syndicate_auction(&defender));
  assert(!start_syndicate_auction(nullptr));
  for (PC_DATA *pc : {&apc, &dpc, &opc}) {
    free_string(pc->syndicate_seller);
    free_string(pc->syndicate_prisoner);
  }
  puts("Dissent, public-response KO, alarm auctions, venue availability and nightmare tests passed.");
}
'''

# Verify production entry points retain the tested policies.
assert 'if (public_start) cortex_public_response(ch, target);' in fight
assert 'const bool public_start = !IS_NPC(ch) && !in_fight(ch) && in_public(ch, target);' in fight
assert 'if (cortex_public_enforcer(ch)) {\n        cortex_enforcer_defeat(ch, victim);' in fight
assert 'dissent_in_room(ch->in_room) || number_percent()' in fight
assert 'CortexLastDissent", fac->last_dissent, fread_number(fp)' in (ROOT / 'src/clans.c').read_text()
assert 'CortexLastDissent %d\\n", (*it)->last_dissent' in (ROOT / 'src/clans.c').read_text()

with tempfile.TemporaryDirectory(prefix='haven-dissent-') as temp:
    path = Path(temp)
    source = path / 'test.cc'
    source.write_text(stubs + production + tests)
    subprocess.run(['g++', '-std=gnu++17', '-g', '-O1', '-Wno-write-strings',
                    '-Wno-deprecated', '-fsanitize=address,undefined', '-no-pie',
                    '-I', str(ROOT / 'src'), str(source), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
