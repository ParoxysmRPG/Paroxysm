#!/usr/bin/env python3
"""Compare actual expose commands with the previous scan algorithm (requires g++)."""
from pathlib import Path
import re
import subprocess
import tempfile


root = Path(__file__).resolve().parents[1]
info = (root / 'src/act_info.c').read_text()
objects = (root / 'src/act_obj.c').read_text()
constants = (root / 'src/const.h').read_text()


def section(text, start, end):
    offset = text.index(start)
    return text[offset:text.index(end, offset)]


stubs = r'''
#include <cassert>
#include <cctype>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <string>
#include <vector>
#define TRUE true
#define FALSE false
#define MSL 4096
#define IS_FLAG(value, flag) ((value) & (flag))
#define IS_SET(value, flag) ((value) & (flag))
#define ITEM_ARMORED (1 << 20)
#define _DOFUN(name) void name(CHAR_DATA *ch, char *argument)
enum { TO_CHAR, TO_ROOM };
'''
stubs += '\n'.join(re.findall(
    r'^#define (?:COVERS_\w+|MAX_COVERS|ITEM_CLOTHING|ITEM_JEWELRY|ITEM_CONTAINER|COMM_BLINDFOLD)\s+[^\n]+',
    constants, re.M)) + '\n'
wear_start = constants.rfind('enum', 0, constants.index('WEAR_NONE = -1'))
stubs += constants[wear_start:constants.index('}', wear_start) + 1] + ';\n'
stubs += section((root / 'src/tables.c').read_text(),
                 'const int cover_table[MAX_COVERS]', '// more pretty columns')
stubs += r'''
struct OBJ_DATA {
  OBJ_DATA *next_content = nullptr;
  int wear_loc = WEAR_NONE, exposed = 0, item_type = ITEM_CLOTHING;
  int value[5] = {}, extra_flags = 0, id = 0;
  bool visible = true;
  char *short_descr = const_cast<char*>("black cotton clothing");
  char *wear_string = const_cast<char*>("beneath the other layers");
};
struct PC_DATA {
  int exposed[MAX_COVERS] = {};
  char *focused_descs[MAX_COVERS] = {};
};
struct CHAR_DATA {
  OBJ_DATA *carrying = nullptr, *selected = nullptr;
  PC_DATA *pcdata;
  int comm = 0;
  bool bath = false, water = false, stream = false;
};
bool in_bath(CHAR_DATA *ch) { return ch->bath; }
bool pedestrian(CHAR_DATA *) { return false; }
bool deep_water(CHAR_DATA *ch) { return ch->water; }
bool in_stream(CHAR_DATA *ch) { return ch->stream; }
bool can_see_obj(CHAR_DATA *, OBJ_DATA *obj) { return obj->visible; }
int safe_strlen(const char *text) { return text ? strlen(text) : 0; }
int str_cmp(const char *a, const char *b) { return strcasecmp(a, b); }
bool is_number(const char *text) {
  if (!*text) return false;
  if (*text == '+' || *text == '-') ++text;
  if (!*text) return false;
  while (*text) if (!isdigit(*text++)) return false;
  return true;
}
bool is_name(const char *name, const char *text) {
  std::string value = std::string(" ") + text + " ";
  return value.find(std::string(" ") + name + " ") != std::string::npos;
}
int allocations = 0, eq_probes = 0, snapshot_probes = 0, coverage_calls = 0;
char *str_dup(const char *text) { ++allocations; return strdup(text); }
namespace haven {
std::string format_text(const char *format, ...) {
  char text[MSL];
  va_list args; va_start(args, format);
  vsnprintf(text, sizeof(text), format, args); va_end(args);
  return text;
}
}
std::vector<std::string> output;
void act(const char *text, CHAR_DATA *, OBJ_DATA *obj, void *, int type) {
  output.push_back(std::to_string(type) + ":" + text + ":" +
                   std::to_string(obj ? obj->id : -1));
}
void send_to_char(const char *text, CHAR_DATA *) { output.push_back(text); }
OBJ_DATA *get_obj_wear(CHAR_DATA *ch, char *name, bool) {
  return !strcmp(name, "item") ? ch->selected : nullptr;
}
bool does_cover(OBJ_DATA *, int);
bool does_conceal(OBJ_DATA *, OBJ_DATA *);
'''
snapshot = (root / 'src/equipment_snapshot.h').read_text().replace('#include "merc.h"', '')
snapshot = snapshot.replace('const int slot = obj->wear_loc;',
                            '++snapshot_probes; const int slot = obj->wear_loc;')
