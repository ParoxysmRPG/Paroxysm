#!/usr/bin/env python3
"""Compile and exercise production augmentation policies (run in WSL)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def section(file, start, end):
    source = (ROOT / 'src' / file).read_text()
    a = source.index(start)
    return source[a:source.index(end, a)]


source = r'''
#include "merc.h"
#include <cassert>
#include <string>
std::string output;
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
bool higher_power(CHAR_DATA *) { return false; }
bool guestmonster(CHAR_DATA *) { return false; }
bool is_super(CHAR_DATA *ch) { return race_table[ch->race].super; }
bool is_undead(CHAR_DATA *) { return false; }
int combat_focus(CHAR_DATA *) { return 0; }
int get_skill(CHAR_DATA *, int) { return 0; }
int get_tier(CHAR_DATA *ch) { return race_table[ch->race].tier; }
bool society_has_room(CHAR_DATA *ch) {
  return !ch->fcore && !ch->fsociety && !ch->legacy_society;
}
'''
source += section('lookup.c', '  bool elligible_modifier(', '  int focuscount(')
source += section('skills.c', '  bool can_train_disc(', '  int train_disc_cost(')
source += section('clans.c', '  bool player_faction_join_allowed(', '  /*Local Functions */')
# Run the departure guard before the original command's roster mutations.
source += 'void leave_cortex(CHAR_DATA *ch, int number) {\n'
source += section('clans.c', '      if (number == FACTION_CORTEX &&', '      if (ch->fcore == number) {')
source += 'ch->fcore = 0; }\n'
source += r'''
int main() {
  CHAR_DATA ch = {};
  for (int race : {RACE_CIVILIAN, RACE_LOCAL, RACE_VISITOR, RACE_STUDENT,
      RACE_SOLDIER, RACE_TIMESWEPT, RACE_WILDLING, RACE_DREAMCHILD,
      RACE_ELSEBORN, RACE_BROWN, RACE_IMPORTANT, RACE_DEPUTY, RACE_GIFTED,
      RACE_SFORCES, RACE_CELEBRITY, RACE_PILLAR, RACE_DABBLER}) {
    ch.race = race;
    for (int faction : {0, FACTION_SCUM, FACTION_CORTEX}) {
      ch.fcore = faction;
      assert(elligible_modifier(&ch, MODIFIER_TEMPLE) == (faction == FACTION_CORTEX));
    }
    ch.modifier = MODIFIER_TEMPLE;
    int cap = race_table[race].tier == 3 ? 20 : 10;
    ch.disciplines[DIS_TOUGHNESS] = cap - 2;
    ch.disciplines[DIS_BONES] = 1;
    assert(can_train_disc(&ch, DIS_TOUGHNESS));
    assert(can_train_disc(&ch, DIS_BONES));
    ch.disciplines[DIS_BONES] = 2;
    assert(!can_train_disc(&ch, DIS_TOUGHNESS));
    assert(!can_train_disc(&ch, DIS_BONES));
  }
  for (int race : {RACE_NEWVAMPIRE, RACE_VETWEREWOLF, RACE_ANIMAL}) {
    ch.race = race;
    assert(!elligible_modifier(&ch, MODIFIER_TEMPLE));
  }
  FACTION_TYPE scum = {}; scum.vnum = FACTION_SCUM; scum.type = FACTION_CORE;
  assert(!player_faction_join_allowed(&ch, &scum, true));
  assert(output.find("turn your body off") != std::string::npos);
  output.clear();
  leave_cortex(&ch, FACTION_CORTEX);
  assert(ch.fcore == FACTION_CORTEX);
  assert(output.find("turn your body off") != std::string::npos);
  ch.modifier = 0;
  assert(player_faction_join_allowed(&ch, &scum, true));
  leave_cortex(&ch, FACTION_CORTEX);
  assert(ch.fcore == 0);
  puts("Science Augmented eligibility, caps, and Cortex departure checks passed.");
}
'''
lookup = (ROOT / 'src/lookup.c').read_text()
assert 'MODIFIER_TEMPLE && no_tech(ch)' not in lookup
with tempfile.TemporaryDirectory(prefix='haven-augmentation-') as tmp:
    path = Path(tmp)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-ffunction-sections',
                    '-fdata-sections', '-Wl,--gc-sections', '-I', str(ROOT / 'src'),
                    str(path / 'test.cc'), str(ROOT / 'src/tables.c'),
                    '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
