#!/usr/bin/env python3
"""Exercise production focus prerequisites and tables with isolated characters (WSL)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def section(file, start, end):
    source = (ROOT / 'src' / file).read_text()
    offset = source.index(start)
    return source[offset:source.index(end, offset)]


source = '''
#include "merc.h"
#include <cassert>
#include <cstdio>
int event_cleanse = 0;
bool college_student(CHAR_DATA *, bool) { return false; }
void send_to_char(const char *, CHAR_DATA *) {}
void printf_to_char(CHAR_DATA *, const char *, ...) {}
int get_skill(CHAR_DATA *ch, int skill) { return ch->skills[skill]; }
int regress_mod(CHAR_DATA *, int) { return 0; }
int get_tier(CHAR_DATA *) { return 5; }
int get_age(CHAR_DATA *) { return 40; }
int get_real_age(CHAR_DATA *) { return 40; }
int get_true_age(CHAR_DATA *) { return 40; }
int human_cap(int) { return 5; }
int npc_cost(CHAR_DATA *) { return 0; }
bool allow_arcane = true;
bool can_train_arcane_focus(CHAR_DATA *) { return allow_arcane; }
'''
for name in ('guestmonster', 'higher_power', 'is_abom',
             'is_angelborn', 'is_demigod', 'is_faeborn', 'is_sufferingsensitive',
             'is_undead', 'is_vampire', 'is_werewolf'):
    source += f'bool {name}(CHAR_DATA *) {{ return false; }}\n'
for name in ('is_super', 'is_demonborn', 'can_train_combat_focus',
             'can_train_prof_focus'):
    source += f'bool {name}(CHAR_DATA *) {{ return true; }}\n'
source += section('tables.c', 'const struct skill_type skill_table[]',
                  'const int skill_table_count')
source += 'const int skill_table_count = sizeof(skill_table) / sizeof(skill_table[0]);\n'
source += section('skills.c', '  int skilltype(int skill)', '  int disciplinetype(')
source += section('skills.c', '  int raw_skillcount(', '  bool can_raise(')
source += section('skills.c', '  int skillbase_count(', '  int skillpointer(')
source += section('lookup.c', '  int focus_power_level(', '  int get_skill(CHAR_DATA *ch, int skill)')
source += section('lookup.c', '  int focuscount(', '  int npc_cost(')
source += section('lookup.c', '  int combat_focus(', '  bool nowindows(')
source += section('skills.c', '  bool has_requirements(', '  bool can_train_disc(')
source += r'''
int main() {
  static_assert(DEFAULT_MAXEXP == 3000000, "Starting combat cap");
  static_assert(DEFAULT_MAXRPEXP == 3000000, "Starting RPXP cap");
  CHAR_DATA ch = {};
  PC_DATA pc = {};
  ch.pcdata = &pc;
  ACCOUNT_TYPE account = {};
  pc.account = &account;
  assert(skilltype(SKILL_PSYCHICFOCUS) == STYPE_ARCANEFOCUS);
  pc.dexp = 0;
  assert(has_requirements(&ch, SKILL_PSYCHICFOCUS, 1, false));
  ch.skills[SKILL_PSYCHICFOCUS] = 1;
  assert(arcane_focus(&ch) == 1);
  assert(has_requirements(&ch, SKILL_PSYCHICFOCUS, 2, false));
  ch.skills[SKILL_PSYCHICFOCUS] = 2;
  assert(arcane_focus(&ch) == 2);
  for (int i = 0; i < skill_table_count; ++i)
    if (skill_table[i].vnum == SKILL_PSYCHICFOCUS)
      assert(skill_table[i].levels[1] == 2 && skill_table[i].levels[2] == 3 && skill_table[i].levels[3] == 0);
  pc.dexp = 0;
  ch.skills[SKILL_PSYCHICFOCUS] = 1;
  assert(!has_requirements(&ch, SKILL_TELEMPATHY, 1, false));
  ch.skills[SKILL_PSYCHICFOCUS] = 2;
  assert(has_requirements(&ch, SKILL_TELEMPATHY, 1, false));
  assert(!has_requirements(&ch, SKILL_TELEPATHY, 1, false));
  assert(has_requirements(&ch, SKILL_PSYCHICFOCUS, 3, false));
  ch.skills[SKILL_PSYCHICFOCUS] = 3;
  assert(arcane_focus(&ch) == 3);
  assert(has_requirements(&ch, SKILL_TELEPATHY, 1, false));
  assert(skilltype(SKILL_PSYCHIC) == STYPE_SABILITIES);
  for (int i = 0; i < skill_table_count; ++i)
    if (skill_table[i].vnum == SKILL_PSYCHIC)
      assert(skill_table[i].levels[0] == 1 && skill_table[i].levels[1] == 2 && skill_table[i].levels[2] == 0);
  ch.skills[SKILL_PSYCHICFOCUS] = 0;
  assert(!has_requirements(&ch, SKILL_PSYCHIC, 1, false));
  ch.skills[SKILL_PSYCHICFOCUS] = 1;
  assert(has_requirements(&ch, SKILL_PSYCHIC, 1, false));
  ch.skills[SKILL_PSYCHIC] = 1;
  assert(arcane_focus(&ch) == 1);
  assert(!has_requirements(&ch, SKILL_PSYCHIC, 2, false));
  ch.skills[SKILL_PSYCHICFOCUS] = 2;
  assert(has_requirements(&ch, SKILL_PSYCHIC, 2, false));
  ch.skills[SKILL_PSYCHIC] = 2;
  assert(arcane_focus(&ch) == 2);
  ch.skills[SKILL_PSYCHIC] = 0;
  allow_arcane = false;
  ch.skills[SKILL_PSYCHICFOCUS] = 0;
  assert(!has_requirements(&ch, SKILL_PSYCHICFOCUS, 1, false));
  allow_arcane = true;
  int trees = 0;
  for (int i = 0; i < skill_table_count; ++i) {
    int focus = skill_table[i].vnum;
    if (focus_power_level(focus, 3) != 4) continue;
    ++trees;
    assert(skill_table[i].levels[2] == 3);
    assert(skill_table[i].levels[3] == 0);
    assert(focus_power_level(focus, 2) == 2);
    ch.skills[focus] = 3;
    assert(focuscount(&ch, skilltype(focus)) == 3);
    assert(get_skill(&ch, focus) == 3);
    assert(!has_requirements(&ch, focus, 4, false));
    ch.skills[focus] = 4;
    assert(!has_requirements(&ch, focus, 5, false));
    for (int j = 0; j < skill_table_count; ++j) {
      int power = skill_table[j].vnum;
      int type = skilltype(power);
      if (type == STYPE_COMBATFOCUS || type == STYPE_ARCANEFOCUS || type == STYPE_PROFFOCUS)
        continue;
      for (int rank = 0; rank < 5; ++rank) {
        ch.skills[power] = rank;
        ch.skills[focus] = 3;
        bool at_three = has_requirements(&ch, power, rank + 1, false);
        ch.skills[focus] = 4;
        assert(at_three == has_requirements(&ch, power, rank + 1, false));
      }
      ch.skills[power] = 0;
    }
    ch.skills[focus] = 0;
  }
  assert(trees == 15);
  ch.skills[SKILL_DEMONWARRIORFOCUS] = 2;
  assert(!has_requirements(&ch, SKILL_DEMONMETABOL, 3, false));
  ch.skills[SKILL_DEMONWARRIORFOCUS] = 3;
  assert(has_requirements(&ch, SKILL_DEMONMETABOL, 3, false));
  assert(focus_power_level(SKILL_SCIENCEFOCUS, 3) == 3);
  assert(focus_power_level(SKILL_WARRIORFOCUS, 3) == 3);
  puts("All 15 focus trees preserve power eligibility at three points; caps and Demonic Metabolism passed.");
}
'''
with tempfile.TemporaryDirectory(prefix='haven-focus-') as directory:
    cpp = Path(directory) / 'focus.cpp'
    binary = Path(directory) / 'focus'
    cpp.write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-fsanitize=address,undefined', '-g', '-Wno-deprecated', '-Wno-write-strings', '-I', str(ROOT / 'src'),
                    str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
