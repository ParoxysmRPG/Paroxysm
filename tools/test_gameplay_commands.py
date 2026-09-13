#!/usr/bin/env python3
"""Linux/WSL sanitizer regression checks for cash, phone handoffs and exits."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def section(filename, start, end):
    text = (ROOT / 'src' / filename).read_text()
    offset = text.index(start)
    return text[offset:text.index(end, offset)]


source = r'''
#include "merc.h"
#include <cassert>
#include <climits>
#include <cstring>
#include <cstdlib>
#include <cstdarg>

CHAR_DATA actor = {}, target = {}, caller = {};
PC_DATA actor_pc = {}, target_pc = {}, caller_pc = {};
MOB_INDEX_DATA target_index = {};
OBJ_DATA item = {}, cash = {};
OBJ_INDEX_DATA item_index = {};
ROOM_INDEX_DATA room = {}, destination = {};
AREA_DATA area = {};
EXIT_DATA exits[10] = {};
CharList people;
bool MOBtrigger = true;
std::string output;
int drops = 0, gifts = 0, changes = 0, bribe_awards = 0;

bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
bool str_prefix(const char *a, const char *b) { return strncasecmp(a, b, strlen(a)) != 0; }
bool is_name(char *name, char *list) { return !str_cmp(name, list); }
char *one_argument(char *input, char *word) {
  while (*input == ' ') ++input;
  while (*input && *input != ' ') *word++ = *input++;
  *word = '\0'; while (*input == ' ') ++input; return input;
}
char *one_argument_nouncap(char *input, char *word) { return one_argument(input, word); }
char *str_dup(const char *text) { return strdup(text); }
void free_string(char *text) { free(text); }
void send_to_char(const char *text, CHAR_DATA *) { output += text; }
void printf_to_char(CHAR_DATA *, const char *format, ...) {
  char buffer[MSL]; va_list args; va_start(args, format);
  vsnprintf(buffer, sizeof(buffer), format, args); va_end(args); output += buffer;
}
void act_new(const char *text, CHAR_DATA *, const void *, const void *, int, int) { output += text; }
void log_string(const char *) {}
void wiznet(char *, CHAR_DATA *, OBJ_DATA *, long, long, int) {}
int get_trust(CHAR_DATA *ch) { return ch->trust; }
bool is_gm(CHAR_DATA *) { return false; }
bool higher_power(CHAR_DATA *) { return false; }
bool is_ghost(CHAR_DATA *) { return false; }
bool is_corporeal(CHAR_DATA *) { return true; }
bool is_griefer(CHAR_DATA *) { return false; }
bool is_helpless(CHAR_DATA *) { return false; }
bool is_possessed(CHAR_DATA *) { return false; }
bool is_prisoner(CHAR_DATA *) { return false; }
bool in_fight(CHAR_DATA *) { return false; }
bool in_fistfight(CHAR_DATA *) { return false; }
bool has_con(CHAR_DATA *, int) { return false; }
bool is_pair(OBJ_DATA *) { return false; }
char *a_or_an(char *) { return (char *)"a"; }
bool is_big(OBJ_DATA *) { return false; }
int get_big_items(CHAR_DATA *) { return 0; }
int get_small_items(CHAR_DATA *) { return 0; }
bool can_drop_obj(CHAR_DATA *, OBJ_DATA *) { return true; }
bool can_see_obj(CHAR_DATA *, OBJ_DATA *) { return true; }
bool stolen_object(CHAR_DATA *, OBJ_DATA *) { return false; }
void steal_object(OBJ_DATA *, CHAR_DATA *) {}
void alter_character(CHAR_DATA *) { ++changes; }
void gain_resources(int, int, CHAR_DATA *, char *) { ++bribe_awards; }
void patrol_personal_award(CHAR_DATA *, int) { ++bribe_awards; }
void affect_to_char(CHAR_DATA *, AFFECT_DATA *) {}
CHAR_DATA *get_char_room(CHAR_DATA *, ROOM_INDEX_DATA *, char *name) {
  if (!str_cmp(name, "Actor")) return &actor;
  return !str_cmp(name, "Target") ? &target : nullptr;
}
OBJ_DATA *get_obj_carry(CHAR_DATA *ch, char *name, CHAR_DATA *) {
  return ch->carrying && is_name(name, ch->carrying->name) ? ch->carrying : nullptr;
}
OBJ_DATA *get_obj_carryhold(CHAR_DATA *ch, char *name, CHAR_DATA *viewer) {
  return get_obj_carry(ch, name, viewer);
}
OBJ_DATA *get_obj_wear(CHAR_DATA *, char *, bool) { return nullptr; }
OBJ_DATA *get_eq_char(CHAR_DATA *, int) { return nullptr; }
OBJ_DATA *get_eqr_char(CHAR_DATA *, int) { return nullptr; }
void equip_char_silent(CHAR_DATA *, OBJ_DATA *, int) {}
void unequip_char(CHAR_DATA *, OBJ_DATA *) {}
bool remove_obj(CHAR_DATA *, int, bool) { return true; }
OBJ_DATA *create_money(int amount, CHAR_DATA *) {
  cash.value[1] = amount; return &cash;
}
void obj_from_char(OBJ_DATA *obj) {
  assert(obj->carried_by);
  obj->carried_by->carrying = nullptr; obj->carried_by = nullptr;
}
void obj_to_char(OBJ_DATA *obj, CHAR_DATA *ch) {
  obj->carried_by = ch; ch->carrying = obj; ++gifts;
}
void obj_to_room(OBJ_DATA *obj, ROOM_INDEX_DATA *to) { obj->in_room = to; ++drops; }
'''
source += section('interp.c', '  bool is_number_float(', '  /*\n* Given a string like 14.foo')
source += section('act_obj.c', '  char *dropprefix(', '  _DOFUN(do_pour)')
source += section('act_move.c', '  const char *dir_name', '  /*\n  * Local functions.')
source += section('act_move.c', '  int find_exit(', '  int room_pop_mortals(')
source += section('act_move.c', '  int turns_to_get(', '  _DOFUN(do_cardinal)')
source += section('act_move.c', '  _DOFUN(do_climb)', '  void move_char(')
source += r'''
void reset() {
  actor = {}; target = {}; caller = {}; actor_pc = {}; target_pc = {}; caller_pc = {};
  room = {}; destination = {}; area = {}; item = {}; item_index = {}; cash = {};
  target_index = {};
  actor.pcdata = &actor_pc; target.pcdata = &target_pc; caller.pcdata = &caller_pc;
  actor.name = (char *)"Actor"; target.name = (char *)"Target";
  target.long_descr = (char *)"Target"; target.pIndexData = &target_index;
  actor.in_room = target.in_room = caller.in_room = &room;
  room.area = &area; room.people = &people; people.clear(); people.push_back(&actor);
  actor.money = 10000; target.money = 100;
  actor.position = POS_STANDING; actor_pc.travel_time = -1;
  actor_pc.travel_to = actor_pc.travel_type = -1;
  for (int i = 0; i < 10; ++i) {
    exits[i] = {}; room.exit[i] = &exits[i]; exits[i].u1.to_room = &destination;
    exits[i].keyword = (char *)dir_name[i][0];
  }
  item.name = (char *)"phone"; item.short_descr = (char *)"phone";
  item.pIndexData = &item_index; item.item_type = ITEM_PHONE;
  item.wear_loc = WEAR_NONE; item.carried_by = &actor; actor.carrying = &item;
  drops = gifts = changes = bribe_awards = 0; output.clear();
}
void command(DO_FUN *fn, const char *input) {
  char buffer[MSL]; snprintf(buffer, sizeof(buffer), "%s", input); fn(&actor, buffer);
}
void test_cash() {
  for (int cents : {1, 29, 113, 115, 199, 9999, INT_MAX}) {
    char amount[80]; snprintf(amount, sizeof(amount), "%d.%02d", cents / 100, cents % 100);
    reset(); actor.money = cents;
    command(do_drop, amount);
    assert(actor.money == 0 && drops == 1 && cash.value[1] == cents && changes == 1);
    reset(); actor.money = cents; target.money = 0;
    std::string gift = std::string(amount) + " dollars Target";
    command(do_give, gift.c_str());
    assert(actor.money == 0 && target.money == cents && changes == 1);
    assert(output.find(std::string(amount) + " dollars") != std::string::npos);
  }
  for (const char *amount : {"0", "0.00", "-1", "0.009", "1.999", "1.2.3", ".", "+",
                           "21474836.48", "21474837", "9999999999999999999999999999999"}) {
    reset(); actor.money = LONG_MAX; command(do_drop, amount);
    assert(actor.money == LONG_MAX && drops == 0 && changes == 0);
    reset(); actor.money = LONG_MAX;
    command(do_give, (std::string(amount) + " dollars Target").c_str());
    assert(actor.money == LONG_MAX && target.money == 100 && changes == 0 && bribe_awards == 0);
  }
  for (const char *amount : {"1", "1.", "+1.00", "0001.00"}) {
    reset(); command(do_drop, amount); assert(cash.value[1] == 100 && actor.money == 9900);
  }
  reset(); command(do_drop, ".5"); assert(cash.value[1] == 50 && actor.money == 9950);
  reset(); actor.money = 28; command(do_drop, "0.29");
  assert(actor.money == 28 && drops == 0 && changes == 0);
  reset(); command(do_give, "0.29 dollars Missing");
  assert(actor.money == 10000 && target.money == 100 && changes == 0);
  reset(); target.money = LONG_MAX; command(do_give, "0.01 dollars Target");
  assert(actor.money == 10000 && target.money == LONG_MAX && changes == 0);
  reset(); actor.money = LONG_MAX; command(do_give, "0.01 dollars Actor");
  assert(actor.money == LONG_MAX);
  reset(); actor_pc.patrol_status = PATROL_BRIBING; actor_pc.patrol_room = &room;
  target.level = 1; target.pcdata = nullptr; SET_FLAG(target.act, ACT_IS_NPC);
  SET_FLAG(target.act, ACT_BRIBEMOB); command(do_give, "1.15 dollars Target");
  assert(actor.money == 9885 && target.money == 215 && bribe_awards == 2);
  assert(target.ttl == 1 && !IS_FLAG(target.act, ACT_BRIBEMOB));
}
void connect_call() {
  actor_pc.connected_to = &caller; caller_pc.connected_to = &actor;
  actor_pc.connection_stage = caller_pc.connection_stage = CONNECT_TALKING;
}
void test_phone() {
  reset(); connect_call(); command(do_give, "phone Target");
  assert(gifts == 1 && item.carried_by == &target && actor_pc.connected_to == nullptr);
  assert(target_pc.connected_to == &caller && caller_pc.connected_to == &target);
  reset(); connect_call(); target.pcdata = nullptr; SET_FLAG(target.act, ACT_IS_NPC);
  command(do_give, "phone Target");
  assert(gifts == 1 && item.carried_by == &target);
  assert(actor_pc.connected_to == nullptr && caller_pc.connected_to == nullptr);
  assert(actor_pc.connection_stage == CONNECT_NONE && caller_pc.connection_stage == CONNECT_NONE);
  reset(); target.pcdata = nullptr; SET_FLAG(target.act, ACT_IS_NPC);
  command(do_give, "phone Target"); assert(gifts == 1 && item.carried_by == &target);
  reset(); command(do_drop, "phone"); assert(drops == 1 && item.in_room == &room);
}
void test_exits() {
  reset();
  for (int i = 0; i < 10; ++i) for (int spelling = 0; spelling < 2; ++spelling)
    assert(find_exit(&actor, (char *)dir_name[i][spelling]) == i);
  exits[DIR_EAST].keyword = (char *)"window";
  assert(find_exit(&actor, (char *)"window") == DIR_EAST);
  assert(find_exit(&actor, (char *)"nowhere") == -1);
  assert(find_exit(&actor, (char *)"") == -1);
  assert(find_exit(&actor, nullptr) == -1 && find_exit(nullptr, (char *)"north") == -1);
  SET_FLAG(actor.comm, COMM_CARDINAL); actor.facing = DIR_EAST;
  assert(find_exit(&actor, (char *)"forward") == DIR_EAST);
  assert(find_exit(&actor, (char *)"right") == DIR_SOUTH);
  assert(find_exit(&actor, (char *)"window") == DIR_EAST);
  assert(find_exit(&actor, (char *)"nowhere") == -1);
  room.exit[DIR_EAST] = nullptr;
  assert(find_exit(&actor, (char *)"forward") == -1);
  actor.in_room = nullptr;
  assert(find_exit(&actor, (char *)"forward") == -1);
}
void test_climb() {
  reset(); destination.vnum = 12345;
  exits[DIR_NORTH].wall = WALL_GLASS; exits[DIR_NORTH].climb = 5;
  SET_FLAG(actor.act, PLR_HIDE);
  SET_FLAG(actor.comm, PLR_HIDE); // Unrelated comm bit at the same bit offset.
  command(do_climb, "north");
  assert(!IS_FLAG(actor.act, PLR_HIDE) && IS_FLAG(actor.comm, PLR_HIDE));
  assert(actor_pc.travel_to == 12345 && actor_pc.travel_type == TRAVEL_CLIMB);
  assert(actor_pc.travel_time == 5);
  reset(); SET_FLAG(actor.act, PLR_HIDE); command(do_climb, "north");
  assert(IS_FLAG(actor.act, PLR_HIDE) && actor_pc.travel_time == -1);
}
int main() {
  test_cash(); test_phone(); test_exits(); test_climb();
  puts("PASS: exact cents, rejected malformed/overflow cash, NPC bribe and phone handoffs, exit targeting and climbing state.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-gameplay-commands-') as temporary:
    scratch = Path(temporary)
    (scratch / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-ffunction-sections', '-fdata-sections',
                    '-Wl,--gc-sections', '-fsanitize=address,undefined', '-no-pie',
                    '-I', str(ROOT / 'src'), str(scratch / 'test.cc'),
                    '-o', str(scratch / 'test')], check=True)
    subprocess.run([str(scratch / 'test')], check=True)
