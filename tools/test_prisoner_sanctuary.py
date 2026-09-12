#!/usr/bin/env python3
"""Exercise the restored prisoner timer and production autorelease in WSL/Linux."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
update = (ROOT / 'src/update.c').read_text()
skills = (ROOT / 'src/skills.c').read_text()


def section(source, start, end):
    a = source.index(start)
    return source[a:source.index(end, a)]


source = r'''
#include "merc.h"
#include <cassert>
time_t current_time = 1000000;
int event_cleanse = 0, moves = 0;
bool haven = true, sanctuary = true, trapped = false;
bool prisoner = true, student = false, patient = false;
ROOM_INDEX_DATA cell = {}, institute = {}, exercise = {}, street = {};
std::vector<EVENT_TYPE *> EventVect;
DescList descriptor_list;
bool in_haven(ROOM_INDEX_DATA *) { return haven; }
bool under_understanding(CHAR_DATA *, CHAR_DATA *) { return sanctuary; }
bool trapped_room(ROOM_INDEX_DATA *, CHAR_DATA *) { return trapped; }
bool institute_room(ROOM_INDEX_DATA *r) { return r == &institute; }
bool clinic_patient(CHAR_DATA *) { return patient; }
bool college_student(CHAR_DATA *, bool) { return student; }
bool is_prisoner(CHAR_DATA *) { return prisoner; }
int number_range(int a, int) { return a; }
ROOM_INDEX_DATA *room_by_coordinates(int, int, int) { return &street; }
ROOM_INDEX_DATA *sourced_room_by_coordinates(ROOM_INDEX_DATA *, int, int, int, bool) { return &street; }
ROOM_INDEX_DATA *get_room_index(int vnum) { assert(vnum == 16295); return &exercise; }
void char_from_room(CHAR_DATA *ch) { ch->in_room = nullptr; }
void char_to_room(CHAR_DATA *ch, ROOM_INDEX_DATA *r) { ch->in_room = r; ++moves; }
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
void dact(const char *, CHAR_DATA *, const void *, const void *, int) {}
'''
source += section(update, '  void autorelease(', '  CHAR_DATA *fetch_guestmonster(')
source += 'void prisoner_tick(CHAR_DATA *ch) {\n'
source += section(update, '      // Restore the original sanctuary prisoner-care',
                  '      if (in_fight(ch) && ch->fight_fast == FALSE')
source += '}\nvoid care_deadline(CHAR_DATA *victim) {\n'
source += section(skills, '    victim->pcdata->prison_care = UMAX(',
                  '    save_char_obj(victim, FALSE, FALSE);')
source += r'''
}
int main() {
  CHAR_DATA ch = {}, companion = {}, elsewhere = {};
  PC_DATA pc = {}, companion_pc = {}, elsewhere_pc = {};
  ch.pcdata = &pc; companion.pcdata = &companion_pc; elsewhere.pcdata = &elsewhere_pc;
  auto reset = [&]() {
    pc.prison_mult = 0; pc.prison_care = 0; pc.travel_time = -1;
    ch.in_room = &cell; ch.wait = 0; moves = 0;
    REMOVE_FLAG(ch.act, PLR_BOUND); REMOVE_FLAG(ch.act, PLR_BOUNDFEET);
    REMOVE_FLAG(ch.comm, COMM_BLINDFOLD);
    haven = sanctuary = prisoner = true;
    trapped = student = patient = false; event_cleanse = 0;
    EventVect.clear(); descriptor_list.clear();
  };
  // Each original captivity trigger starts a five-hour grace period.
  for (int kind = 0; kind < 3; ++kind) {
    reset();
    if (kind == 0) SET_FLAG(ch.act, PLR_BOUND);
    if (kind == 1) SET_FLAG(ch.act, PLR_BOUNDFEET);
    if (kind == 2) trapped = true;
    prisoner_tick(&ch);
    assert(pc.prison_mult == 1 && pc.prison_care == current_time + 5 * 3600);
    current_time = pc.prison_care;
    prisoner_tick(&ch); assert(moves == 0); // Strictly after the deadline.
    ++current_time;
    prisoner_tick(&ch); assert(moves == 1 && ch.in_room == &street);
    assert(!IS_FLAG(ch.act, PLR_BOUND) && !IS_FLAG(ch.act, PLR_BOUNDFEET));
  }
  // Care extends an existing deadline, capped at twenty hours from now.
  reset(); SET_FLAG(ch.act, PLR_BOUND); prisoner_tick(&ch);
  care_deadline(&ch);
  assert(pc.prison_care == current_time + 17 * 3600 && pc.prison_mult == 3);
  care_deadline(&ch);
  assert(pc.prison_care == current_time + 20 * 3600 && pc.prison_mult == 9);
  current_time += 19 * 3600; prisoner_tick(&ch); assert(moves == 0);
  current_time += 3601; prisoner_tick(&ch); assert(moves == 1);
  reset(); pc.prison_mult = 1; pc.prison_care = current_time - 1;
  care_deadline(&ch); assert(pc.prison_care == current_time + 12 * 3600);
  // Outside eligibility the original logic rolls the deadline to fourteen hours.
  for (int reason = 0; reason < 4; ++reason) {
    reset(); SET_FLAG(ch.act, PLR_BOUND);
    pc.prison_mult = 3; pc.prison_care = current_time - 1;
    if (reason == 0) haven = false;
    if (reason == 1) sanctuary = false;
    if (reason == 2) event_cleanse = 1;
    if (reason == 3) REMOVE_FLAG(ch.act, PLR_BOUND);
    prisoner_tick(&ch);
    assert(moves == 0 && pc.prison_care == current_time + 14 * 3600);
    assert(pc.prison_mult == 3);
  }
  // Preserve the historical event window: scheduled, not already-started events.
  for (int type : {EVENT_UNDERSTANDINGMINUS, EVENT_CLEANSE}) {
    for (bool secondary : {false, true}) {
      reset(); SET_FLAG(ch.act, PLR_BOUND);
      EVENT_TYPE event = {};
      event.valid = true; event.active_time = current_time + 60;
      event.deactive_time = current_time + 120;
      if (secondary) event.typetwo = type; else event.type = type;
      EventVect.push_back(&event);
      event.valid = false; prisoner_tick(&ch); assert(moves == 0);
      event.valid = true; event.active_time = current_time - 1;
      prisoner_tick(&ch); assert(moves == 0);
      event.active_time = current_time + 60; event.deactive_time = current_time - 1;
      prisoner_tick(&ch); assert(moves == 0);
      event.deactive_time = current_time + 120;
      prisoner_tick(&ch); assert(moves == 1);
    }
  }
  // The existing release routine removes both restraints and blindfolds.
  // Cortex Academy of Civic Integration students/patients go to exercise room 16295.
  for (bool as_patient : {false, true}) {
    reset(); ch.in_room = &institute;
    student = !as_patient; patient = as_patient;
    SET_FLAG(ch.act, PLR_BOUND); SET_FLAG(ch.act, PLR_BOUNDFEET);
    SET_FLAG(ch.comm, COMM_BLINDFOLD);
    pc.prison_mult = 1; pc.prison_care = current_time - 1;
    prisoner_tick(&ch);
    assert(ch.in_room == &exercise && moves == 1 && pc.travel_time == 0);
    assert(!IS_FLAG(ch.act, PLR_BOUND) && !IS_FLAG(ch.act, PLR_BOUNDFEET));
    assert(!IS_FLAG(ch.comm, COMM_BLINDFOLD) && ch.wait == PULSE_PER_SECOND * 5);
  }
  // Original non-prisoner rescue moves all connected occupants of the room.
  reset(); prisoner = false; trapped = true;
  companion.in_room = &cell; elsewhere.in_room = &exercise;
  DESCRIPTOR_DATA d = {}, d2 = {}, d3 = {};
  d.character = &ch; d2.character = &companion; d3.character = &elsewhere;
  d.connected = d2.connected = d3.connected = CON_PLAYING;
  descriptor_list.push_back(&d); descriptor_list.push_back(&d2); descriptor_list.push_back(&d3);
  SET_FLAG(companion.act, PLR_BOUNDFEET); SET_FLAG(companion.comm, COMM_BLINDFOLD);
  pc.prison_mult = 1; pc.prison_care = current_time - 1;
  prisoner_tick(&ch);
  assert(ch.in_room == &street && companion.in_room == &street && elsewhere.in_room == &exercise);
  assert(moves == 2 && !IS_FLAG(companion.act, PLR_BOUNDFEET));
  assert(!IS_FLAG(companion.comm, COMM_BLINDFOLD));
  descriptor_list.clear();
  puts("PASS: prisoner grace/expiry, care extension/cap, eligibility, historical events, restraints, institute and room-wide rescue.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-prisoner-sanctuary-') as tmp:
    path = Path(tmp)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-Wno-write-strings', '-Wno-deprecated',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-no-pie',
                    '-I', str(ROOT / 'src'), str(path / 'test.cc'), '-o', str(path / 'test')],
                   check=True)
    subprocess.run([str(path / 'test')], check=True)
