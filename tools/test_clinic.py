#!/usr/bin/env python3
"""Exercise production clinic permissions/discharge without booting the world."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'src/institute.c').read_text()
production = source[source.index('  bool clinic_patient('):source.index('  bool college_staff(')]
stubs = r'''
#include "merc.h"
#include <cassert>
#include <cstring>
std::vector<INSTITUTE_TYPE *> InVect;
FACTION_TYPE society = {};
ROOM_INDEX_DATA discharge = {};
int saves = 0;
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
bool same_player(CHAR_DATA *a, CHAR_DATA *b) { return a == b; }
bool asylum_room(ROOM_INDEX_DATA *r) { return r && r->subarea && !strcmp(r->subarea, "clinic"); }
FACTION_TYPE *clan_lookup(int id) { return id == 123 ? &society : nullptr; }
ROOM_INDEX_DATA *get_room_index(int id) { return id == ROOM_INDEX_CLINICDISCHARGE ? &discharge : nullptr; }
void char_from_room(CHAR_DATA *ch) { ch->in_room = nullptr; }
void char_to_room(CHAR_DATA *ch, ROOM_INDEX_DATA *r) { ch->in_room = r; }
void save_institutes(bool) { ++saves; }
void send_to_char(const char *, CHAR_DATA *) {}
'''
tests = r'''
int main() {
  CHAR_DATA patient = {}, sponsor = {}, stranger = {};
  patient.name = (char *)"Patient"; sponsor.name = (char *)"Sponsor";
  stranger.name = (char *)"Stranger";
  ROOM_INDEX_DATA clinic = {}, outside = {};
  clinic.subarea = (char *)"clinic"; patient.in_room = &clinic;
  INSTITUTE_TYPE ins = {};
  ins.name = patient.name; ins.asylum_owner = sponsor.name;
  ins.asylum_prestige = 100; ins.asylum_status = ASYLUM_REMOTECOMMIT;
  InVect.push_back(&ins);
  assert(clinic_execution_allowed(&sponsor, &patient));
  assert(!clinic_execution_allowed(&stranger, &patient));
  assert(!clinic_execution_allowed(&patient, &patient));
  society.name = (char *)"Society"; ins.asylum_owner = society.name;
  sponsor.faction = 123;
  assert(clinic_execution_allowed(&sponsor, &patient));
  sponsor.faction = 0; sponsor.factiontwo = 123;
  assert(clinic_execution_allowed(&sponsor, &patient));
  ins.asylum_status = ASYLUM_SELFCOMMIT;
  assert(!clinic_execution_allowed(&sponsor, &patient));
  ins.asylum_status = ASYLUM_COLLEGECOMMIT;
  assert(!clinic_execution_allowed(&sponsor, &patient));
  patient.in_room = &outside;
  assert(clinic_execution_allowed(&stranger, &patient));
  patient.in_room = &clinic;
  SET_FLAG(patient.act, PLR_BOUND); SET_FLAG(patient.act, PLR_BOUNDFEET);
  release_clinic_after_respawn(&patient);
  assert(!clinic_patient(&patient) && ins.asylum_inactive == 1 && ins.asylum_status == 0);
  assert(patient.in_room == &discharge && saves == 1);
  assert(!IS_FLAG(patient.act, PLR_BOUND) && !IS_FLAG(patient.act, PLR_BOUNDFEET));
  release_clinic_after_respawn(&patient); assert(saves == 1);
  ins.asylum_inactive = 0; ins.clinic_breakout = 180;
  patient.in_room = &outside;
  release_clinic_after_respawn(&patient);
  assert(ins.clinic_breakout == 0 && ins.asylum_inactive == 1 && saves == 2);
  assert(patient.in_room == &outside);
  puts("PASS: sponsor-only execution, self/college admissions, outside-clinic behavior, discharge location, restraints, breakouts, and repeated release.");
}
'''
with tempfile.TemporaryDirectory(prefix='haven-clinic-') as temp:
    path = Path(temp)
    (path / 'test.cc').write_text(stubs + production + tests)
    subprocess.run(['g++', '-std=gnu++17', '-Wno-write-strings', '-Wno-deprecated',
                    '-I', str(ROOT / 'src'), str(path / 'test.cc'), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
