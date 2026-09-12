#!/usr/bin/env python3
"""Compile the actual look helpers against small, instrumented engine stubs.

Run with python3 tools/test_look_optimization.py (requires g++).
No world files are loaded or changed.
"""
from pathlib import Path
import subprocess
import tempfile

source = (Path(__file__).resolve().parents[1] / 'src/act_info.c').read_text()


def section(start, end, text=source):
    offset = text.index(start)
    return text[offset:text.index(end, offset)]


stubs = r'''
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <list>
#include <string>
#include <unordered_map>
#include <vector>
#define TRUE true
#define FALSE false
#define MAX_STRING_LENGTH 4096
#define COMM_COMBINE 1
#define ITEM_WARDROBE 1
#define PLR_SHROUD 1
#define WEAR_NONE -1
#define CON_PLAYING 0
#define ITEM_FLASHLIGHT 7
#define ITEM_OFF 2
#define SECT_FOREST 9
#define IS_NPC(c) ((c)->npc)
#define IS_FLAG(v,f) ((v)&(f))
#define IS_SET(v,f) ((v)&(f))
#define CH(d) ((d)->original ? (d)->original : (d)->character)
struct ROOM_INDEX_DATA;
struct OBJ_DATA;
struct PC_DATA { int account = 0, litup = 0; char *place = nullptr; };
struct DESCRIPTOR_DATA;
struct CHAR_DATA {
  DESCRIPTOR_DATA *desc = nullptr;
  ROOM_INDEX_DATA *in_room = nullptr;
  PC_DATA *pcdata = nullptr;
  bool npc = false, gm = false;
  int comm = 0, act = 0, score = 0, signals = 0;
  int recent_moved = -301, world = 0;
  OBJ_DATA *held = nullptr, *worn = nullptr;
};
struct DESCRIPTOR_DATA {
  int connected = CON_PLAYING;
  CHAR_DATA *character = nullptr, *original = nullptr;
};
typedef std::list<CHAR_DATA*> CharList;
typedef std::list<DESCRIPTOR_DATA*> DescList;
DescList descriptor_list;
CharList char_list;
struct EXTRA_DESCR_DATA { char *keyword; EXTRA_DESCR_DATA *next = nullptr; };
struct ROOM_INDEX_DATA {
  CharList *people = nullptr;
  OBJ_DATA *contents = nullptr;
  EXTRA_DESCR_DATA *places = nullptr;
  bool shadowed = false, haven = false, battle = false, fighting = false;
  int x = 0, y = 0, sector_type = 0, level = 0;
};
struct OBJ_DATA {
  OBJ_DATA *next_content = nullptr;
  CHAR_DATA *carried_by = nullptr;
  int wear_loc = WEAR_NONE, extra_flags = 0;
  bool big = false, visible = true;
  char *name = nullptr;
  int item_type = 0, value[1] = {0};
};
struct Buffer {
  std::string text;
  void strcat(const char *s) { text += s; }
};
std::string output;
int allocations = 0, score_calls = 0, signal_calls = 0;
void *alloc_mem(size_t n) { ++allocations; return malloc(n); }
void free_mem(void *p, size_t) { --allocations; free(p); }
char *str_dup(const char *s) { ++allocations; return strdup(s); }
void free_string(char *s) { --allocations; free(s); }
bool is_big(OBJ_DATA *o) { return o->big; }
bool can_see_obj(CHAR_DATA *, OBJ_DATA *o) { return o->visible; }
bool is_name(char *a, char *b) { return !strcmp(a, b); }
char *format_obj_to_char(OBJ_DATA *o, CHAR_DATA *, bool) { return o->name; }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void page_to_char(const Buffer &b, CHAR_DATA *) { output += b.text; }
int get_attract(CHAR_DATA *c, CHAR_DATA *) { ++score_calls; return c->score; }
int gm_calls = 0;
bool is_gm(CHAR_DATA *c) { ++gm_calls; return c->gm; }
bool seems_suggestible(CHAR_DATA *c) { ++signal_calls; return c->signals & 1; }
bool seems_suffer_sensitive(CHAR_DATA *c) { ++signal_calls; return c->signals & 2; }
bool seems_fatesensitive(CHAR_DATA *c) { ++signal_calls; return c->signals & 4; }
const int SKILL_MINDREADING = 125;
int get_skill(CHAR_DATA *c, int) { ++signal_calls; return (c->signals & 8) ? 1 : 0; }
int event_cleanse = 0, shadow_calls = 0, world_calls = 0;
bool shadowcloaked(ROOM_INDEX_DATA *r) { ++shadow_calls; return r->shadowed; }
OBJ_DATA *get_held(CHAR_DATA *c, int) { return c->held; }
OBJ_DATA *get_worn(CHAR_DATA *c, int) { return c->worn; }
int safe_strlen(const char *s) { return s ? strlen(s) : 0; }
int str_cmp(const char *a, const char *b) { return strcasecmp(a, b); }
bool battleground(ROOM_INDEX_DATA *r) { return r->battle; }
bool room_fight(ROOM_INDEX_DATA *r, bool, bool, bool) { return r->fighting; }
int room_level(ROOM_INDEX_DATA *r) { return r->level; }
bool in_haven(ROOM_INDEX_DATA *r) { return r->haven; }
int get_world(CHAR_DATA *c) { ++world_calls; return c->world; }
bool is_cloaked(CHAR_DATA *c) { return c->act & 2; }
bool public_room(ROOM_INDEX_DATA *) { return true; }
bool can_see(CHAR_DATA *, CHAR_DATA *c) { return !(c->act & 4); }
int charlineofsight_character(CHAR_DATA *c, CHAR_DATA *v) {
  auto dx = (long long)c->in_room->x - v->in_room->x;
  auto dy = (long long)c->in_room->y - v->in_room->y;
  return dx > 100 || dx < -100 || dy > 100 || dy < -100 ? -1 : 1;
}
std::vector<CHAR_DATA*> remote_shown;
void show_char_to_char_0(CHAR_DATA *v, CHAR_DATA *, int) { remote_shown.push_back(v); }
'''

