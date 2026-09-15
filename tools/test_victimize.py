#!/usr/bin/env python3
"""Run extracted production victimize flows with isolated world stubs (WSL)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def section(file, start, end):
    source = (ROOT / 'src' / file).read_text()
    at = source.index(start)
    return source[at:source.index(end, at)]


source = r'''
#include "merc.h"
#include <cassert>
#include <cstdarg>
#include <cstring>
time_t current_time = 2000000;
std::string output;
CHAR_DATA *target;
int tier = 3, rewards = 0, blood_given = 0, difficult = 0;
bool helpless = true, pinned = false, slave = false;
FACTION_TYPE faction = {};
OBJ_DATA blood = {}; OBJ_INDEX_DATA blood_index = {};
bool is_virgin(CHAR_DATA *) { return false; }
bool is_faeborn(CHAR_DATA *) { return false; }
bool is_angelborn(CHAR_DATA *) { return false; }
bool is_demonborn(CHAR_DATA *) { return false; }
bool is_demigod(CHAR_DATA *) { return false; }
bool is_vampire(CHAR_DATA *) { return false; }
// These tests exercise the unchanged player response flow. Pedestrian commands
// and their null-PC eligibility branches are covered in test_pedestrian_commands.
bool pedestrian(CHAR_DATA *) { return false; }
bool pedestrian_helpless(CHAR_DATA *) { return false; }
bool pedestrian_drain(CHAR_DATA *, CHAR_DATA *) { assert(false); return false; }
bool is_ghost(CHAR_DATA *) { return false; }
bool in_fight(CHAR_DATA *) { return false; }
bool is_safe(CHAR_DATA *, CHAR_DATA *) { return false; }
bool room_hostile(ROOM_INDEX_DATA *) { return false; }
void start_hostilefight(CHAR_DATA *) {}
bool is_werewolf(CHAR_DATA *) { return false; }
bool generic_faction_vnum(int) { return false; }
int blood_level(CHAR_DATA *, CHAR_DATA *) { return 1; }
OBJ_INDEX_DATA *get_obj_index(int) { return &blood_index; }
OBJ_DATA *create_object(OBJ_INDEX_DATA *, int) { return &blood; }
void obj_to_char(OBJ_DATA *, CHAR_DATA *) { ++blood_given; }
bool is_dreaming(CHAR_DATA *ch) { return ch->pcdata->dream_room > 0; }
bool physical_dreamer(CHAR_DATA *) { return false; }
bool is_helpless(CHAR_DATA *) { return helpless; }
bool is_pinned(CHAR_DATA *) { return pinned; }
bool dream_slave(CHAR_DATA *) { return slave; }
bool is_super(CHAR_DATA *ch) { return ch->race != RACE_HUMAN; }
bool is_gm(CHAR_DATA *) { return false; }
int get_tier(CHAR_DATA *) { return tier; }
int get_trust(CHAR_DATA *ch) { return ch->level; }
bool institute_room(ROOM_INDEX_DATA *) { return false; }
bool has_weakness(CHAR_DATA *, CHAR_DATA *) { return false; }
bool is_weakness(CHAR_DATA *, CHAR_DATA *) { return false; }
bool are_allies(CHAR_DATA *, CHAR_DATA *) { return false; }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a,b) != 0; }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
char *PERS(CHAR_DATA *ch, CHAR_DATA *) { return ch->name; }
char *dream_name(CHAR_DATA *ch) { return ch->name; }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void page_to_char(const char *s, CHAR_DATA *ch) { send_to_char(s,ch); }
void printf_to_char(CHAR_DATA *, char *fmt, ...) {
  char buf[8192]; va_list args; va_start(args,fmt);
  vsnprintf(buf,sizeof(buf),fmt,args); va_end(args); output += buf;
}
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
void dreamscape_message(CHAR_DATA *, int, char *) {}
void become_difficult(CHAR_DATA *) { ++difficult; }
void handout_lifeforce(CHAR_DATA *) {}
void villain_mod(CHAR_DATA *, int, char *) {}
void use_lifeforce(CHAR_DATA *ch, int amount, char *) { ch->lf_used += amount; }
void take_lifeforce(CHAR_DATA *ch, int amount, char *) { ch->lf_taken += amount; }
void give_lifeforce(CHAR_DATA *ch, int amount, char *reason) {
  ++rewards; record_feeding(ch, amount, reason);
}
void institute_victimize(CHAR_DATA *, CHAR_DATA *, int) {}
void give_respect_noecho(CHAR_DATA *ch, int amount, int fac) {
  assert(fac == FACTION_CORTEX);
  if (IS_FLAG(ch->comm, COMM_NOLEADER)) amount = amount * 2 / 3;
  ch->esteem_faction += amount;
}
FACTION_TYPE *clan_lookup(int) { return &faction; }
int position_difference(FACTION_TYPE *, FACTION_TYPE *) { return 0; }
void gain_resources(int, int, CHAR_DATA *, char *) {}
void give_intel(CHAR_DATA *, int) {}
void guest_match(CHAR_DATA *) {}
void log_string(const char *) {}
void wiznet(char *, CHAR_DATA *, OBJ_DATA *, long, long, int) {}
void process_prey_emote(CHAR_DATA *) {}
void process_villain_emote(CHAR_DATA *) {}
int number_percent() { return 1; }
void free_string(char *) {}
char *str_dup(const char *s) { return const_cast<char *>(s); }
CHAR_DATA *get_char_room(CHAR_DATA *, ROOM_INDEX_DATA *, char *) { return target; }
CHAR_DATA *get_char_dream(CHAR_DATA *, char *) { return target; }
char *one_argument_nouncap(char *arg, char *first) {
  while (*arg && *arg != ' ') *first++ = *arg++;
  *first = 0; while (*arg == ' ') ++arg; return arg;
}
'''
source += section('feeding.c', '// These intervals', 'void feeding_update(')
source += section('institute.c', '  char *const victimize_actions', '  _DOFUN(do_victimtest)')
source += section('institute.c', '  bool nice_victimize(', '  void become_difficult(')
source += section('institute.c', '  // Only an actual shared scene', '  void victimize_emote_process(')
source += section('institute.c', '  void victimize_emote_process(', '  void victim_prompt(')
source += section('institute.c', '  void victim_prompt(', '  void institute_victimize(')
source += r'''
void tick(CHAR_DATA *ch) {
'''
source += section('update.c', '    if (ch->pcdata->victimize_vic_timer > 0) {', '    if (IS_FLAG(ch->comm, COMM_RUNNING))')
source += r'''
}
int main() {
  CHAR_DATA actor = {}, victim = {}, npc = {};
  PC_DATA ap = {}, vp = {}; ROOM_INDEX_DATA room = {}, elsewhere = {};
  actor.pcdata = &ap; victim.pcdata = &vp;
  actor.race = victim.race = RACE_NEWVAMPIRE;
  actor.name = (char *)"Actor"; victim.name = (char *)"Victim";
  actor.in_room = victim.in_room = &room;
  victim.played = 100 * 3600; target = &victim;
  auto prepare = [&](int action) {
    clear_victim_response(&victim);
    char command[256]; snprintf(command,sizeof(command),"Victim %s",victimize_actions[action]);
    do_victimize(&actor, command); assert(ap.victimize_char_select == action);
    victimize_emote_process(&actor);
    assert(vp.victimize_vic_response_to == action && vp.victimize_vic_timer == 120);
  };
  for (int action = 1; action <= VICTIMIZE_MAX; ++action) {
    for (bool intel : {false, true}) {
      bool seen[RESPONSE_MAX + 1] = {}; int previous = 101;
      for (int n = 1; n <= RESPONSE_MAX; ++n) {
        int r = victim_response_at(action,n,intel);
        if (r < 0) break;
        assert(!seen[r]); seen[r] = true;
        assert(response_value(action,r) <= previous); previous = response_value(action,r);
      }
      for (int r = 1; r <= RESPONSE_MAX; ++r)
        assert(seen[r] == (response_value(action,r) >= 0 && (intel || r != RESPONSE_INTEL)));
      assert(seen[RESPONSE_STOIC]);
    }
    prepare(action);
    int before = rewards; process_victim_number(&victim,1);
    assert(rewards == before + 1);
    process_victim_number(&victim,1); assert(rewards == before + 1);
  }
  for (tier = 3; tier <= 5; ++tier) {
    ap.monster_fed = -10000;
    for (int exchange = 0; exchange < 3; ++exchange) {
      prepare(exchange % 2 ? VICTIMIZE_BANTER : VICTIMIZE_MILDPAIN);
      process_victim_number(&victim,1);
      assert(ap.last_feeding == current_time);
      current_time += 60;
    }
    int days = tier == 3 ? 30 : tier == 4 ? 21 : 14;
    current_time = ap.last_feeding + days * 86400 - 1;
    assert(feeding_stage(&actor) == 0);
    ++current_time; assert(feeding_stage(&actor) == 1);
  }
  prepare(VICTIMIZE_MILDPAIN); output.clear();
  int before = rewards;
  for (int n : {-1,0,33,999}) process_victim_number(&victim,n);
  process_victim_choice(&victim,RESPONSE_INTEL);
  assert(rewards == before && vp.victimize_vic_select == 0);
  for (int i = 0; i < 12; ++i) tick(&victim);
  assert(vp.victimize_vic_timer == 60 && output.find("One minute") != std::string::npos);
  for (int i = 0; i < 12; ++i) tick(&victim);
  assert(!vp.victimize_vic_timer && !vp.victimize_vic_point && rewards == before);
  prepare(VICTIMIZE_MILDPAIN); process_victim_number(&victim,1);
  for (int i = 0; i < 179; ++i) tick(&victim);
  assert(vp.victimize_vic_timer == 5); tick(&victim); assert(!vp.victimize_vic_timer && !vp.victimize_vic_point);
  prepare(VICTIMIZE_MILDPAIN);
  vp.intel = 1000; output.clear(); victim_prompt(&victim);
  assert(output.find("Provide Intel") != std::string::npos);
  process_victim_choice(&victim,RESPONSE_INTEL); assert(vp.victimize_vic_select == RESPONSE_INTEL);
  vp.intel = 0;
  prepare(VICTIMIZE_MILDPAIN); before = rewards;
  victim.in_room = &elsewhere;
  process_victim_choice(&victim,RESPONSE_SCREAMPAIN);
  assert(rewards == before && !vp.victimize_vic_point);
  assert(!victimize_together(&actor,&victim)); // Both inactive dream IDs are zero.
  ap.dream_room = vp.dream_room = 42; assert(victimize_together(&actor,&victim));
  vp.dream_room = 43; assert(!victimize_together(&actor,&victim));
  victim.in_room = &room; assert(!victimize_together(&actor,&victim));
  ap.dream_room = vp.dream_room = 0;
  assert(!victimize_together(&actor,&actor));
  SET_FLAG(npc.act,ACT_IS_NPC); assert(!victimize_together(&actor,&npc));
  target = &npc; do_victimize(&actor,(char *)"NPC bleed"); assert(!ap.victimize_char_select);
  target = &victim; helpless = false; pinned = true;
  prepare(VICTIMIZE_MILDPAIN); process_victim_number(&victim,1);
  assert(vp.victimize_vic_select > 0);
  pinned = false; slave = true; prepare(VICTIMIZE_MILDPAIN);
  slave = false; before = rewards; process_victim_number(&victim,1);
  assert(rewards == before && !vp.victimize_vic_point);
  helpless = true;
  prepare(VICTIMIZE_MILDPAIN);
  do_victimize(&actor,(char *)"Victim banter"); assert(!ap.victimize_char_select);
  clear_victim_response(&victim);
  do_victimize(&actor,(char *)"Victim banter");
  victim.in_room = &elsewhere; victimize_emote_process(&actor);
  assert(!ap.victimize_char_select && !vp.victimize_vic_timer);
  victim.in_room = &room; vp.last_victim_bled = current_time;
  do_victimize(&actor,(char *)"Victim bleed"); assert(!ap.victimize_char_select);
  current_time += 4 * 86400; do_victimize(&actor,(char *)"Victim bleed");
  assert(ap.victimize_char_select == VICTIMIZE_BLEED);
  victimize_emote_process(&actor); process_victim_number(&victim,1);
  before = blood_given; victimize_emote_process(&victim);
  assert(blood_given == before + 1 && vp.last_victim_bled == current_time);
  victimize_emote_process(&victim); assert(blood_given == before + 1);
  do_victimize(&actor,(char *)"Victim bleed"); assert(!ap.victimize_char_select);
  actor.race = RACE_HUMAN;
  actor.fcore = victim.fcore = FACTION_CORTEX;
  current_time = (current_time / 86400 + 1) * 86400;
  prepare(VICTIMIZE_MILDPAIN);
  process_victim_number(&victim, 999);
  assert(actor.esteem_faction == 0);
  process_victim_number(&victim, 1);
  assert(actor.esteem_faction == 100 && ap.cortex_victimize_standing == 100);
  process_victim_number(&victim, 1);
  assert(actor.esteem_faction == 100); // A response cannot pay twice.
  for (int i = 0; i < 12; ++i) {
    prepare(VICTIMIZE_MILDPAIN); process_victim_number(&victim, 1);
  }
  assert(actor.esteem_faction == 1000 && ap.cortex_victimize_standing == 1000);
  current_time = (current_time / 86400 + 1) * 86400 - 1;
  cortex_victimize_standing(&actor, &victim);
  assert(actor.esteem_faction == 1000);
  ++current_time;
  prepare(VICTIMIZE_MILDPAIN); process_victim_number(&victim, 1);
  assert(actor.esteem_faction == 1100 && ap.cortex_victimize_standing == 100);
  prepare(VICTIMIZE_MILDPAIN); process_victim_choice(&victim, RESPONSE_STOIC);
  assert(actor.esteem_faction == 1100);
  actor.race = RACE_NEWVAMPIRE; cortex_victimize_standing(&actor, &victim);
  actor.race = RACE_HUMAN; victim.race = RACE_HUMAN;
  cortex_victimize_standing(&actor, &victim);
  victim.race = RACE_NEWVAMPIRE; victim.fcore = FACTION_SCUM;
  cortex_victimize_standing(&actor, &victim);
  victim.fcore = FACTION_CORTEX; actor.fcore = FACTION_SCUM;
  cortex_victimize_standing(&actor, &victim);
  actor.fcore = FACTION_CORTEX;
  cortex_victimize_standing(&actor, &actor);
  cortex_victimize_standing(&actor, &npc);
  cortex_victimize_standing(nullptr, &victim);
  assert(actor.esteem_faction == 1100 && ap.cortex_victimize_standing == 100);
  ap.cortex_victimize_standing = 975;
  cortex_victimize_standing(&actor, &victim);
  assert(actor.esteem_faction == 1125 && ap.cortex_victimize_standing == 1000);
  current_time += 86400;
  SET_FLAG(actor.comm, COMM_NOLEADER);
  cortex_victimize_standing(&actor, &victim);
  assert(actor.esteem_faction == 1191 && ap.cortex_victimize_standing == 66);
  puts("Victimize flows, guards, feeding deadlines, and Cortex standing eligibility/daily cap passed.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-victimize-') as tmp:
    path = Path(tmp)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-fsanitize=address,undefined',
                    '-no-pie', '-I', str(ROOT / 'src'), str(path / 'test.cc'),
                    '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
