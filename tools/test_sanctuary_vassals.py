#!/usr/bin/env python3
"""Check vassal Sanctuary ownership in production eligibility/display functions."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
abominations = (ROOT / 'src/abominations.c').read_text()
start = abominations.index('  bool seems_under_limited(')
end = abominations.index('  _DOFUN(do_shadowcloak)', start)

source = r'''
#include "merc.h"
#include <cassert>
#include <cstring>

time_t current_time = 100;
std::vector<EVENT_TYPE *> EventVect;
ROOM_INDEX_DATA haven = {}, outside = {}, special = {};
bool population_blocked = false, feeding_blocked = false;
bool full_coverage = false;

bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
bool debt_blocks_sanctuary(CHAR_DATA *) { return false; }
bool sanctuary_population_blocked() { return population_blocked; }
bool feeding_blocks_sanctuary(CHAR_DATA *) { return feeding_blocked; }
bool under_understanding(CHAR_DATA *, CHAR_DATA *) { return full_coverage; }
bool seems_under_understanding(CHAR_DATA *, CHAR_DATA *) { return full_coverage; }
bool sanctuary_eligible(CHAR_DATA *, CHAR_DATA *, bool) { return false; }
bool seems_sanctuary_eligible(CHAR_DATA *, CHAR_DATA *, bool) { return false; }
bool in_haven(ROOM_INDEX_DATA *room) { return room == &haven; }
int in_world(CHAR_DATA *ch) { return ch->in_room->area->world; }
bool has_praestes(CHAR_DATA *, CHAR_DATA *) { return false; }
bool deepforest(ROOM_INDEX_DATA *) { return false; }
bool full_moon() { return false; }
bool guestmonster(CHAR_DATA *) { return false; }
'''
source += abominations[start:end]
source += r'''
int main() {
  AREA_DATA area = {}; area.world = WORLD_EARTH; area.vnum = 1;
  haven.area = outside.area = special.area = &area;
  haven.vnum = 100; outside.vnum = 101; special.vnum = 18999;
  CHAR_DATA protected_ch = {}, observer = {};
  PC_DATA protected_pc = {}, observer_pc = {};
  protected_ch.pcdata = &protected_pc; observer.pcdata = &observer_pc;
  protected_ch.name = (char *)"Protected"; observer.name = (char *)"Observer";
  protected_pc.fixation_name = observer_pc.fixation_name = (char *)"";
  protected_pc.understanding = observer_pc.understanding = (char *)"All";

  auto check = [&](bool expected) {
    assert(under_limited(&protected_ch, &observer) == expected);
    assert(seems_under_limited(&protected_ch, &observer) == expected);
  };
  // An attacker's/observer's membership never lends or removes coverage.
  // Both actual eligibility and the displayed aura belong to the first PC.
  for (int membership : {0, 17}) {
    protected_ch.vassal = membership;
    for (int observer_membership : {0, 18}) {
      observer.vassal = observer_membership;
      for (ROOM_INDEX_DATA *protected_room : {&haven, &outside, &special}) {
        protected_ch.in_room = protected_room;
        for (ROOM_INDEX_DATA *observer_room : {&haven, &outside}) {
          observer.in_room = observer_room;
          check(membership != 0 && protected_room == &haven);
        }
      }
    }
  }
  // The existing common restrictions and full-aura precedence still apply.
  protected_ch.vassal = 17; observer.vassal = 0;
  protected_ch.in_room = observer.in_room = &haven;
  population_blocked = true; check(false); population_blocked = false;
  feeding_blocked = true; check(false); feeding_blocked = false;
  protected_pc.understanding = (char *)"None"; check(false);
  protected_pc.understanding = (char *)"All";
  full_coverage = true; check(false); full_coverage = false;
  check(true);
  puts("PASS: vassal Sanctuary and aura use the protected character's affiliation/location, with asymmetric actors and existing restrictions.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-sanctuary-vassals-') as tmp:
    path = Path(tmp)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-Wno-write-strings', '-Wno-deprecated',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-no-pie',
                    '-I', str(ROOT / 'src'), str(path / 'test.cc'), '-o', str(path / 'test')],
                   check=True)
    subprocess.run([str(path / 'test')], check=True)
