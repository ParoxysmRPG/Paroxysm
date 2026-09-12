#!/usr/bin/env python3
"""Exercise production feeding/quota rules and command guards under sanitizers (WSL)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def section(file, start, end):
    text = (ROOT / 'src' / file).read_text()
    a = text.index(start)
    return text[a:text.index(end, a)]


source = r'''
#include "merc.h"
#include <cassert>
#include <cstring>
#include <cstdarg>
#include <climits>
#include <cmath>
time_t current_time = 100000;
int tier = 3, saves = 0, logs = 0;
bool vampire = false, animal = false;
int alts = 2;
bool is_vampire(CHAR_DATA *) { return vampire; }
bool animal_feeder(CHAR_DATA *) { return animal; }
int alt_count(CHAR_DATA *) { return alts; }
bool cardinal(CHAR_DATA *) { return false; }
void once_per_day(CHAR_DATA *) {}
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
FACTION_TYPE cortex = {}, saved = {};
std::string output;
int get_tier(CHAR_DATA *) { return tier; }
int get_trust(CHAR_DATA *ch) { return ch->level; }
bool is_gm(CHAR_DATA *) { return false; }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void printf_to_char(CHAR_DATA *, char *fmt, ...) {
  char buf[4096]; va_list args; va_start(args,fmt);
  vsnprintf(buf,sizeof(buf),fmt,args); va_end(args); output += buf;
}
void log_string(const char *) {}
void guest_match(CHAR_DATA *) {}
FACTION_TYPE *clan_lookup(int vnum) { return vnum == FACTION_CORTEX ? &cortex : nullptr; }
bool save_clans(bool) { ++saves; saved = cortex; return true; }
void send_log(int, char *) { ++logs; }
time_t utc(int year, int month, int day) {
  tm date = {}; date.tm_year = year - 1900; date.tm_mon = month - 1; date.tm_mday = day;
  return timegm(&date);
}
'''
source += section('lookup.c', '  int unused_lifeforce(', '  void use_lifeforce(')
# Exercise the production counter updates without unrelated daily event processing.
source += section('update.c', '  void regenerate_lifeforce(', '    int resting = 10000;')
source += '}\n'
source += 'bool discipline_allowed(CHAR_DATA *ch, int skill, int level, bool show) {\n'
source += section('skills.c', '    if (skill == SKILL_MENTALDISCIPLINE &&', '    int value = ch->skills[skill];')
source += 'return true; }\n'
source += 'void clinic_guard(CHAR_DATA *ch, const char *arg1) {\n'
source += section('institute.c', '    if (!str_cmp(arg1, "arrest")', '    if (is_griefer(ch))')
source += '}\nvoid dream_guard(CHAR_DATA *ch, const char *arg) {\n'
source += section('skills.c', '    if (!str_cmp(arg, "snare"))', '    if (is_ghost(ch))')
source += '}\n'
source += r'''
int main() {
  CHAR_DATA ch = {}; PC_DATA pc = {}; DESCRIPTOR_DATA desc = {};
  ch.pcdata = &pc; ch.desc = &desc; desc.connected = CON_PLAYING;
  ch.lifeforce = 10000;
  ROOM_INDEX_DATA room = {}; room.vnum = 100; ch.in_room = &room;
  for (bool vamp : {false, true}) {
    vampire = vamp;
    for (int alt : {1, 2}) {
      alts = alt;
      // An actual feed splits 100 LF of surplus between the two counters.
      ch.lf_used = ch.lf_taken = 0;
      give_lifeforce(&ch, 10000, (char *)"Vampire bite");
      assert(ch.lf_used == -5000 && ch.lf_taken == -5000);
      regenerate_lifeforce(&ch);
      int decay = alt == 1 ? 210 : 140;
      assert(ch.lf_used == -5000 + decay);
      assert(ch.lf_taken == -5000 + decay);
      // Small bonuses must reach zero without turning into LF debt.
      for (int bonus : {1, 24, 49, 74}) {
        ch.lf_used = ch.lf_taken = -bonus;
        regenerate_lifeforce(&ch);
        assert(ch.lf_used <= 0 && ch.lf_used > -bonus);
        assert(ch.lf_taken <= 0 && ch.lf_taken > -bonus);
        for (int i = 0; i < 10 && ch.lf_taken < 0; ++i)
          regenerate_lifeforce(&ch);
        assert(ch.lf_used == 0 && ch.lf_taken == 0);
      }
      // Spent LF continues to recover at the original rate.
      ch.lf_used = 5000; ch.lf_taken = vamp ? 15000 : 5000;
      regenerate_lifeforce(&ch);
      assert(ch.lf_used == 5000 - (alt == 1 ? (vamp ? 525 : 420) : 350));
      assert(ch.lf_taken == (vamp ? 15000 : 5000)
          - (vamp ? (alt == 1 ? 420 : 280) : (alt == 1 ? 420 : 350)));
    }
  }
  vampire = true;
  for (bool animal_feed : {false, true}) {
    animal = animal_feed;
    int baseline = animal ? 20000 : 10000;
    for (int taken : {0, 1, 5000, baseline - 1, baseline}) {
      ch.lf_used = 0; ch.lf_taken = taken;
      regenerate_lifeforce(&ch);
      assert(ch.lf_taken == UMIN(baseline, taken + 25));
    }
  }
  vampire = animal = false; alts = 2;
  ch.lf_used = ch.lf_taken = 0;
  pc.last_feeding = pc.feeding_reminder = 0;
  assert(feeding_interval(nullptr) == 0);
  for (tier = 1; tier <= 6; ++tier) {
    pc.last_feeding = 0; pc.feeding_reminder = 0;
    feeding_update(&ch);
    if (tier < 3) { assert(!feeding_interval(&ch)); continue; }
    int days = tier == 3 ? 30 : tier == 4 ? 21 : 14;
    assert(feeding_interval(&ch) == days * 86400);
    int start = pc.last_feeding;
    current_time = start + days * 86400 - 1;
    assert(feeding_stage(&ch) == 0);
    ++current_time;
    for (int stage = 1; stage <= 4; ++stage) {
      assert(feeding_stage(&ch) == stage);
      assert(base_lifeforce(&ch) == 10000 - feeding_lf_penalty(&ch));
      assert(unused_lifeforce(&ch) == base_lifeforce(&ch));
      assert(feeding_blocks_sanctuary(&ch) == (stage == 4));
      current_time += 7 * 86400;
    }
    assert(feeding_stage(&ch) == 4);
    record_feeding(&ch, 1000, "blood transfusion");
    record_feeding(&ch, 0, "Vampire bite");
    record_feeding(&ch, -1, "Fear Feeding");
    assert(pc.last_feeding == start && feeding_stage(&ch) == 4);
    give_lifeforce_nouse(&ch, 100, (char *)"Vampire bite");
    assert(pc.last_feeding == current_time && !feeding_blocks_sanctuary(&ch));
    ch.lf_taken = ch.lf_used = 0;
    current_time += days * 86400;
    ch.lf_taken = 500; // Early return in give_lifeforce must still record a feed.
    give_lifeforce(&ch, 10, (char *)"Fear Feeding");
    assert(pc.last_feeding == current_time && feeding_stage(&ch) == 0);
    ch.lf_taken = ch.lf_used = 0;
  }
  // Weekly reminders state the current penalty and exact next consequence.
  for (tier = 3; tier <= 5; ++tier) {
    int days = tier == 3 ? 30 : tier == 4 ? 21 : 14;
    pc.last_feeding = current_time; pc.feeding_reminder = 0;
    output.clear(); feeding_update(&ch);
    assert(output.find("after " + std::to_string(days) + " days") != std::string::npos);
    assert(output.find("within " + std::to_string(days) + " days") != std::string::npos);
    assert(output.find("5 LF penalty") != std::string::npos);
    assert(feeding_lf_penalty(&ch) == 0);
    output.clear(); current_time += 86400; feeding_update(&ch); assert(output.empty());
    current_time += 6 * 86400 - 1; feeding_update(&ch); assert(output.empty());
    ++current_time; feeding_update(&ch);
    assert(output.find("within " + std::to_string(days - 7) + " days") != std::string::npos);
    const int penalties[] = {500, 1500, 3000, 5000};
    for (int stage = 1; stage <= 4; ++stage) {
      current_time = pc.last_feeding + days * 86400 + (stage - 1) * 7 * 86400;
      pc.feeding_reminder = current_time - 7 * 86400;
      output.clear(); feeding_update(&ch);
      assert(feeding_stage(&ch) == stage);
      assert(output.find("by " + std::to_string(penalties[stage - 1] / 100) + " LF") != std::string::npos);
      if (stage < 4) {
        assert(output.find("within 7 days") != std::string::npos);
        assert(output.find("increase to " + std::to_string(penalties[stage] / 100) + " LF") != std::string::npos);
      }
      if (stage == 3) assert(output.find("will lose both full and limited sanctuary") != std::string::npos);
      if (stage == 4) assert(output.find("have lost both full and limited sanctuary") != std::string::npos);
      output.clear(); current_time += 3600; feeding_update(&ch); assert(output.empty());
      current_time += 86400; feeding_update(&ch); assert(output.empty());
      current_time = pc.feeding_reminder + 7 * 86400 - 1;
      feeding_update(&ch); assert(output.empty());
      ++current_time; feeding_update(&ch); assert(!output.empty());
    }
    // An off-schedule login gives the remaining days, not a fixed seven-day warning.
    current_time = pc.last_feeding + days * 86400 + 6 * 86400;
    pc.feeding_reminder = current_time - 7 * 86400;
    output.clear(); feeding_update(&ch);
    assert(output.find("within 1 day,") != std::string::npos);
    PC_DATA reloaded = pc; ch.pcdata = &reloaded;
    output.clear(); feeding_update(&ch); assert(output.empty());
    assert(feeding_stage(&ch) == 1);
    ch.desc = nullptr; current_time += 7 * 86400;
    feeding_update(&ch); assert(output.empty());
    ch.desc = &desc; feeding_update(&ch); assert(!output.empty());
    ch.pcdata = &pc;
    record_feeding(&ch, 10, "victimize");
    output.clear(); feeding_update(&ch); assert(output.empty());
    assert(feeding_stage(&ch) == 0 && feeding_lf_penalty(&ch) == 0);
  }
  SET_FLAG(ch.act, PLR_GUEST); assert(feeding_interval(&ch) == 0);
  REMOVE_FLAG(ch.act, PLR_GUEST);
  tier = 2; feeding_update(&ch); assert(pc.last_feeding == 0);
  tier = 3; feeding_update(&ch); assert(pc.last_feeding == current_time);

  tier = 4; output.clear();
  assert(!discipline_allowed(&ch, SKILL_MENTALDISCIPLINE, 1, true));
  assert(output.find("too far gone to find salvation now") != std::string::npos);
  assert(discipline_allowed(&ch, SKILL_MENTALDISCIPLINE, 0, false));
  tier = 3; assert(discipline_allowed(&ch, SKILL_MENTALDISCIPLINE, 1, true));
  tier = 5; assert(discipline_allowed(&ch, SKILL_MENTALDISCIPLINE, 1, true));
  for (auto command : {"arrest", "MakeArrest", "BribeArrest", "ApproveArrest"}) {
    output.clear(); clinic_guard(&ch, command); assert(output == "go capture them coward.\n\r");
  }
  output.clear(); dream_guard(&ch, "snare"); assert(output == "Dream snares are disabled.\n\r");

  cortex.vnum = FACTION_CORTEX; cortex.resource = 2000;
  current_time = utc(2026,12,1); cortex_quota_update();
  assert(cortex.resource == 2000 && cortex.lf_quota_harvested == 0 && saves == 1);
  cortex_record_harvest(&ch, 20); assert(cortex.lf_quota_harvested == 0);
  ch.fcore = FACTION_CORTEX; ch.faction = FACTION_SCUM;
  cortex_record_harvest(&ch, 19); assert(cortex.lf_quota_harvested == 19);
  cortex_record_harvest(&ch, 0); assert(cortex.lf_quota_harvested == 19);
  current_time = utc(2027,1,1); cortex_record_harvest(&ch, 1);
  assert(cortex.resource == 1000 && cortex.lf_quota_harvested == 1 && logs == 1);
  cortex_record_harvest(&ch, INT_MAX); assert(cortex.lf_quota_harvested == 20);
  current_time = utc(2027,2,1); cortex_quota_update();
  assert(cortex.resource == 1250 && cortex.lf_quota_harvested == 0 && logs == 2);
  cortex = saved; cortex_quota_update(); assert(cortex.resource == 1250 && logs == 2);
  current_time = utc(2027,4,1); cortex_quota_update();
  assert(cortex.resource == -750 && logs == 3); // February and March both missed.
  output.clear(); show_cortex_quota(&ch, &cortex); assert(output.find("0/20") != std::string::npos);
  output.clear(); ch.fcore = 0; show_cortex_quota(&ch, &cortex); assert(output.empty());
  ch.level = LEVEL_IMMORTAL; show_cortex_quota(&ch, &cortex); assert(!output.empty());
  FACTION_TYPE other = {}; other.vnum = FACTION_SCUM;
  output.clear(); show_cortex_quota(&ch, &other); assert(output.empty());
  puts("Feeding bonus decay, deadlines, penalties, reminders, restrictions, and Cortex quota rollover passed.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-feeding-') as tmp:
    path = Path(tmp)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-fsanitize=address,undefined',
                    '-fsanitize=float-cast-overflow', '-fno-sanitize-recover=all',
                    '-no-pie', '-I', str(ROOT / 'src'), str(path / 'test.cc'),
                    str(ROOT / 'src/feeding.c'), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
