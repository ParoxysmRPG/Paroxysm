#!/usr/bin/env python3
"""Exercise the production affect report and LF calculation (WSL/Linux)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
lookup = (ROOT / 'src/lookup.c').read_text()
start = lookup.index('  static void lifeforce_effect(')
end = lookup.index('  int get_display_lfmod(', start)
source = r'''
#include "merc.h"
#include <cassert>
#include <cstdarg>
#include <cstring>
std::string output;
time_t current_time = 100000;
vector<EVENT_TYPE *> EventVect;
vector<FACTION_TYPE *> FacVect;
FACTION_TYPE society = {};
int hunger = 0, tier = 1, age = 25, weather = 0;
bool vampire = false, wolf = false, domain = false, wellfed = false;
bool power = false, monster = false;
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void printf_to_char(CHAR_DATA *, char *fmt, ...) {
  char buf[4096]; va_list args; va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args); va_end(args); output += buf;
}
int get_trust(CHAR_DATA *ch) { return ch->level; }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
int feeding_lf_penalty(CHAR_DATA *) { return hunger; }
int base_lifeforce(CHAR_DATA *ch) {
  return ch->lifeforce - hunger - ch->lf_used - ch->lf_taken - ch->lf_sused;
}
bool pact_holder(CHAR_DATA *) { return false; }
bool is_vampire(CHAR_DATA *) { return vampire; }
bool is_werewolf(CHAR_DATA *) { return wolf; }
int sunlight_debuff(CHAR_DATA *) { return 10; }
bool new_moon() { return true; }
bool full_moon() { return false; }
int sunphase(ROOM_INDEX_DATA *) { return 3; }
FACTION_TYPE *clan_lookup(int n) { return n == 1 ? &society : NULL; }
bool trust_elligible(CHAR_DATA *, FACTION_TYPE *, bool, CHAR_DATA *) { return true; }
bool college_student(CHAR_DATA *, bool) { return false; }
int get_tier(CHAR_DATA *) { return tier; }
char *dream_detail(CHAR_DATA *, char *, int) { return (char *)"dream"; }
int weather_bonus(CHAR_DATA *) { return weather; }
bool is_super(CHAR_DATA *) { return false; }
bool under_understanding(CHAR_DATA *, CHAR_DATA *) { return true; }
bool under_limited(CHAR_DATA *, CHAR_DATA *) { return true; }
bool in_haven(ROOM_INDEX_DATA *) { return false; }
bool clinic_staff(CHAR_DATA *, bool) { return false; }
bool college_staff(CHAR_DATA *, bool) { return false; }
bool has_weakness(CHAR_DATA *, CHAR_DATA *) { return false; }
bool under_opression(CHAR_DATA *) { return false; }
int get_true_age(CHAR_DATA *) { return age; }
int get_age(CHAR_DATA *) { return age; }
bool is_undead(CHAR_DATA *) { return false; }
bool is_ill(CHAR_DATA *) { return false; }
bool higher_power(CHAR_DATA *) { return power; }
bool guestmonster(CHAR_DATA *) { return monster; }
bool is_gm(CHAR_DATA *) { return false; }
int number_range(int a, int) { return a; }
bool battleground(ROOM_INDEX_DATA *) { return false; }
bool cardinal(CHAR_DATA *) { return false; }
int sincount(CHAR_DATA *) { return 0; }
int get_hour(ROOM_INDEX_DATA *) { return 12; }
bool has_relic(CHAR_DATA *) { return true; }
bool nearby_water(CHAR_DATA *) { return false; }
bool in_society_domain(CHAR_DATA *) { return domain; }
bool has_territory_bonus(CHAR_DATA *, int) { return wellfed; }
int cortex_lifeforce_bonus(CHAR_DATA *, CHAR_DATA *) { return 0; }
bool indentured_servant(CHAR_DATA *) { return false; }
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
'''
source += lookup[start:end]
source += r'''
std::string uncolored(const std::string &text) {
  std::string result;
  for (size_t i = 0; i < text.size(); ++i) {
    if (text[i] == '`' && i + 1 < text.size()) ++i;
    else result += text[i];
  }
  return result;
}
void contains(const char *s) {
  if (uncolored(output).find(uncolored(s)) == std::string::npos) {
    fprintf(stderr, "Missing: %s\nOutput:\n%s\n", s, output.c_str());
    abort();
  }
}
int main() {
  CHAR_DATA ch = {}; PC_DATA pc = {}; ROOM_INDEX_DATA room = {};
  ch.pcdata = &pc; ch.in_room = &room; room.vnum = 1000;
  ch.name = (char *)"Tester"; society.leader = (char *)"Someone";
  ch.lifeforce = 10000;
  do_affect(&ch, (char *)"");
  contains("Current LifeForce: 100"); contains("Base lifeforce: 100.00");
  contains("\n\r         `WCurrent LifeForce: 100`x\n\r");
  assert(output.find("Ranch") == std::string::npos);
  assert(output.find("Study") == std::string::npos);

  output.clear(); hunger = 1500; ch.lf_used = -250; ch.lf_taken = -250;
  do_affect(&ch, (char *)"");
  contains("Current LifeForce: 90"); contains("Feeding hunger");
  contains("victimizing): +2.50 LF");
  assert(ch.lf_used == -250 && ch.lf_taken == -250 && ch.lifeforce == 10000);

  hunger = 0; ch.lf_used = ch.lf_taken = 0;
  // Weighted society modifier is -1, then critical wounds halve 99 to 49.
  ch.fcore = ch.faction = 1; tier = 4;
  society.axes[AXES_CORRUPT] = AXES_NEUTRAL;
  ch.wounds = 3; output.clear(); do_affect(&ch, (char *)"");
  contains("Current LifeForce: 49");
  contains("Society (faction)`x - Reduces by 1 base modifier points");
  contains("Critical wound`x - Reduces by 50 base modifier points");
  ch.wounds = 0; tier = 1; society.axes[AXES_CORRUPT] = AXES_FARRIGHT;
  output.clear(); do_affect(&ch, (char *)"");
  contains("Society (faction)`x - Increases by 5 base modifier points");
  contains("Current LifeForce: 105");

  ch.fcore = 0; vampire = true; output.clear(); do_affect(&ch, (char *)"");
  contains("Current LifeForce: 90"); contains("Vampire sunlight");
  vampire = false; wolf = true; output.clear(); do_affect(&ch, (char *)"");
  contains("Current LifeForce: 80"); contains("New moon"); wolf = false;

  pc.deluded_duration = current_time + 1; pc.deluded_cost = 5;
  pc.fixation_mourning = current_time + 1; pc.lf_modifier = 3;
  pc.maintained_target = (char *)"Tester"; pc.maintain_cost = 2;
  output.clear(); do_affect(&ch, (char *)"");
  contains("Current LifeForce: 76"); contains("Delusion");
  contains("Fixation mourning"); contains("Maintained ritual");
  domain = wellfed = true; output.clear(); do_affect(&ch, (char *)"");
  contains("Current LifeForce: 105"); contains("Sanctified domain");
  contains("Well-fed territory"); domain = wellfed = false;

  // Report generation must not change the result across wound/age/weather cases.
  for (int w = 0; w <= 3; ++w)
    for (age = 20; age <= 90; age += 10)
      for (weather = -100; weather <= 20; weather += 20) {
        ch.wounds = w; output.clear();
        int plain = get_lifeforce(&ch, TRUE, NULL);
        int traced = get_lifeforce(&ch, TRUE, &ch);
        assert(plain == traced);
      }
  power = true; output.clear(); do_affect(&ch, (char *)"");
  contains("Current LifeForce: 100"); contains("Higher power");
  assert(output.find("Critical wound") == std::string::npos);
  power = false; monster = true; output.clear(); do_affect(&ch, (char *)"");
  contains("Monster guest"); monster = false;
  age = 25; weather = 0; ch.wounds = 0;
  pc.deluded_duration = pc.fixation_mourning = pc.lf_modifier = 0;
  pc.maintained_target = (char *)"";
  SET_FLAG(ch.affected_by, AFF_BITTEN); pc.bittenloss = 2000;
  output.clear(); do_affect(&ch, (char *)"");
  contains("Current LifeForce: 110"); contains("Display adjustment: +10 LF");
  REMOVE_FLAG(ch.affected_by, AFF_BITTEN);
  SET_FLAG(ch.act, ACT_IS_NPC); output.clear(); do_affect(&ch, (char *)"");
  assert(output.empty()); REMOVE_FLAG(ch.act, ACT_IS_NPC);
  room.vnum = 100; output.clear(); do_affect(&ch, (char *)"");
  contains("Creation room"); contains("Current LifeForce: 100");
  output.clear(); do_affect(&ch, (char *)"someone");
  assert(output == "`cSyntax`g:`W affect `xor `Waffects`x\n\r");
  puts("Affect report, society weighting, wounds, hunger, gains, overrides and modifiers passed.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-affect-') as tmp:
    path = Path(tmp)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-fsanitize=address,undefined',
                    '-no-pie', '-I', str(ROOT / 'src'), str(path / 'test.cc'),
                    '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
