#!/usr/bin/env python3
"""Run production scheme visibility, numbering, and save code with engine stubs.

Run under Linux/WSL with python3 tools/test_schemes.py; requires g++.
No player or game data is read or changed.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
events = (ROOT / 'src/events.c').read_text()
recycle = (ROOT / 'src/recycle.c').read_text()
structs = (ROOT / 'src/structs.h').read_text()
stories = (ROOT / 'src/stories.c').read_text()


def section(text, start, end):
    offset = text.index(start)
    return text[offset:text.index(end, offset)]


source = r'''
#include <algorithm>
#include <cassert>
#include <cctype>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <strings.h>
#include <string>
#include <vector>
using std::vector;
#define EVENT_STATE_OF_EMERGENCY 32
#define SKILL_SOCIALFOCUS 161
#define TRUE true
#define FALSE false
#define MSL 4096
#define UPPER(c) toupper(c)
#define UMAX(a,b) std::max(a,b)
#define VALIDATE(e) ((e)->valid = true)
#define IS_NPC(c) ((c)->npc)
#define IS_IMMORTAL(c) ((c)->immortal)
#define KEY(literal, field, value) if (!str_cmp(word, literal)) { field = value; fMatch = true; break; }
struct ACCOUNT_DATA { char *name; };
struct PC_DATA { ACCOUNT_DATA *account = nullptr; int influence = 0, scheme_influence = 0; int week_tracker[1] = {}, life_tracker[1] = {}; };
struct CHAR_DATA { char *name; PC_DATA *pcdata; int focus = 0, faction = 0; bool npc = false, immortal = false; int socialite = 0; vector<int> rewards = {}; };
vector<int> offline_rewards;
bool has_territory_bonus(CHAR_DATA *ch, int bonus) {
  return ch && !ch->npc && ch->pcdata && std::find(ch->rewards.begin(), ch->rewards.end(), bonus) != ch->rewards.end();
}
struct DESCRIPTOR_DATA { CHAR_DATA *character = nullptr; };
struct NEWS_TYPE { char *author; char *message; int stats[10] = {}; bool valid = true; int timer = 100; };
int current_time = 100;
int loads = 0, frees = 0, offline_focus = 3;
bool load_success = true;
PC_DATA pc;
CHAR_DATA *online = nullptr;
vector<void *> allocations;
void *alloc_perm(size_t n) { void *p = calloc(1, n); allocations.push_back(p); return p; }
char *str_dup(const char *s) { char *p = static_cast<char *>(alloc_perm(strlen(s)+1)); strcpy(p, s); return p; }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a,b) != 0; }
bool is_name(char *, char *) { return false; }
bool is_exact_name(char *name, char *names) {
  const char *p = names; while (*p) { while (*p == ' ') ++p; const char *start = p;
    while (*p && *p != ' ') ++p;
    if (static_cast<size_t>(p-start) == strlen(name) && !strncasecmp(start, name, p-start)) return true;
  } return false;
}
void free_string(char *) {} // Tracked allocations are freed at the end.
CHAR_DATA *get_char_world_pc(char *) { return online; }
int prof_focus(CHAR_DATA *ch) { return ch->focus; }
bool load_char_obj(DESCRIPTOR_DATA *d, char *name) {
  ++loads; d->character = new CHAR_DATA{name, &pc, offline_focus};
  d->character->rewards = offline_rewards; return load_success;
}
void free_char(CHAR_DATA *ch) { ++frees; delete ch; }
void bug(const char *, int) { assert(false); }
void fread_to_eol(FILE *f) { int c; while ((c = fgetc(f)) != EOF && c != '\n') {} }
char *fread_word(FILE *f) { static char b[4096]; assert(fscanf(f, "%4095s", b) == 1); return b; }
int fread_number(FILE *f) { int n; assert(fscanf(f, "%d", &n) == 1); return n; }
char *fread_string(FILE *f) {
  std::string s; int c; do { c = fgetc(f); } while (c != EOF && isspace(c));
  while (c != EOF && c != '~') { s += c; c = fgetc(f); }
  return str_dup(s.c_str());
}
std::string output;
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void printf_to_char(CHAR_DATA *, const char *format, ...) {
  char b[8192]; va_list args; va_start(args, format); vsnprintf(b, sizeof b, format, args); va_end(args); output += b;
}
bool gm = false;
bool is_gm(CHAR_DATA *) { return gm; }
bool is_super(CHAR_DATA *) { return false; }
int get_skill(CHAR_DATA *ch, int skill) { return skill == SKILL_SOCIALFOCUS ? ch->socialite : 0; }
'''
source += section((ROOT / 'src/const.h').read_text(), 'enum TerritoryBonus {', '// This must be at the end')
source += section((ROOT / 'src/world.c').read_text(), '  int territory_investigation_cost(', '  int territory_influence_gain(')
source += section(structs, '    struct event_type', '    /*\n      struct participant_type')
source += 'typedef event_type EVENT_TYPE;\nvector<EVENT_TYPE *> EventVect;\nEVENT_TYPE *nullevent;\n'
source += 'void free_event(EVENT_TYPE *e) { e->valid = false; }\n'
source += section(recycle, '  EVENT_TYPE *new_event(void)', '  void free_event(')
source += section(events, '  void fread_event(', '  void load_events(')
source += section(events, '  static void write_event(', '  void save_events_backup(')
source += section(events, '  EVENT_TYPE *get_event(', '  bool has_event(')
source += section(stories, '  bool can_see_news(', '  void show_news(')
source += section((ROOT / 'src/const.h').read_text(), '#define EVENT_NONE', '#define MAX_EVENT')
source += section(events, '  int scheme_cost(', '  int scheme_duration(')
source += r'''
#define INFLUENCE_SCHEME 1
#define TRACK_SCHEMES_THWARTED 0
vector<NEWS_TYPE *> NewsVect;
int charges = 0, saves = 0, event_saves = 0, ends = 0, dice_index = 0;
int dice[2] = {50, 50};
int number_range(int low, int high) { int v = dice[dice_index++ % 2]; assert(v >= low && v <= high); return v; }
void charge_influence(CHAR_DATA *ch, int, int amount) {
  ++charges; int aid = std::min(amount, ch->pcdata->scheme_influence);
  ch->pcdata->scheme_influence -= aid; ch->pcdata->influence -= amount - aid;
}
void save_char_obj(CHAR_DATA *, bool, bool) { ++saves; }
void save_events() { ++event_saves; }
vector<std::string> notifications, notification_recipients;
void offline_message(char *name, char *message) {
  notification_recipients.push_back(name); notifications.push_back(message);
}
void event_end(EVENT_TYPE *) { ++ends; }
bool is_number(const char *s) { if (!*s) return false; for (; *s; ++s) if (!isdigit(*s)) return false; return true; }
'''
source += section(events, '  static int scheme_thwart_cost(', '  _DOFUN(do_event)')
source += section(events, '  char *const event_names[]', '  int scheme_cost(')
source += 'void command(CHAR_DATA *ch, const char *arg1, const char *arg2) {\n'
source += section(events, '    if (!str_cmp(arg1, "list"))', '    if (!str_cmp(arg1, "aid"))')
source += section(events, '    if (!str_cmp(arg1, "investigate"))', '    if (IS_AFFECTED(ch, AFF_OUTCAST))')
source += '}\n'
assert events.count('write_event(fpout, *it);') == 2
assert events.count('event->professional_focus = prof_focus(ch);') == 2
assert events.count('event->socialite_bonus = scheme_socialite_bonus(ch);') == 2
assert events.count('charge_influence(ch, INFLUENCE_SCHEME, event->launch_cost);') == 2
assert 'launch_scheme_thwart' not in events
assert 'investigate_scheme(ch, atoi(ch->pcdata->order_target), TRUE);' in (ROOT / 'src/clans.c').read_text()

source += r'''
int main() {
  CHAR_DATA viewer{str_dup("Viewer"), &pc, 2};
  CHAR_DATA author{str_dup("Schemer"), &pc, 3};
  online = &author;
  EVENT_TYPE *hidden = new_event(), *visible = new_event(), *future = new_event();
  hidden->author = author.name; hidden->active_time = 90; hidden->deactive_time = 200;
  hidden->type = 1; hidden->typetwo = 2;
  hidden->socialite_bonus = 0; hidden->professional_focus = 3; hidden->introduction = str_dup("Secret introduction");
  hidden->description = str_dup("Secret details");
  *visible = *hidden; visible->author = str_dup("Visible"); visible->professional_focus = 2;
  *future = *hidden; future->active_time = 101;
  nullevent = new_event(); EventVect = {hidden, future, visible};
  assert(!can_see_scheme(&viewer, hidden));
  viewer.focus = 30; assert(!can_see_scheme(&viewer, hidden)); viewer.focus = 2;
  assert(can_see_scheme(&author, hidden));
  assert(!can_see_scheme(nullptr, hidden) && !can_see_scheme(&viewer, nullptr));
  assert(!can_see_scheme(&viewer, future));
  hidden->researched = str_dup("Viewers"); assert(!can_see_scheme(&viewer, hidden));
  visible->researched = str_dup("Viewer"); assert(can_see_scheme(&viewer, visible));
  viewer.npc = true; assert(!can_see_scheme(&viewer, visible)); viewer.npc = false;
  viewer.immortal = true; assert(!can_see_scheme(&viewer, hidden)); viewer.immortal = false;
  command(&viewer, "list", "");
  assert(output.find("A SCHEME IS UNDERWAY") != std::string::npos);
  assert(output.find("Schemer") == std::string::npos && output.find("Secret") == std::string::npos);
  assert(output.find("Visible") != std::string::npos && loads == 0);
  output.clear(); command(&viewer, "info", "1");
  assert(output.find("A SCHEME IS UNDERWAY") != std::string::npos && output.find("Thwart cost") == std::string::npos);
  output.clear(); command(&viewer, "thwart", "1"); assert(charges == 0);
  assert(get_event_number(visible) == 2 && get_event(2) == visible);
  assert(get_event_number(nullptr) == 0 && get_event_number(future) == 0);
  assert(get_event(99) == nullevent);
  NEWS_TYPE news{str_dup("Town Events"), hidden->introduction};
  EventVect = {hidden, future, visible};
  assert(!can_see_news(&viewer, &news));
  ACCOUNT_DATA investigation_account{str_dup("ViewerAccount")}; pc.account = &investigation_account;
  pc.influence = 2000;
  // Lower focus can win; focus is no longer a hard visibility threshold.
  dice[0] = 60; dice[1] = 45; // 80 versus 80: defender wins the tie.
  command(&viewer, "investigate", "1");
  assert(charges == 1 && pc.influence == 1500 && !can_see_scheme(&viewer, hidden));
  dice[0] = 61; dice[1] = 45;
  command(&viewer, "investigate", "1");
  assert(charges == 2 && pc.influence == 1000 && can_see_scheme(&viewer, hidden));
  assert(can_see_news(&viewer, &news));
  output.clear(); command(&viewer, "info", "1"); assert(output.find("Secret details") != std::string::npos);
  command(&viewer, "investigate", "1"); assert(charges == 2);
  // No roll, fee or author load for invalid requests or already known details.
  command(&viewer, "investigate", "999"); assert(charges == 2 && loads == 0);
  hidden->professional_focus = -1; online = &author;
  assert(scheme_professional_focus(hidden) == 3 && loads == 0);
  online = nullptr; hidden->professional_focus = -1;
  assert(scheme_professional_focus(hidden) == 3 && loads == 1 && frees == 1);
  assert(scheme_professional_focus(hidden) == 3 && loads == 1);
  hidden->professional_focus = -1; load_success = false;
  assert(scheme_professional_focus(hidden) == -1 && loads == 2 && frees == 2);
  load_success = true; assert(scheme_professional_focus(hidden) == 3);
  FILE *f = tmpfile(); assert(f); write_event(f, hidden); rewind(f);
  assert(!strcmp(fread_word(f), "#EVENT")); fread_event(f); fclose(f);
  EVENT_TYPE *restored = EventVect.back();
  assert(restored->professional_focus == 3 && restored->type == 1 && restored->typetwo == 2);
  assert(can_see_scheme(&viewer, restored));
  // Prepaid orders use the contest but must not charge the fee twice.
  hidden->researched = str_dup(""); dice[0] = 100; dice[1] = 1;
  investigate_scheme(&viewer, 1, true);
  assert(charges == 2 && can_see_scheme(&viewer, hidden));
  f = tmpfile(); assert(f); fputs("Author Schemer~\nType 1\nActiveTime 90\nDeactiveTime 200\nEnd\n", f); rewind(f);
  fread_event(f); fclose(f); assert(EventVect.back()->professional_focus == -1);
  assert(!can_see_scheme(&viewer, EventVect.back()));
  hidden->researched = str_dup(""); hidden->deactive_time = current_time - 1;
  assert(can_see_scheme(&viewer, hidden));
  charges = saves = event_saves = dice_index = 0;

  EventVect = {hidden, visible};
  hidden->valid = true; visible->valid = true;
  hidden->type = EVENT_STATE_OF_EMERGENCY; hidden->typetwo = 0;
  hidden->active_time = current_time + 1; hidden->deactive_time = current_time + 10;
  visible->type = 1; visible->typetwo = 0;
  assert(!state_of_emergency());
  hidden->active_time = current_time - 1; assert(state_of_emergency());
  hidden->valid = false; assert(!state_of_emergency()); hidden->valid = true;
  visible->typetwo = EVENT_STATE_OF_EMERGENCY;
  visible->active_time = current_time - 1; visible->deactive_time = current_time + 20;
  hidden->deactive_time = current_time; assert(state_of_emergency());
  visible->deactive_time = current_time; assert(!state_of_emergency());
  current_time = 2000000000;
  ACCOUNT_DATA account{str_dup("ViewerAccount")}, second_account{str_dup("SecondAccount")};
  pc.account = &account; pc.influence = 10000; pc.scheme_influence = 1000;
  PC_DATA second_pc; second_pc.account = &second_account; second_pc.influence = 10000;
  CHAR_DATA second{str_dup("Second"), &second_pc, 3};
  viewer.focus = 3;
  hidden->type = EVENT_STATE_OF_EMERGENCY; hidden->typetwo = 0;
  hidden->account = str_dup("SchemerAccount"); hidden->professional_focus = 3;
  hidden->active_time = current_time - 1; hidden->deactive_time = current_time + 86400;
  hidden->launch_cost = 20000; hidden->thwart_cooldown = 0;
  hidden->researched = str_dup("Viewer Second");
  EventVect = {hidden};
  assert(scheme_thwart_cost(hidden) == 6667);
  visible->launch_cost = 0; visible->limited = 0; visible->type = EVENT_STORM; visible->typetwo = EVENT_HURRICANE;
  assert(scheme_thwart_cost(visible) == 13334 && visible->launch_cost == 40000);
  visible->launch_cost = 0; visible->limited = 1;
  assert(scheme_thwart_cost(visible) == 1667 && visible->launch_cost == 5000);
  for (const char *bad : {"accept", "finish", "0", "1abc", "999"}) command(&viewer, "thwart", bad);
  assert(charges == 0);
  gm = true; command(&viewer, "thwart", "1"); gm = false; assert(charges == 0);
  char *saved_account = hidden->account; hidden->account = account.name;
  command(&viewer, "thwart", "1"); assert(charges == 0); hidden->account = saved_account;
  pc.influence = 5666; command(&viewer, "thwart", "1"); assert(charges == 0);
  pc.influence = 5667;
  // A tie after the schemer's +5 is a failed attempt, charged exactly once.
  dice[0] = 55; dice[1] = 50;
  command(&viewer, "thwart", "1");
  assert(charges == 1 && pc.influence == 0 && pc.scheme_influence == 0);
  assert(hidden->thwart_attempted == 1 && hidden->thwart_cooldown == current_time + 21600);
  assert(ends == 0 && saves == 1 && event_saves == 1 && state_of_emergency());
  assert(notifications.size() == 1 && notification_recipients[0] == "Schemer");
  assert(notifications[0].find("Viewer attempted to thwart your scheme #1 and failed.") != std::string::npos);
  assert(notifications[0].find("six hours") != std::string::npos);
  command(&second, "thwart", "1"); assert(charges == 1 && second_pc.influence == 10000);
  // Shared cooldown and original cost survive a save/reload.
  f = tmpfile(); write_event(f, hidden); rewind(f); assert(!strcmp(fread_word(f), "#EVENT")); fread_event(f); fclose(f);
  restored = EventVect.back(); EventVect = {restored};
  assert(restored->launch_cost == 20000 && restored->thwart_cooldown == hidden->thwart_cooldown);
  command(&second, "thwart", "1"); assert(charges == 1);
  current_time = restored->thwart_cooldown - 1; command(&second, "thwart", "1"); assert(charges == 1);
  ++current_time;
  news.message = restored->introduction; NewsVect = {&news};
  dice[0] = 56; dice[1] = 50;
  command(&second, "thwart", "1");
  assert(charges == 2 && second_pc.influence == 3333 && ends == 1);
  assert(restored->deactive_time < current_time && !state_of_emergency() && news.timer == 0);
  assert(second_pc.week_tracker[0] == 1 && second_pc.life_tracker[0] == 1);
  assert(saves == 2 && event_saves == 2);
  assert(notifications.size() == 2 && notification_recipients[1] == "Schemer");
  assert(notifications[1].find("Second attempted to thwart your scheme #1 and succeeded.") != std::string::npos);
  assert(notifications[1].find("Your scheme has ended.") != std::string::npos);
  command(&second, "thwart", "1"); assert(charges == 2);
  assert(notifications.size() == 2);
  // Death ends all of the author's launched schemes, including pending ones.
  current_time = 100;
  hidden->active_time = 90;
  restored->deactive_time = 99;
  hidden->deactive_time = 200; hidden->thwart_cooldown = 300;
  future->deactive_time = 200;
  visible->deactive_time = 200;
  EVENT_TYPE *draft = new_event(); draft->author = author.name;
  EventVect = {hidden, future, visible, restored, draft};
  news.message = hidden->introduction; news.timer = 100;
  int previous_ends = ends, previous_saves = event_saves;
  end_schemes_on_death(nullptr);
  author.npc = true; end_schemes_on_death(&author); author.npc = false;
  assert(event_saves == previous_saves);
  end_schemes_on_death(&author);
  assert(hidden->deactive_time < current_time && future->deactive_time < current_time);
  assert(visible->deactive_time == 200 && draft->deactive_time == 0);
  assert(hidden->thwart_cooldown == 0 && news.timer == 0);
  assert(ends == previous_ends + 1 && event_saves == previous_saves + 1);
  assert(!state_of_emergency());
  assert(charges == 2 && second_pc.week_tracker[0] == 1);
  end_schemes_on_death(&author);
  assert(ends == previous_ends + 1 && event_saves == previous_saves + 1);
  f = tmpfile(); write_event(f, hidden); rewind(f);
  assert(!strcmp(fread_word(f), "#EVENT")); fread_event(f); fclose(f);
  assert(EventVect.back()->deactive_time == hidden->deactive_time);
  // Bonus scales independently of professional focus on either side.
  int attack, defense; dice[0] = dice[1] = 50; viewer.focus = 3;
  for (int rank = 0; rank <= 3; ++rank) {
    viewer.socialite = rank;
    scheme_contest(&viewer, 3, 0, attack, defense);
    assert(attack == 80 + 5 * rank && defense == 85);
    scheme_contest(&viewer, 3, 5 * rank, attack, defense);
    assert(attack == 80 + 5 * rank && defense == 85 + 5 * rank);
  }
  viewer.socialite = 2;
  assert(scheme_contest(&viewer, 3, 0, attack, defense));
  assert(!scheme_contest(&viewer, 3, 10, attack, defense));
  // A missing socialite bonus is backfilled without changing saved launch focus.
  hidden->professional_focus = 2; hidden->socialite_bonus = -1;
  author.focus = 9; author.socialite = 3; online = &author;
  assert(scheme_professional_focus(hidden) == 2 && hidden->socialite_bonus == 15);
  online = nullptr; int previous_loads = loads;
  assert(scheme_professional_focus(hidden) == 2 && loads == previous_loads);
  f = tmpfile(); write_event(f, hidden); rewind(f); assert(!strcmp(fread_word(f), "#EVENT")); fread_event(f); fclose(f);
  assert(EventVect.back()->professional_focus == 2 && EventVect.back()->socialite_bonus == 15);
  hidden->socialite_bonus = -1; load_success = false;
  assert(scheme_professional_focus(hidden) == -1);
  load_success = true; assert(scheme_professional_focus(hidden) == 2 && hidden->socialite_bonus == 0);
  // Shanghai removes the affordability gate and fee, but still requires a winning roll.
  current_time = 100; EventVect = {hidden}; online = &author;
  viewer.focus = author.focus = 3; viewer.socialite = author.socialite = 0;
  hidden->professional_focus = 3; hidden->socialite_bonus = 0;
  hidden->active_time = 90; hidden->deactive_time = 86400;
  hidden->researched = str_dup(""); hidden->thwart_cooldown = 0;
  pc.influence = pc.scheme_influence = 0;
  viewer.rewards = {TERRITORY_FREE_INVESTIGATION};
  dice[0] = 55; dice[1] = 50; dice_index = 0;
  int before_charges = charges;
  command(&viewer, "investigate", "1");
  assert(charges == before_charges && !can_see_scheme(&viewer, hidden));
  dice[0] = 56;
  command(&viewer, "investigate", "1");
  assert(charges == before_charges && pc.influence == 0 && can_see_scheme(&viewer, hidden));
  hidden->researched = str_dup(""); viewer.rewards.clear();
  int before_dice = dice_index;
  command(&viewer, "investigate", "1");
  assert(dice_index == before_dice && !can_see_scheme(&viewer, hidden));

  // Investigation bonuses are distinct from thwart bonuses on both sides.
  pc.influence = 10000; dice[0] = 55;
  viewer.rewards = {TERRITORY_THWART_ATTACK};
  command(&viewer, "investigate", "1");
  assert(!can_see_scheme(&viewer, hidden));
  viewer.rewards = {TERRITORY_INVESTIGATE_ATTACK};
  author.rewards = {TERRITORY_THWART_DEFENSE};
  command(&viewer, "investigate", "1");
  assert(can_see_scheme(&viewer, hidden));
  hidden->researched = str_dup("");
  author.rewards = {TERRITORY_INVESTIGATE_DEFENSE};
  command(&viewer, "investigate", "1");
  assert(!can_see_scheme(&viewer, hidden));

  // Current offline memberships provide defenses, and allocated authors are freed.
  online = nullptr; offline_rewards = {TERRITORY_THWART_DEFENSE, TERRITORY_BOUGHT_TIME};
  int before_loads = loads, before_frees = frees;
  assert(scheme_territory_defenses(hidden) == (SCHEME_GUARD_THWART | SCHEME_GUARD_TIME));
  assert(loads == before_loads + 1 && frees == before_frees + 1);
  load_success = false;
  assert(scheme_territory_defenses(hidden) == 0 && frees == before_frees + 2);
  load_success = true;
  hidden->researched = str_dup("Viewer"); hidden->launch_cost = 3000;
  viewer.rewards = {TERRITORY_THWART_ATTACK}; pc.influence = 10000;
  command(&viewer, "thwart", "1"); // +10 on both sides retains the defender's tie.
  assert(hidden->thwart_cooldown == current_time + 7 * 3600);
  assert(notifications.back().find("seven hours") != std::string::npos);
  // Losing the territory removes its protection for the next eligible attempt.
  offline_rewards.clear(); current_time = hidden->thwart_cooldown;
  command(&viewer, "thwart", "1");
  assert(hidden->deactive_time < current_time);

  current_time = 100; hidden->deactive_time = 86400; hidden->thwart_cooldown = 0;
  online = &author; author.rewards = {TERRITORY_INVESTIGATE_DEFENSE};
  viewer.rewards = {TERRITORY_THWART_ATTACK};
  command(&viewer, "thwart", "1"); // Investigation defense must not stop a thwart.
  assert(hidden->deactive_time < current_time);
  hidden->deactive_time = 86400; hidden->thwart_cooldown = 0;
  author.rewards.clear(); viewer.rewards = {TERRITORY_INVESTIGATE_ATTACK};
  command(&viewer, "thwart", "1"); // Investigation attack must not improve a thwart.
  assert(hidden->thwart_cooldown == current_time + 6 * 3600);

  // Both launch paths discount the actual payment; display and thwart payment agree.
  hidden->type = EVENT_STORM; hidden->typetwo = EVENT_HURRICANE;
  viewer.rewards = {TERRITORY_SCHEME_DISCOUNT};
  assert(scheme_launch_cost(&viewer, hidden, false) == 36000);
  assert(scheme_launch_cost(&viewer, hidden, true) == 4500);
  viewer.rewards.clear();
  assert(scheme_launch_cost(&viewer, hidden, false) == 40000);
  assert(scheme_launch_cost(&viewer, hidden, true) == 5000);
  hidden->launch_cost = 20000;
  viewer.rewards = {TERRITORY_THWART_DISCOUNT};
  assert(scheme_thwart_cost(hidden, &viewer) == 5667);
  hidden->thwart_cooldown = 0;
  output.clear(); command(&viewer, "info", "1");
  assert(output.find("Thwart cost: 5667 influence") != std::string::npos);
  pc.influence = 5667; pc.scheme_influence = 0;
  command(&viewer, "thwart", "1");
  assert(pc.influence == 0 && hidden->thwart_cooldown == current_time + 6 * 3600);
  for (void *p : allocations) free(p);
  puts("Scheme visibility, command access, numbering, legacy/offline authors, news, save round-trip, emergency lifecycle, contested thwarts, fees, shared cooldown and persistence checks passed.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-schemes-') as directory:
    cpp = Path(directory) / 'schemes.cpp'
    binary = Path(directory) / 'schemes'
    cpp.write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-Wall', '-Wextra', '-Wno-write-strings',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-no-pie', '-g',
                    str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
