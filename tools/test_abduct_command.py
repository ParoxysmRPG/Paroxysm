#!/usr/bin/env python3
"""Run offline abduction, lookup and escape lifecycle regressions under ASan/UBSan."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
houses = (ROOT / 'src/houses.c').read_text()


def section(start, end):
    offset = houses.index(start)
    return houses[offset:houses.index(end, offset)]


source = r'''
#include "merc.h"
#include "recycle.h"
#include <algorithm>
#include <cassert>
#include <cstring>
#include <cstdlib>

CHAR_DATA actor = {}, saved = {};
PC_DATA actor_pc = {}, saved_pc = {};
ROOM_INDEX_DATA room = {}, elsewhere = {};
AREA_DATA area = {};
PROP_TYPE property = {};
ACCOUNT_TYPE shared_account = {};
CharList char_list, people, other_people;
time_t current_time = 2000000;
int crisis_prologue = 0;
int loads = 0, frees = 0, saves = 0, registrations = 0, guards = 0, effects = 0;
bool found = true, online = false, gm = false, institute = false;
bool clinic_power = false, activate_guard = false, no_destination = false;
bool attach_account = false, borrow_account = false;
int account_frees = 0;
std::string output, saved_messages;

bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
char *str_dup(const char *s) { return strdup(s); }
void free_string(char *s) { free(s); }
bool is_name(char *a, char *b) { return !str_cmp(a, b); }
char *one_argument(char *input, char *word) {
  while (*input == ' ') ++input;
  while (*input && *input != ' ') *word++ = *input++;
  *word = '\0'; while (*input == ' ') ++input; return input;
}
void send_to_char(const char *text, CHAR_DATA *) { output += text; }
void act_new(const char *text, CHAR_DATA *, const void *, const void *, int, int) { output += text; }
void log_string(const char *) {}
int get_trust(CHAR_DATA *ch) { return ch->trust; }
bool is_griefer(CHAR_DATA *) { return false; }
bool is_helpless(CHAR_DATA *) { return false; }
bool in_fight(CHAR_DATA *) { return false; }
bool is_animal(CHAR_DATA *) { return false; }
bool is_ghost(CHAR_DATA *) { return false; }
bool guestmonster(CHAR_DATA *) { return false; }
bool higher_power(CHAR_DATA *) { return false; }
bool is_gm(CHAR_DATA *ch) { return ch != &actor && gm; }
bool is_vampire(CHAR_DATA *) { return false; }
bool institute_room(ROOM_INDEX_DATA *) { return institute; }
bool room_in_school(int) { return institute; }
bool college_student(CHAR_DATA *, bool) { return false; }
bool college_staff(CHAR_DATA *, bool) { return false; }
bool clinic_staff(CHAR_DATA *, bool) { return false; }
bool clinic_patient(CHAR_DATA *) { return false; }
bool has_clinic_power_chars(CHAR_DATA *, CHAR_DATA *) { return clinic_power; }
bool has_access(CHAR_DATA *, ROOM_INDEX_DATA *) { return false; }
bool is_weakness(CHAR_DATA *, CHAR_DATA *) { return false; }
bool has_weakness(CHAR_DATA *, CHAR_DATA *) { return false; }
int get_security(ROOM_INDEX_DATA *) { return 0; }
int get_lifeforce(CHAR_DATA *, bool, CHAR_DATA *) { return 100; }
int get_skill(CHAR_DATA *, int) { return 0; }
int number_range(int, int) { return 0; }
int number_percent() { return 1; }
int newbie_level(CHAR_DATA *) { return 10; }
int sunphase(ROOM_INDEX_DATA *) { return 4; }
PROP_TYPE *room_prop(ROOM_INDEX_DATA *) { return &property; }
PROP_TYPE *in_prop(CHAR_DATA *) { return &property; }
void from_sleepers(CHAR_DATA *, PROP_TYPE *) {}
bool bodyguard_abduct(CHAR_DATA *, CHAR_DATA *victim) {
  ++guards;
  if (!activate_guard || victim->pcdata->guard_number < 1) return false;
  victim->pcdata->guard_number = 0; return true;
}
void affect_to_char(CHAR_DATA *ch, AFFECT_DATA *af) {
  assert(af->bitvector == AFF_ABDUCTED); ++effects;
  SET_FLAG(ch->affected_by, af->bitvector);
}
CHAR_DATA *get_char_world_pc(char *) {
  if (online) return &saved;
  return char_list.empty() ? nullptr : char_list.front();
}
ACCOUNT_TYPE *get_online_account(char *) { return borrow_account ? &shared_account : nullptr; }
void free_account(ACCOUNT_TYPE *account) {
  assert(account != &shared_account); ++account_frees; delete account;
}
bool load_char_obj(DESCRIPTOR_DATA *d, char *) {
  assert(d->descriptor == -1 && d->character == nullptr);
  ++loads;
  d->character = new CHAR_DATA(saved);
  d->character->pcdata = new PC_DATA(saved_pc);
  if (attach_account) {
    auto *account = borrow_account ? &shared_account : new ACCOUNT_TYPE{};
    account->name = (char *)"SleeperAccount";
    d->character->pcdata->account = account;
  }
  d->character->desc = d;
  return found;
}
void free_char(CHAR_DATA *ch) {
  assert(ch->desc == nullptr);
  assert(std::find(char_list.begin(), char_list.end(), ch) == char_list.end());
  assert(std::find(people.begin(), people.end(), ch) == people.end());
  assert(std::find(other_people.begin(), other_people.end(), ch) == other_people.end());
  ++frees; delete ch->pcdata; delete ch;
}
void register_live_character(CHAR_DATA *ch) {
  assert(char_list.size() == 1 && char_list.front() == ch); ++registrations;
}
void char_to_room(CHAR_DATA *ch, ROOM_INDEX_DATA *to) {
  assert(char_list.size() == 1 && char_list.front() == ch);
  ch->in_room = to; to->people->push_back(ch); ++area.nplayer;
}
void char_from_room(CHAR_DATA *) { assert(false && "offline players must not change room lists"); }
void real_quit(CHAR_DATA *) { assert(false && "offline validation must not quit/save/delete players"); }
void extract_char(CHAR_DATA *, bool) { assert(false && "offline players are not live occupants"); }
void save_char_obj(CHAR_DATA *ch, bool, bool) {
  ++saves; saved = *ch; saved_pc = *ch->pcdata;
}
ROOM_INDEX_DATA *get_fleeroom(CHAR_DATA *, PROP_TYPE *) {
  return no_destination ? nullptr : &elsewhere;
}
void append_messages(CHAR_DATA *, char *text) { saved_messages += text; }
'''
source += section('  bool can_house_flee(', '  _DOFUN(do_tuckin)')
source += section('  _DOFUN(do_lookfor)', '  int get_price(')
source += section('  void autohouseflee(', '  _DOFUN(do_houseeval)')
source += r'''
void cleanup() {
  while (!char_list.empty()) {
    auto *ch = char_list.front(); char_list.pop_front();
    ch->in_room->people->remove(ch); --area.nplayer; free_sleeping_player(ch);
  }
  assert(loads == frees);
}
void reset() {
  cleanup(); actor = {}; saved = {}; actor_pc = {}; saved_pc = {};
  room = {}; elsewhere = {}; area = {}; property = {};
  people.clear(); other_people.clear();
  actor.name = (char *)"Actor"; saved.name = (char *)"Sleeper";
  actor.pcdata = &actor_pc; saved.pcdata = &saved_pc;
  actor.in_room = saved.in_room = &room;
  actor.played = saved.played = 200 * 3600; saved.lastlogoff = current_time - 3600;
  actor.money = 10000; actor_pc.privatepartner = (char *)"";
  room.area = elsewhere.area = &area; room.people = &people; elsewhere.people = &other_people;
  room.vnum = 1200; elsewhere.vnum = 1201; room.sector_type = SECT_HOUSE;
  area.nplayer = 1; people.push_back(&actor); property.type = PROP_HOUSE; property.logoffs = 1;
  loads = frees = saves = registrations = guards = effects = 0;
  crisis_prologue = 0; found = true; online = gm = institute = false;
  clinic_power = activate_guard = no_destination = false; output.clear(); saved_messages.clear();
  attach_account = borrow_account = false; account_frees = 0;
}
void run(DO_FUN *command, const char *argument = "Sleeper") {
  char input[MSL]; strcpy(input, argument); output.clear(); command(&actor, input);
}
void unchanged() {
  assert(char_list.empty() && people.size() == 1 && other_people.empty());
  assert(area.nplayer == 1 && saves == 0 && registrations == 0 && effects == 0);
  assert(loads == frees && actor.money == 10000 && property.logoffs == 1);
}
int main() {
  // Prechecks and unsuccessful loads allocate no lasting temporary resources.
  reset(); run(do_abduct, ""); assert(loads == 0); unchanged();
  reset(); online = true; run(do_abduct); assert(loads == 0); unchanged();
  reset(); found = false; run(do_abduct); assert(loads == 1 && frees == 1); unchanged();
  reset(); found = false; run(do_lookfor); unchanged();
  reset(); found = false; attach_account = true; run(do_abduct);
  assert(account_frees == 1); unchanged();
  reset(); attach_account = true; run(do_lookfor); assert(account_frees == 1); unchanged();
  reset(); attach_account = borrow_account = true; run(do_lookfor);
  assert(account_frees == 0); unchanged();
  reset(); SET_FLAG(actor.act, ACT_IS_NPC); actor.pcdata = nullptr;
  run(do_abduct); run(do_lookfor); assert(loads == 0); unchanged();

  // Rejecting an offline target must not invoke real_quit or rewrite their save.
  reset(); gm = true; run(do_abduct); assert(output.find("Story Runners") != std::string::npos); unchanged();
  reset(); gm = true; run(do_lookfor); unchanged();
  reset(); saved.in_room = &elsewhere; run(do_abduct); unchanged();
  reset(); saved.in_room = nullptr; run(do_abduct); unchanged();
  reset(); saved.in_room = &elsewhere; run(do_lookfor); unchanged();
  reset(); SET_FLAG(saved.act, PLR_FREEZE); run(do_abduct); unchanged();
  reset(); SET_FLAG(saved.act, PLR_STASIS); run(do_abduct); unchanged();
  reset(); saved.lastlogoff = current_time - 5 * 24 * 3600; run(do_abduct); unchanged();
  reset(); actor.money = 0; run(do_abduct); assert(actor.money == 0 && loads == frees && saves == 0);
  reset(); institute = true; activate_guard = true; saved_pc.guard_number = 2;
  run(do_abduct); assert(output.find("security staff") != std::string::npos);
  assert(guards == 0 && saved_pc.guard_number == 2); unchanged();

  // Lookup remains a read-only query and leaves no invisible live characters.
  reset(); run(do_lookfor); assert(output.find("asleep here") != std::string::npos); unchanged();
  reset(); saved.lastlogoff = current_time - 50000; run(do_lookfor); unchanged();

  // Successful capture still charges once, applies sleep and exposes one live target.
  reset(); run(do_abduct);
  assert(actor.money == 5000 && property.logoffs == 0 && loads == 1 && frees == 0);
  assert(registrations == 1 && char_list.size() == 1 && people.size() == 2 && area.nplayer == 2);
  auto *victim = char_list.front();
  assert(victim->desc == nullptr && victim->pcdata->sleeping == 30 && effects == 1);
  run(do_abduct); assert(loads == 1 && actor.money == 5000); cleanup();
  reset(); institute = clinic_power = true; run(do_abduct);
  assert(actor.money == 10000 && registrations == 1); cleanup();

  // A defended attempt persists guard expenditure and the offline escape location.
  reset(); activate_guard = true; saved_pc.guard_number = 2; run(do_abduct);
  assert(loads == 2 && frees == 2 && saves == 2 && registrations == 0);
  assert(saved_pc.guard_number == 0 && saved.in_room == &elsewhere && actor.money == 10000);
  assert(people.size() == 1 && other_people.empty() && area.nplayer == 1);
  assert(saved_messages.find("Actor") != std::string::npos);

  reset(); found = false; autohouseflee(saved.name, &property, actor.name); unchanged();
  reset(); no_destination = true; autohouseflee(saved.name, &property, actor.name); unchanged();
  reset(); online = true; autohouseflee(saved.name, &property, actor.name); assert(loads == 0); unchanged();
  cleanup();
  puts("PASS: offline abduction/lookup cleanup, rejected-target preservation, guard authorization, successful capture and safe escape lists.");
}
'''

with tempfile.TemporaryDirectory(prefix='abduct-command-') as temporary:
    scratch = Path(temporary)
    (scratch / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-ffunction-sections', '-fdata-sections',
                    '-Wl,--gc-sections', '-fsanitize=address,undefined', '-no-pie',
                    '-I', str(ROOT / 'src'), str(scratch / 'test.cc'),
                    '-o', str(scratch / 'test')], check=True)
    subprocess.run([str(scratch / 'test')], check=True)
