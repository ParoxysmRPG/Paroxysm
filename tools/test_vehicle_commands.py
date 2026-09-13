#!/usr/bin/env python3
"""Exercise production garage transactions and drive validation in Linux/WSL."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
travel = (ROOT / 'src/travel.c').read_text()


def section(start, end):
    offset = travel.index(start)
    return travel[offset:travel.index(end, offset)]


source = section('#define CAR_SPORT ', '  const char *world_names') + r'''
#include "merc.h"
#include <cassert>
#include <cstdarg>
#include <cstdlib>
#include <cstring>
DescList descriptor_list;
CharList char_list;
const TAXI_TYPE taxi_table[MAX_TAXIS] = {{1000, 0, 0}, {1001, 0, 0}};
int crisis_nodrive = 0, event_cleanse = 0;
CHAR_DATA actor = {}, borrower = {};
PC_DATA pc = {}, borrower_pc = {};
ROOM_INDEX_DATA home = {}, street = {}, cabin = {};
AREA_DATA area = {};
bool route_allowed = true, cabin_available = true;
OBJ_DATA key = {}, unrelated = {};
DESCRIPTOR_DATA descriptor = {};
std::string output;
std::vector<char *> allocations;
int extracted = 0, maps = 0;
char *str_dup(const char *s) { char *p = strdup(s ? s : ""); allocations.push_back(p); return p; }
void free_string(char *) {}
bool str_cmp(const char *a, const char *b) { return strcasecmp(a ? a : "", b ? b : "") != 0; }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void printf_to_char(CHAR_DATA *, const char *format, ...) {
  char text[MSL]; va_list args; va_start(args, format);
  vsnprintf(text, sizeof(text), format, args); va_end(args); output += text;
}
char *one_argument_nouncap(char *input, char *word) {
  while (*input == ' ') ++input;
  while (*input && *input != ' ') *word++ = *input++;
  *word = '\0'; while (*input == ' ') ++input; return input;
}
bool is_number(char *s) {
  if (*s == '+' || *s == '-') ++s;
  if (!*s) return false;
  for (; *s; ++s) if (*s < '0' || *s > '9') return false;
  return true;
}
bool is_helpless(CHAR_DATA *) { return false; }
bool is_ghost(CHAR_DATA *) { return false; }
bool in_fight(CHAR_DATA *) { return false; }
bool room_hostile(ROOM_INDEX_DATA *) { return false; }
bool can_logoff(CHAR_DATA *) { return true; }
char *carqualityname(int, int, int) { return (char *)"Quality"; }
char *cartypename(int, int) { return (char *)"Car"; }
char *carstatusname(int) { return (char *)"Status"; }
void string_append(CHAR_DATA *, char **) {}
int cartype(char *) { return CAR_SAFE; }
bool valid_carpair(int, int) { return true; }
char *default_carname(int) { return (char *)"Car"; }
char *new_lplate(CHAR_DATA *) { return (char *)"ABC"; }
OBJ_INDEX_DATA *get_obj_index(int) { return nullptr; }
OBJ_DATA *create_object(OBJ_INDEX_DATA *, int) { assert(false); return nullptr; }
void obj_to_char(OBJ_DATA *, CHAR_DATA *) { assert(false); }
EXTRA_DESCR_DATA *new_extra_descr() { assert(false); return nullptr; }
bool is_name(char *, char *) { return false; }
bool is_key_for(OBJ_DATA *obj, char *) { return obj == &key; }
void extract_obj(OBJ_DATA *obj) {
  ++extracted;
  for (CHAR_DATA *owner : {&actor, &borrower}) {
    OBJ_DATA **link = &owner->carrying;
    while (*link && *link != obj) link = &(*link)->next_content;
    if (*link) *link = obj->next_content;
  }
  obj->next_content = nullptr;
}
ROOM_INDEX_DATA *get_room_index(int vnum) {
  if (vnum == home.vnum) return &home;
  if (vnum == street.vnum) return &street;
  if (vnum == cabin.vnum) return &cabin;
  return nullptr;
}
void char_from_room(CHAR_DATA *ch) { ch->in_room = nullptr; }
void char_to_room(CHAR_DATA *ch, ROOM_INDEX_DATA *room) { ch->in_room = room; }
void maketownmap(CHAR_DATA *ch) { assert(ch->in_room == &street); ++maps; }
bool is_pinned(CHAR_DATA *) { return false; }
bool shipment_carrier(CHAR_DATA *) { return false; }
bool clinic_patient(CHAR_DATA *) { return false; }
bool has_active_vehicle(CHAR_DATA *) { return true; }
void remember_location(CHAR_DATA *, char *) {}
int vehicle_location(CHAR_DATA *ch) { return ch->pcdata->garage_location[0]; }
void set_vehicle_location(CHAR_DATA *ch, int location) { ch->pcdata->garage_location[0] = location; }
int vehicle_typeone(CHAR_DATA *ch) { return ch->pcdata->garage_typeone[0]; }
int vehicle_typetwo(CHAR_DATA *ch) { return ch->pcdata->garage_typetwo[0]; }
int vehicle_cost(CHAR_DATA *ch) { return ch->pcdata->garage_cost[0]; }
char *vehicle_name(CHAR_DATA *ch) { return ch->pcdata->garage_name[0]; }
char *vehicle_desc(CHAR_DATA *) { return (char *)"A vehicle."; }
char *vehicle_lplate(CHAR_DATA *ch) { return ch->pcdata->garage_lplate[0]; }
int landmark_vnum(char *, CHAR_DATA *) { return 0; }
int get_roomx(ROOM_INDEX_DATA *) { return 0; }
int get_roomy(ROOM_INDEX_DATA *) { return 0; }
int get_dist(int, int, int, int) { return 1; }
int mist_level(ROOM_INDEX_DATA *) { return 0; }
bool world_blocked(CHAR_DATA *, int) { return !route_allowed; }
bool can_world_travel(CHAR_DATA *, ROOM_INDEX_DATA *, ROOM_INDEX_DATA *) { return true; }
bool room_empty(ROOM_INDEX_DATA *) { return cabin_available; }
int street_distance(ROOM_INDEX_DATA *, ROOM_INDEX_DATA *, CHAR_DATA *) { return 3; }
void unplace_car(CHAR_DATA *) {}
void set_generated_room_description(ROOM_INDEX_DATA *, const char *) {}
char *PERS(CHAR_DATA *ch, CHAR_DATA *) { return ch->name; }
bool is_gm(CHAR_DATA *) { return false; }
int max_passengers(CHAR_DATA *) { return 4; }
void makevehicle(CHAR_DATA *) {}
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
void dact(const char *, CHAR_DATA *, const void *, const void *, int) {}
'''
source += section('  bool valid_parking_spot(', '  _DOFUN(do_park)')
source += section('  bool has_town_vehicle(', '  _DOFUN(do_drive)')
source += section('  _DOFUN(do_garage)', '  bool valid_parking_spot(')
source += r'''
void reset() {
  actor = {}; borrower = {}; pc = {}; borrower_pc = {};
  key = {}; unrelated = {}; descriptor = {};
  actor.pcdata = &pc; actor.in_room = &home; actor.name = (char *)"Owner";
  borrower.pcdata = &borrower_pc; borrower.in_room = &home;
  home.vnum = 1000; street.vnum = 1001;
  home.name = (char *)"Home"; street.name = (char *)"Street";
  home.sector_type = street.sector_type = SECT_STREET;
  home.area = street.area = cabin.area = &area; area.world = WORLD_EARTH;
  cabin.vnum = INIT_CABS; route_allowed = cabin_available = true;
  actor.shape = SHAPE_HUMAN;
  pc.garage_cost[0] = 5000; pc.garage_status[0] = GARAGE_LOANED;
  pc.garage_name[0] = (char *)"Car"; pc.garage_lplate[0] = (char *)"ABC";
  pc.garage_typeone[0] = CAR_SAFE; pc.total_money = 10000;
  descriptor.character = &borrower; descriptor.connected = CON_PLAYING;
  descriptor_list = {&descriptor};
  char_list.clear();
  key.item_type = ITEM_KEY; extracted = maps = 0; output.clear();
}
void run(const char *input) {
  char text[MSL]; strcpy(text, input); output.clear(); do_garage(&actor, text);
}
void drive(const char *input) {
  char text[MSL]; strcpy(text, input); output.clear(); do_newdrive(&actor, text);
}
int main() {
  for (int damaged : {0, 1}) {
    reset(); actor.carrying = &key; key.value[3] = damaged;
    run("recover 1");
    assert(actor.carrying == &key && extracted == 0 && pc.total_money == 10000);
    assert(pc.garage_status[0] == GARAGE_LOANED && pc.garage_timer[0] == 0);
    assert(output.find("garage reclaim") != std::string::npos);
    run("reclaim 1");
    assert(!actor.carrying && extracted == 1 && pc.total_money == 10000);
    assert(pc.garage_status[0] == (damaged ? GARAGE_REPAIR : GARAGE_GARAGED));
    assert(pc.garage_timer[0] == (damaged ? 2880 : 0));
  }
  puts("PASS: rejected recovery preserves keys and damage state; reclaim remains free and repairs damage.");
  for (int balance : {-1, 0, 9999}) {
    reset(); pc.total_money = balance; borrower.carrying = &key; key.value[3] = 1;
    run("recover 1");
    assert(borrower.carrying == &key && extracted == 0 && pc.total_money == balance);
    assert(pc.garage_status[0] == GARAGE_LOANED && pc.garage_timer[0] == 0);
  }
  for (int damaged : {0, 1}) {
    reset(); borrower.carrying = &unrelated; unrelated.next_content = &key;
    key.value[3] = damaged;
    run("recover 1");
    assert(borrower.carrying == &unrelated && !unrelated.next_content && extracted == 1);
    assert(pc.total_money == 0 && pc.garage_timer[0] == 1440);
    assert(pc.garage_status[0] == (damaged ? GARAGE_RECOVERREPAIR : GARAGE_RECOVER));
    run("recover 1"); assert(pc.total_money == 0 && extracted == 1);
  }
  reset(); descriptor_list.clear(); run("recover 1");
  assert(pc.total_money == 0 && pc.garage_status[0] == GARAGE_RECOVER);
  puts("PASS: recovery checks funds before touching borrowed keys, charges once, and retains recovery timing.");
  for (int balance : {-1, 0, 499}) {
    reset(); pc.total_money = balance; pc.garage_location[0] = street.vnum;
    run("locate 1"); assert(pc.total_money == balance && maps == 0 && actor.in_room == &home);
  }
  reset(); pc.total_money = 500; pc.garage_location[0] = street.vnum;
  run("locate 1"); assert(pc.total_money == 0 && maps == 1 && actor.in_room == &home);
  for (int location : {0, 99999}) {
    reset(); pc.garage_location[0] = location;
    run("locate 1"); assert(pc.total_money == 10000 && maps == 0 && pc.garage_location[0] == 0);
  }
  puts("PASS: locate requires funds for a map and does not charge for vehicles already in the garage.");
  for (int type : {CAR_SAFE, CAR_HORSE}) {
    reset(); pc.garage_typeone[0] = type; pc.garage_status[0] = GARAGE_GARAGED;
    assert(has_town_vehicle(&actor) == (type != CAR_HORSE));
    assert(has_world_vehicle(&actor) == (type == CAR_HORSE));
    run("unlease 1");
    assert(!has_town_vehicle(&actor) && !has_world_vehicle(&actor));
  }
  reset(); do_garage(nullptr, (char *)"view");
  actor.pcdata = nullptr; run("view");
  actor.pcdata = &pc; actor.in_room = nullptr; run("view");
  actor.in_room = &home; SET_FLAG(actor.act, ACT_IS_NPC); run("view");
  assert(output.empty());
  puts("PASS: returned leases cannot grant travel access, and garage rejects nonplayer/missing state.");
  for (int scenario = 0; scenario < 4; ++scenario) {
    reset(); SET_FLAG(actor.act, PLR_HIDE); pc.driving_around = true; pc.process_timer = 20;
    if (scenario == 2) route_allowed = false;
    if (scenario == 3) cabin_available = false;
    drive(scenario == 0 ? "list" : scenario == 1 ? "nonsense" : "2");
    assert(IS_FLAG(actor.act, PLR_HIDE) && pc.driving_around && pc.process_timer == 20);
    assert(actor.in_room == &home && pc.travel_time == 0);
  }
  reset(); SET_FLAG(actor.act, PLR_HIDE); pc.driving_around = true; pc.process_timer = 20;
  drive("2");
  assert(!IS_FLAG(actor.act, PLR_HIDE) && !pc.driving_around && pc.process_timer == 0);
  assert(actor.in_room == &cabin && pc.travel_time == 3 && pc.travel_to == street.vnum);
  assert(pc.travel_from == home.vnum && pc.travel_type == TRAVEL_CAR);
  puts("PASS: destination listing and rejected drives preserve state; accepted journeys commit travel changes.");
  for (char *allocation : allocations) free(allocation);
}
'''

with tempfile.TemporaryDirectory(prefix='vehicle-command-') as tmp:
    cpp, binary = Path(tmp) / 'test.cpp', Path(tmp) / 'test'
    cpp.write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-Wall', '-Wextra', '-Wno-write-strings',
                    '-Wno-unused-parameter', '-Wno-deprecated', '-g',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-no-pie',
                    '-I', str(ROOT / 'src'), str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
