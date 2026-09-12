#!/usr/bin/env python3
"""Exercise production monthly recolor accrual and universal shadow slots (WSL/Linux)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
lookup = (ROOT / 'src/lookup.c').read_text()
fight = (ROOT / 'src/fight.c').read_text()
source = '#include "merc.h"\n#include <cassert>\n#include <climits>\ntime_t current_time;\n'
source += lookup[lookup.index('  void refresh_recolors('):lookup.index('  int available_donated(')]
start = fight.index('  int find_free_shadow(')
source += fight[start:fight.index('\n  }', start) + 4]
source += r'''
void date(int year, int month, int day = 1) {
  struct tm utc = {};
  utc.tm_year = year - 1900;
  utc.tm_mon = month - 1;
  utc.tm_mday = day;
  current_time = timegm(&utc);
}
int main() {
  ACCOUNT_TYPE a = {};
  a.colours = 7;
  date(2026, 9);
  refresh_recolors(&a);
  assert(a.colours == 10); // Preserve legacy balance and grant first month.
  refresh_recolors(&a);
  assert(a.colours == 10); // Repeated access / another character on same account.
  --a.colours;
  date(2026, 9, 30);
  refresh_recolors(&a);
  assert(a.colours == 9); // Spending does not reset the monthly grant.
  date(2026, 10);
  refresh_recolors(&a);
  assert(a.colours == 12);
  date(2027, 2);
  refresh_recolors(&a);
  assert(a.colours == 24); // Offline months and year rollover.
  ACCOUNT_TYPE restored = {};
  restored.colours = a.colours;
  restored.recolor_month = a.recolor_month;
  refresh_recolors(&restored);
  assert(restored.colours == 24); // Restored persistence fields do not duplicate.
  date(2026, 12);
  refresh_recolors(&a);
  assert(a.colours == 24); // Clock rollback cannot double award.
  a = {};
  date(2027, 2);
  refresh_recolors(&a);
  assert(a.colours == 18); // Legacy account first returning six months in.
  a = {};
  a.recolor_month = 2027 * 12 + 1 - 1;
  refresh_recolors(&a);
  assert(a.colours == 3); // New accounts start in their creation month.
  a.colours = INT_MAX - 1;
  date(2027, 3);
  refresh_recolors(&a);
  assert(a.colours == INT_MAX); // Overflow cannot destroy accumulated balance.
  refresh_recolors(NULL);
  CHAR_DATA ch = {};
  PC_DATA pc = {};
  ch.pcdata = &pc;
  for (int i = 0; i < 20; ++i) {
    assert(find_free_shadow(&ch) == i);
    pc.shadow_attacks[i][0] = 1;
  }
  assert(find_free_shadow(&ch) == -1);
}
'''
with tempfile.TemporaryDirectory(prefix='haven-rewards-') as directory:
    cpp = Path(directory) / 'rewards.cpp'
    binary = Path(directory) / 'rewards'
    cpp.write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-fsanitize=address,undefined',
                    '-Wno-deprecated', '-Wno-write-strings', '-I', str(ROOT / 'src'),
                    str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
comm = (ROOT / 'src/comm.c').read_text()
assert 'KEY("ColourMonth", account->recolor_month, fread_number(fp));' in comm
assert 'fprintf(fp, "ColourMonth %d\\n", account->recolor_month);' in comm
for filename in ['act_comm.c', 'act_info.c', 'act_move.c', 'act_wiz.c', 'fight.c', 'skills.c']:
    text = (ROOT / 'src' / filename).read_text()
    assert 'available_donated(' not in text, filename
    assert 'account->donated <' not in text, filename
print('Monthly accrual, offline catch-up, rollover, shared balance, overflow, and all 20 shadow slots passed.')
