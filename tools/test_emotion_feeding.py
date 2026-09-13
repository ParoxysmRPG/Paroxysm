#!/usr/bin/env python3
"""Exercise production feel/scene feeding, LF accounting and notices (Linux/WSL)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def section(file, start, end):
    text = (ROOT / 'src' / file).read_text()
    at = text.index(start)
    return text[at:text.index(end, at)]


source = r'''
#include "merc.h"
#include <cassert>
#include <cstring>
#include <cstdarg>
#include <cctype>
time_t current_time = 10000000;
DescList descriptor_list;
std::map<CHAR_DATA *, std::string> output;
CHAR_DATA donor = {}, feeder = {}, other = {};
PC_DATA dp = {}, fp = {}, op = {};
ACCOUNT_TYPE account = {};
ROOM_INDEX_DATA room = {}, elsewhere = {};
AREA_DATA area = {};
CharList people;
bool weakness = false, advantage = false, institute = false;
CHAR_DATA *neutralized = nullptr, *silent = nullptr;
int get_tier(CHAR_DATA *ch) { return ch->level; }
int get_trust(CHAR_DATA *) { return 1; }
bool is_super(CHAR_DATA *ch) { return ch->race != RACE_HUMAN; }
bool is_gm(CHAR_DATA *) { return false; }
bool is_ghost(CHAR_DATA *) { return false; }
bool higher_power(CHAR_DATA *) { return false; }
bool is_helpless(CHAR_DATA *ch) { return ch->wounds > 3; }
bool is_pinned(CHAR_DATA *) { return false; }
bool is_prisoner(CHAR_DATA *) { return false; }
bool in_fight(CHAR_DATA *) { return false; }
bool is_sparring(CHAR_DATA *) { return false; }
bool is_neutralized(CHAR_DATA *ch) { return ch == neutralized; }
bool silenced(CHAR_DATA *ch) { return ch == silent; }
bool room_hostile(ROOM_INDEX_DATA *) { return false; }
bool institute_room(ROOM_INDEX_DATA *) { return institute; }
bool college_student(CHAR_DATA *, bool) { return institute; }
bool clinic_patient(CHAR_DATA *) { return false; }
bool in_lodge(ROOM_INDEX_DATA *) { return false; }
bool public_room(ROOM_INDEX_DATA *) { return false; }
bool same_faction(CHAR_DATA *, CHAR_DATA *) { return false; }
bool has_weakness(CHAR_DATA *, CHAR_DATA *) { return weakness; }
bool is_weakness(CHAR_DATA *, CHAR_DATA *) { return advantage; }
bool same_pack(CHAR_DATA *, CHAR_DATA *) { return false; }
bool cardinal(CHAR_DATA *) { return false; }
bool sinmatch(CHAR_DATA *, CHAR_DATA *) { return false; }
bool can_spy(CHAR_DATA *, CHAR_DATA *) { return false; }
bool mindbroken(CHAR_DATA *) { return false; }
int get_world(CHAR_DATA *) { return 0; }
int get_gmtrust(CHAR_DATA *, CHAR_DATA *) { return 0; }
int get_snooptrust(CHAR_DATA *, CHAR_DATA *) { return 0; }
int pc_pop(ROOM_INDEX_DATA *r) { return r->people->size(); }
int number_percent() { return 1; }
int number_range(int, int) { return 1; }
void real_kill(CHAR_DATA *, CHAR_DATA *, bool, bool) { assert(false); }
void free_string(char *) {}
char *str_dup(const char *s) { return const_cast<char *>(s); }
char *capitalize(char *s) { return s; }
char *PERS(CHAR_DATA *ch, CHAR_DATA *) { return ch->name; }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a ? a : "", b ? b : "") != 0; }
bool str_prefix(char *a, char *b) { return strncasecmp(a, b, strlen(a)) != 0; }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
void send_to_char(const char *s, CHAR_DATA *ch) { output[ch] += s; }
void printf_to_char(CHAR_DATA *ch, char *fmt, ...) {
  char buf[MSL]; va_list args; va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args); va_end(args); output[ch] += buf;
}
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
void log_string(const char *) {}
void rp_log(char *) {}
void prp_rplog(CHAR_DATA *, char *) {}
void guest_match(CHAR_DATA *) {}
void remove_color(char *out, char *in) {
  while (*in) {
    if (*in == '`' && in[1]) in += 2;
    else *out++ = *in++;
  }
  *out = 0;
}
'''
source += section('interp.c', '  char *one_argument(', '  char *one_argument_nouncap(')
source += section('handler.c', 'bool is_exact_name(', '/* enchanted stuff')
source += section('feeding.c', '// These intervals', 'void feeding_update(')
source += section('lookup.c', '  int base_lifeforce(', '  bool is_ill(')
source += section('abominations.c', '  static void feeding_notice(', '  _DOFUN(do_feed)')
source += section('act_comm.c', '  bool can_send_feels(', '  _DOFUN(do_direct)')
source += r'''
void reset(int source_tier = 2, int feeder_tier = 4) {
  donor = {}; feeder = {}; other = {}; dp = {}; fp = {}; op = {}; account = {};
  donor.pcdata = &dp; feeder.pcdata = &fp; other.pcdata = &op;
  donor.name = (char *)"Feeler"; feeder.name = (char *)"Feeder"; other.name = (char *)"Other";
  donor.level = source_tier; feeder.level = other.level = feeder_tier;
  donor.race = RACE_HUMAN; feeder.race = other.race = RACE_NEWVAMPIRE;
  donor.played = feeder.played = other.played = 100 * 3600;
  donor.lifeforce = 10000; feeder.lifeforce = other.lifeforce = 9000;
  donor.in_room = feeder.in_room = other.in_room = &room;
  people = {&donor, &feeder}; room.people = &people; room.area = &area;
  dp.account = fp.account = op.account = &account;
  for (int i = 0; i < 3; ++i) dp.last_sexed[i] = fp.last_sexed[i] = op.last_sexed[i] = (char *)"";
  weakness = advantage = institute = false; neutralized = silent = nullptr;
  output.clear(); descriptor_list.clear();
}
void feel(const char *emotion) {
  char command[MSL]; strcpy(command, emotion); do_feel(&donor, command);
}
bool noticed(CHAR_DATA *ch) { return output[ch].find("[Feeding:") != std::string::npos; }
void assert_fed(const char *emotion) {
  assert(donor.lf_taken > 0 && base_lifeforce(&feeder) > 9000);
  assert(fp.last_feeding == current_time && feeding_stage(&feeder) == 0);
  assert(output[&donor].find(std::string("Feeder feeds on your ") + emotion) != std::string::npos);
  assert(output[&feeder].find(std::string("You feed on Feeler's ") + emotion) != std::string::npos);
  assert(output[&feeder].find("You are fully fed") != std::string::npos);
}
int main() {
  // Absolute tier thresholds, including equal/higher tier feelers and feed focus.
  for (int source_tier : {1, 2, 3, 4, 5, 6}) for (int tier = 2; tier <= 6; ++tier)
    for (bool focused : {false, true}) for (int type : {PSYCHIC_FEAR, PSYCHIC_LUST}) {
      reset(source_tier, tier);
      if (focused) SET_FLAG(feeder.comm, COMM_FEEDING);
      fp.last_feeding = current_time - 90 * 86400;
      int initial_lf = base_lifeforce(&feeder);
      bool eligible = tier >= (type == PSYCHIC_FEAR ? 3 : 4);
      feel(type == PSYCHIC_FEAR ? "afraid" : "lust");
      if (eligible) assert_fed(type == PSYCHIC_FEAR ? "fear" : "lust");
      else {
        assert(!noticed(&donor) && !noticed(&feeder));
        assert(donor.lf_taken == 0 && base_lifeforce(&feeder) == initial_lf);
        assert(fp.last_feeding == current_time - 90 * 86400);
      }
    }
  for (const char *word : {"afraid", "FEAR!", "scared.", "fearful", "frightened", "terrified",
       "terror", "dread", "panic", "panicked", "panicking", "panicky", "petrified",
       "intimidated", "alarmed", "spooked", "unnerved", "dreading", "anxious", "anxiety",
       "nervous", "apprehensive", "apprehension", "`rFear`x!", "very NERVOUS!"}) {
    reset(2, 3); feel(word); assert_fed("fear");
  }
  for (const char *word : {"lust", "DESIRE!", "horny", "aroused.", "lustful", "arousal",
       "desirous", "randy", "randiness", "lusting", "lustfully", "horniness", "lecherous",
       "lascivious", "libidinous", "amorous", "lewd", "`rLust`x!", "a little `rRANDY`x!"}) {
    reset(); feel(word); assert_fed("lust");
  }
  for (const char *word : {"fearless", "scaredycat", "illustration", "desireless", "unafraid",
       "unintimidated", "unalarmed", "unapprehensive", "calm", "excited", ""}) {
    reset(); feel(word); assert(!noticed(&donor) && !noticed(&feeder));
  }
  // Rejected feels, invalid recipients, depleted sources, and full feeders do not announce a feed.
  for (int type : {PSYCHIC_FEAR, PSYCHIC_LUST}) for (int blocked = 0; blocked < 10; ++blocked) {
    reset();
    if (blocked == 0) SET_FLAG(account.flags, ACCOUNT_NOFEEL);
    if (blocked == 1) feeder.in_room = &elsewhere;
    if (blocked == 2) fp.sleeping = 10;
    if (blocked == 3) neutralized = &feeder;
    if (blocked == 4) neutralized = &donor;
    if (blocked == 5) silent = &feeder;
    if (blocked == 6) institute = true;
    if (blocked == 7) donor.lifeforce = type == PSYCHIC_FEAR ? 8500 : 5000;
    if (blocked == 8) feeder.lifeforce = 12000;
    if (blocked == 9) SET_FLAG(feeder.act, ACT_IS_NPC);
    feel(type == PSYCHIC_FEAR ? "fear" : "lust");
    assert(!noticed(&donor) && !noticed(&feeder) && fp.last_feeding == 0);
    assert(donor.lf_taken == 0);
  }
  reset(); feel("lust - curious"); assert(!noticed(&feeder) && !donor.lf_taken);
  // A full recipient cannot prevent another eligible recipient from feeding.
  reset(); feeder.lifeforce = 12000; people.push_back(&other); feel("lust");
  assert(!noticed(&feeder) && noticed(&other) && noticed(&donor));
  assert(op.last_feeding == current_time && fp.last_feeding == 0);
  reset(); people = {&donor}; donor.race = RACE_NEWVAMPIRE; donor.level = 5;
  SET_FLAG(donor.comm, COMM_FEEDING); feel("fear"); assert(!noticed(&donor) && !donor.lf_taken);
  // Passive feeding retains its focus/tier rules and does not produce feel notices.
  reset(2, 3); psychic_feast(&donor, PSYCHIC_LUST, 1); assert(fp.last_feeding == 0);
  SET_FLAG(feeder.comm, COMM_FEEDING); psychic_feast(&donor, PSYCHIC_LUST, 1);
  assert(fp.last_feeding == current_time && !noticed(&feeder));
  // Scene rewards use victimization tier scaling: 1 LF drained, 1.5x reward.
  for (int tier = 1; tier <= 3; ++tier) {
    reset(tier, 4); psychic_feast(&donor, PSYCHIC_SEX, 1);
    assert(donor.lf_taken == 100);
    // give_lifeforce splits surplus between two integer balances, rounding odd units down.
    int reward = tier == 1 ? 49 : tier == 2 ? 150 : 195;
    assert(base_lifeforce(&feeder) - 9000 == reward / 2 * 2);
    assert_fed("lust"); assert(dp.ill_count == 0 && dp.sleeping == 0);
  }
  reset(); donor.skills[SKILL_MENTALDISCIPLINE] = 1;
  psychic_feast(&donor, PSYCHIC_SEX, 1); assert(base_lifeforce(&feeder) == 9194);
  reset(); dp.last_sexed[0] = feeder.name;
  psychic_feast(&donor, PSYCHIC_SEX, 1); assert(base_lifeforce(&feeder) == 9074);
  reset(); donor.played = 19 * 3600;
  psychic_feast(&donor, PSYCHIC_SEX, 1); assert(base_lifeforce(&feeder) == 9030);
  reset(); weakness = true;
  psychic_feast(&donor, PSYCHIC_SEX, 1); assert(base_lifeforce(&feeder) == 9098);
  reset(); advantage = true; donor.faction = 1;
  psychic_feast(&donor, PSYCHIC_SEX, 1); assert(base_lifeforce(&feeder) == 9224);
  reset(); SET_FLAG(donor.affected_by, AFF_ABDUCTED);
  psychic_feast(&donor, PSYCHIC_SEX, 1); assert(base_lifeforce(&feeder) == 9074);
  reset(); donor.lf_taken = 950;
  psychic_feast(&donor, PSYCHIC_SEX, 1);
  assert(donor.lf_taken == 1000 && base_lifeforce(&feeder) == 9074);
  output.clear(); current_time += 60;
  psychic_feast(&donor, PSYCHIC_SEX, 1);
  assert(donor.lf_taken == 1000 && base_lifeforce(&feeder) == 9074);
  assert(!noticed(&donor) && fp.last_feeding == current_time - 60);
  reset(); for (int i = 0; i < 20; ++i) psychic_feast(&donor, PSYCHIC_SEX, 1);
  assert(donor.lf_taken == 1000 && base_lifeforce(&feeder) == 10500);
  reset(); feeder.lifeforce = 12000; psychic_feast(&donor, PSYCHIC_SEX, 1);
  assert(!donor.lf_taken && !fp.last_feeding && !noticed(&donor));
  reset(); feeder.lifeforce = 11990; psychic_feast(&donor, PSYCHIC_SEX, 1);
  assert(base_lifeforce(&feeder) == 12000 && noticed(&feeder));
  puts("PASS: emotion keywords, absolute tier thresholds, both notices, hunger reset, guards, passive rules, scene scaling and caps.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-emotion-feeding-') as tmp:
    path = Path(tmp)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-fsanitize=address,undefined',
                    '-no-pie', '-I', str(ROOT / 'src'), str(path / 'test.cc'),
                    '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
