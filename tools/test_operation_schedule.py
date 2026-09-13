#!/usr/bin/env python3
"""Check production operation reminders and clock catch-up in Linux/WSL.

Compiles an isolated ASan/UBSan executable; no game data is loaded or changed.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
update = (ROOT / 'src/update.c').read_text()
hourly = update.index('  void hourly_update(int hour)')
start = update.index('    for (vector<OPERATION_TYPE *>::iterator it = OpVect.begin();', hourly)
operation_loop = update[start:update.index('    faction_antagonist_update();', start)]
start = update.index('  void clock_update(void) {')
clock = update[start:update.index('  int terrain_pointer(', start)]

source = r'''
#include <cassert>
#include <cstdio>
#include <string>
#include <utility>
#include <vector>
using std::vector;
constexpr int MSL = 4096, COMPETE_CLOSED = 2, PULSE_PER_SECOND = 4;
struct OPERATION_TYPE {
  bool valid = true;
  int hour = 12, day = 0, faction = 26, competition = 0, territoryvnum = 1;
};
struct FACTION_TYPE { int vnum; const char *name; };
struct LOCATION_TYPE { const char *name; };
FACTION_TYPE host{26, "The Golden Shadow"}, opponent{1, "The Order"};
LOCATION_TYPE location{"Lauriea"};
vector<OPERATION_TYPE *> OpVect;
vector<FACTION_TYPE *> FacVect{&host, &opponent};
vector<std::pair<int, std::string>> messages;
vector<int> hours, launches;
int now_hour = 0, now_minute = 0, event_cleanse = 0;
int clock_hour = 0, clock_minute = 0, clock_second = 0;
long current_time = 0;
int get_hour(void *) { return now_hour; }
int get_minute() { return now_minute; }
void minute_update(int) {}
FACTION_TYPE *clan_lookup(int vnum) {
  for (auto *fac : FacVect) if (fac->vnum == vnum) return fac;
  return nullptr;
}
LOCATION_TYPE *territory_by_number(int vnum) { return vnum == 1 ? &location : nullptr; }
void send_message_temp(int faction, const char *message) {
  messages.emplace_back(faction, message);
}
void launch_operation(OPERATION_TYPE *op) {
  launches.push_back(op->faction);
  op->hour = 0; // Unopposed launch resolution retires the operation this way.
}
void hourly_update(int hour) {
  hours.push_back(hour);
'''
source += operation_loop + '\n}\n' + clock
source += r'''
void reset(OPERATION_TYPE &op, int previous_hour, int actual_hour, int minute = 0) {
  op = OPERATION_TYPE{};
  OpVect = {&op};
  messages.clear(); hours.clear(); launches.clear();
  clock_hour = previous_hour; now_hour = actual_hour;
  clock_minute = now_minute = minute;
  event_cleanse = 0;
}
int main() {
  OPERATION_TYPE op;
  // Reproduce the report: catching up 11:00 and 12:00 in one clock tick must
  // still launch the overdue operation, without an expired signup reminder.
  reset(op, 10, 12);
  clock_update();
  assert((hours == vector<int>{11, 12}));
  assert(messages.empty());
  assert(launches.size() == 1 && op.hour == 0);
  clock_update();
  assert(launches.size() == 1);

  // Larger backlogs span multiple calls; all scheduled hours still run.
  reset(op, 8, 13);
  while (clock_hour != now_hour) clock_update();
  assert((hours == vector<int>{9, 10, 11, 12, 13}));
  assert(messages.empty() && launches.size() == 1);

  // Normal reminders still reach both sides, and identify the departure.
  reset(op, 10, 11);
  clock_update();
  assert(messages.size() == 2 && launches.empty());
  assert(messages[0].first == host.vnum && messages[1].first == opponent.vnum);
  for (const auto &message : messages) {
    assert(message.second.find("The Golden Shadow") != std::string::npos);
    assert(message.second.find("Lauriea") != std::string::npos);
    assert(message.second.find("12:00") != std::string::npos);
    assert(message.second.find("operation signup") != std::string::npos);
    assert(message.second.find("Your comms announce") == std::string::npos);
  }
  clock_update();
  assert(messages.size() == 2);
  now_hour = 12;
  clock_update();
  assert(messages.size() == 2 && launches.size() == 1);

  // A late tick within the warning hour must not promise another full hour.
  reset(op, 10, 11, 59);
  clock_update();
  assert(messages.size() == 2);
  assert(messages[0].second.find("12:00") != std::string::npos);
  assert(messages[0].second.find("in one hour") == std::string::npos);
  assert(messages[0].second.find("in an hour") == std::string::npos);

  // Closed operations stay private and cleanse suppresses reminders.
  reset(op, 10, 11);
  op.competition = COMPETE_CLOSED;
  clock_update();
  assert(messages.size() == 1 && messages[0].first == host.vnum);
  reset(op, 10, 11);
  event_cleanse = 1;
  clock_update();
  assert(messages.empty());

  // Hour zero marks completed/cancelled operations, not midnight departures.
  reset(op, 22, 23);
  op.hour = 0;
  clock_update();
  assert(messages.empty() && launches.empty());
  reset(op, 10, 11);
  op.valid = false;
  clock_update();
  now_hour = 12;
  clock_update();
  assert(messages.empty() && launches.empty());

  // Catch-up over midnight retains legitimate future reminders and launches.
  reset(op, 23, 1);
  op.hour = 1;
  clock_update();
  assert((hours == vector<int>{0, 1}));
  assert(messages.empty() && launches.size() == 1);
  reset(op, 23, 0);
  op.hour = 1;
  clock_update();
  assert(messages.size() == 2 && launches.empty());

  // Day counts decrement at the departure hour, even during catch-up.
  reset(op, 10, 12);
  op.day = 1;
  clock_update();
  assert(op.day == 0 && messages.empty() && launches.empty());
  clock_hour = 10; now_hour = 11;
  clock_update();
  assert(messages.size() == 2 && launches.empty());
  now_hour = 12;
  clock_update();
  assert(launches.size() == 1);
  puts("PASS: overdue reminders, normal departures, late ticks, midnight, inactive operations and day counts.");
}
'''
with tempfile.TemporaryDirectory(prefix='operation-schedule-') as tmp:
    cpp, exe = Path(tmp) / 'test.cpp', Path(tmp) / 'test'
    cpp.write_text(source)
    subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-g',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-no-pie',
                    str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
