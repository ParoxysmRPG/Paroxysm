#!/usr/bin/env python3
"""Exercise the actual clothing renderer with instrumented visibility stubs.

Run with python3 tools/test_clothing_optimization.py (requires g++).
No world files are loaded or changed.
"""
from pathlib import Path
import subprocess
import tempfile


root = Path(__file__).resolve().parents[1]
source = (root / 'src/act_info.c').read_text()


def section(start, end, text=source):
    offset = text.index(start)
    return text[offset:text.index(end, offset)]


constants = (root / 'src/const.h').read_text()
enum_end = constants.index('} wear_locations;') + len('} wear_locations;')
enum_start = constants.rindex('typedef enum', 0, enum_end)
snapshot = (root / 'src/equipment_snapshot.h').read_text()
snapshot = snapshot.replace('#include "merc.h"', '')
snapshot = snapshot.replace('int count = 0;', '++snapshots; int count = 0;')
snapshot = snapshot.replace('const int slot = obj->wear_loc;',
                            '++inventory_steps; const int slot = obj->wear_loc;')

stubs = r'''
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#define TRUE true
#define FALSE false
#define MSL 8192
#define MAX_STRING_LENGTH MSL
#define UMAX(a,b) ((a) > (b) ? (a) : (b))
#define UMIN(a,b) ((a) < (b) ? (a) : (b))
#define IS_SET(v,f) ((v)&(f))
#define IS_IMMORTAL(c) ((c)->immortal)
#define ITEM_JEWELRY 1
#define ITEM_CONTAINER 2
#define ITEM_WEAPON 3
#define ITEM_RANGED 4
#define ITEM_TRASH 5
#define ITEM_WARDROBE 1
#define SEX_MALE 1
struct OBJ_DATA {
  OBJ_DATA *next_content = nullptr;
  int wear_loc = WEAR_NONE, item_type = 0, size = 0, extra_flags = 0;
  char *wear_temp = nullptr, *wear_string = nullptr;
  std::string text;
  bool visible = true, covered = false;
};
struct CHAR_DATA {
  OBJ_DATA *carrying = nullptr;
  int sex = SEX_MALE;
  bool xray = false, immortal = false, shield = false;
};
int snapshots = 0, inventory_steps = 0, visibility_calls[MAX_WEAR] = {};
std::vector<char*> allocations;
char *str_dup(const char *s) {
  char *copy = strdup(s); allocations.push_back(copy); return copy;
}
void remove_color(char *out, const char *in) { strcpy(out, in); }
char *format_obj_to_char(OBJ_DATA *obj, CHAR_DATA *, bool) {
  return const_cast<char*>(obj->text.c_str());
}
bool can_see_obj(CHAR_DATA *, OBJ_DATA *obj) { return obj->visible; }
bool has_xray(CHAR_DATA *ch) { return ch->xray; }
bool is_spyshield(CHAR_DATA *ch) { return ch->shield; }
'''

visibility = r'''
extern "C" bool can_see_wear_equipped(CHAR_DATA *, int slot,
                                      const haven::EquipmentSnapshot &equipment) {
  ++visibility_calls[slot];
  OBJ_DATA *obj = equipment.get(slot);
  return !obj || !obj->covered;
}
'''

