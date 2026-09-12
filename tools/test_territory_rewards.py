#!/usr/bin/env python3
"""Exercise production territory rewards and NPC scheduling with engine stubs.
Run in WSL/Linux: python3 tools/test_territory_rewards.py
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
world = (ROOT / 'src/world.c').read_text()
clans = (ROOT / 'src/clans.c').read_text()

def section(source, start, end):
    a = source.index(start)
    return source[a:source.index(end, a)]

stubs = r"""
#include <algorithm>
#include <cassert>
#include <cctype>
#include <cstring>
#include <cstdio>
#include <set>
#include <string>
#include <vector>
#include <strings.h>
#include "const.h"
#include "alliance.h"
#include "territory_rewards.h"
#define TRUE true
#define FALSE false
using std::vector;
#undef IS_NPC
#undef LOWER
#undef UMAX
#define IS_NPC(c) ((c)->npc)
#define LOWER(c) std::tolower(c)
#define UMAX(a,b) std::max(a,b)
struct PC_DATA { int garage_cost[10] = {}, garage_typeone[10] = {}, deactivated_stats[10] = {}; int job_type_one = 0; };
struct CHAR_DATA {
  bool npc = false, monster = false;
  int faction = 0, factiontwo = 0, factiontrue = -1;
  int fcore = 0, fsociety = 0, legacy_society = 0;
  PC_DATA *pcdata = nullptr;
  int skills[1000] = {};
  int tier = 1, professional_focus = 0;
};
struct FACTION_TYPE {
  bool valid = true;
  int vnum = 0, antagonist = 0, stasis = 0, slot = -1, resource = 0;
  const char *name = "";
};
struct LOCATION_TYPE {
  bool valid = true;
  const char *name = "Test";
  int territory_bonus = 0, territory_bonus_secondary = 0, reward_controller = -1;
  int base_faction_core = 0, base_society = 0, base_society_secondary = 0;
  int reward_footholds[3] = {-1, -1, -1};
  int phil_amount[TERRITORY_SUPPORT_SLOTS] = {}, other_amount[10] = {};
  const char *other_name[10] = {};
};
struct OPERATION_TYPE { bool valid = true; int hour = 0, day = 0, faction = 0; };
std::vector<LOCATION_TYPE *> locationVect;
std::vector<FACTION_TYPE *> FacVect;
std::vector<OPERATION_TYPE *> OpVect;
int str_cmp(const char *a, const char *b) { return strcasecmp(a ? a : "", b ? b : ""); }
FACTION_TYPE *clan_lookup(int n) {
  for (auto f : FacVect) if (f->vnum == n) return f;
  return nullptr;
}
FACTION_TYPE *clan_lookup_name(const char *n) {
  for (auto f : FacVect) if (!str_cmp(f->name, n)) return f;
  return nullptr;
}
int faction_support_slot(const FACTION_TYPE *f) { return f ? f->slot : -1; }
bool generic_faction_vnum(int n) { return n == FACTION_CORTEX || n == FACTION_ORDER || n == FACTION_SCUM; }
void send_log(int, const char *) {}
bool forest_monster(CHAR_DATA *ch) { return ch->npc && ch->monster; }
int event_cleanse = 0;
bool is_neutralized(CHAR_DATA *) { return false; }
int skilltype(int skill) {
  switch (skill) {
    case SKILL_CPOLICE: case SKILL_CMILITARY: case SKILL_CGOVERNMENT:
    case SKILL_CMEDIA: case SKILL_CCRIMINAL: case SKILL_COCCULT:
    case SKILL_CHOMELESS: case SKILL_CCORTEX: case SKILL_CORDER:
    case SKILL_CSCUM: case SKILL_CSUBFACTION: return STYPE_CONTACTS;
    default: return skill == SKILL_LIGHTUP ? STYPE_SUPERNATURAL : STYPE_SKILLS;
  }
}
int get_tier(CHAR_DATA *ch) { return ch->tier; }
int prof_focus(CHAR_DATA *ch) { return ch->professional_focus; }
int focus_power_bonus(CHAR_DATA *, int) { return 0; }
void printf_to_char(CHAR_DATA *, const char *, ...) {}
int get_skill_without_territory(CHAR_DATA *ch, int skill) { return ch->skills[skill]; }
int soc_wealth_mod(CHAR_DATA *, bool) { return 0; }
int now = 0, saves = 0, warnings = 0;
bool target_available = true;
int get_hour(void *) { return now; }
int number_range(int low, int) { return low; }
void save_operations(bool) { ++saves; }
void log_string(const char *) { ++warnings; }
bool make_antag_op(FACTION_TYPE *fac, int hour, int days) {
  if (!target_available) return false;
  auto *op = new OPERATION_TYPE;
  op->hour = hour; op->day = days; op->faction = fac->vnum;
  OpVect.push_back(op);
  return true;
}
"""
code = stubs + section(world, '  bool is_territory_support(', '  void territory_plus(')
code += section((ROOT / 'src/lookup.c').read_text(), '  int get_skill(CHAR_DATA *ch, int skill)', '  bool is_unlit(')
skills = (ROOT / 'src/skills.c').read_text()
tables = (ROOT / 'src/tables.c').read_text()
contact_rows = re.findall(r'^\{SKILL_C(?:POLICE|MILITARY|GOVERNMENT|MEDIA|CRIMINAL|OCCULT|HOMELESS|CORTEX|ORDER|SCUM|SUBFACTION),.*$', tables, re.M)
assert len(contact_rows) == 11
code += 'struct SkillEntry { int vnum; const char *name; int levels[6]; };\n'
code += 'const SkillEntry skill_table[] = {\n' + '\n'.join(contact_rows) + '\n};\n'
code += 'const int skill_table_count = sizeof(skill_table) / sizeof(skill_table[0]);\n'
code += section(skills, '  int skillcount(', '  bool can_raise(')
# Exercise the actual purchase restrictions alongside effective skill reads.
contact_start = skills.rfind('    if (skilltype(skill) == STYPE_CONTACTS)', 0, skills.index('Employees cannot have contacts.'))
contact_end = skills.index('    if (skill == SKILL_DEMONOLOGY)', contact_start)
code += 'bool contact_purchase_allowed(CHAR_DATA *ch, int skill, int value) { bool show = false;\n'
code += skills[contact_start:contact_end] + '\nreturn true; }\n'
code += section(clans, '  bool is_operation(', '  static bool make_antag_op(')
code += section(clans, '  void faction_antagonist_update(void)', '  void faction_daily_update(')
travel = (ROOT / 'src/travel.c').read_text()
code += section(travel, '  int carcost(', '  int garage_charge(')
code += r"""
int main() {
  FACTION_TYPE core, rival, npc, affiliate, society1, society2;
  core.vnum = core.slot = FACTION_CORTEX; core.name = "Core";
  rival.vnum = rival.slot = FACTION_ORDER; rival.name = "Rival";
  npc.vnum = 100; npc.antagonist = 1; npc.name = "NPC";
  affiliate.vnum = 101; affiliate.slot = FACTION_CORTEX;
  society1.vnum = 102; society1.slot = ALLIANCE_SIDELEFT;
  society2.vnum = 103; society2.slot = ALLIANCE_SIDELEFT;
  FacVect = {&core, &rival, &npc, &affiliate, &society1, &society2};
  PC_DATA pc;
  CHAR_DATA player, monster, civilian;
  player.pcdata = &pc; player.fcore = core.vnum;
  monster.npc = monster.monster = true;
  civilian.npc = true;
  LOCATION_TYPE loc;
  loc.territory_bonus = TERRITORY_LANDLORD;
  locationVect = {&loc};
  assert(!has_territory_bonus(&player, TERRITORY_LANDLORD));
  loc.phil_amount[core.slot] = 100; // Support is not a foothold.
  assert(!has_territory_bonus(&player, TERRITORY_LANDLORD));
  loc.base_faction_core = core.vnum;
  assert(territory_skill_bonus(&player, SKILL_WEALTH) == 1);
  assert(!has_territory_bonus(&monster, TERRITORY_LANDLORD));
  assert(!has_territory_bonus(nullptr, TERRITORY_LANDLORD));
  loc.phil_amount[rival.slot] = 100;
  loc.other_amount[9] = 100; loc.other_name[9] = "NPC";
  assert(has_territory_bonus(&player, TERRITORY_LANDLORD));
  player.fcore = affiliate.vnum;
  assert(!has_territory_bonus(&player, TERRITORY_LANDLORD));
  loc.base_society = society1.vnum;
  loc.base_society_secondary = society2.vnum;
  for (auto *soc : {&society1, &society2}) {
    player.fsociety = soc->vnum;
    assert(has_territory_bonus(&player, TERRITORY_LANDLORD));
  }
  player.fsociety = 0;
  player.faction = 999; player.fcore = core.vnum;
  assert(has_territory_bonus(&player, TERRITORY_LANDLORD));
  player.fcore = 0; player.fsociety = core.vnum;
  assert(has_territory_bonus(&player, TERRITORY_LANDLORD));
  player.fsociety = 0;
  assert(!has_territory_bonus(&player, TERRITORY_LANDLORD));
  player.fcore = core.vnum;
  LOCATION_TYPE duplicate = loc;
  locationVect.push_back(&duplicate);
  assert(territory_skill_bonus(&player, SKILL_WEALTH) == 1);
  locationVect.pop_back();
  loc.name = "New York";
  loc.territory_bonus = TERRITORY_FREE_MARKET;
  loc.territory_bonus_secondary = TERRITORY_ARISTOCRACY;
  assert(territory_shop_price(&player, 1000) == 900);
  assert(territory_shop_price(&player, 1) == 1);
  assert(territory_shop_price(&player, 0) == 0);
  assert(territory_shop_price(&player, -5) == -5);
  assert(territory_influence_gain(&player, 1000) == 1000);
  assert(loc.territory_bonus_secondary == 0);
  loc.name = "London, England";
  loc.territory_bonus = TERRITORY_ARISTOCRACY;
  assert(territory_influence_gain(&player, 1000) == 1100);
  assert(territory_influence_gain(&player, -100) == -100);
  loc.name = "Yellowstone, Wyoming";
  loc.territory_bonus = TERRITORY_FEYWOOD;
  loc.territory_bonus_secondary = TERRITORY_DARKWOOD;
  assert(territory_damage_amount(&monster, &player, 100) == 150);
  assert(territory_damage_amount(&player, &monster, 100) == 100);
  loc.name = "Oslo, Norway";
  loc.territory_bonus = TERRITORY_DARKWOOD;
  assert(territory_damage_amount(&player, &monster, 100) == 75);
  assert(territory_damage_amount(&civilian, &player, 100) == 100);
  assert(territory_damage_amount(&player, &player, 100) == 100);
  loc.name = "Austin, Texas";
  loc.territory_bonus = TERRITORY_FREE_LEASE;
  pc.garage_cost[0] = 100000; pc.garage_typeone[0] = 1;
  assert(carcost(&player, 0) == 0);
  pc.garage_typeone[0] = CAR_HORSE;
  assert(carcost(&player, 0) == 100000);
  loc.name = "Vancouver, Canada";
  loc.territory_bonus = TERRITORY_IMPORT_EXPORT;
  loc.territory_bonus_secondary = 0;
  territory_rewards_update(); // Migration is not capture.
  assert(core.resource == 0);
  loc.base_faction_core = 0;
  territory_rewards_update();
  loc.base_faction_core = core.vnum;
  territory_rewards_update();
  assert(core.resource == 1000 && affiliate.resource == 0);
  territory_rewards_update(); assert(core.resource == 1000);
  loc.base_society = loc.base_society_secondary = 0;
  territory_rewards_update();
  loc.base_society = society1.vnum;
  loc.base_society_secondary = society2.vnum;
  territory_rewards_update();
  assert(society1.resource == 500 && society2.resource == 500);
  loc.phil_amount[core.slot] = 0;
  loc.phil_amount[ALLIANCE_SIDERIGHT] = 100;
  territory_rewards_update();
  assert(core.resource == 1000 && society1.resource == 500 && society2.resource == 500);
  // Reward migration produces the same unique assignments as shipped data.
  locationVect.clear();
  int reward_counts[TERRITORY_BONUS_COUNT] = {};
  for (auto entry : territory_reward_defaults) {
    auto *l = new LOCATION_TYPE; l->name = entry.name;
    l->territory_bonus = TERRITORY_BEACH_BOD; // Existing single-bonus saves migrate too.
    locationVect.push_back(l);
    assert(territory_reward(l) == entry.primary);
    assert(l->territory_bonus_secondary == entry.secondary);
    assert(l->territory_bonus_secondary == 0);
    ++reward_counts[l->territory_bonus];
    // Stale explicit bonuses must never give potion territories another reward.
    if (entry.primary == 0) {
      l->territory_bonus = TERRITORY_IMPORT_EXPORT;
      l->territory_bonus_secondary = TERRITORY_LANDLORD;
      assert(territory_reward(l) == 0 && l->territory_bonus_secondary == 0);
    }
  }
  assert(locationVect.size() == 83 && reward_counts[0] == 19);
  for (int i = 1; i < TERRITORY_BONUS_COUNT; ++i)
    assert(reward_counts[i] == (i == TERRITORY_HAUTE_COUTURE ? 2 : 1));
  for (auto l : locationVect) delete l;
  locationVect.clear();
  locationVect.push_back(&loc);
  loc.name = "New York, New York";
  player.skills[SKILL_CGOVERNMENT] = 3;
  assert(get_skill(&player, SKILL_CGOVERNMENT) == 4);
  assert(player.skills[SKILL_CGOVERNMENT] == 3);
  pc.deactivated_stats[0] = SKILL_CGOVERNMENT;
  assert(get_skill(&player, SKILL_CGOVERNMENT) == 3);
  pc.deactivated_stats[0] = 0;
  loc.name = "Minsk, Belarus";
  assert(get_skill(&player, SKILL_FORENSICS) == 2);
  player.skills[SKILL_FORENSICS] = 2;
  assert(get_skill(&player, SKILL_FORENSICS) == 2);
  loc.name = "Moscow, Russia";
  assert(get_skill(&player, SKILL_PROTECTIONDETAIL) == 2);
  player.skills[SKILL_PROTECTIONDETAIL] = 2;
  assert(get_skill(&player, SKILL_PROTECTIONDETAIL) == 2);
  loc.name = "Jerusalem, Israel";
  assert(get_skill(&player, SKILL_LIGHTUP) == 1);
  event_cleanse = 1;
  assert(get_skill(&player, SKILL_LIGHTUP) == 0);
  event_cleanse = 0;
  loc.name = "Shanghai, China";
  assert(territory_investigation_cost(&player, 500) == 0);
  assert(territory_investigation_cost(&player, 20000) == 0);
  assert(territory_skill_bonus(&player, SKILL_INCANTATION) == 0);
  loc.base_faction_core = loc.base_society = loc.base_society_secondary = 0;
  assert(territory_investigation_cost(&player, 500) == 500);
  loc.name = "Unassigned"; loc.territory_bonus = 0;
  assert(territory_reward(&loc) == 0);
  locationVect.clear();
  // All seven territory contacts work with no purchased rank or spare budget.
  struct ContactReward { const char *territory; int skill; };
  const ContactReward contact_rewards[] = {
    {"Gravesend", SKILL_CPOLICE}, {"Richmond, Virginia", SKILL_CMILITARY},
    {"New York, New York", SKILL_CGOVERNMENT}, {"Los Angeles, California", SKILL_CMEDIA},
    {"Bangkok, Thailand", SKILL_CCRIMINAL}, {"Bucharest, Romania", SKILL_COCCULT},
    {"Bogota, Columbia", SKILL_CHOMELESS}
  };
  locationVect = {&loc}; loc.base_faction_core = core.vnum;
  for (const auto &reward : contact_rewards) {
    loc.name = reward.territory;
    for (int tier : {1, 2, 5}) {
      player.tier = tier; player.professional_focus = 0;
      std::fill(player.skills, player.skills + 1000, 0);
      assert(get_skill(&player, reward.skill) == 1);
      assert(raw_skillcount(&player, STYPE_CONTACTS) == 0);
      assert(raw_skillcount_level(&player, STYPE_CONTACTS) == 0);
      assert(skillcount(&player, STYPE_CONTACTS) == 1);
      // Four purchased contacts exhaust the slots, and at low tiers the budget.
      player.skills[SKILL_CCORTEX] = player.skills[SKILL_CORDER] = 5;
      player.skills[SKILL_CSCUM] = player.skills[SKILL_CSUBFACTION] = 5;
      assert(!contact_purchase_allowed(&player, reward.skill, 0));
      assert(get_skill(&player, reward.skill) == 1);
      assert(skillcount(&player, STYPE_CONTACTS) == 5);
      assert(raw_skillcount(&player, STYPE_CONTACTS) == 4);
      assert(raw_skillcount_level(&player, STYPE_CONTACTS) == 20);
      for (int purchased : {0, 1, 5}) {
        player.skills[reward.skill] = purchased;
        assert(get_skill(&player, reward.skill) == purchased + 1);
        assert(player.skills[reward.skill] == purchased);
        assert(raw_skillcount_level(&player, STYPE_CONTACTS) == 20 + purchased);
        loc.base_faction_core = 0;
        assert(get_skill(&player, reward.skill) == purchased);
        loc.base_faction_core = core.vnum;
      }
    }
  }
  // At tier one the purchased point budget is full, but a bonus is still free.
  std::fill(player.skills, player.skills + 1000, 0);
  loc.name = "Gravesend"; player.tier = 1; player.professional_focus = 5;
  player.skills[SKILL_CMEDIA] = 1;
  assert(!contact_purchase_allowed(&player, SKILL_CPOLICE, 0));
  assert(get_skill(&player, SKILL_CPOLICE) == 1);
  player.skills[SKILL_CMEDIA] = 0;
  assert(contact_purchase_allowed(&player, SKILL_CPOLICE, 0));
  assert(raw_skillcount_level(&player, STYPE_CONTACTS) == 0);
  locationVect.clear();
  // Repeated hourly scheduling survives every midnight without duplicates.
  now = 0;
  faction_antagonist_update();
  assert(OpVect.size() == 16 && saves == 1);
  faction_antagonist_update();
  assert(OpVect.size() == 16 && saves == 1);
  int launched_today = 0;
  for (int elapsed = 1; elapsed <= 24 * 15; ++elapsed) {
    now = elapsed % 24;
    if (now == 0) {
      assert(launched_today >= 2);
      launched_today = 0;
    }
    for (auto op : OpVect) {
      if (!op->valid || op->hour != now) continue;
      if (op->day > 0) --op->day;
      else { op->valid = false; ++launched_today; }
    }
    faction_antagonist_update();
    for (int date = 1; date <= 7; ++date) {
      int count = 0;
      std::set<int> hours;
      for (auto op : OpVect)
        if (op->valid && op->day + (op->hour <= now ? 1 : 0) == date) {
          ++count; assert(hours.insert(op->hour).second);
          assert(op->hour != 7 && op->hour != 17);
        }
      assert(count >= 2);
    }
  }
  for (auto op : OpVect) delete op;
  OpVect.clear();
  // Occupied time slots remain untouched; failures return without random loops.
  now = 0;
  auto *booked = new OPERATION_TYPE;
  booked->hour = 12; booked->day = 1; booked->faction = core.vnum;
  OpVect.push_back(booked);
  faction_antagonist_update();
  assert(booked->hour == 12 && booked->day == 1 && booked->faction == core.vnum);
  int same_slot = 0;
  for (auto op : OpVect) if (op->hour == 12 && op->day == 1) ++same_slot;
  assert(same_slot == 1 && OpVect.size() == 15);
  for (auto op : OpVect) delete op;
  OpVect.clear();
  // Two conflicting legacy bookings count as a single playable slot.
  for (int i = 0; i < 2; ++i) {
    auto *op = new OPERATION_TYPE;
    op->hour = 12; op->day = 1; op->faction = npc.vnum;
    OpVect.push_back(op);
  }
  faction_antagonist_update();
  bool second_hour = false;
  for (auto op : OpVect) if (op->day == 1 && op->hour != 12) second_hour = true;
  assert(second_hour);
  for (auto op : OpVect) delete op;
  OpVect.clear();
  target_available = false;
  faction_antagonist_update();
  assert(OpVect.empty() && warnings == 7);
  npc.stasis = 1;
  faction_antagonist_update();
  assert(OpVect.empty());
}
"""
# Check all shipped assignments and the in-game help directory agree.
defaults = re.findall(r'\{"([^"]+)", (\d+), (\d+)\}', (ROOT / 'src/territory_rewards.h').read_text())
locations = re.findall(r'^Name (.*?)~\nBonus (\d+)\nBonusSecondary (\d+)', (ROOT / 'data/locations.txt').read_text(), re.M)
assert defaults == locations and len(defaults) == 83
helptext = (ROOT / 'area/help.are').read_text()
assert 'Keyword territoryrewards territorybonuses factionbonuses~' in helptext
for name, _, _ in defaults:
    assert name + ':' in helptext
with tempfile.TemporaryDirectory(prefix='haven-territory-') as tmp:
    cpp, exe = Path(tmp) / 'test.cpp', Path(tmp) / 'test'
    cpp.write_text(code)
    subprocess.run(['g++', '-std=c++11', '-O1', '-g', '-fsanitize=address,undefined',
                    '-fno-omit-frame-pointer', '-I', str(ROOT / 'src'), str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('Territory rewards, 83 assignments/help entries, and 15 days of NPC scheduling passed.')
