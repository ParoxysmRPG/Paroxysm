#!/usr/bin/env python3
"""Run production personal-karma progression against isolated accounts (Linux/WSL)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
lookup = (ROOT / 'src/lookup.c').read_text()
start = lookup.index('  void gain_personal_karma(')
end = lookup.index('  void refresh_recolors(', start)
source = '#include "merc.h"\n#include <cassert>\n#include <climits>\n'
source += lookup[start:end]
source += r'''
int main() {
  CHAR_DATA ch = {};
  PC_DATA pc = {};
  ACCOUNT_TYPE account = {};
  ch.pcdata = &pc;
  pc.account = &account;
  for (int band = 0; band < 5; ++band) {
    account = {};
    account.pkarma = band * 10000;
    gain_personal_karma(&ch, 60);
    assert(account.pkarma == band * 10000 + 60 / (band + 1));
  }
  // One large award and many tiny awards must produce identical results.
  account = {};
  gain_personal_karma(&ch, 149999);
  assert(account.pkarma == 49999 && account.pkarma_remainder == 4);
  account = {};
  for (int i = 0; i < 149999; ++i) gain_personal_karma(&ch, 1);
  assert(account.pkarma == 49999 && account.pkarma_remainder == 4);
  gain_personal_karma(&ch, 1);
  assert(account.pkarma == 50000 && account.pkarma_remainder == 0);
  gain_personal_karma(&ch, INT_MAX);
  assert(account.pkarma == 50000);
  account = {};
  gain_personal_karma(&ch, INT_MAX);
  assert(account.pkarma == 50000 && account.pkarma_remainder == 0);
  // Spending and switching characters on the account retain the earning band.
  account = {};
  account.pkarma = 5000;
  account.pkarmaspent = 25000;
  ch.spentpkarma = 10000;
  gain_personal_karma(&ch, 400);
  assert(account.pkarma == 5100);
  ch.spentpkarma = 0;
  gain_personal_karma(&ch, 400);
  assert(account.pkarma == 5200);
  // Recover at least the character's spending from old reset account counters.
  account = {};
  ch.spentpkarma = 40000;
  gain_personal_karma(&ch, 5);
  assert(account.pkarmaspent == 40000 && account.pkarma == 1);
  gain_personal_karma(&ch, INT_MAX);
  assert(account.pkarma == 10000 && available_pkarma(&ch) == 10000);
  account.pkarma = 60000;
  gain_personal_karma(&ch, 1000);
  assert(account.pkarma == 60000); // Do not confiscate existing balances.
  ch.spentpkarma = 50001;
  assert(available_pkarma(&ch) == 0);
  ch.spentpkarma = 0;
  assert(available_pkarma(&ch) == 50000);
  account = {};
  gain_personal_karma(&ch, 0);
  gain_personal_karma(&ch, -100);
  assert(account.pkarma == 0);
  SET_FLAG(ch.act, PLR_GUEST);
  gain_personal_karma(&ch, 1000);
  assert(account.pkarma == 0 && available_pkarma(&ch) == 0);
  REMOVE_FLAG(ch.act, PLR_GUEST);
  pc.account = NULL;
  gain_personal_karma(&ch, 1000);
  ch.pkarma = 60000;
  assert(available_pkarma(&ch) == 50000);
  gain_personal_karma(NULL, 1000);
  static_assert(!ENCOUNTERS_ENABLED && !STORY_IDEAS_ENABLED, "Disabled features");
}
'''
with tempfile.TemporaryDirectory(prefix='haven-personal-karma-') as directory:
    cpp = Path(directory) / 'karma.cpp'
    binary = Path(directory) / 'karma'
    cpp.write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-fsanitize=address,undefined',
                    '-Wno-deprecated', '-Wno-write-strings', '-I', str(ROOT / 'src'),
                    str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print('Personal karma bands, rounding, cap, spending and exclusions passed.')