get_eq = section((root / 'src/handler.c').read_text(),
                 'OBJ_DATA *get_eq_char(', 'OBJ_DATA *get_held(')
get_eq = get_eq.replace('limit++;', 'limit++; ++eq_probes;')
parser = section((root / 'src/interp.c').read_text(),
                 '  char *one_argument_nouncap(', '  char *one_argument_true(')
coverage = section(info, '  bool is_covered_equipped(', '  bool is_covered(')
coverage = coverage.replace('    OBJ_DATA *obj;', '    ++coverage_calls;\n    OBJ_DATA *obj;')
visibility = section(info, '  bool can_see_wear_equipped(', '  bool can_see_wear(')
# The previous commands already used wrappers that built a snapshot per call.
# Keep those wrappers intact so probe counts measure only this command change.
legacy_coverage = section(info, '  bool is_covered(', '  bool is_transperant(').replace(
    'is_covered(', 'reference_covered(')
legacy_visibility = section(info, '  bool can_see_wear(', '  bool compare_characters(').replace(
    'can_see_wear(', 'reference_wear(')
helpers = section(info, '  bool is_transperant(', '  char *get_focused(')
commands = section(objects, '  _DOFUN(do_expose)', '  _DOFUN(do_arrange)')

tests = r'''
// Reference retains the old before/after loops over every cover and wear slot.
void reference_adjust(CHAR_DATA *ch, OBJ_DATA *obj, int location, bool expose) {
  if (!obj && location < 0) { send_to_char("You do not have that item.\n\r", ch); return; }
  act(obj ? "You adjust your $a $p." : "You adjust your clothes.", ch, obj, nullptr, TO_CHAR);
  act(obj ? "$n adjusts $s $p." : "$n adjusts $s clothes.", ch, obj, nullptr, TO_ROOM);
  int &state = obj ? obj->exposed : ch->pcdata->exposed[location];
  const int before = expose ? 0 : 111, after = expose ? 111 : 0;
  for (int i = 0; i < MAX_COVERS; ++i) {
    state = before;
    if (reference_covered(ch, cover_table[i]) == expose) {
      state = after;
      if (reference_covered(ch, cover_table[i]) != expose && safe_strlen(ch->pcdata->focused_descs[i]) > 5) {
        char first[MSL];
        char *rest = one_argument_nouncap(ch->pcdata->focused_descs[i], first);
        std::string text = expose ? "Revealing that; " : "Concealing that; ";
        if (!is_number(first)) { text += first; text += " "; }
        text += rest;
        act(text.c_str(), ch, nullptr, nullptr, TO_CHAR);
        act(text.c_str(), ch, nullptr, nullptr, TO_ROOM);
      }
    }
  }
  if (obj) {
    for (int slot = 0; slot < MAX_WEAR; ++slot) {
      state = before;
      OBJ_DATA *other = get_eq_char(ch, slot);
      if (!other || !can_see_obj(ch, obj) || reference_wear(ch, slot) != expose) {
        state = after;
        other = get_eq_char(ch, slot);
        if (other && can_see_obj(ch, obj) && reference_wear(ch, slot) == expose) {
          std::string text = expose ? "Revealing;" : "Concealing;";
          text += other->wear_string; text += " $o";
          act(text.c_str(), ch, other, nullptr, TO_CHAR);
          act(text.c_str(), ch, other, nullptr, TO_ROOM);
        }
      }
    }
  }
  state = after;
}

int main() {
  std::mt19937 random(7192);
  PC_DATA pc;
  CHAR_DATA ch;
  ch.pcdata = &pc;
  std::vector<OBJ_DATA> items(220);
  const char *locations[] = {"hands", "lowerarms", "upperarms", "feet", "lowerlegs",
    "forehead", "thighs", "groin", "arse", "lowerback", "upperback", "lowerchest",
    "breasts", "upperchest", "neck", "lowerface", "hair", "eyes"};
  const char *descriptions[] = {"42 numbered description", "Natural description",
    "'A quoted phrase' follows", "123456", "short", "", nullptr};
  long old_probes = 0, new_probes = 0;
  for (int trial = 0; trial < 500; ++trial) {
    const int count = trial % 5 == 0 ? 220 : random() % 60;
    ch.carrying = count ? &items[0] : nullptr;
    ch.comm = trial % 11 == 0 ? COMM_BLINDFOLD : 0;
    ch.bath = trial % 17 == 0; ch.water = trial % 19 == 0; ch.stream = trial % 23 == 0;
    ch.selected = count ? &items[random() % count] : nullptr;
    for (int i = 0; i < count; ++i) {
      items[i] = OBJ_DATA();
      items[i].id = i;
      items[i].next_content = i + 1 < count ? &items[i + 1] : nullptr;
      items[i].wear_loc = int(random() % (MAX_WEAR + 3)) - 1;
      items[i].value[0] = random() % 262144;
      items[i].value[3] = random() % 262144;
      items[i].value[4] = random() % 21;
      items[i].short_descr = const_cast<char*>(trial % 13 == 0 ? "white cotton shirt" : "black cotton clothing");
      items[i].item_type = i % 7 == 0 ? ITEM_JEWELRY : i % 9 == 0 ? ITEM_CONTAINER : ITEM_CLOTHING;
      items[i].exposed = random() % 2 ? 111 : 0;
      items[i].visible = random() % 5 != 0;
    }
    for (int i = 0; i < MAX_COVERS; ++i) {
      pc.exposed[i] = random() % 2 ? 111 : 0;
      pc.focused_descs[i] = const_cast<char*>(descriptions[random() % 7]);
    }
    for (int target = -2; target < MAX_COVERS; ++target) {
      for (bool expose : {false, true}) {
        PC_DATA saved = pc;
        const int object_state = ch.selected ? ch.selected->exposed : 0;
        output.clear(); eq_probes = snapshot_probes = 0;
        reference_adjust(&ch, target == -1 ? ch.selected : nullptr, target, expose);
        const auto expected = output;
        old_probes += eq_probes + snapshot_probes;
        const PC_DATA expected_pc = pc;
        const int expected_object = ch.selected ? ch.selected->exposed : 0;
        pc = saved;
        if (ch.selected) ch.selected->exposed = object_state;
        output.clear(); eq_probes = snapshot_probes = coverage_calls = 0;
        char argument[MSL];
        strcpy(argument, target == -2 ? "missing" : target == -1 ? "item" : locations[target]);
        if (expose) do_expose(&ch, argument); else do_unexpose(&ch, argument);
        assert(output == expected);
        assert(memcmp(pc.exposed, expected_pc.exposed, sizeof(pc.exposed)) == 0);
        if (ch.selected) assert(ch.selected->exposed == expected_object);
        assert(allocations == 0 && eq_probes == 0);
        if (target >= 0) assert(coverage_calls <= 2);
        new_probes += snapshot_probes;
      }
    }
  }
  printf("PASS: 20,000 expose/unexpose comparisons, including layered/transparent clothing, water, blindfolds, duplicate slots and the 200-object limit.\n");
  printf("Inventory probes: %ld -> %ld; body-location coverage calls capped at 2; no string allocations.\n", old_probes, new_probes);
}
'''

with tempfile.TemporaryDirectory(prefix='haven-expose-test-') as directory:
    cpp = Path(directory) / 'expose.cpp'
    binary = Path(directory) / 'expose-test'
    cpp.write_text(stubs + snapshot + get_eq + parser + coverage + visibility
                   + legacy_coverage + legacy_visibility + helpers + commands + tests)
    subprocess.run(['g++', '-std=c++11', '-O2', '-Wall', '-Wextra',
                    '-Wno-unused-parameter', '-fsanitize=address,undefined',
                    str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
