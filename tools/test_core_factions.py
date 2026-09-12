#!/usr/bin/env python3
"""Exercise production core membership, lifeforce, and chip policies in WSL."""
from pathlib import Path
import subprocess
import tempfile
import re

ROOT = Path(__file__).resolve().parents[1]
clans = (ROOT / 'src/clans.c').read_text()
skills = (ROOT / 'src/skills.c').read_text()
lookup = (ROOT / 'src/lookup.c').read_text()
institute = (ROOT / 'src/institute.c').read_text()

def section(source, start, end):
    a = source.index(start)
    return source[a:source.index(end, a)]

stubs = r'''
#include "merc.h"
#include <cassert>
#include <cstring>
#include <cstdlib>
#include <cstdarg>
std::vector<FACTION_TYPE *> factions;
FACTION_TYPE *nullfac = nullptr;
std::string output;
int removals = 0;
char *str_dup(const char *s) { return strdup(s); }
void free_string(char *s) { free(s); }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void printf_to_char(CHAR_DATA *, const char *fmt, ...) {
  char buf[4096]; va_list args; va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args); va_end(args); output += buf;
}
void send_log(int, char *) {}
void remove_from_clanroster(char *, int) { ++removals; }
FACTION_TYPE *clan_lookup(int id) {
  for (auto *fac : factions) if (fac->vnum == id) return fac;
  return nullptr;
}
int get_tier(CHAR_DATA *ch) { return ch->level; }
int skillbase_count(CHAR_DATA *ch, int) { return ch->skills[SKILL_HYPERREGEN] > 0; }
bool seems_super(CHAR_DATA *ch) { return ch->race == RACE_NEWVAMPIRE; }
bool is_super(CHAR_DATA *ch) { return seems_super(ch); }
CHAR_DATA *online_brander = nullptr;
CHAR_DATA *get_char_world_pc(char *) { return online_brander; }
bool trust_elligible(CHAR_DATA *, FACTION_TYPE *, bool, CHAR_DATA *) { return true; }
std::vector<INSTITUTE_TYPE *> InVect;
bool clinic_patient(CHAR_DATA *) { return false; }
bool generic_faction_vnum(int id) { return id == FACTION_CORTEX || id == FACTION_SCUM || id == FACTION_ORDER; }
bool banishing_trust = false;
bool has_trust(CHAR_DATA *, int, int) { return banishing_trust; }
'''

production = '\n'.join([
    section(institute, '  bool college_student(', '  int college_group('),
    section(lookup, '  static void lifeforce_effect(', '  int monster_lf_mod('),
    section(lookup, '  bool pact_holder(', '  bool in_wilds('),
    section(clans, '  bool cortex_loyalty_brainwashed(', '  void normalize_society_record('),
    section(skills, '  int focus_point_per_tier(', '  bool can_train_combat_focus('),
    section(clans, '  static int faction_secrecy_decay(', '  void faction_daily('),
    section(clans, '  void normalize_society_record(', '  /*Local Functions */'),
    section(clans, '  void join_to_clan(', '  void vassal_to_clan('),
    section(clans, '  void join_to_clan_two(', '  void remove_from_clanroster('),
    section(lookup, '  int clan_lifeforce_mod(', '  int soc_lf_mod('),
    section(skills, '  bool faction_chip_control(', '  _DOFUN(do_control)'),
])

# Exercise the command guards before any roster or character mutations.
production += '\nvoid try_leave(CHAR_DATA *ch, int number) {\n'
production += section(clans, '      if (number == FACTION_CORTEX &&', '      if (ch->fcore == number) {')
production += 'ch->fcore = 0;\n}\n'
banish = section(clans, '    if (!str_cmp(arg, "banish")) {', '      argument = one_argument_nouncap(argument, arg2);')
production += '\nbool banished = false;\nvoid try_banish(CHAR_DATA *ch, FACTION_TYPE *fac) {\n'
production += banish[banish.index('\n') + 1:]
production += 'banished = true;\n}\n'


