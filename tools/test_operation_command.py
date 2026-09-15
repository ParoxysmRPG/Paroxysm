#!/usr/bin/env python3
"""Exercise the production operation command with isolated engine stubs in WSL/Linux.

ASan/UBSan check selection and troop accounting without loading game data.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
clans = (ROOT / 'src/clans.c').read_text()
start = clans.index('  // Command numbers must use the same live, visible operations')
command = clans[start:clans.index('  void battle_message(', start)]
start = clans.index('  bool join_to_operation(')
join = clans[start:clans.index('  void battle_faction(', start)]

source = r'''
#include "merc.h"
#include "game_time.h"
#include <cassert>
#include <climits>
#include <cstdarg>
#include <cstdlib>
#include <cstring>
using std::vector;
vector<OPERATION_TYPE *> OpVect;
bool isactiveoperation = false;
OPERATION_TYPE *activeoperation = nullptr;
OPERATION_TYPE *shown = nullptr, *won = nullptr, *launched = nullptr;
FACTION_TYPE host = {}, guest = {}, hidden = {};
CHAR_DATA actor = {};
PC_DATA pc = {};
ROOM_INDEX_DATA room = {};
std::string output;
vector<char *> allocations;
bool trusted = true;
int charges = 0, lookup_calls = 0, actor_trust = 1;
time_t current_time = 1789488000;
char *str_dup(const char *s) { char *p = strdup(s ? s : ""); allocations.push_back(p); return p; }
void free_string(char *) {} // Release the arena after all scenarios.
bool str_cmp(const char *a, const char *b) { return strcasecmp(a ? a : "", b ? b : "") != 0; }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void printf_to_char(CHAR_DATA *, const char *fmt, ...) {
  char buf[MSL]; va_list args; va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args); va_end(args); output += buf;
}
char *one_argument_nouncap(char *input, char *word) {
  while (*input == ' ') ++input;
  while (*input && *input != ' ') *word++ = *input++;
  *word = '\0'; while (*input == ' ') ++input; return input;
}
FACTION_TYPE *clan_lookup(int vnum) {
  ++lookup_calls;
  for (auto *f : {&host, &guest, &hidden}) if (vnum && f->vnum == vnum) return f;
  return nullptr;
}
LOCATION_TYPE *territory_by_number(int) { return nullptr; }
bool same_alliance(FACTION_TYPE *a, FACTION_TYPE *b) {
  return a && b && a->alliance == b->alliance;
}
bool has_trust(CHAR_DATA *, int, int faction) { return faction != 0 && trusted; }
int get_trust(CHAR_DATA *) { return actor_trust; }
bool is_gm(CHAR_DATA *) { return false; }
bool battleground(ROOM_INDEX_DATA *) { return false; }
bool higher_power(CHAR_DATA *) { return false; }
bool cardinal(CHAR_DATA *) { return false; }
bool generic_faction_vnum(int) { return false; }
bool power_operation_goal(int goal) { return goal == GOAL_ATTACK_POWER || goal == GOAL_WORSHIP; }
bool targeted_operation_power(CHAR_DATA *, OPERATION_TYPE *) { return false; }
char *operation_location(OPERATION_TYPE *op) { return op->description; }
void show_operation_to_char(CHAR_DATA *, OPERATION_TYPE *op) { shown = op; }
void launch_operation(OPERATION_TYPE *op) { launched = op; }
void win_operation(int, OPERATION_TYPE *op) { won = op; op->hour = 0; }
bool can_afford_faction_spending(const FACTION_TYPE *, int, int) { return true; }
void use_resources(int, int, CHAR_DATA *, char *) { ++charges; }
int border_count(FACTION_TYPE *) { return 0; }
bool join_to_operation(int, OPERATION_TYPE *);
'''
source += clans[clans.index('  int operation_order('):clans.index('  void load_operations()')] + join + command
source += r'''
void run(const char *input) {
  char buf[MSL]; strcpy(buf, input); output.clear(); do_operation(&actor, buf);
}
OPERATION_TYPE operation(const char *name) {
  OPERATION_TYPE op = {};
  op.valid = true; op.hour = 12; op.day = 2; op.territoryvnum = 1;
  op.faction = host.vnum; op.max_pcs = 5;
  op.author = actor.name; op.description = str_dup(name); return op;
}
int main() {
  host.vnum = 10; guest.vnum = 20; hidden.vnum = 30;
  host.alliance = 1; guest.alliance = 2; hidden.alliance = 3;
  host.name = (char *)"Host"; guest.name = (char *)"Guest";
  hidden.name = (char *)"Hidden";
  actor.name = (char *)"Player"; actor.pcdata = &pc;
  actor.faction = guest.vnum; actor.in_room = &room;
  auto retired = operation("Retired"), private_op = operation("Private");
  auto invalid = operation("Invalid"), orphan = operation("Orphan");
  auto nowhere = operation("Nowhere"), first = operation("First"), second = operation("Second");
  retired.hour = 0; private_op.competition = COMPETE_CLOSED; private_op.faction = hidden.vnum;
  invalid.valid = false; orphan.faction = 999; nowhere.territoryvnum = 0;
  OpVect = {nullptr, &retired, &private_op, &invalid, &orphan, &nowhere, &first, &second};
  run("list");
  assert(output.find("[01] Host's operation in First") != std::string::npos);
  assert(output.find("[02] Host's operation in Second") != std::string::npos);
  assert(output.find("[03]") == std::string::npos);
  assert(nowhere.hour == 12); // Listing must not cancel or alter saved operations.
  run("info 1"); assert(shown == &first);
  run("info 2"); assert(shown == &second);
  actor.factiontwo = hidden.vnum;
  run("info 1"); assert(shown == &private_op);
  actor.factiontwo = 0;
  run("bribe 2"); assert(won == &second && charges == 1 && first.hour == 12);
  run("bribe 1"); assert(won == &first && charges == 2);
  puts("PASS: list, info and bribe share numbering across inactive, hidden, missing and null records.");

  first = operation("First"); private_op.hour = 13;
  run("timeshift 1 1");
  assert(first.hour == 12 && first.timeshifted == 0);
  assert(output.find("already an operation") != std::string::npos);
  private_op.hour = 14; invalid.hour = 13;
  run("timeshift 1 1"); assert(first.hour == 13 && first.timeshifted == 1);
  puts("PASS: timeshifts ignore retired/null records and still reserve departures of hidden operations.");

  first = operation("First"); OpVect = {&first};
  first.enrolled[0] = guest.vnum; first.home_soldiers = 10; first.soldiers[0] = 2;
  guest.manpower = 100;
  run("withdraw 1 8");
  assert(first.soldiers[0] == 0 && guest.manpower == 102 && first.home_soldiers == 10);
  run("withdraw 1 8"); assert(first.soldiers[0] == 0 && guest.manpower == 102);
  first.home_soldiers = 1; first.soldiers[0] = 8; guest.manpower = 100;
  run("withdraw 1 3"); assert(first.soldiers[0] == 5 && guest.manpower == 103);
  run("withdraw 1"); assert(first.soldiers[0] == 0 && guest.manpower == 108);
  first.soldiers[0] = 5; guest.manpower = 100;
  run("withdraw 1 -1"); assert(first.soldiers[0] == 0 && guest.manpower == 105);
  actor.faction = host.vnum; host.manpower = 100; first.home_soldiers = 4;
  run("withdraw 1 2"); assert(first.home_soldiers == 2 && host.manpower == 102);
  run("withdraw 1 20"); assert(first.home_soldiers == 0 && host.manpower == 104);
  puts("PASS: withdrawals conserve troops for host and enrolled factions, including oversized and default amounts.");

  actor.faction = guest.vnum;
  first = operation("First"); guest.manpower = 100;
  trusted = false; run("reinforce 1 3");
  assert(first.enrolled[0] == 0 && guest.manpower == 100);
  trusted = true;
  for (const char *input : {"reinforce 1", "reinforce 1 -1", "reinforce 1 101", "reinforce 1 11"}) {
    run(input); assert(first.enrolled[0] == 0 && guest.manpower == 100);
  }
  actor.faction = 999; run("reinforce 1 3"); assert(first.enrolled[0] == 0);
  actor.faction = guest.vnum;
  run("reinforce 1 3");
  assert(first.enrolled[0] == guest.vnum && first.soldiers[0] == 3 && guest.manpower == 97);
  run("reinforce 1 8"); assert(first.soldiers[0] == 3 && guest.manpower == 97);
  run("reinforce 1 7"); assert(first.soldiers[0] == 10 && guest.manpower == 90);
  guest.manpower = INT_MAX; run("reinforce 1 2147483647");
  assert(first.soldiers[0] == 10 && guest.manpower == INT_MAX);
  actor.faction = host.vnum; host.manpower = 100;
  run("reinforce 1 4"); assert(first.home_soldiers == 4 && host.manpower == 96);
  run("reinforce 1 7"); assert(first.home_soldiers == 4 && host.manpower == 96);
  puts("PASS: rejected reinforcement requests cannot reserve faction slots; valid transfers respect capacity and authority.");

  // A newly appended operation can depart sooner, including across midnight.
  auto morning = operation("Morning"), tonight = operation("Tonight");
  morning.hour = 8; morning.day = 0;
  tonight.hour = 22; tonight.day = 0;
  current_time = 1789488000; // 2026-09-15 16:00 UTC, game hour 11.
  OpVect = {&morning, &tonight};
  run("list");
  assert(output.find("Tonight") < output.find("Morning"));
  run("info 1"); assert(shown == &tonight);
  auto sooner = operation("Sooner"); sooner.hour = 12; sooner.day = 0;
  OpVect.push_back(&sooner);
  run("info 1"); assert(shown == &sooner);
  run("signup 1"); assert(!str_cmp(sooner.sign_up[0], actor.name));
  assert(morning.sign_up[0] == nullptr && tonight.sign_up[0] == nullptr);
  puts("PASS: appended operations sort by actual departure; info/signup share list numbering across midnight.");
  OpVect = {&first};

  // Launched troops already exist on the battlefield. Refunding, replacing or
  // adding their accounting entries must not be possible through planning commands.
  activeoperation = &first; isactiveoperation = true; actor_trust = MAX_LEVEL;
  for (int faction : {host.vnum, guest.vnum}) {
    actor.faction = faction;
    for (const char *input : {"cancel 1", "withdraw 1 3", "reinforce 1 1",
                              "timeshift 1 1", "launch 1", "launchfast 1"}) {
      run(input);
      assert(output.find("already launched") != std::string::npos);
      assert(first.hour == 12 && first.home_soldiers == 4 && first.soldiers[0] == 10);
      assert(first.timeshifted == 0 && first.speed == 0 && launched == nullptr);
      assert(host.manpower == 96 && guest.manpower == INT_MAX);
    }
  }
  run("info 1"); assert(shown == &first);
  actor_trust = 1; actor.faction = host.vnum;
  auto upcoming = operation("Upcoming"); OpVect = {&first, &upcoming};
  run("reinforce 2 1");
  assert(upcoming.home_soldiers == 1 && first.home_soldiers == 4 && host.manpower == 95);
  OpVect = {&first};
  isactiveoperation = false; actor.faction = host.vnum;
  run("withdraw 1 1"); assert(first.home_soldiers == 3 && host.manpower == 96);
  puts("PASS: active operations remain inspectable but cannot be refunded, rescheduled, reinforced or relaunched.");
  for (auto *p : allocations) free(p);
}
'''

with tempfile.TemporaryDirectory(prefix='operation-command-') as tmp:
    cpp, binary = Path(tmp) / 'test.cpp', Path(tmp) / 'test'
    cpp.write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-Wall', '-Wextra', '-Wno-write-strings',
                    '-Wno-unused-parameter', '-Wno-deprecated', '-g',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-no-pie',
                    '-I', str(ROOT / 'src'), str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
