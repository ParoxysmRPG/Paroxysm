#!/usr/bin/env python3
"""Exercise production pedestrian command branches with null PC data (WSL/Linux)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def section(file, start, end):
    text = (ROOT / 'src' / file).read_text()
    offset = text.index(start)
    return text[offset:text.index(end, offset)]


source = r'''
#include "merc.h"
#include <cassert>
#include <cstring>
#include <cstdarg>

time_t current_time = 1000000;
int event_cleanse = 0;
CHAR_DATA actor = {}, walker = {}, shopkeeper = {}, player = {};
PC_DATA actor_pc = {}, player_pc = {};
ACCOUNT_TYPE account = {};
AREA_DATA area = {};
ROOM_INDEX_DATA room = {};
CHAR_DATA *target = &walker;
bool vampire = true, pinned = false, ghost = false, dreaming = false;
bool safe = false, hostile = false, public_area = false, institute = false;
bool knocked_out = false, drained = false;
int drains = 0, binds = 0, knockouts = 0, cortex = 0, hypnos = 0, player_path = 0;
int hostile_starts = 0;
std::string output, hypno_argument;

bool pedestrian(CHAR_DATA *ch) { return ch == &walker && IS_NPC(ch); }
bool pedestrian_helpless(CHAR_DATA *ch) {
  return pedestrian(ch) && (knocked_out || IS_FLAG(ch->act, PLR_BOUND)
      || IS_FLAG(ch->act, PLR_BOUNDFEET));
}
void pedestrian_bound(CHAR_DATA *ch) { if (pedestrian(ch)) ++binds; }
void pedestrian_knockout(CHAR_DATA *ch) { assert(pedestrian(ch)); ++knockouts; knocked_out = true; }
bool pedestrian_drain(CHAR_DATA *ch, CHAR_DATA *victim) {
  assert(ch == &actor && pedestrian(victim) && victim->pcdata == nullptr);
  if (drained) { output += "They're drained dry."; return false; }
  drained = true; ++drains; return true;
}
bool pedestrian_hypnotise(CHAR_DATA *ch, CHAR_DATA *victim, const char *arg) {
  assert(ch == &actor && pedestrian(victim) && victim->pcdata == nullptr);
  ++hypnos; hypno_argument = arg; return true;
}
void cortex_public_response(CHAR_DATA *, CHAR_DATA *) { ++cortex; }
bool is_vampire(CHAR_DATA *) { return vampire; }
bool is_dreaming(CHAR_DATA *ch) { return ch == &actor && dreaming; }
bool is_ghost(CHAR_DATA *ch) { return ch == &actor && ghost; }
bool is_pinned(CHAR_DATA *ch) { return ch == &actor && pinned; }
bool is_helpless(CHAR_DATA *ch) {
  return pedestrian(ch) ? pedestrian_helpless(ch) : IS_FLAG(ch->act, PLR_BOUND);
}
bool in_fight(CHAR_DATA *ch) { return ch->in_fight; }
bool is_safe(CHAR_DATA *, CHAR_DATA *) { return safe; }
bool in_public(CHAR_DATA *, CHAR_DATA *) { return public_area; }
bool room_hostile(ROOM_INDEX_DATA *) { return hostile; }
void start_hostilefight(CHAR_DATA *) { ++hostile_starts; }
bool room_ambush(ROOM_INDEX_DATA *) { return false; }
bool institute_room(ROOM_INDEX_DATA *) { return institute; }
bool clinic_patient(CHAR_DATA *) { return false; }
bool college_student(CHAR_DATA *, bool) { return false; }
bool is_prisoner(CHAR_DATA *) { return false; }
bool in_fistfight(CHAR_DATA *) { return false; }
bool is_manifesting(CHAR_DATA *) { return false; }
bool deplete_ghostpool(CHAR_DATA *, int) { return false; }
bool higher_power(CHAR_DATA *) { return false; }
bool power_bound(CHAR_DATA *) { return false; }
bool is_gm(CHAR_DATA *) { return false; }
bool lair_room(ROOM_INDEX_DATA *) { return false; }
bool is_animal(CHAR_DATA *) { return false; }
int get_animal_genus(CHAR_DATA *, int) { return GENUS_HYBRID; }
int get_trust(CHAR_DATA *) { return 0; }
int get_skill(CHAR_DATA *ch, int skill) { return ch->skills[skill]; }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
void message_to_char(char *, char *) {}
void breakcontrol(char *, int) {}
void free_string(char *) {}
char *str_dup(const char *s) { return const_cast<char *>(s); }
void printf_to_char(CHAR_DATA *, char *format, ...) {
  char buf[MSL]; va_list args; va_start(args, format);
  vsnprintf(buf, sizeof(buf), format, args); va_end(args); output += buf;
}
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
char *one_argument_nouncap(char *input, char *arg) {
  while (*input == ' ') ++input;
  while (*input && *input != ' ') *arg++ = *input++;
  *arg = '\0'; while (*input == ' ') ++input; return input;
}
CHAR_DATA *get_char_room(CHAR_DATA *, ROOM_INDEX_DATA *, char *) { return target; }
CHAR_DATA *get_char_dream(CHAR_DATA *, char *) { return nullptr; }
CHAR_DATA *get_char_world_pc(char *) { return nullptr; }
void do_wake(CHAR_DATA *, char *) {}
void do_function(CHAR_DATA *ch, DO_FUN *fn, char *arg) { fn(ch, arg); }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void act_new(const char *s, CHAR_DATA *, const void *, const void *, int, int) { output += s; }
'''

# Full binding commands cover every hands/feet/both mutation and forest branch.
source += section('skills.c', '  _DOFUN(do_bind)', '  _DOFUN(do_execute)')
# Only truncate after the early pedestrian return, before unrelated PC machinery.
# The sentinel detects an accidental fallthrough instead of hiding it.
source += section('skills.c', '  bool biteable(', '    if (ch->race == RACE_WIGHT) {')
source += '++player_path; return false; }\n'
source += section('skills.c', '  _DOFUN(do_bite)', '    if (ch->race == RACE_WIGHT) {')
source += '++player_path; }\n'
source += section('skills.c', '  _DOFUN(do_knockoutpunch)',
                  '    if (!guestmonster(ch) && !guestmonster(victim)) {')
source += '++player_path; }\n'
source += section('skills.c', '  _DOFUN(do_hypnotise)',
                  '    if (get_skill(ch, SKILL_HYPNOTISM) <= 0 && !mindbroken(victim)) {')
source += '++player_path; }\n'
source += section('institute.c', '  char *const victimize_actions[] = {',
                  '  char *const victimize_responses')
source += section('institute.c', '  _DOFUN(do_victimize)',
                  '    if (!victimize_together(ch, victim) ||')
source += '++player_path; }\n'
# Player-only workflows must not queue a walker for later PC-data processing.
source += section('skills.c', '  _DOFUN(do_harvest)', '    if (!harvesting_room(ch->in_room)) {')
source += '++player_path; }\n'
source += section('skills.c', '  _DOFUN(do_exorcise)', '  _DOFUN(do_carefor)')
source += section('skills.c', '  _DOFUN(do_carefor)', '    if (get_skill(ch, SKILL_MEDICINE) < 2) {')
source += '++player_path; }\n'
source += section('skills.c', '  _DOFUN(do_turn)',
                  '    if (!is_helpless(victim) && victim->pcdata->destiny_feature != DEST_FEAT_TURN) {')
source += '++player_path; }\n'
source += section('abominations.c', '  _DOFUN(do_enthrall)', '    if (!is_helpless(victim)) {')
source += '++player_path; }\n'
source += section('abominations.c', '  _DOFUN(do_enrapture)',
                  '    if (!IS_NPC(victim) && victim->pcdata->trance > 0)')
source += '++player_path; }\n'
source += section('abominations.c', '  _DOFUN(do_fleshform)', '    if (!str_cmp(arg1, "self")) {')
source += '++player_path; }\n'
source += section('abominations.c', '  _DOFUN(do_murder)', '    if (is_ghost(ch)) {')
source += '++player_path; }\n'
source += section('act_obj.c', '  void stake(', '    if (ch->pcdata->bloodaura > 0) {')
source += '++player_path; }\n'
source += 'void try_stake(CHAR_DATA *ch, char *argument) { stake(ch, argument, nullptr); }\n'
source += r'''

void command(DO_FUN *fn, const char *arg) {
  char input[MSL]; strcpy(input, arg); fn(&actor, input);
}
void reset() {
  actor = {}; walker = {}; shopkeeper = {}; player = {};
  actor_pc = {}; player_pc = {}; account = {}; room = {}; area = {};
  actor.pcdata = &actor_pc; actor_pc.account = &account;
  player.pcdata = &player_pc; player_pc.account = &account;
  actor.played = 100 * 3600; account.maxhours = 100;
  SET_FLAG(walker.act, ACT_IS_NPC); SET_FLAG(shopkeeper.act, ACT_IS_NPC);
  area.vnum = OUTER_NORTH_FOREST; room.area = &area; room.vnum = 123;
  actor.in_room = walker.in_room = shopkeeper.in_room = player.in_room = &room;
  walker.hit = 100; player.hit = 100;
  vampire = true;
  pinned = ghost = dreaming = safe = hostile = public_area = institute = false;
  knocked_out = drained = false;
  drains = binds = knockouts = cortex = hypnos = player_path = hostile_starts = 0;
  output.clear(); hypno_argument.clear(); target = &walker; event_cleanse = 0;
}

int main() {
  // An awake stranger refuses binding and feeding; a KO walker accepts both.
  reset(); command(do_bind, "walker"); assert(binds == 0);
  command(do_bite, "walker mild"); command(do_victimize, "walker mild pain");
  assert(drains == 0 && player_path == 0);
  for (const char *part : {"", "hands", "feet"}) {
    reset(); knocked_out = true;
    std::string arg = std::string("walker ") + part;
    command(do_bind, arg.c_str());
    assert(binds == 1 && pedestrian_helpless(&walker));
    assert(bool(IS_FLAG(walker.act, PLR_BOUND)) == (strcmp(part, "feet") != 0));
    assert(bool(IS_FLAG(walker.act, PLR_BOUNDFEET)) == (strcmp(part, "hands") != 0));
    command(do_untie, arg.c_str());
    assert(binds == 2 && !IS_FLAG(walker.act, PLR_BOUND) && !IS_FLAG(walker.act, PLR_BOUNDFEET));
    assert(walker.hit == 100 && walker.pcdata == nullptr);
  }
  reset(); knocked_out = true; command(do_bind, "walker hands");
  command(do_bind, "walker feet"); assert(binds == 2);
  command(do_untie, "walker hands");
  assert(binds == 3 && IS_FLAG(walker.act, PLR_BOUNDFEET));
  command(do_untie, "walker feet"); assert(binds == 4 && walker.hit == 100);
  // Preserve player untie behavior, including the forest recovery field.
  reset(); target = &player; SET_FLAG(player.act, PLR_BOUND);
  command(do_untie, "player");
  assert(player.hit == 0 && player_pc.spawned_monsters == 400 && binds == 0);

  for (const char *severity : {"", "mild", "severe", "critical", "fatal"}) {
    reset(); knocked_out = true;
    std::string arg = std::string("walker ") + severity;
    command(do_bite, arg.c_str()); assert(drains == 1 && player_path == 0);
    command(do_victimize, "walker mild pain");
    assert(drains == 1 && output.find("drained dry") != std::string::npos);
  }
  reset(); knocked_out = true; command(do_victimize, "walker");
  assert(drains == 1 && actor_pc.victimize_char_point == nullptr);
  command(do_bite, "walker mild"); assert(drains == 1 && player_path == 0);
  reset(); knocked_out = true;
  command(do_bite, "walker invalid"); command(do_victimize, "walker invalid");
  assert(drains == 0);
  for (int guard = 0; guard < 8; ++guard) {
    reset(); knocked_out = true;
    if (guard == 0) pinned = true;
    if (guard == 1) ghost = true;
    if (guard == 2) dreaming = true;
    if (guard == 3) safe = true;
    if (guard == 4) hostile = true;
    if (guard == 5) actor.in_fight = true;
    if (guard == 6) SET_FLAG(actor.act, PLR_BOUND);
    if (guard == 7) target = &shopkeeper;
    command(do_bite, "walker mild"); command(do_victimize, "walker mild pain");
    assert(drains == 0);
  }
  reset(); knocked_out = true; vampire = false;
  command(do_bite, "walker mild"); assert(drains == 0);
  actor.race = RACE_WIGHT; command(do_bite, "walker mild"); assert(drains == 1);

  reset(); public_area = true; command(do_knockoutpunch, "walker");
  assert(knockouts == 1 && cortex == 1 && player_path == 0 && actor.wait > 0);
  reset(); command(do_knockoutpunch, "walker"); assert(knockouts == 1 && cortex == 0);
  for (int guard = 0; guard < 8; ++guard) {
    reset();
    if (guard == 0) target = &shopkeeper;
    if (guard == 1) pinned = true;
    if (guard == 2) actor.in_fight = true;
    if (guard == 3) safe = true;
    if (guard == 4) institute = true;
    if (guard == 5) { actor.played = 0; account.maxhours = 0; }
    if (guard == 6) SET_FLAG(actor.act, PLR_BOUND);
    if (guard == 7) SET_FLAG(actor.act, PLR_SHROUD);
    command(do_knockoutpunch, "walker"); assert(knockouts == 0 && cortex == 0);
  }
  for (const char *option : {"follow", "release", "invalid"}) {
    reset(); std::string arg = std::string("walker ") + option;
    command(do_hypnotise, arg.c_str());
    assert(hypnos == 1 && hypno_argument == option && player_path == 0);
  }
  reset(); target = &shopkeeper; command(do_hypnotise, "shopkeeper follow");
  assert(hypnos == 0 && player_path == 0);
  reset(); target = &player; command(do_hypnotise, "player instruction");
  assert(hypnos == 0 && player_path == 1);
  for (DO_FUN *fn : {do_harvest, do_exorcise, do_carefor, do_turn}) {
    for (CHAR_DATA *npc : {&walker, &shopkeeper}) {
      reset(); target = npc; knocked_out = true; SET_FLAG(npc->act, PLR_BOUND);
      command(fn, "target");
      assert(player_path == 0 && actor_pc.process_target == nullptr);
      assert(output.find("NPC") != std::string::npos || output.find("players") != std::string::npos);
    }
    reset(); target = &player; SET_FLAG(player.act, PLR_BOUND);
    command(fn, "player");
    assert(player_path == 1 || actor_pc.process_target == &player);
  }
  for (DO_FUN *fn : {do_enthrall, do_enrapture, do_fleshform, do_murder, try_stake}) {
    for (CHAR_DATA *victim : {&walker, &shopkeeper, &player}) {
      reset(); target = victim; knocked_out = true;
      actor.skills[SKILL_FLESHFORMING] = 1;
      SET_FLAG(actor.act, PLR_GUEST); actor_pc.guest_type = GUEST_NIGHTMARE;
      command(fn, "target");
      assert(player_path == (victim == &player ? 1 : 0));
      if (IS_NPC(victim)) assert(output.find("players") != std::string::npos);
    }
  }
  puts("PASS: null-PC binding, partial untie/HP, bite/victimize dispatch and guards, public knockout and hypnosis routing.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-pedestrian-commands-') as tmp:
    path = Path(tmp)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-fsanitize=address,undefined',
                    '-fno-sanitize-recover=all', '-no-pie',
                    '-I', str(ROOT / 'src'), str(path / 'test.cc'),
                    '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
