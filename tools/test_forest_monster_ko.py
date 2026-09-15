#!/usr/bin/env python3
"""Exercise forest KO retirement and real abduction eligibility in WSL/Linux."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
fight = (ROOT / 'src/fight.c').read_text()
update = (ROOT / 'src/update.c').read_text()
lookup = (ROOT / 'src/lookup.c').read_text()
abominations = (ROOT / 'src/abominations.c').read_text()
stories = (ROOT / 'src/stories.c').read_text()


def section(source, start, end):
    a = source.index(start)
    return source[a:source.index(end, a)]


source = r'''
#include "merc.h"
#include "runtime_indexes.cc"
#include <cassert>
#include <climits>
#include <cmath>

DescList descriptor_list;
std::vector<LAIR_TYPE *> LairVect;
int invasion_one = 1, invasion_two = 0, invasion_three = 0;
bool public_location = false, property_room = false, room_combat = true;
bool battle = false, guest = false, gm = false;
int mist = 3, extracted = 0, damage_fallthrough = 0, survived_update = 0;
PROP_TYPE property = {};
bool full_moon_pack(CHAR_DATA *) { return false; }
bool in_public(CHAR_DATA *, CHAR_DATA *) { return public_location; }
PROP_TYPE *in_prop(CHAR_DATA *) { return property_room ? &property : nullptr; }
int mist_level(ROOM_INDEX_DATA *) { return mist; }
bool is_gm(CHAR_DATA *) { return gm; }
bool room_fight(ROOM_INDEX_DATA *, bool, bool, bool) { return room_combat; }
bool battleground(ROOM_INDEX_DATA *) { return battle; }
bool guestmonster(CHAR_DATA *) { return guest; }
bool is_vampire(CHAR_DATA *) { return false; }
bool pedestrian(CHAR_DATA *) { return false; }
bool pedestrian_helpless(CHAR_DATA *) { return false; }
bool is_ghost(CHAR_DATA *) { return false; }
bool is_undead(CHAR_DATA *) { return false; }
bool higher_power(CHAR_DATA *) { return false; }
int pc_pop(ROOM_INDEX_DATA *) { return 1; }
bool in_fight(CHAR_DATA *ch) { return ch->in_fight; }
bool cortex_breach_monster(CHAR_DATA *) { return false; }
CHAR_DATA *find_prey(CHAR_DATA *) { return nullptr; }
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
void extract_char(CHAR_DATA *ch, bool pull) {
  assert(pull);
  ++extracted;
  unregister_live_character(ch);
  ch->in_room = nullptr;
}
'''
source += section(fight, '  bool forest_monster(', '  CHAR_DATA *find_prey(')
source += section(fight, '  int get_dist(', '  void move_message(')
source += section(abominations, '  bool in_lair(', '  bool lair_room(')
source += section(stories, '  bool is_invader(', '  int find_dream_door(')
source += section(lookup, '  bool is_forcibly_helpless(', '  bool is_pinned(')
source += section(fight, '  CHAR_DATA *find_abductee(', '  _DOFUN(do_suicide)')
source += 'void npc_ko_branch(CHAR_DATA *ch, CHAR_DATA *victim) {\n'
attack = section(fight, '  void npc_combat_attack(', '  CHAR_DATA *get_npc_follow(')
source += section(attack, '    if ((forest_monster(ch) || is_invader(ch)) && !IS_NPC(victim)',
                  '    combat_damage(victim, ch, dam, discipline_table[point].vnum);')
source += '  ++damage_fallthrough;\n}\n'
source += 'void mobile_lifetime_tick(CHAR_DATA *ch) {\n'
source += section(update, '    if (ch->ttl > 0 && ch->ttl < 25',
                  '    if (ch->wounds >= 4)')
source += r'''
  ++survived_update;
}

int main() {
  CHAR_DATA mob = {}, victim = {}, other = {};
  PC_DATA pc = {}, other_pc = {};
  MOB_INDEX_DATA index = {};
  AREA_DATA area = {};
  ROOM_INDEX_DATA room = {}, nearby = {};
  DESCRIPTOR_DATA desc = {}, other_desc = {};
  LAIR_TYPE lair = {};
  auto reset = [&]() {
    unregister_live_character(&mob);
    descriptor_list.clear(); LairVect.clear();
    mob = {}; victim = {}; other = {}; pc = {}; other_pc = {};
    index = {}; area = {}; room = {}; nearby = {}; desc = {}; other_desc = {}; lair = {};
    public_location = property_room = battle = guest = gm = false;
    room_combat = true; mist = 3;
    extracted = damage_fallthrough = survived_update = 0;
    area.vnum = INNER_NORTH_FOREST;
    room.area = &area; room.sector_type = SECT_FOREST; room.vnum = 1234;
    nearby = room; nearby.vnum = 1235; nearby.x = 5;
    index.vnum = 20;
    mob.pIndexData = &index; mob.in_room = &room; mob.name = "monster";
    SET_FLAG(mob.act, ACT_IS_NPC);
    mob.ttl = 15; mob.attacking = 1;
    register_live_character(&mob); set_combat_state(&mob, TRUE);
    victim.pcdata = &pc; victim.in_room = &room; victim.played = 50 * 3600;
    pc.monster_beaten = 1; pc.title = "";
    other.pcdata = &other_pc; other.in_room = &nearby; other.played = 50 * 3600;
    other_pc.monster_beaten = 1; other_pc.title = "";
    desc.character = &victim; desc.connected = CON_PLAYING;
    other_desc.character = &other; other_desc.connected = CON_PLAYING;
    descriptor_list.push_back(&desc);
  };
  auto assert_retired = [&]() {
    assert(pc.sleeping == 240 && damage_fallthrough == 0);
    assert(mob.ttl == 0 && mob.attacking == 0 && !in_fight(&mob));
    unsigned long long cursor = 0;
    assert(next_combat_character(&cursor) == nullptr);
    // KO callers may still hold the mob: extraction waits for mobile_update.
    assert(extracted == 0 && mob.in_room == &room);
    mobile_lifetime_tick(&mob);
    assert(extracted == 1 && mob.in_room == nullptr && survived_update == 0);
  };
  auto assert_preserved = [&]() {
    assert(mob.ttl == 15 && mob.attacking == 1 && in_fight(&mob));
    assert(extracted == 0);
    unsigned long long cursor = 0;
    assert(next_combat_character(&cursor) == &mob);
  };

  // Newbie protection ends at fifty played hours; even 49h59m must retire.
  for (int played : {0, 49 * 3600 + 59 * 60, 50 * 3600 - 1}) {
    reset(); victim.played = played;
    npc_ko_branch(&mob, &victim);
    assert_retired();
  }
  for (int played : {50 * 3600, 100 * 3600}) {
    reset(); victim.played = played;
    assert(find_abductee(&mob, true) == nullptr); // Not helpless before KO.
    npc_ko_branch(&mob, &victim);
    assert(pc.sleeping == 240 && damage_fallthrough == 0);
    assert_preserved();
    assert(find_abductee(&mob, true) == &victim);
    assert(find_abductee(&mob) == nullptr); // Normal abduction still waits for combat.
    room_combat = false;
    assert(find_abductee(&mob) == &victim);
  }

  // Every existing abduction exclusion still retires a roaming forest monster.
  for (int reason = 0; reason < 9; ++reason) {
    reset();
    if (reason == 0) public_location = true;
    if (reason == 1) mist = 2;
    if (reason == 2) property_room = true;
    if (reason == 3) room.sector_type = SECT_STREET;
    if (reason == 4) pc.monster_beaten = 0;
    if (reason == 5) gm = true;
    if (reason == 6) {
      SET_FLAG(victim.act, PLR_BOUND);
      lair.valid = true; lair.room = room.vnum; lair.mob = 99;
      LairVect.push_back(&lair);
    }
    if (reason == 7) desc.connected = -1;
    if (reason == 8) { victim.in_room = &nearby; nearby.x = 6; }
    npc_ko_branch(&mob, &victim);
    assert_retired();
  }

  // A monster guarding its lair stays, including when the victim is a newbie.
  reset(); victim.played = 0;
  lair.valid = true; lair.room = room.vnum; lair.mob = index.vnum;
  LairVect.push_back(&lair);
  assert(in_lair(&mob));
  npc_ko_branch(&mob, &victim);
  assert(pc.sleeping == 240); assert_preserved();

  // Invaders keep their existing KO and abduction behavior.
  reset(); index.vnum = 151; victim.played = 0;
  npc_ko_branch(&mob, &victim);
  assert(pc.sleeping == 240); assert_preserved();
  victim.played = 50 * 3600; room_combat = false;
  assert(find_abductee(&mob) == &victim);
  victim.wounds = 3;
  assert(find_abductee(&mob) == nullptr);

  // Another eligible captive within range preserves the pending abduction.
  reset(); victim.played = 0; other_pc.sleeping = 240;
  descriptor_list.push_back(&other_desc);
  npc_ko_branch(&mob, &victim);
  assert(pc.sleeping == 240); assert_preserved();
  assert(find_abductee(&mob, true) == &other);
  room_combat = false;
  assert(find_abductee(&mob) == &other);

  // Eligibility probes never change shroud; actual selection still synchronizes it.
  for (bool prey_shrouded : {false, true}) {
    reset(); pc.sleeping = 240;
    if (prey_shrouded) SET_FLAG(victim.act, PLR_SHROUD);
    else SET_FLAG(mob.act, PLR_SHROUD);
    assert(find_abductee(&mob, true) == &victim);
    assert(bool(IS_FLAG(mob.act, PLR_SHROUD)) == !prey_shrouded);
    assert(find_abductee(&mob) == nullptr);
    assert(bool(IS_FLAG(mob.act, PLR_SHROUD)) == !prey_shrouded);
    room_combat = false;
    assert(find_abductee(&mob) == &victim);
    assert(bool(IS_FLAG(mob.act, PLR_SHROUD)) == prey_shrouded);
  }

  // The KO branch still excludes live defenses, battlegrounds, guests and NPCs.
  for (int reason = 0; reason < 5; ++reason) {
    reset(); victim.played = 0;
    if (reason == 0) victim.hit = 1;
    if (reason == 1) battle = true;
    if (reason == 2) guest = true;
    if (reason == 3) SET_FLAG(victim.act, ACT_IS_NPC);
    if (reason == 4) index.vnum = 100;
    npc_ko_branch(&mob, &victim);
    assert(pc.sleeping == 0 && damage_fallthrough == 1);
    assert_preserved();
  }
  unregister_live_character(&mob);
  descriptor_list.clear(); LairVect.clear();
  puts("PASS: forest KO retirement, deferred extraction, newbie boundary, pending abductions, lair/invader exclusions and shroud behavior.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-forest-monster-ko-') as tmp:
    path = Path(tmp)
    test_source = path / 'test.cc'
    binary = path / 'test'
    command = ['g++', '-std=gnu++17', '-Wno-write-strings', '-Wno-deprecated',
               '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-no-pie',
               '-I', str(ROOT / 'src'), str(test_source), '-o', str(binary)]
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
               UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    test_source.write_text(source)
    subprocess.run(command, check=True)
    subprocess.run([str(binary)], env=env, check=True, timeout=30)
    if '--check-regression' in sys.argv:
        # Prove the protected-player assertion catches the original KO behavior.
        retirement = section(source,
                             '      if (forest_monster(ch) && !in_lair(ch)',
                             '      return;\n    }')
        test_source.write_text(source.replace(retirement, '', 1))
        subprocess.run(command, check=True)
        regression = subprocess.run([str(binary)], env=env, capture_output=True,
                                    text=True, timeout=30)
        assert regression.returncode != 0, 'Original KO behavior unexpectedly passed'
        assert 'mob.ttl == 0' in regression.stderr, regression.stderr
        print('PASS: restoring the original KO branch fails the retirement assertion.')
