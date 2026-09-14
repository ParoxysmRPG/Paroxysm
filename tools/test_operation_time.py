#!/usr/bin/env python3
"""Check production time/operation displays against the scheduling clock in WSL/Linux."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
info = (ROOT / 'src/act_info.c').read_text()
clans = (ROOT / 'src/clans.c').read_text()


def section(text, start, end):
    offset = text.index(start)
    return text[offset:text.index(end, offset)]


source = r'''
#include "game_time.h"
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#define _DOFUN(name) void name(CHAR_DATA *ch)
#define IS_IMMORTAL(ch) false
#define FALSE false
#define TRUE true
constexpr int GOAL_PSYCHIC = 1;
struct AREA { int vnum = 0; };
struct ROOM_INDEX_DATA { int timezone = 0; AREA *area; };
struct PROP_TYPE { int timeshift = 0, timefrozen = 0; };
struct PC_DATA { int jetlag = 0; };
struct CHAR_DATA {
  PC_DATA *pcdata; ROOM_INDEX_DATA *in_room;
  const char *name = "Tester"; int faction = 0, factiontwo = 0;
};
struct FACTION_TYPE { const char *name = "The Golden Shadow"; };
struct LOCATION_TYPE { int timezone = -3; };
struct OPERATION_TYPE {
  int faction = 1, hour = 12, day = 0, goal = 0, terrain = 0;
  int max_pcs = 2, competition = 0, challenge = 2, size = 1000, speed = 3;
  int home_soldiers = 4, territoryvnum = 1;
  int enrolled[10] = {}, soldiers[10] = {};
  const char *sign_up[100] = {}, *target = "", *description = "";
  const char *preferred = "", *storyrunners = "";
};
FACTION_TYPE faction;
LOCATION_TYPE location;
time_t current_time;
std::string output;
const char *terrain_names[] = {"Field"}, *moon_real[] = {"waxing crescent"};
const char *comp_types[] = {"Open"};
bool in_haven(ROOM_INDEX_DATA *room) { return room->timezone == 0; }
PROP_TYPE *prop_from_room(ROOM_INDEX_DATA *) { return nullptr; }
int get_last_hour(ROOM_INDEX_DATA *) { return 0; }
int moon_pointer(int, int, int, void *) { return 0; }
FACTION_TYPE *clan_lookup(int) { return &faction; }
LOCATION_TYPE *territory_by_number(int) { return &location; }
bool str_cmp(const char *a, const char *b) { return !b || strcmp(a, b); }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
bool is_name(const char *, const char *) { return false; }
const char *nosr_name(const char *s) { return s; }
bool power_operation_goal(int) { return false; }
const char *operation_location(OPERATION_TYPE *) { return "Vancouver, Canada"; }
const char *op_goal(OPERATION_TYPE *) { return "Secure the area"; }
const char *visible_goal(int) { return "Control"; }
const char *weather_forecast(LOCATION_TYPE *, int) { return "Clear"; }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void printf_to_char(CHAR_DATA *, const char *fmt, ...) {
  char buf[4096]; va_list args; va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args); va_end(args); output += buf;
}
'''
source += section(info, '  int get_hour(ROOM_INDEX_DATA *room) {', '  int get_last_hour(')
source += section(info, '  _DOFUN(do_time) {', '  _DOFUN(do_helpseealso)')
source += section(clans, '  void show_operation_to_char(', '  // Command numbers must')
source += r'''
time_t utc(int year, int month, int day, int hour, int minute = 0, int second = 0) {
  tm fields{}; fields.tm_year = year - 1900; fields.tm_mon = month - 1;
  fields.tm_mday = day; fields.tm_hour = hour; fields.tm_min = minute;
  fields.tm_sec = second; return timegm(&fields);
}
void contains(const char *s) { assert(output.find(s) != std::string::npos); }
int main() {
  AREA area; ROOM_INDEX_DATA room{0, &area}; PC_DATA pc;
  CHAR_DATA actor{&pc, &room}; OPERATION_TYPE op;
  // The same saved schedule and timestamps must work under any host timezone,
  // including hosts that apply daylight saving and fractional-hour offsets.
  for (const char *zone : {"UTC0", "EST5EDT,M3.2.0,M11.1.0", "JST-9", "NPT-5:45"}) {
    setenv("TZ", zone, 1); tzset();
    current_time = utc(2026, 9, 14, 3, 1, 20);
    assert(get_hour(nullptr) == 22);
    output.clear(); do_time(&actor);
    contains("The time is Sun Sep 13 22:01:20 2026");
    contains("Your time is Sun Sep 13 22:01:20 2026");
    output.clear(); show_operation_to_char(&actor, &op);
    contains("Leaving at 12 hundred hours in 0 days.");
    contains("Your time: Mon Sep 14 12:00:00 2026");
    contains("Local time will be 9 hundred hours.");
    const time_t departure = haven::operation_departure_time(current_time, 12, 0);
    assert(departure == utc(2026, 9, 14, 17));
    current_time = departure - 1; assert(get_hour(nullptr) == 11);
    current_time = departure; assert(get_hour(nullptr) == 12);
    output.clear(); do_time(&actor);
    contains("Your time is Mon Sep 14 12:00:00 2026");

    // Personal and destination clocks cross dates correctly.
    current_time = utc(2026, 9, 14, 3, 1, 20);
    pc.jetlag = 8; room.timezone = -3;
    output.clear(); do_time(&actor);
    contains("Your time is Mon Sep 14 06:01:20 2026");
    contains("Local time is Sun Sep 13 19:01:20 2026");
    output.clear(); show_operation_to_char(&actor, &op);
    contains("Your time: Mon Sep 14 20:00:00 2026");
    op.goal = GOAL_PSYCHIC;
    output.clear(); show_operation_to_char(&actor, &op);
    contains("Your time: Mon Sep 14 20:00:00 2026");
    op.goal = 0; op.hour = 1; pc.jetlag = -4;
    output.clear(); show_operation_to_char(&actor, &op);
    contains("Your time: Sun Sep 13 21:00:00 2026");
    contains("Local time will be 22 hundred hours.");
    pc.jetlag = 0; room.timezone = 0; op.hour = 12;
  }
  // Before, at, and after the departure hour; day is a recurrence count.
  for (int hour : {1, 12, 22, 23}) {
    for (int day : {0, 1, 6}) {
      const time_t departure = utc(2026, 12, 31, hour + 5);
      assert(haven::operation_departure_time(departure - 1, hour, day)
          == departure + day * 86400);
      assert(haven::operation_departure_time(departure, hour, day)
          == departure + (day + 1) * 86400);
      assert(haven::operation_departure_time(departure + 3599, hour, day)
          == departure + (day + 1) * 86400);
    }
  }
  puts("PASS: time and operation displays agree with scheduler across host timezones, offsets, midnight and year rollover.");
}
'''
with tempfile.TemporaryDirectory(prefix='operation-time-') as tmp:
    cpp, exe = Path(tmp) / 'test.cpp', Path(tmp) / 'test'
    cpp.write_text(source)
    subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-g',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-no-pie',
                    '-I', str(ROOT / 'src'), str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