tests = r'''
int main() {
  CHAR_DATA viewer;
  DESCRIPTOR_DATA descriptor;
  viewer.desc = &descriptor;
  OBJ_DATA objects[6];
  const char *names[] = {"apple", "pear", "apple", "Apple", "pear", ""};
  for (int i = 0; i < 6; ++i) {
    objects[i].name = const_cast<char*>(names[i]);
    if (i < 5) objects[i].next_content = &objects[i+1];
  }
  viewer.comm = COMM_COMBINE;
  show_list_to_char(objects, &viewer, false, false, nullptr);
  assert(output == "( 2) apple\n\r( 2) pear\n\r      Apple\n\r");
  assert(allocations == 0);
  output.clear(); viewer.comm = 0;
  show_list_to_char(objects, &viewer, false, false, nullptr);
  assert(output == "apple\n\rpear\n\rapple\n\rApple\n\rpear\n\r");
  output.clear(); viewer.comm = COMM_COMBINE;
  objects[0].visible = false; objects[1].wear_loc = 0;
  objects[2].extra_flags = ITEM_WARDROBE;
  show_list_to_char(objects, &viewer, false, false, const_cast<char*>("pear"));
  assert(output == "      pear\n\r");
  output.clear();
  show_list_to_char(objects, &viewer, false, true, const_cast<char*>("absent"));
  assert(output == "     Nothing.\n\r");
  assert(allocations == 0);
  show_list_to_char(objects, nullptr, false, false, nullptr);

  // Compare order, including tied scores, with the previous comparator.
  std::vector<CHAR_DATA> people(1000);
  CharList list;
  for (int i = 0; i < 1000; ++i) {
    people[i].score = (i * 37) % 101;
    list.push_back(&people[i]);
  }
  std::vector<CHAR_DATA*> reference(list.begin(), list.end());
  std::sort(reference.begin(), reference.end(), [](CHAR_DATA *a, CHAR_DATA *b) {
    return get_attract(b, nullptr) < get_attract(a, nullptr);
  });
  int previous_calls = score_calls;
  score_calls = 0;
  auto sorted = sorted_look_characters(&list, &viewer);
  assert(score_calls == 1000);
  for (int i = 0; i < 1000; ++i) assert(sorted[i].character == reference[i]);
  people[0].score = 200;
  assert(sorted_look_characters(&list, &viewer)[0].character == &people[0]);
  printf("PASS: sorting 1000 occupants: %d -> 1000 score calls; order preserved.\n", previous_calls);

  ROOM_INDEX_DATA room, elsewhere;
  PC_DATA viewer_pc, other_pc;
  viewer.pcdata = &viewer_pc; other_pc.account = 1;
  CHAR_DATA candidate;
  candidate.pcdata = &other_pc; candidate.in_room = &room; candidate.signals = 15;
  DESCRIPTOR_DATA d;
  d.character = &candidate; descriptor_list.push_back(&d);
  bool desire, suffering, fate, mindreading;
  for (int excluded = 0; excluded < 7; ++excluded) {
    candidate.in_room = excluded == 0 ? &elsewhere : &room;
    candidate.gm = excluded == 1;
    other_pc.account = excluded == 2 ? 0 : 1;
    candidate.act = excluded == 3 ? PLR_SHROUD : 0;
    d.connected = excluded == 4 ? 1 : CON_PLAYING;
    candidate.npc = excluded == 5;
    d.original = excluded == 6 ? &viewer : nullptr;
    look_room_signals(&room, &viewer, desire, suffering, fate, mindreading);
    assert(!desire && !suffering && !fate && !mindreading);
  }
  d.original = nullptr;
  signal_calls = 0;
  look_room_signals(&room, &viewer, desire, suffering, fate, mindreading);
  assert(desire && suffering && fate && mindreading && signal_calls == 4);
  candidate.signals = 2;
  look_room_signals(&room, &viewer, desire, suffering, fate, mindreading);
  assert(!desire && suffering && !fate && !mindreading);
  candidate.signals = 8;
  look_room_signals(&room, &viewer, desire, suffering, fate, mindreading);
  assert(!desire && !suffering && !fate && mindreading);
  puts("PASS: object grouping, case, order, filtering, allocations and room signal exclusions.");

  // Lighting must preserve the existing floor-light multiplier and litup rules.
  CharList occupants;
  room.people = &occupants;
  OBJ_DATA lights[100];
  for (int i = 0; i < 100; ++i) {
    lights[i].item_type = ITEM_FLASHLIGHT; lights[i].value[0] = 2;
    if (i < 99) lights[i].next_content = &lights[i+1];
  }
  room.contents = lights;
  assert(torch_count(&room) == 0 && shadow_calls == 0);
  for (int i = 0; i < 100; ++i) {
    people[i].in_room = &room; people[i].pcdata = &other_pc;
    people[i].held = lights; people[i].worn = lights;
    occupants.push_back(&people[i]);
  }
  assert(torch_count(&room) == 10200 && shadow_calls == 1);
  other_pc.litup = 1;
  assert(torch_count(&room) == 10500);
  room.shadowed = true;
  assert(torch_count(&room) == 300);
  event_cleanse = 1;
  assert(torch_count(&room) == 0);
  event_cleanse = 0; other_pc.litup = 0; room.shadowed = false;
  lights[0].next_content = &lights[0];
  assert(torch_count(&room) == 300);
  lights[0].extra_flags = ITEM_OFF;
  assert(torch_count(&room) == 0);
  lights[0].extra_flags = 0; lights[0].value[0] = 1;
  assert(torch_count(&room) == 0);
  puts("PASS: 100 occupants/100 floor lights: shadow scans 10200 -> 1; lighting values preserved.");

  std::vector<PC_DATA> places(100);
  std::vector<std::string> names_storage(100);
  EXTRA_DESCR_DATA static_place;
  static_place.keyword = const_cast<char*>("Bench");
  room.places = &static_place;
  for (int i = 0; i < 100; ++i) {
    names_storage[i] = "place " + std::to_string(i);
    places[i].place = const_cast<char*>(names_storage[i].c_str());
    people[i].pcdata = &places[i];
  }
  places[0].place = const_cast<char*>("bench");
  places[1].place = const_cast<char*>("Table");
  places[2].place = const_cast<char*>("TABLE");
  places[3].place = nullptr;
  places[4].place = const_cast<char*>("ab");
  char *collected[20] = {};
  assert(collect_look_places(&room, collected, 20) == 20);
  assert(!strcmp(collected[0], "Table") && !strcmp(collected[1], "ab"));
  assert(!strcmp(collected[19], "place 22"));
  assert(collect_look_places(&room, collected, 1) == 1);
  puts("PASS: dynamic-place case matching, static exclusion, nulls, order and display cap.");

  std::vector<DESCRIPTOR_DATA> crowd(1000);
  descriptor_list.clear();
  for (int i = 0; i < 1000; ++i) {
    people[i].in_room = i < 900 ? &elsewhere : &room;
    crowd[i].character = &people[i]; descriptor_list.push_back(&crowd[i]);
  }
  gm_calls = 0;
  assert(crowded_room(&room) && gm_calls == 8);
  room.level = 1; assert(!crowded_room(&room)); room.level = 0;
  for (int i = 907; i < 1000; ++i) crowd[i].connected = 1;
  assert(!crowded_room(&room));
  crowd[907].connected = CON_PLAYING;
  people[907].recent_moved = 0; assert(!crowded_room(&room));
  people[907].recent_moved = -300; assert(crowded_room(&room));
  puts("PASS: crowded-room threshold, movement and descriptor filters; 1000 -> 8 GM checks.");

  viewer.in_room = &room;
  elsewhere.x = 101;
  ROOM_INDEX_DATA edge;
  edge.x = 100; edge.y = -100;
  char_list.clear();
  for (int i = 0; i < 1000; ++i) {
    people[i].in_room = i < 990 ? &elsewhere : &edge;
    char_list.push_back(&people[i]);
  }
  people[997].world = 1; people[998].act = 2; people[999].act = 4;
  world_calls = 0;
  alt_remote_view(&viewer);
  assert(world_calls == 11 && remote_shown.size() == 7);
  for (int i = 0; i < 7; ++i) assert(remote_shown[i] == &people[990+i]);
  puts("PASS: remote-view distance boundaries and character filters; 1001 -> 11 world checks.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-look-test-') as directory:
    cpp = Path(directory) / 'look.cpp'
    binary = Path(directory) / 'look-test'
    cpp.write_text(stubs + section('  void show_list_to_char(OBJ_DATA *list',
                                  '  char *const consider_colours')
                   + section('  struct LookCharacter', '  void show_char_to_char(CharList *list')
                   + section('  static void look_room_signals', '  _DOFUN(do_look)')
                   + section('  int torch_count(ROOM_INDEX_DATA *room)', '  int light_level(')
                   + section('  static int collect_look_places', '  bool has_dynamic_places(')
                   + section('  void alt_remote_view(', '  void remote_view(')
                   + section('  bool crowded_room(', '  bool gravesite(',
                             (Path(__file__).resolve().parents[1] / 'src/lookup.c').read_text())
                   + tests)
    subprocess.run(['g++', '-std=c++11', '-O2', '-Wall', '-Wextra',
                    '-Wno-unused-parameter', '-fsanitize=address,undefined',
                    str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
