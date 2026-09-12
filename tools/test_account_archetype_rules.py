#!/usr/bin/env python3
"""Check retired archetypes, contract membership, and production account defaults."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def section(file, start, end):
    text = (ROOT / 'src' / file).read_text()
    begin = text.index(start)
    return text[begin:text.index(end, begin)]


source = r'''
#include "merc.h"
#include <cassert>
#include <cstdlib>
#include <cstring>
#include <vector>
time_t current_time = 0;
std::vector<void *> allocations;
void *alloc_perm(size_t size) {
  void *p = malloc(size); allocations.push_back(p); return p;
}
char *str_dup(const char *s) {
  char *p = strdup(s); allocations.push_back(p); return p;
}
void SET_INIT(SET s) { memset(s, 0, sizeof(SET)); }
void send_to_char(const char *, CHAR_DATA *) {}
'''
source += section('recycle.c', '  ACCOUNT_TYPE *new_account(void)', '  void free_account(')
source += section('lookup.c', '  int available_karma(', '  void gain_personal_karma(')
source += section('skills.c', '  bool has_requirements(', '    if (skill == SKILL_MENTALDISCIPLINE')
source += 'return TRUE; }\n'
source += r'''
int main() {
  const auto &brown = race_table[RACE_BROWN];
  assert(brown.vnum == RACE_BROWN);
  assert(!brown.pc_race && !brown.creatable && !brown.change_to);
  assert(race_table[RACE_STUDENT].creatable);
  CHAR_DATA ch = {};
  for (int faction : {0, FACTION_ORDER, FACTION_SCUM, FACTION_CORTEX}) {
    ch.fcore = faction;
    for (bool show : {false, true}) {
      assert(has_requirements(&ch, SKILL_COLLEGECONTRACT, 1, show)
             == (faction == FACTION_CORTEX));
      assert(has_requirements(&ch, SKILL_CLINICCONTRACT, 1, show));
    }
  }
  ACCOUNT_TYPE *account = new_account();
  assert(account->karma == 0 && account->pkarma == 0);
  assert(account->karmabank == 0 && account->karmaearned == 0);
  assert(account->pkarmaspent == 0 && account->pkarma_remainder == 0);
  PC_DATA pc = {};
  ch.pcdata = &pc;
  pc.account = account;
  assert(available_karma(&ch) == 0);
  account->karma = 1200;
  ch.karma = 300;
  assert(available_karma(&ch) == 1200);
  pc.account = nullptr;
  assert(available_karma(&ch) == 300);
  ch.karma = 0;
  assert(available_karma(&ch) == 0);
  pc.account = account;
  SET_FLAG(ch.act, PLR_GUEST);
  assert(available_karma(&ch) == 0);
  for (void *p : allocations) free(p);
  puts("Archetype availability, Cortex contract eligibility, and zero account karma passed.");
}
'''
with tempfile.TemporaryDirectory(prefix='haven-account-rules-') as tmp:
    path = Path(tmp)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-ffunction-sections',
                    '-fdata-sections', '-Wl,--gc-sections',
                    '-fsanitize=address,undefined', '-no-pie', '-I', str(ROOT / 'src'),
                    str(path / 'test.cc'), str(ROOT / 'src/tables.c'),
                    str(ROOT / 'src/bit.c'),
                    '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