tests = r'''
static std::string render(CHAR_DATA &viewer, CHAR_DATA &victim) {
  snapshots = inventory_steps = 0;
  memset(visibility_calls, 0, sizeof(visibility_calls));
  std::string result = equip_string(&viewer, &victim);
  assert(snapshots == 1);
  for (int slot = 0; slot < MAX_WEAR; ++slot)
    assert(visibility_calls[slot] <= 1);
  for (char *copy : allocations) free(copy);
  allocations.clear();
  return result;
}
int main() {
  CHAR_DATA viewer, victim;
  const std::string heading = "\n\rHe is using:\n\r\n\r";
  const std::string tail = "\n\n\r\n\r\n\r";
  assert(render(viewer, victim) == tail);
  assert(inventory_steps == 0);

  OBJ_DATA offhand;
  offhand.wear_loc = WEAR_HOLD_2; offhand.text = "offhand";
  victim.carrying = &offhand;
  assert(render(viewer, victim) == heading + "offhand\n\r" + tail);
  assert(inventory_steps == 1);
  assert(visibility_calls[WEAR_HOLD] == 1 && visibility_calls[WEAR_HOLD_2] == 1);
  puts("PASS: secondary hand renders once, primary-hand fallback preserved for padding only.");

  OBJ_DATA items[7];
  for (int i = 0; i < 7; ++i) {
    items[i].text = std::to_string(i);
    if (i < 6) items[i].next_content = &items[i+1];
  }
  items[0].wear_loc = WEAR_BODY_1;
  items[1].wear_loc = WEAR_HOLD;
  items[2].wear_loc = WEAR_BODY_3; items[2].item_type = ITEM_JEWELRY;
  items[3].wear_loc = WEAR_BODY_2;
  items[4].wear_loc = WEAR_HOLD_2;
  items[5].wear_loc = WEAR_BODY_4; items[5].covered = true;
  items[6].wear_loc = WEAR_BODY_5; items[6].visible = false;
  victim.carrying = items;
  const std::string prefix = heading + "1\n\r4\n\r\n\n\r";
  assert(render(viewer, victim) == prefix + "3\n\r0\n\r\n\r2\n\r\n\r");
  viewer.xray = true;
  assert(render(viewer, victim) == prefix + "5\n\r3\n\r0\n\r\n\r2\n\r\n\r");
  viewer.immortal = victim.shield = true;
  assert(render(viewer, victim) == prefix + "3\n\r0\n\r\n\r2\n\r\n\r");
  viewer.immortal = victim.shield = viewer.xray = false;
  puts("PASS: hand/body/jewelry order, object visibility, concealed clothing and spyshield.");

  OBJ_DATA padded;
  padded.text = "coat"; padded.wear_loc = WEAR_BODY_1;
  padded.wear_temp = const_cast<char*>("(worn)");
  padded.wear_string = const_cast<char*>("a much longer ignored label");
  victim.carrying = &padded;
  assert(render(viewer, victim) == "\n\n\r" + heading + "(worn)   coat\n\r\n\r\n\r");
  padded.wear_temp = const_cast<char*>(", loosely");
  assert(render(viewer, victim) == "\n\n\r" + heading + "coat, loosely\n\r\n\r\n\r");
  padded.wear_temp = nullptr;
  padded.wear_string = const_cast<char*>("(worn)");
  assert(render(viewer, victim) == "\n\n\r" + heading + "(worn)   coat\n\r\n\r\n\r");
  puts("PASS: padding, temporary label precedence, wear labels and punctuation.");

  OBJ_DATA carried[4];
  for (int i = 0; i < 4; ++i) {
    carried[i].text = std::to_string(i);
    if (i < 3) carried[i].next_content = &carried[i+1];
  }
  carried[0].size = 25;
  carried[2].extra_flags = ITEM_WARDROBE;
  carried[3].item_type = ITEM_TRASH;
  victim.carrying = carried;
  assert(render(viewer, victim) == tail + heading + "0\n\r");
  viewer.xray = true;
  assert(render(viewer, victim) == tail + heading + "0\n\r1\n\r");
  victim.xray = true;
  assert(render(victim, victim) == tail + heading + "0\n\r");
  viewer.xray = victim.xray = false;
  puts("PASS: carried items, wardrobe/trash filtering and self versus other xray.");

  std::vector<OBJ_DATA> large(205);
  for (size_t i = 0; i < large.size(); ++i) {
    large[i].text = std::to_string(i);
    if (i + 1 < large.size()) large[i].next_content = &large[i+1];
  }
  large[0].wear_loc = large[1].wear_loc = WEAR_BODY_1;
  large[199].wear_loc = WEAR_BODY_2;
  large[200].wear_loc = WEAR_BODY_3;
  victim.carrying = large.data();
  assert(render(viewer, victim) == "\n\n\r" + heading + "199\n\r0\n\r\n\r\n\r");
  assert(inventory_steps == 200);
  large[199].wear_loc = WEAR_NONE;
  assert(render(viewer, victim) == "\n\n\r" + heading + "0\n\r\n\r\n\r");
  assert(visibility_calls[WEAR_BODY_2] == 0);
  puts("PASS: one 200-item inventory scan, first duplicate wins, fresh equipment each render.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-clothing-test-') as directory:
    cpp = Path(directory) / 'clothing.cpp'
    binary = Path(directory) / 'clothing-test'
    cpp.write_text(constants[enum_start:enum_end] + stubs + snapshot + visibility
                   + section('  int where_length(', '  char *number_to_text(')
                   + tests)
    subprocess.run(['g++', '-std=c++11', '-O2', '-Wall', '-Wextra',
                    '-Wno-unused-parameter', '-Wno-write-strings',
                    '-fsanitize=address,undefined', str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
