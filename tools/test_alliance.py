#!/usr/bin/env python3
"""Run production alliance helpers with engine stubs under ASan/UBSan.

Run in Linux/WSL: python3 tools/test_alliance.py. No game data is accessed.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
clans = (ROOT / 'src/clans.c').read_text()
world = (ROOT / 'src/world.c').read_text()


def section(source, start, end):
    a = source.index(start)
    return source[a:source.index(end, a)]


stubs = r'''
#include "merc.h"
#include <cassert>
#include <climits>
#include <cmath>
#include <cstring>
using std::vector;
vector<FACTION_TYPE *> FacVect;
vector<LOCATION_TYPE *> locationVect;
TIME_INFO_DATA time_info = {};
int messages = 0;
bool generic_faction_vnum(int id) {
  return id == FACTION_CORTEX || id == FACTION_ORDER || id == FACTION_SCUM;
}
int fac_power(FACTION_TYPE *fac) { return fac->resource; }
void send_message(int, char *) { ++messages; }
FACTION_TYPE *clan_lookup(int id) {
  for (auto *fac : FacVect) if (fac && fac->vnum == id) return fac;
  return nullptr;
}
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
'''

production = '\n'.join([
    section(clans, '  bool alliance_eligible(', '  int fac_power('),
    section(clans, '  static bool alliance_participant(', '  bool faction_hardelligible('),
    section(clans, '  int alliance_position(', '  int faction_secrecy('),
    section(clans, '  bool char_in_alliance_with(', '  bool has_base('),
    section(world, '  bool is_territory_support(', '  static int territory_reward('),
    section(world, '  void territory_plus(', '  void antagonist_plus('),
    section(world, '  void territory_minus(', '  void antagonist_minus('),
    section(world, '  static void format_territory_support(', '  void show_territory_to_char('),
])

tests = r'''
FACTION_TYPE faction(int id, int side, int type = FACTION_SOCIETY) {
  FACTION_TYPE fac = {};
  fac.vnum = id; fac.alliance = side; fac.type = type;
  fac.resource = 100; fac.lifeearned = 300;
  for (int &axis : fac.axes) axis = AXES_NEUTRAL;
  for (int &power : fac.member_power) power = 100;
  return fac;
}
int main() {
  static_assert(ALLIANCE_COUNT == 2, "Exactly two alliance sides");
  auto left = faction(100, ALLIANCE_SIDELEFT);
  auto right = faction(101, ALLIANCE_SIDERIGHT);
  auto middle = faction(102, 2);
  auto sect = faction(103, 2, FACTION_SOCIETY);
  auto opted_out = faction(104, 2); opted_out.nopart = 1;
  auto core = faction(105, FACTION_CORTEX, FACTION_CORE);
  auto hand = faction(FACTION_CORTEX, FACTION_CORTEX, FACTION_CORE);
  LOCATION_TYPE loc = {}; loc.valid = TRUE;
  // Historical Phil records retain all twenty positions, including core data.
  const char *saved = "0 20 31 30 0 71 72 73 0 0 0 99 9 98 0 0 0 0 0 0";
  std::istringstream old_record(saved);
  for (int &value : loc.phil_amount) old_record >> value;
  loc.colour = 12;
  locationVect = {&loc};
  FacVect = {&left, &right, &middle, &sect, &opted_out, &core, &hand};
  time_info.society_alliance_issue = AXES_CORRUPT;
  middle.axes[AXES_CORRUPT] = AXES_NEARLEFT;
  sect.axes[AXES_CORRUPT] = AXES_NEARRIGHT;
  normalize_alliance_data();
  assert(left.alliance == ALLIANCE_SIDELEFT && right.alliance == ALLIANCE_SIDERIGHT);
  assert(middle.alliance == ALLIANCE_SIDELEFT && sect.alliance == ALLIANCE_SIDERIGHT);
  assert(opted_out.alliance == ALLIANCE_NONE && core.alliance == FACTION_CORTEX);
  assert(is_alliance(faction_alliance(&core)) && is_alliance(faction_alliance(&hand)));
  assert(same_strategic_alliance(&core, &hand) == (core.strategic_alliance == hand.strategic_alliance));
  assert(middle.member_power[0] == 100 && middle.lifeearned == 300 && messages == 0);
  assert(loc.phil_amount[1] == 100 && loc.phil_amount[3] == 100 && loc.phil_amount[2] == 0);
  assert(loc.phil_amount[11] == 0 && loc.phil_amount[13] == 0 && loc.phil_amount[12] == 0);
  assert(loc.phil_amount[5] == 71 && loc.phil_amount[6] == 72 && loc.phil_amount[7] == 73);
  int before[TERRITORY_SUPPORT_SLOTS]; memcpy(before, loc.phil_amount, sizeof(before));
  normalize_alliance_data(); // Reloading a migrated record cannot add support.
  assert(memcmp(before, loc.phil_amount, sizeof(before)) == 0);
  std::ostringstream new_record;
  for (int value : loc.phil_amount) new_record << value << ' ';
  LOCATION_TYPE reloaded = {};
  std::istringstream input(new_record.str());
  for (int &value : reloaded.phil_amount) input >> value;
  assert(memcmp(before, reloaded.phil_amount, sizeof(before)) == 0);

  assert(!is_alliance(0) && !is_alliance(2) && !is_alliance(9));
  assert(opposing_alliance(ALLIANCE_SIDELEFT) == ALLIANCE_SIDERIGHT);
  assert(opposing_alliance(ALLIANCE_NONE) == ALLIANCE_NONE);
  assert(get_alliance(nullptr, 1) == ALLIANCE_NONE);
  left.axes[AXES_CORRUPT] = AXES_DEMONIC;
  assert(get_alliance(&left, AXES_CORRUPT) == ALLIANCE_SIDELEFT);
  left.axes[AXES_CORRUPT] = AXES_FARLEFT;
  assert(get_alliance(&left, -1) == ALLIANCE_NONE && get_alliance(&left, AXES_MAX+1) == ALLIANCE_NONE);
  for (int axis = 1; axis <= AXES_MAX; ++axis) {
    for (int position = AXES_FARLEFT; position <= AXES_FARRIGHT; ++position) {
      middle.axes[axis] = position;
      assert(is_alliance(get_alliance(&middle, axis)));
    }
  }
  middle.axes[1] = 0; assert(get_alliance(&middle, 1) == ALLIANCE_NONE);
  middle.axes[1] = AXES_NEUTRAL; middle.alliance = ALLIANCE_NONE;
  assert(get_alliance(&middle, 1) == ALLIANCE_SIDELEFT);
  auto neutral = faction(107, ALLIANCE_NONE);
  assert(get_alliance(&neutral, 1) == ALLIANCE_SIDERIGHT);
  auto neutral_reload = neutral;
  assert(get_alliance(&neutral_reload, 1) == ALLIANCE_SIDERIGHT);
  assert(get_alliance(&right, 1) == ALLIANCE_SIDERIGHT);
  assert(!same_alliance(nullptr, &left));
  assert(!same_alliance(&left, &right));
  assert(!same_alliance(&middle, &opted_out));
  assert(same_alliance(&right, &sect)); // All societies use one alliance pool.
  assert(same_alliance(&core, &hand));
  assert(same_alliance(&opted_out, &opted_out)); // Same society still cooperates.
  CHAR_DATA ch = {}; ch.faction = left.vnum; ch.factiontwo = sect.vnum;
  assert(!char_in_alliance_with(&ch, 9999));
  assert(char_in_alliance_with(&ch, sect.vnum));
  assert(faction_support_slot(&sect) == 3 && faction_support_slot(&core) == FACTION_CORTEX);
  assert(faction_support_slot(&opted_out) == -1);
  for (int slot : {INT_MIN, -1, 0, 2, 4, 9, 10, 11, 12, 13, 19, 20, INT_MAX}) {
    assert(!is_territory_support(slot));
    territory_plus(&loc, slot); territory_minus(&loc, slot);
  }
  assert(memcmp(before, loc.phil_amount, sizeof(before)) == 0);
  territory_plus(nullptr, 1); territory_minus(nullptr, 1);
  territory_plus(&loc, 11); assert(loc.phil_amount[11] == 0);
  char display[1024]; format_territory_support(display, sizeof(display), &loc);
  assert(strstr(display, "Balanced") == nullptr);
  assert(strstr(display, "Society Support:") && !strstr(display, "Sect Support:"));
  assert(strstr(display, "The Cortex") && strstr(display, "The Order") && strstr(display, "The Scum"));
  char small[4]; format_territory_support(small, sizeof(small), &loc); assert(small[3] == '\0');
  assert(!clan_in_alliance(&opted_out, const_cast<char *>("Balanced")));
  assert(clan_in_alliance(&right, alliance_names(AXES_CORRUPT, ALLIANCE_SIDERIGHT)));

  // A rebalance must change only participating societies and apply territory
  // decay once, independent of how many societies switch sides.
  auto a = faction(200, ALLIANCE_SIDELEFT), b = faction(201, ALLIANCE_SIDELEFT);
  auto c = faction(202, ALLIANCE_SIDELEFT), d = faction(203, ALLIANCE_SIDELEFT);
  for (auto *fac : {&a, &b, &c, &d}) {
    for (int &axis : fac->axes) axis = AXES_FARLEFT;
  }
  c.axes[AXES_MATERIAL] = d.axes[AXES_MATERIAL] = AXES_FARRIGHT;
  auto dormant = faction(204, ALLIANCE_SIDERIGHT); dormant.stasis = 1;
  FacVect = {&a, &b, &c, &d, &opted_out, &dormant, &core};
  time_info.society_alliance_issue = AXES_CORRUPT;
  core.strategic_alliance = ALLIANCE_SIDELEFT;
  assert(currentalliancebalance(FACTION_CORE) == static_cast<int>(500 * sqrt(500)));
  core.nopart = 1; // Preserve the original four-society balance fixture below.
  loc.phil_amount[1] = loc.phil_amount[3] = 80;
  assert(currentalliancebalance(FACTION_SOCIETY) == 8000);
  assert(minalliancebalance(FACTION_SOCIETY) == 0);
  new_alliance(FACTION_SOCIETY);
  assert(time_info.society_alliance_issue == AXES_MATERIAL);
  assert(c.alliance == ALLIANCE_SIDERIGHT && d.alliance == ALLIANCE_SIDERIGHT);
  assert(messages == 2 && c.member_power[0] == 10 && a.member_power[0] == 100);
  assert(loc.phil_amount[1] == 40 && loc.phil_amount[3] == 40);
  assert(loc.phil_amount[11] == 0 && loc.phil_amount[FACTION_CORTEX] == 71);
  assert(dormant.member_power[0] == 100 && opted_out.alliance == ALLIANCE_NONE);
  new_alliance(FACTION_SOCIETY);
  assert(messages == 2 && loc.phil_amount[1] == 40 && c.member_power[0] == 10);
  assert(alliance_position(&a) == 1 && alliance_position(&c) == 2);
  assert(alliance_position(&opted_out) == 0);
  for (auto *fac : {&a, &b, &c, &d}) fac->resource = INT_MAX;
  c.alliance = d.alliance = ALLIANCE_SIDELEFT;
  assert(currentalliancebalance(FACTION_SOCIETY) == INT_MAX);
  FacVect.clear(); assert(minalliancebalance(FACTION_SOCIETY) == 0);
  new_alliance(FACTION_CORE); assert(messages == 2);
  time_info.society_alliance_issue = INT_MAX;
  normalize_alliance_data();
  assert(time_info.society_alliance_issue == AXES_CORRUPT);
  puts("Alliance migration, relationships, displays, and rebalance checks passed.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-alliance-') as temporary:
    path = Path(temporary)
    source = path / 'alliance_test.cc'
    source.write_text('#include <sstream>\n' + stubs.replace('messages', 'message_count')
                      + production + tests.replace('messages', 'message_count'))
    executable = path / 'alliance_test'
    subprocess.run(['g++', '-std=gnu++17', '-g', '-O1', '-Wno-write-strings',
                    '-Wno-deprecated', '-fsanitize=address,undefined',
                    '-fno-omit-frame-pointer', '-no-pie', '-I', str(ROOT / 'src'),
                    str(source), '-o', str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
