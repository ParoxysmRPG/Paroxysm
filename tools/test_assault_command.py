#!/usr/bin/env python3
"""Linux/WSL regression checks for scene eligibility and shared aftermath."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / 'src/sex.c').read_text()


def section(start, end):
    a = text.index(start)
    return text[a:text.index(end, a)]


source = r'''
#include "merc.h"
#include <cassert>
#include <cstring>
#include <cstdlib>
#include <cstdarg>
#undef PERS
#define PERS(ch, looker) ((ch)->name)
time_t current_time = 1000000;
char log_buf[MSL];
std::vector<char *> allocations;
std::string output;
CHAR_DATA actor = {}, target = {}, admin = {};
PC_DATA actor_pc = {}, target_pc = {}, admin_pc = {};
ACCOUNT_TYPE account = {};
ROOM_INDEX_DATA room = {};
CHAR_DATA *full = nullptr, *limited = nullptr;
bool present = true, visible = true, contraceptive = true, dreaming = false;
bool ghost = false, manifest = false, pool = true, dead = false;
int prompts = 0, records = 0;
char *str_dup(const char *s) { char *p = strdup(s ? s : ""); allocations.push_back(p); return p; }
void free_string(char *) {} // Arena released after all scenarios.
bool str_cmp(const char *a, const char *b) { return strcasecmp(a ? a : "", b ? b : "") != 0; }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void printf_to_char(CHAR_DATA *, const char *format, ...) {
  char buffer[MSL]; va_list args; va_start(args, format);
  vsnprintf(buffer, sizeof(buffer), format, args); va_end(args); output += buffer;
}
void act_new(const char *s, CHAR_DATA *, const void *, const void *, int, int) { output += s; }
void wiznet(char *, CHAR_DATA *, OBJ_DATA *, long, long, int) { ++records; }
bool is_helpless(CHAR_DATA *ch) { return ch->wounds > 3; }
bool under_understanding(CHAR_DATA *ch, CHAR_DATA *) { return ch == full; }
bool under_limited(CHAR_DATA *ch, CHAR_DATA *) { return ch == limited; }
int get_trust(CHAR_DATA *ch) { return ch == &admin ? LEVEL_IMMORTAL : 1; }
bool is_gm(CHAR_DATA *) { return false; }
bool is_dreaming(CHAR_DATA *) { return dreaming; }
bool is_ghost(CHAR_DATA *) { return ghost; }
bool is_manifesting(CHAR_DATA *) { return manifest; }
bool deplete_ghostpool(CHAR_DATA *, int) { return pool; }
bool is_dead(CHAR_DATA *) { return dead; }
bool is_undead(CHAR_DATA *) { return false; }
bool higher_power(CHAR_DATA *) { return false; }
bool is_angelborn(CHAR_DATA *) { return false; }
bool is_vampire(CHAR_DATA *) { return false; }
bool is_demigod(CHAR_DATA *) { return false; }
bool is_super(CHAR_DATA *) { return false; }
int get_tier(CHAR_DATA *) { return 2; }
int get_skill(CHAR_DATA *ch, int skill) { return ch->skills[skill]; }
int get_attract(CHAR_DATA *, CHAR_DATA *) { return 50; }
int number_percent() { return 50; }
void psychic_feast(CHAR_DATA *, int, int) {}
void social_behave_mod(CHAR_DATA *, int, char *) {}
void update_standards(CHAR_DATA *, CHAR_DATA *) {}
void disease_check(CHAR_DATA *, CHAR_DATA *) {}
void nounderglow(CHAR_DATA *) {}
void affect_to_char(CHAR_DATA *ch, AFFECT_DATA *af) { SET_FLAG(ch->affected_by, af->bitvector); }
void do_negtrain(CHAR_DATA *ch, char *) { ch->skills[SKILL_VIRGIN] = 0; }
void do_function(CHAR_DATA *ch, DO_FUN *fun, char *arg) { fun(ch, arg); }
char *dream_name(CHAR_DATA *ch) { return ch->name; }
char *one_argument_nouncap(char *argument, char *word) {
  while (*argument == ' ') ++argument;
  while (*argument && *argument != ' ') *word++ = *argument++;
  *word = '\0'; while (*argument == ' ') ++argument; return argument;
}
CHAR_DATA *get_char_world(CHAR_DATA *, char *name) {
  if (!present) return nullptr;
  if (!str_cmp(name, actor.name)) return &actor;
  return !str_cmp(name, target.name) ? &target : nullptr;
}
CHAR_DATA *get_char_room(CHAR_DATA *ch, ROOM_INDEX_DATA *, char *name) { return get_char_world(ch, name); }
CHAR_DATA *get_char_dream(CHAR_DATA *ch, char *name) { return get_char_world(ch, name); }
bool can_see_char_distance(CHAR_DATA *, CHAR_DATA *, int) { return visible; }
char *habit_level(int, int level) {
  static char *risks[] = {(char *)"none", (char *)"condom", (char *)"pullout",
                         (char *)"pretend", (char *)"accident", (char *)"slipoff"};
  return risks[level];
}
bool has_contraceptive_device(CHAR_DATA *, char *) { return contraceptive; }
void sex_category(CHAR_DATA *, char *, char *) {}
void append_file(CHAR_DATA *, char *, char *) {}
void apply_seekingsex(CHAR_DATA *ch, int) { ++prompts; SET_FLAG(ch->affected_by, AFF_SEEKINGSEX); }
'''
source += section('  void apply_godlysex(', '  // For time limitation on sex propositions')
source += section('  void baby_batter(', '  // Handles valid type arguments and interpretations')
source += section('  char *process_type_arguments(', '  void update_standards(')
source += section('  void sex_bloodify(', '  char *day_ordinal(')
source += section('  static void sex_command(', '  void dream_sex(')
source += r'''
void reset() {
  actor = {}; target = {}; admin = {};
  actor_pc = {}; target_pc = {}; admin_pc = {};
  actor.pcdata = &actor_pc; target.pcdata = &target_pc; admin.pcdata = &admin_pc;
  actor.name = (char *)"Actor"; target.name = (char *)"Target";
  actor.id = 101; target.id = 202;
  actor.in_room = target.in_room = &room;
  actor_pc.account = target_pc.account = &account; account.maxhours = 200;
  actor_pc.penis = 10; actor_pc.sex_potency = 100;
  actor_pc.dream_link = &target; target_pc.dream_link = &actor;
  actor.skills[SKILL_VIRGIN] = target.skills[SKILL_VIRGIN] = 1;
  target.wounds = 5;
  full = limited = nullptr;
  present = visible = contraceptive = pool = true;
  ghost = manifest = dreaming = dead = false;
  prompts = records = 0; output.clear();
}
void command(DO_FUN *fn, CHAR_DATA *ch, const char *input) {
  char buffer[MSL]; strcpy(buffer, input); fn(ch, buffer);
}
std::vector<long long> aftermath() {
  std::vector<long long> result;
  for (CHAR_DATA *ch : {&actor, &target}) {
    PC_DATA *pc = ch->pcdata;
    for (long long value : {static_cast<long long>(pc->last_sex),
         static_cast<long long>(pc->last_sextype), static_cast<long long>(pc->last_sexprotection),
         static_cast<long long>(pc->inseminated), static_cast<long long>(pc->inseminated_daddy_ID),
         static_cast<long long>(pc->sex_potency), static_cast<long long>(pc->hymen_lost),
         static_cast<long long>(pc->virginity_lost), static_cast<long long>(pc->blood[0]),
         static_cast<long long>(pc->week_tracker[TRACK_SEX]), static_cast<long long>(pc->life_tracker[TRACK_SEX]),
         static_cast<long long>(pc->attract[ATTRACT_PROM]), static_cast<long long>(pc->last_true_sexed_ID)})
      result.push_back(value);
  }
  return result;
}
void assert_blocked(const char *input = "Target coital", CHAR_DATA *ch = &actor) {
  command(do_rape, ch, input);
  assert(records == 0 && prompts == 0);
  assert(actor_pc.sexing == nullptr && target_pc.sexing == nullptr);
  assert(actor_pc.last_sex == 0 && target_pc.last_sex == 0 && target_pc.inseminated == 0);
}
int main() {
  reset(); target.wounds = 0; assert_blocked();
  // Each sanctuary source on either participant blocks ordinary and admin invocation.
  for (int side = 0; side < 2; ++side) for (int source = 0; source < 3; ++source) {
    for (bool immortal : {false, true}) {
      reset(); CHAR_DATA *protected_ch = side ? &target : &actor;
      if (source == 0) full = protected_ch;
      if (source == 1) limited = protected_ch;
      if (source == 2) SET_FLAG(protected_ch->affected_by, AFF_UNDERSTANDING);
      assert_blocked(immortal ? "Actor Target none coital" : "Target coital", immortal ? &admin : &actor);
      assert(output.find("Sanctuary") != std::string::npos);
    }
  }
  reset(); assert_blocked("Actor coital");
  reset(); present = false; assert_blocked();
  reset(); visible = false; assert_blocked();
  reset(); SET_FLAG(target.act, ACT_IS_NPC); assert_blocked();
  reset(); actor.wounds = 5; assert_blocked();
  reset(); assert_blocked("Target nonsense");
  reset(); assert_blocked("Target voyeur");
  reset(); actor_pc.habit[HABIT_PROTECTION] = 1; contraceptive = false; assert_blocked();
  reset(); ghost = true; assert_blocked();
  reset(); ghost = manifest = true; pool = false; assert_blocked();
  reset(); dead = true; assert_blocked();
  // Normal sex still prompts even when sanctuary is present.
  reset(); full = &target; command(do_sex, &actor, "Target coital");
  assert(prompts == 1 && records == 0 && target_pc.sexing == &actor);
  // Compare actual shared consequences across risk/type and anatomical orientation.
  for (int risk = 0; risk < 6; ++risk) for (bool reverse : {false, true}) {
    for (const char *type : {"coital", "noncoital", "outercourse"}) {
      std::string input = std::string("Target ") + type;
      reset(); actor_pc.habit[HABIT_PROTECTION] = risk;
      if (reverse) { actor_pc.penis = 0; target_pc.penis = 10; actor_pc.sex_potency = 0; target_pc.sex_potency = 100; }
      command(do_sex, &actor, input.c_str());
      assert(prompts == 1 && records == 0);
      char risk_arg[MSL], type_arg[MSL];
      strcpy(risk_arg, target_pc.sex_risk); strcpy(type_arg, target_pc.sex_type);
      have_sex(&actor, &target, risk_arg, type_arg, &target);
      auto expected = aftermath();
      reset(); actor_pc.habit[HABIT_PROTECTION] = risk;
      if (reverse) { actor_pc.penis = 0; target_pc.penis = 10; actor_pc.sex_potency = 0; target_pc.sex_potency = 100; }
      command(do_rape, &actor, input.c_str());
      assert(records == 1 && prompts == 0 && aftermath() == expected);
      assert(actor_pc.sexing == nullptr && target_pc.sexing == nullptr);
      assert(output == "The agreed scene is resolved without narration.\n\rThe agreed scene is resolved without narration.\n\r");
      bool pregnancy_risk = !strcmp(type, "coital") && risk != 1 && risk != 2;
      assert((reverse ? actor_pc.inseminated : target_pc.inseminated) == (pregnancy_risk ? current_time : 0));
    }
  }
  reset(); command(do_rape, &admin, "Actor Target condom coital");
  assert(records == 1 && prompts == 0 && target_pc.inseminated == 0);
  for (char *p : allocations) free(p);
  puts("PASS: helplessness, all sanctuary sources, admin restrictions, rejection state, consent preservation, neutral output and 36 aftermath comparisons.");
}
'''

commands = (ROOT / 'data/commands.txt').read_text()
assert commands.count('Name      rape~') == 1
assert 'Code      do_rape' in commands
assert 'DECLARE_DO_FUN( do_rape );' in (ROOT / 'src/functions.h').read_text()
with tempfile.TemporaryDirectory(prefix='haven-assault-command-') as tmp:
    path = Path(tmp)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-ffunction-sections', '-fdata-sections',
                    '-Wl,--gc-sections', '-fsanitize=address,undefined', '-no-pie',
                    '-I', str(ROOT / 'src'), str(path / 'test.cc'), str(ROOT / 'src/tables.c'),
                    '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
