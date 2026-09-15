#!/usr/bin/env python3
"""Linux/WSL sanitizer regression for public attack rumors and visible identities."""
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
#include "text_format.h"
#include <cassert>
#include <cstdlib>
#include <cstring>
#include <set>

time_t current_time = 2000000000;
CHAR_DATA attacker = {}, victim = {};
PC_DATA attacker_pc = {}, victim_pc = {};
ROOM_INDEX_DATA room = {}, other_room = {};
AREA_DATA area = {};
std::set<char *> allocations;
std::vector<std::string> rumors;
int roll = 25, rolls = 0, public_responses = 0, phase = 4, mist = 0;
bool protected_target = false, prisoner = false, institute = false;
bool dark = false, shadow = false, elsewhere = false, quiet = false;

char *str_dup(const char *value) {
  char *copy = strdup(value ? value : "");
  assert(copy && allocations.insert(copy).second);
  return copy;
}
void free_string(char *value) {
  if (!value) return;
  assert(allocations.erase(value) == 1);
  free(value);
}
size_t safe_strlen(const char *value) { return value ? strlen(value) : 0; }
int number_percent() { ++rolls; return roll; }
void gossip(char *value) { rumors.emplace_back(value); }
char *roomtitle(ROOM_INDEX_DATA *where, bool capital) {
  assert(!capital);
  return str_dup(where->name);
}
bool is_covered(CHAR_DATA *, int part) { return part == COVERS_GROIN; }
int sunphase(ROOM_INDEX_DATA *) { return phase; }
int mist_level(ROOM_INDEX_DATA *) { return mist; }
bool shadowcloaked(ROOM_INDEX_DATA *) { return shadow; }
int get_roomy(ROOM_INDEX_DATA *where) { return where->y; }
bool is_dark(ROOM_INDEX_DATA *) { return dark; }
bool offworld(CHAR_DATA *) { return elsewhere; }
bool silenced(CHAR_DATA *) { return quiet; }
bool institute_room(ROOM_INDEX_DATA *) { return institute; }
bool in_fight(CHAR_DATA *ch) { return ch->in_fight; }
bool pedestrian(CHAR_DATA *) { return false; }
bool pedestrian_helpless(CHAR_DATA *) { return false; }
bool sin_cortex_guard(CHAR_DATA *) { return false; }
bool sin_cortex_guard_target(CHAR_DATA *, CHAR_DATA *) { return false; }
bool sin_vigilante(CHAR_DATA *) { return false; }
bool sin_vigilante_target(CHAR_DATA *, CHAR_DATA *) { return false; }
bool full_moon_pack(CHAR_DATA *) { return false; }
bool full_moon_pack_target(CHAR_DATA *, CHAR_DATA *) { return false; }
bool public_target_excluded(CHAR_DATA *, CHAR_DATA *) { return protected_target; }
bool is_institute_taught(CHAR_DATA *) { return false; }
bool can_institute_teach(CHAR_DATA *) { return false; }
bool is_prisoner(CHAR_DATA *) { return prisoner; }
bool forest_monster(CHAR_DATA *) { return false; }
bool cortex_breach_monster(CHAR_DATA *) { return false; }
bool is_invader(CHAR_DATA *) { return false; }
bool can_shroud(CHAR_DATA *) { return false; }
bool guestmonster(CHAR_DATA *) { return false; }
void send_to_char(const char *, CHAR_DATA *) {}
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
void add_aggro(CHAR_DATA *, CHAR_DATA *, int) {}
void forest_fight(CHAR_DATA *, CHAR_DATA *) {}
void set_combat_state(CHAR_DATA *ch, bool active) { ch->in_fight = active; }
void join_to_fight(CHAR_DATA *ch) { set_combat_state(ch, true); }
void do_spar(CHAR_DATA *ch, char *) { SET_FLAG(ch->comm, COMM_SPARRING); }
void do_function(CHAR_DATA *ch, DO_FUN *function, char *arg) { function(ch, arg); }
CHAR_DATA *next_fight_member_init(CHAR_DATA *) { return nullptr; }
CHAR_DATA *next_fight_member(CHAR_DATA *) { return nullptr; }
void reset_turns(CHAR_DATA *) {}
void next_attacker(CHAR_DATA *, bool) {}
bool same_fight(CHAR_DATA *, CHAR_DATA *) { return true; }
void cortex_public_response(CHAR_DATA *, CHAR_DATA *) { ++public_responses; }
'''

source += section('lookup.c', '  bool is_masked(', '  bool is_cloaked(')
source += section('lookup.c', '  bool is_cloaked(', '  bool all_covered(')
source += section('act_info.c', '  char *mask_intro(', '  _DOFUN(do_mask)')
source += section('act_info.c', '  char *get_intro(', '  int vision_range_character(')
source += section('fight.c', '  bool is_sparring_room(', '  bool sparring_conditions(')
source += section('clans.c', '  bool public_room(', '  bool in_base(')
source += section('fight.c', '  static void public_attack_rumor(', '  void start_roomfight(')

source += r'''
void reset() {
  assert(allocations.empty());
  attacker = {}; victim = {}; attacker_pc = {}; victim_pc = {};
  room = {}; other_room = {}; area = {};
  attacker.pcdata = &attacker_pc; victim.pcdata = &victim_pc;
  attacker.name = (char *)"SecretAttackerName";
  victim.name = (char *)"SecretVictimName";
  attacker.short_descr = (char *)"a hostile stranger";
  victim.short_descr = (char *)"a uniformed guard";
  attacker.shape = victim.shape = SHAPE_HUMAN;
  attacker.in_room = victim.in_room = &room;
  room.area = other_room.area = &area;
  area.vnum = 100;
  room.room_flags = ROOM_PUBLIC;
  room.name = (char *)"at the Market Square";
  other_room.name = (char *)"at the North Gate";
  attacker_pc.intro_desc = (char *)"A red-haired woman";
  victim_pc.intro_desc = (char *)"A tall man";
  attacker_pc.mask_intro_one = (char *)"A fox-masked figure";
  attacker_pc.mask_intro_two = (char *)"A silver-masked figure";
  victim_pc.mask_intro_one = (char *)"A raven-masked figure";
  victim_pc.mask_intro_two = (char *)"A golden-masked figure";
  attacker_pc.wolfintro = (char *)"A scarred gray wolf";
  victim_pc.wolfintro = (char *)"A white wolf";
  attacker_pc.mermaidintro = (char *)"A green-tailed mermaid";
  victim_pc.mermaidintro = (char *)"A blue-tailed mermaid";
  attacker_pc.animal_intros[0] = (char *)"A large black cat";
  victim_pc.animal_intros[0] = (char *)"A small brown bear";
  roll = 25; rolls = public_responses = 0; phase = 4; mist = 0;
  protected_target = prisoner = institute = false;
  dark = shadow = elsewhere = quiet = false;
  rumors.clear();
}
void assert_rumor(const char *actor_intro, const char *target_intro,
                  const char *location = "at the Market Square") {
  assert(rumors.size() == 1 && rolls == 1);
  assert(rumors[0] == std::string(actor_intro) + " was seen attacking "
      + target_intro + " " + location + ".");
  assert(rumors[0].find("SecretAttackerName") == std::string::npos);
  assert(rumors[0].find("SecretVictimName") == std::string::npos);
  assert(allocations.empty());
}
void assert_no_rumor() {
  start_fight(&attacker, &victim);
  assert(rumors.empty() && rolls == 0 && allocations.empty());
}
int main() {
  reset(); start_fight(&attacker, &victim);
  assert(attacker.in_fight && victim.in_fight && public_responses == 1);
  assert_rumor("A red-haired woman", "A tall man");
  // Subsequent combat starts and retaliation do not reroll the same fight.
  start_fight(&attacker, &victim); start_fight(&victim, &attacker);
  assert(rumors.size() == 1 && rolls == 1 && public_responses == 1);
  reset(); roll = 26; start_fight(&attacker, &victim);
  assert(rumors.empty() && rolls == 1 && attacker.in_fight && victim.in_fight);
  start_fight(&attacker, &victim); assert(rolls == 1);
  reset(); roll = 1; start_fight(&attacker, &victim);
  assert_rumor("A red-haired woman", "A tall man");

  // Each participant's selected mask is independent, including matching slots.
  for (int actor_mask : {0, 1, 2}) for (int target_mask : {0, 1, 2}) {
    reset(); attacker_pc.maskednumber = actor_mask; victim_pc.maskednumber = target_mask;
    const char *actor_intro[] = {attacker_pc.intro_desc, attacker_pc.mask_intro_one,
                                attacker_pc.mask_intro_two};
    const char *target_intro[] = {victim_pc.intro_desc, victim_pc.mask_intro_one,
                                 victim_pc.mask_intro_two};
    start_fight(&attacker, &victim);
    assert_rumor(actor_intro[actor_mask], target_intro[target_mask]);
    if (actor_mask) assert(rumors[0].find(attacker_pc.intro_desc) == std::string::npos);
    if (target_mask) assert(rumors[0].find(victim_pc.intro_desc) == std::string::npos);
  }
  reset(); attacker_pc.maskednumber = 1; attacker_pc.mask_intro_one = (char *)"Mask";
  start_fight(&attacker, &victim); assert_rumor("A masked figure", "A tall man");
  for (int side : {0, 1, 2}) {
    reset();
    if (side != 1) SET_FLAG(attacker.comm, COMM_CLOAKED);
    if (side != 0) SET_FLAG(victim.comm, COMM_CLOAKED);
    start_fight(&attacker, &victim);
    assert_rumor(side == 1 ? "A red-haired woman" : "A blurry shape",
                 side == 0 ? "A tall man" : "A blurry shape");
  }
  reset(); SET_FLAG(attacker.comm, COMM_CLOAKED); attacker_pc.maskednumber = 2;
  start_fight(&attacker, &victim); assert_rumor("A silver-masked figure", "A tall man");
  for (int shape : {SHAPE_WOLF, SHAPE_MERMAID, SHAPE_ANIMALONE}) {
    reset(); attacker.shape = victim.shape = shape;
    start_fight(&attacker, &victim);
    assert_rumor(shape == SHAPE_WOLF ? "A scarred gray wolf" : shape == SHAPE_MERMAID
        ? "A green-tailed mermaid" : "A large black cat",
        shape == SHAPE_WOLF ? "A white wolf" : shape == SHAPE_MERMAID
        ? "A blue-tailed mermaid" : "A small brown bear");
  }
  reset(); attacker.shape = SHAPE_MERMAID; attacker_pc.maskednumber = 1;
  start_fight(&attacker, &victim); assert_rumor("A fox-masked figure", "A tall man");
  reset(); attacker.shape = SHAPE_WOLF; attacker_pc.maskednumber = 1;
  start_fight(&attacker, &victim); assert_rumor("A scarred gray wolf", "A tall man");

  reset(); SET_FLAG(victim.act, ACT_IS_NPC); victim.pcdata = nullptr;
  start_fight(&attacker, &victim); assert_rumor("A red-haired woman", "a uniformed guard");
  reset(); SET_FLAG(attacker.act, ACT_IS_NPC); attacker.pcdata = nullptr; assert_no_rumor();
  reset(); attacker.in_room = &other_room; start_fight(&attacker, &victim);
  assert_rumor("A red-haired woman", "A tall man", "at the Market Square");

  // Exercise production public-room policy and exclusions before combat starts.
  reset(); room.room_flags = ROOM_PRIVATE; assert_no_rumor();
  reset(); room.room_flags = 0; assert_no_rumor();
  reset(); room.room_flags |= ROOM_SPARRING; assert_no_rumor();
  reset(); room.room_flags |= ROOM_UNLIT; phase = 1; assert_no_rumor();
  reset(); dark = true; assert_no_rumor();
  reset(); mist = 3; phase = 3; assert_no_rumor();
  reset(); elsewhere = true; assert_no_rumor();
  reset(); quiet = true; assert_no_rumor();
  reset(); victim_pc.bloodaura = 1; assert_no_rumor();
  for (int side : {0, 1}) {
    reset(); SET_FLAG((side ? victim : attacker).comm, COMM_SPARRING); assert_no_rumor();
    reset(); SET_FLAG((side ? victim : attacker).act, PLR_DEEPSHROUD); assert_no_rumor();
    reset(); SET_FLAG((side ? victim : attacker).act, PLR_SHROUD); assert_no_rumor();
  }
  reset(); SET_FLAG(attacker.act, PLR_SHROUD); SET_FLAG(victim.act, PLR_SHROUD);
  assert_no_rumor(); assert(attacker.in_fight && victim.in_fight);
  reset(); protected_target = true; assert_no_rumor(); assert(!attacker.in_fight);
  reset(); prisoner = true; assert_no_rumor(); assert(!attacker.in_fight);
  reset(); victim_pc.sleeping = 1; assert_no_rumor(); assert(!attacker.in_fight);
  reset(); institute = true; room.room_flags |= ROOM_INDOORS;
  assert_no_rumor(); assert(!attacker.in_fight);
  reset(); attacker_pc.patrol_status = PATROL_ATTACKSEARCHING;
  assert_no_rumor(); assert(!attacker.in_fight);
  reset(); victim.in_fight = true; assert_no_rumor();

  // Direct helper guards remain safe even with incomplete character state.
  reset(); public_attack_rumor(nullptr, &victim); public_attack_rumor(&attacker, nullptr);
  public_attack_rumor(&attacker, &attacker);
  attacker.in_room = nullptr; public_attack_rumor(&attacker, &victim);
  attacker.in_room = &room; victim.in_room = nullptr; public_attack_rumor(&attacker, &victim);
  assert(rumors.empty() && rolls == 0 && allocations.empty());
  // Formatting preserves long user-authored intros without a fixed buffer overflow.
  reset(); std::string long_intro(12000, 'x'); attacker_pc.intro_desc = long_intro.data();
  start_fight(&attacker, &victim); assert_rumor(long_intro.c_str(), "A tall man");
  puts("PASS: public attack chance, mask/cloak/form identities, location, private and nightmare exclusions, blocked/repeated combat, and string ownership.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-public-attack-rumor-') as tmp:
    path = Path(tmp)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-fsanitize=address,undefined',
                    '-fno-sanitize-recover=all', '-fno-omit-frame-pointer', '-no-pie',
                    '-I', str(ROOT / 'src'), str(path / 'test.cc'),
                    '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