seed = (ROOT / 'data/clans.txt').read_text()
profile_init = 'void load_core_profiles(FACTION_TYPE &cortex, FACTION_TYPE &scum, FACTION_TYPE &order) {\n'
for record in seed.split('#FACTION'):
    ident = re.search(r'^Vnum\s+(\d+)', record, re.M)
    if not ident or int(ident[1]) not in (5, 6, 7): continue
    name = {5: 'cortex', 6: 'order', 7: 'scum'}[int(ident[1])]
    for field in ('name', 'description', 'manifesto'):
        value = re.search(r'^'+field+r'\s+(.*?)~', record, re.M|re.S|re.I)[1]
        import json
        profile_init += f'{name}.{field} = str_dup({json.dumps(value)});\n'
    for field in ('axes','restrictions'):
        values = re.search(r'^'+field+r'\s+([^\n]+)',record,re.M|re.I)[1].split()
        for index,value in enumerate(values): profile_init += f'{name}.{field}[{index}] = {value};\n'
    profile_init += f'{name}.closed = '+re.search(r'^Closed\s+(\d+)',record,re.M)[1]+';\n'
profile_init += '}\n'

tests = r'''
int main() {
  FACTION_TYPE cortex = {}, scum = {}, order = {};
  cortex.vnum = FACTION_CORTEX; scum.vnum = FACTION_SCUM; order.vnum = FACTION_ORDER;
  cortex.type = scum.type = order.type = FACTION_CORE;
  scum.restrictions[RESTRICT_SUPERNATURALS] = 1;
  cortex.restrictions[RESTRICT_PRIMARY_COMBAT] = 1;
  scum.restrictions[RESTRICT_PRIMARY_ARCANE] = 1;
  load_core_profiles(cortex, scum, order);
  assert(!strcmp(cortex.name, "The Cortex") && !strcmp(scum.name, "The Scum"));
  assert(cortex.axes[AXES_CORRUPT] == AXES_FARLEFT);
  assert(cortex.axes[AXES_DEMOCRATIC] == AXES_FARLEFT);
  assert(cortex.axes[AXES_SUPERNATURAL] == AXES_FARRIGHT);
  assert(scum.axes[AXES_CORRUPT] == AXES_NEUTRAL);
  assert(scum.axes[AXES_DEMOCRATIC] == AXES_FARRIGHT);
  assert(scum.axes[AXES_SUPERNATURAL] == AXES_MIDLEFT);
  for (int axis : {AXES_MATERIAL, AXES_COMBAT, AXES_ANARCHY})
    assert(cortex.axes[axis] == AXES_NEUTRAL && scum.axes[axis] == AXES_NEUTRAL);
  assert(!cortex.restrictions[RESTRICT_PRIMARY_COMBAT]);
  assert(!scum.restrictions[RESTRICT_PRIMARY_ARCANE] && !scum.restrictions[RESTRICT_SUPERNATURALS]);
  assert(order.closed == 1 && strstr(order.manifesto, "destroyed by the Cortex"));
  factions = {&cortex, &scum, &order};
  CHAR_DATA ch = {}, target = {}, npc = {};
  PC_DATA pc = {}, target_pc = {};
  ch.pcdata = &pc; target.pcdata = &target_pc;
  ch.name = const_cast<char *>("Player"); target.name = const_cast<char *>("Target");
  ch.fcore = FACTION_CORTEX; ch.race = RACE_NEWVAMPIRE;
  try_leave(&ch, FACTION_CORTEX);
  assert(ch.fcore == FACTION_CORTEX);
  assert(!player_faction_join_allowed(&ch, &scum, false));
  assert(player_faction_join_allowed(&ch, &cortex, false));
  banishing_trust = true;
  try_banish(&ch, &cortex); assert(!banished); // Slave rank cannot grant authority.
  ch.race = RACE_HUMAN;
  banishing_trust = false;
  try_banish(&ch, &cortex); assert(!banished);
  banishing_trust = true;
  ch.fcore = FACTION_SCUM;
  try_banish(&ch, &cortex); assert(!banished);
  ch.fcore = FACTION_CORTEX;
  try_banish(&ch, &cortex); assert(banished);
  assert(player_faction_join_allowed(&ch, &scum, false));
  try_leave(&ch, FACTION_CORTEX); assert(ch.fcore == 0);
  ch.race = RACE_NEWVAMPIRE; ch.fcore = FACTION_SCUM;
  try_leave(&ch, FACTION_SCUM); assert(ch.fcore == 0);
  banished = false;
  try_banish(&ch, &scum); assert(banished); // Other factions retain their policy.
  ch.race = RACE_HUMAN; output.clear();
  ch.fcore = ch.faction = FACTION_CORTEX; ch.factiontwo = FACTION_SCUM;
  ch.esteem_faction = 900;
  join_to_clan(&ch, FACTION_ORDER);
  join_to_clan_two(&ch, FACTION_ORDER);
  assert(ch.fcore == FACTION_CORTEX && ch.faction == FACTION_CORTEX);
  assert(ch.factiontwo == FACTION_SCUM && ch.esteem_faction == 900 && removals == 0);
  assert(order.member_names[0] == nullptr && output.find("not open") != std::string::npos);
  SET_FLAG(npc.act, ACT_IS_NPC);
  assert(player_faction_join_allowed(&npc, &order, false));
  assert(!player_faction_join_allowed(nullptr, &order, false));
  join_to_clan(&ch, 9999); assert(ch.fcore == FACTION_CORTEX);
  ch.fcore = ch.faction = ch.factiontwo = 0;
  join_to_clan(&ch, FACTION_SCUM);
  assert(ch.fcore == FACTION_SCUM && !strcmp(scum.member_names[0], "Player"));

  FACTION_TYPE society = {}, extra = {};
  society.type = extra.type = FACTION_SOCIETY;
  society.vnum = 100; extra.vnum = 101;
  {
    CHAR_DATA student = {}; student.name = const_cast<char *>("Student");
    PC_DATA student_pc = {}; student.pcdata = &student_pc;
    INSTITUTE_TYPE enrollment = {}; enrollment.name = student.name;
    enrollment.college_prestige = 1; InVect.push_back(&enrollment);
    for (int suspended : {0, 1}) {
      enrollment.college_suspended = suspended;
      assert(player_faction_join_allowed(&student, &cortex, false));
      for (auto *fac : {&scum, &order, &society}) {
        output.clear();
        assert(!player_faction_join_allowed(&student, fac, false));
        assert(output.empty());
        assert(!player_faction_join_allowed(&student, fac, true));
        assert(output.find("expelled") != std::string::npos);
        assert(output.find("drop out") != std::string::npos);
      }
      join_to_clan(&student, FACTION_SCUM);
      join_to_clan_two(&student, FACTION_SCUM);
      assert(student.fcore == 0 && student.faction == 0 && student.factiontwo == 0);
    }
    enrollment.college_prestige = 0; // Dropping out ends the restriction.
    assert(player_faction_join_allowed(&student, &scum, false));
    assert(player_faction_join_allowed(&student, &society, false));
    InVect.clear(); output.clear();
  }
  ch.level = 3;
  assert(!is_containment_priority(&ch));
  ch.skills[SKILL_HYPERREGEN] = 1;
  assert(is_containment_priority(&ch));
  output.clear(); show_containment_priority(&ch, &ch);
  assert(output.find("CONTAINMENT PRIORITY") != std::string::npos);
  assert(output.find("brainwashed") != std::string::npos);
  ch.skills[SKILL_HYPERREGEN] = 0;
  for (int tier = 1; tier <= 6; ++tier) {
    ch.level = tier;
    assert(is_containment_priority(&ch) == (tier >= 4));
    const int base = focus_point_per_tier(&ch);
    ch.modifier = MODIFIER_PACT;
    assert(focus_point_per_tier(&ch) == base + 1);
    SET_FLAG(ch.act, PLR_DEMONPACT);
    assert(focus_point_per_tier(&ch) == base + 1); // Never double-count a pact.
    ch.modifier = 0;
    assert(focus_point_per_tier(&ch) == base + 1);
    REMOVE_FLAG(ch.act, PLR_DEMONPACT);
  }
  ch.fcore = ch.faction = 0;
  ch.modifier = MODIFIER_PACT;
  {
    CHAR_DATA branded = {}, human = {};
    PC_DATA branded_pc = {}, human_pc = {};
    branded.pcdata = &branded_pc; human.pcdata = &human_pc;
    branded.level = 4; branded.race = RACE_NEWVAMPIRE;
    branded.fcore = human.fcore = FACTION_CORTEX;
    human.race = RACE_HUMAN;
    assert(is_containment_priority(&branded));
    assert(cortex_lifeforce_bonus(&branded, nullptr) == 0);
    branded_pc.brainwash_loyalty = const_cast<char *>("cOrTeX");
    assert(!is_containment_priority(&branded));
    assert(cortex_lifeforce_bonus(&branded, nullptr) == 2);
    branded_pc.brainwash_loyalty = cortex.name;
    assert(!is_containment_priority(&branded));
    branded_pc.branddate = 123;
    branded_pc.brander = const_cast<char *>("Human");
    online_brander = &human;
    output.clear();
    assert(cortex_lifeforce_bonus(&branded, &branded) == 4);
    assert(output.find("Cortex human brand: +2 LF") != std::string::npos);
    assert(output.find("Cortex loyalty brainwashing: +2 LF") != std::string::npos);
    online_brander = nullptr;
    assert(cortex_lifeforce_bonus(&branded, nullptr) == 4); // Offline brander.
    branded_pc.branddate = 0;
    assert(cortex_lifeforce_bonus(&branded, nullptr) == 2);
    branded_pc.branddate = 123;
    online_brander = &human;
    human.fcore = FACTION_SCUM;
    assert(cortex_lifeforce_bonus(&branded, nullptr) == 2);
    human.fcore = FACTION_CORTEX; human.race = RACE_NEWVAMPIRE;
    assert(cortex_lifeforce_bonus(&branded, nullptr) == 2);
    human.race = RACE_HUMAN;
    branded_pc.brainwash_loyalty = const_cast<char *>("Someone else");
    assert(is_containment_priority(&branded));
    assert(cortex_lifeforce_bonus(&branded, nullptr) == 2);
    branded_pc.brainwash_loyalty = const_cast<char *>("");
    assert(is_containment_priority(&branded));
    branded.fcore = FACTION_SCUM;
    assert(cortex_lifeforce_bonus(&branded, nullptr) == 0);
    branded.fcore = FACTION_CORTEX; branded.race = RACE_HUMAN;
    assert(cortex_lifeforce_bonus(&branded, nullptr) == 0);
    assert(cortex_lifeforce_bonus(nullptr, nullptr) == 0);
    assert(cortex_lifeforce_bonus(&npc, nullptr) == 0);
    online_brander = nullptr;
  }
  for (int stance : {0, AXES_DEMONIC, AXES_FARLEFT, AXES_MIDLEFT, AXES_NEARLEFT,
                    AXES_NEUTRAL, AXES_NEARRIGHT, AXES_MIDRIGHT, AXES_FARRIGHT}) {
    society.axes[AXES_CORRUPT] = stance;
    assert(player_faction_join_allowed(&ch, &society, false)
           == (stance == AXES_DEMONIC || stance == AXES_FARLEFT));
  }
  assert(!player_faction_join_allowed(&ch, &cortex, true));
  assert(output.find("loyalty to a demonic master") != std::string::npos);
  assert(!player_faction_join_allowed(&ch, &scum, false));
  ch.modifier = 0; SET_FLAG(ch.act, PLR_DEMONPACT);
  assert(!player_faction_join_allowed(&ch, &cortex, false));
  REMOVE_FLAG(ch.act, PLR_DEMONPACT);
  ch.fcore = ch.faction = FACTION_SCUM;
  society.axes[AXES_CORRUPT] = AXES_NEUTRAL;
  assert(!player_faction_join_allowed(&ch, &society, false)); // Faction excludes society.
  ch.fcore = ch.faction = 0;
  assert(player_faction_join_allowed(&ch, &society, false));
  ch.fsociety = society.vnum;
  assert(!player_faction_join_allowed(&ch, &cortex, false)); // Society excludes faction.
  assert(!player_faction_join_allowed(&ch, &extra, false));
  ch.legacy_society = extra.vnum; ch.faction = extra.vnum;
  assert(selected_society(&ch) == extra.vnum);
  assert(player_faction_join_allowed(&ch, &extra, false)); // Preserve membership.
  ch.fsociety = 0; ch.esteem_legacy_society = 123; ch.deploy_legacy_society = 1;
  normalize_society_memberships(&ch);
  assert(ch.fsociety == extra.vnum && !ch.legacy_society);
  assert(ch.esteem_society == 123 && ch.deploy_society == 1);
  assert(!player_faction_join_allowed(&ch, &society, false));
  ch.fsociety = ch.faction = 0;
  assert(player_faction_join_allowed(&ch, &cortex, false));
  society.type = 4; society.patron_relation = -1; society.eidilon = const_cast<char *>("Patron");
  normalize_society_record(&society);
  assert(society.type == FACTION_SOCIETY && society.patron_relation == SOCIETY_PATRON_WORSHIP);
  society.patron_relation = SOCIETY_PATRON_NONE;
  normalize_society_record(&society);
  assert(society.patron_relation == SOCIETY_PATRON_NONE);

  for (int age : {0, 30, 3000}) {
    society.secret_days = age;
    society.resource = 0; society.outcast = 1;
    assert(faction_secrecy_decay(&society, 9999999) == 0);
  }
  assert(faction_secrecy_decay(&cortex, 9999999) == 0);
  FACTION_TYPE historical = {}; historical.type = FACTION_CORE; historical.vnum = 200;
  assert(faction_secrecy_decay(&historical, 9999999) == 0);
  historical.stasis = 1; assert(faction_secrecy_decay(&historical, 9999999) == 0);

  // Axis changes must not change LF for naturals/supernaturals, including leaders.
  for (auto *fac : {&cortex, &scum}) {
    for (int tier = 1; tier <= 5; ++tier) {
      ch.level = tier;
      for (int race : {RACE_HUMAN, RACE_NEWVAMPIRE}) {
        ch.race = race;
        for (const char *leader : {"Player", "Other"}) {
          fac->leader = const_cast<char *>(leader);
          fac->axes[AXES_SUPERNATURAL] = AXES_NEUTRAL;
          int baseline = clan_lifeforce_mod(&ch, nullptr, fac);
          for (int axis = AXES_FARLEFT; axis <= AXES_FARRIGHT; ++axis) {
            fac->axes[AXES_SUPERNATURAL] = axis;
            assert(clan_lifeforce_mod(&ch, nullptr, fac) == baseline);
          }
        }
      }
    }
  }
  ch.level = target.level = 3; ch.race = RACE_HUMAN; target.race = RACE_NEWVAMPIRE;
  ch.fcore = target.fcore = FACTION_CORTEX;
  cortex.axes[AXES_SUPERNATURAL] = AXES_FARRIGHT;
  assert(faction_chip_control(&ch, &target));
  assert(!faction_chip_control(&target, &ch));
  assert(!faction_chip_control(&ch, &ch));
  target.fcore = FACTION_SCUM; assert(!faction_chip_control(&ch, &target));
  ch.fcore = FACTION_SCUM; scum.axes[AXES_SUPERNATURAL] = AXES_MIDLEFT;
  assert(!faction_chip_control(&ch, &target) && !faction_chip_control(&target, &ch));
  scum.axes[AXES_SUPERNATURAL] = AXES_FARLEFT;
  assert(faction_chip_control(&target, &ch));
  for (auto *fac : {&cortex, &scum, &order}) {
    free_string(fac->name); free_string(fac->description); free_string(fac->manifesto);
    for (char *name : fac->member_names) free_string(name);
  }
  puts("Core profiles, Order joining, LF independence, and faction chip tests passed.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-core-') as temporary:
    path = Path(temporary)
    source = path / 'test.cc'
    source.write_text(stubs + production + profile_init + tests)
    subprocess.run(['g++', '-std=gnu++17', '-g', '-O1', '-Wno-write-strings',
                    '-Wno-deprecated', '-fsanitize=address,undefined', '-no-pie',
                    '-I', str(ROOT / 'src'), str(source), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
