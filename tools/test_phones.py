#!/usr/bin/env python3
"""Run production phone/scheme helpers and phone controls under ASan/UBSan (WSL/Linux)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def section(file, start, end):
    source = (ROOT / 'src' / file).read_text()
    begin = source.index(start)
    return source[begin:source.index(end, begin)]


source = r'''
#include "merc.h"
#include "recycle.h"
#include "global.h"
#include <algorithm>
#include <cassert>
#include <cstdarg>
#include <random>
time_t current_time = 100;
DescList descriptor_list;
vector<EVENT_TYPE *> EventVect;
vector<MATCH_TYPE *> MatchVect;
std::mt19937 random_engine(42);
std::string output;
CHAR_DATA *saved_character = nullptr;
int saves = 0;
char *str_dup(const char *s) { return strdup(s ? s : ""); }
void free_string(char *s) { free(s); }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
bool is_name(char *s, char *names) { return names && strstr(names, s); }
bool is_animal(CHAR_DATA *) { return false; }
bool is_gm(CHAR_DATA *ch) { return ch->level == 100; }
int get_animal_genus(CHAR_DATA *, int) { return 0; }
int get_skill(CHAR_DATA *, int) { return 5; }
int get_trust(CHAR_DATA *ch) { return ch->level; }
bool is_town_blackout() { return false; }
bool is_blind(CHAR_DATA *) { return false; }
bool is_dreaming(CHAR_DATA *) { return false; }
bool cell_signal(CHAR_DATA *) { return true; }
bool can_see(CHAR_DATA *, CHAR_DATA *) { return true; }
CHAR_DATA *get_char_room(CHAR_DATA *, ROOM_INDEX_DATA *, char *) { return nullptr; }
bool at_workshop(CHAR_DATA *) { return true; }
bool at_jeweler(CHAR_DATA *) { return true; }
void maketownmap(CHAR_DATA *) {}
bool holding_phone(CHAR_DATA *) { return true; }
bool wearing_phone(CHAR_DATA *) { return false; }
OBJ_DATA *get_eq_char(CHAR_DATA *ch, int wear) {
  for (auto *obj = ch->carrying; obj; obj = obj->next_content)
    if (obj->wear_loc == wear) return obj;
  return nullptr;
}
OBJ_DATA *get_held(CHAR_DATA *ch, int type) {
  for (auto *obj = ch->carrying; obj; obj = obj->next_content)
    if (obj->item_type == type && (obj->wear_loc == WEAR_HOLD || obj->wear_loc == WEAR_HOLD_2)) return obj;
  return nullptr;
}
char *one_argument_nouncap(char *argument, char *first) {
  while (*argument == ' ') ++argument;
  while (*argument && *argument != ' ') *first++ = *argument++;
  *first = 0;
  while (*argument == ' ') ++argument;
  return argument;
}
char *newtexttime() { return (char *)"12:00"; }
int number_range(int low, int high) { return std::uniform_int_distribution<int>(low, high)(random_engine); }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void printf_to_char(CHAR_DATA *, char *fmt, ...) {
  char buf[MSL]; va_list args; va_start(args,fmt);
  vsnprintf(buf,sizeof(buf),fmt,args); va_end(args); output += buf;
}
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
void save_char_obj(CHAR_DATA *ch, bool, bool) { ++saves; saved_character = ch; }
void do_hangup(CHAR_DATA *, char *) { assert(false); } // No calls in this unit fixture.
EXTRA_DESCR_DATA *new_extra_descr() {
  auto *ed = new EXTRA_DESCR_DATA{};
  ed->description = str_dup(""); return ed;
}
void free_extra_descr(EXTRA_DESCR_DATA *ed) {
  free_string(ed->description); free_string(ed->keyword); delete ed;
}
'''
source += section('act_comm.c', '  static CHAR_DATA *phone_owner(', '  _DOFUN(do_call)')
source += section('act_comm.c', '  static OBJ_DATA *find_carried_phone(', '  _DOFUN(do_speeddial)')
source += section('act_obj.c', '  _DOFUN(do_phone)', '  // Based on mult_argument')
source += section('events.c', '  int scheme_cost(', '  int scheme_duration(')
# Extract the complete duration function without coupling to the next function name.
events = (ROOT / 'src/events.c').read_text()
start = events.index('  int scheme_duration(')
source += events[start:events.index('\n  }', start) + 5]
source += r'''
int main() {
  CHAR_DATA sender = {}, intended = {}, alice = {}, bob = {};
  PC_DATA pcs[4] = {};
  CHAR_DATA *chars[] = {&sender, &intended, &alice, &bob};
  ROOM_INDEX_DATA room = {};
  OBJ_DATA phones[4] = {};
  DESCRIPTOR_DATA descriptors[4] = {};
  const char *names[] = {"Sender", "Intended", "Alice", "Bob"};
  for (int i = 0; i < 4; ++i) {
    chars[i]->pcdata = &pcs[i]; chars[i]->name = (char *)names[i]; chars[i]->in_room = &room;
    phones[i].item_type = ITEM_PHONE; phones[i].value[0] = 100 + i;
    phones[i].name = (char *)"phone"; phones[i].description = (char *)"phone";
    phones[i].material = str_dup(""); phones[i].wear_loc = WEAR_HOLD;
    phones[i].carried_by = chars[i]; chars[i]->carrying = &phones[i];
    descriptors[i].valid = true; descriptors[i].connected = CON_PLAYING;
    descriptors[i].character = chars[i]; descriptor_list.push_back(&descriptors[i]);
  }
  EVENT_TYPE scheme = {};
  scheme.valid = true; scheme.type = EVENT_COMPROMISED;
  scheme.target = (char *)"sender"; scheme.active_time = 100; scheme.deactive_time = 200;
  EventVect.push_back(&scheme);
  assert(scheme_cost(EVENT_COMPROMISED) == 30000 && scheme_duration(EVENT_COMPROMISED) == 48);
  assert(compromised_text_sender(&sender));
  assert(!compromised_text_sender(&alice) && !compromised_text_sender(nullptr));
  current_time = 99; assert(!compromised_text_sender(&sender));
  current_time = 200; assert(!compromised_text_sender(&sender));
  current_time = 100; scheme.valid = false; assert(!compromised_text_sender(&sender));
  scheme.valid = true; scheme.type = 0; scheme.typetwo = EVENT_COMPROMISED;
  assert(compromised_text_sender(&sender));
  EventVect.push_back(&scheme); // Multiple matching schemes must still copy only once.
  int alice_count = 0, bob_count = 0;
  for (int i = 0; i < 200; ++i) {
    int previous = saves;
    leak_compromised_text(&sender, 100, "Meet me at midnight.", &intended);
    assert(saves == previous + 1);
    assert(saved_character == &alice || saved_character == &bob);
    if (saved_character == &alice) ++alice_count; else ++bob_count;
    assert(strstr(saved_character->carrying->material, "Meet me at midnight."));
    for (int j = 2; j < 4; ++j) { free_string(phones[j].material); phones[j].material = str_dup(""); }
  }
  assert(alice_count > 60 && bob_count > 60); // Both eligible recipients are sampled.
  GROUPTEXT_TYPE group = {}; group.pnumber[0] = 101; group.pnumber[1] = 102;
  assert(group_text_member(&group, 102) && !group_text_member(&group, 0));
  leak_compromised_text(&sender, 100, "group message", nullptr, &group);
  assert(saved_character == &bob);
  SET_BIT(phones[3].extra_flags, ITEM_OFF);
  int previous = saves;
  leak_compromised_text(&sender, 100, "no eligible recipients", nullptr, &group);
  assert(saves == previous);
  REMOVE_BIT(phones[3].extra_flags, ITEM_OFF);
  descriptors[3].connected = -1;
  leak_compromised_text(&sender, 100, "offline excluded", nullptr, &group); assert(saves == previous);
  descriptors[3].connected = CON_PLAYING;

  char history[MSL], line[MSL];
  free_string(phones[2].material); phones[2].material = str_dup(std::string(15990, 'x').c_str());
  assert(!format_phone_text(&phones[2], "sender", "too long", history, line));
  assert(strlen(phones[2].material) == 15990);
  leak_compromised_text(&sender, 100, "full inbox skipped", &intended); assert(saved_character == &bob);
  char *rolling = str_dup("");
  for (int i = 0; i < 200; ++i) append_text_history(&rolling, (std::to_string(i) + std::string(400, 'x')).c_str());
  assert(strlen(rolling) <= MSL - 1000 && strstr(rolling, "199xxx"));
  free_string(rolling);

  OBJ_DATA bag = {}, nested = {}, secondary = {};
  bag.item_type = ITEM_CONTAINER; bag.carried_by = &sender; bag.contains = &nested;
  nested.item_type = ITEM_PHONE; nested.name = (char *)"phone"; nested.value[0] = 555; nested.in_obj = &bag;
  secondary.item_type = ITEM_PHONE; secondary.name = (char *)"phone"; secondary.value[0] = 556;
  secondary.wear_loc = WEAR_HOLD_2; secondary.next_content = &bag;
  phones[0].next_content = &secondary;
  assert(find_phone(&sender, 555) == &nested && find_phone(&sender, 556) == &secondary);
  assert(find_phone(&sender, 999) == nullptr && find_phone(nullptr, 100) == nullptr);
  assert(phone_owner(&nested) == &sender);
  SET_BIT(bag.extra_flags, ITEM_WARDROBE);
  assert(find_phone(&sender, 555) == nullptr && phone_owner(&nested) == nullptr);

  auto command = [&](const char *value) { char input[100]; strcpy(input, value); do_phone(&sender, input); };
  command("on"); assert(!IS_SET(phones[0].extra_flags, ITEM_OFF));
  command("off"); assert(IS_SET(phones[0].extra_flags, ITEM_OFF));
  command("off"); assert(IS_SET(phones[0].extra_flags, ITEM_OFF));
  command("on"); assert(!IS_SET(phones[0].extra_flags, ITEM_OFF));
  command("signalboost"); assert(phones[0].extra_descr && IS_FLAG(sender.comm, COMM_RACIAL));
  auto loudspeaker = [&]() {
    for (auto *ed = phones[0].extra_descr; ed; ed = ed->next)
      if (!str_cmp(ed->keyword, "+loudspeaker")) return true;
    return false;
  };
  command("loudspeaker"); assert(loudspeaker());
  command("loudspeaker on"); assert(loudspeaker());
  command("loudspeaker invalid"); assert(loudspeaker());
  command("loudspeaker off"); assert(!loudspeaker());
  command("loudspeaker off"); assert(!loudspeaker());
  command("loudspeaker on"); assert(loudspeaker());
  command("loudspeaker"); assert(!loudspeaker());
  assert(phones[0].extra_descr && !str_cmp(phones[0].extra_descr->keyword, "+signalboost"));
  command("signalboost"); assert(phones[0].extra_descr); // Cooldown does not mutate the phone.
  REMOVE_FLAG(sender.comm, COMM_RACIAL);
  command("signalboost"); assert(!phones[0].extra_descr);
  phones[0].wear_loc = WEAR_BODY_1;
  secondary.wear_loc = WEAR_NONE;
  command("off"); assert(IS_SET(phones[0].extra_flags, ITEM_OFF));
  command("on"); assert(!IS_SET(phones[0].extra_flags, ITEM_OFF));
  for (auto &phone : phones) free_string(phone.material);
  puts("PASS: scheme windows, random single copies, exclusions, inbox/history bounds, phone lookup and controls");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-phone-test-') as temporary:
    path = Path(temporary)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-fsanitize=address,undefined', '-no-pie',
                    '-I', str(ROOT / 'src'), str(path / 'test.cc'), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
