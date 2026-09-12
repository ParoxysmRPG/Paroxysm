#!/usr/bin/env python3
"""Run production spy-camera commands/delivery under ASan/UBSan (WSL/Linux)."""
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
#include "spy_camera.h"
#include "text_format.h"
#include <cassert>
#include <cstdarg>
#include <cstring>
time_t current_time = 1000000;
ObjList object_list;
ROOM_INDEX_DATA *room_index_hash[MAX_KEY_HASH] = {};
std::string output, owner_notice, notice_owner;
int consumed = 0, skill = 0, notices = 0, alerts = 0;
bool public_location = false, school = false, haven_location = true;
bool dark = false, mist = false, signal = true, consumable = true;
char *str_dup(const char *s) { return strdup(s ? s : ""); }
void free_string(char *s) { free(s); }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
bool is_name(char *s, char *names) { return s && *s && names && !strncmp(names, s, strlen(s)); }
bool public_room(ROOM_INDEX_DATA *) { return public_location; }
bool room_in_school(int) { return school; }
bool in_haven(ROOM_INDEX_DATA *) { return haven_location; }
bool is_dark(ROOM_INDEX_DATA *) { return dark; }
bool mist_room(ROOM_INDEX_DATA *) { return mist; }
bool cell_signal(CHAR_DATA *ch) { return ch && ch->in_room && signal; }
bool is_ghost(CHAR_DATA *) { return false; }
bool is_helpless(CHAR_DATA *) { return false; }
bool is_pinned(CHAR_DATA *) { return false; }
bool in_fight(CHAR_DATA *) { return false; }
bool can_manual_task(CHAR_DATA *) { return true; }
bool can_see_obj(CHAR_DATA *, OBJ_DATA *) { return true; }
int get_skill(CHAR_DATA *, int) { return skill; }
bool has_consume(CHAR_DATA *, int item) { assert(item == 46405); if (consumable) ++consumed; return consumable; }
char *get_intro(CHAR_DATA *ch) { return ch->name; }
CHAR_DATA *get_char_vision(CHAR_DATA *, ROOM_INDEX_DATA *, char *word) { assert(strlen(word) < MAX_INPUT_LENGTH); return nullptr; }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void printf_to_char(CHAR_DATA *, char *fmt, ...) {
  char buf[MSL]; va_list args; va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args); va_end(args); output += buf;
}
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) { ++alerts; }
void offline_message(char *owner, char *message) { ++notices; notice_owner = owner; owner_notice = message; }
EXTRA_DESCR_DATA *new_extra_descr() {
  auto *ed = new EXTRA_DESCR_DATA{}; ed->description = str_dup(""); return ed;
}
char *one_argument_nouncap(char *argument, char *first) {
  while (*argument == ' ') ++argument;
  while (*argument && *argument != ' ') *first++ = *argument++;
  *first = 0;
  while (*argument == ' ') ++argument;
  return argument;
}
'''
source += section('interp.c', '  char *one_argument_true(', '  /*\n* Contributed by Alander.')
source += section('act_comm.c', '  static CHAR_DATA *phone_owner(', '  static bool group_text_member(')
source += section('act_comm.c', '  char *spyware_message(', '  char *emote_name(')
source += section('act_comm.c', '  void spymessage(', '  bool eligible_malady(')
source += section('act_obj.c', '  _DOFUN(do_plantcamera)', '  bool has_cash(')
source += section('act_info.c', '  bool bugged_room(', '\n  }') + '\n  }\n'
source += r'''
static void assign(char *&field, const std::string &value) { free_string(field); field = str_dup(value.c_str()); }
static void command(CHAR_DATA *ch, DO_FUN *handler, const char *text) {
  char input[100]; strcpy(input, text); handler(ch, input);
}
int main() {
  AREA_DATA area = {}; area.vnum = 2;
  ROOM_INDEX_DATA room = {}; room.area = &area; room.name = (char *)"Test room";
  room_index_hash[0] = &room;
  CHAR_DATA planter = {}, receiver = {}; PC_DATA pc = {};
  planter.name = (char *)"Planter"; planter.in_room = receiver.in_room = &room;
  planter.pcdata = &pc; planter.shape = SHAPE_HUMAN; planter.money = 100000;
  OBJ_DATA phone = {}, second = {}, prefix = {}, bag = {}, inner = {};
  phone.item_type = second.item_type = prefix.item_type = ITEM_PHONE;
  phone.value[0] = 1234; second.value[0] = 5678; prefix.value[0] = 123;
  phone.name = (char *)"phone"; phone.description = (char *)"a phone";
  phone.carried_by = &planter; planter.carrying = &phone;
  second.carried_by = prefix.carried_by = &receiver;
  object_list.push_back(&phone); object_list.push_back(&second); object_list.push_back(&prefix);
  assert(haven::camera_lifetime_hours(-1) == 168);
  for (int i = 1; i <= 5; ++i) assert(haven::camera_lifetime_hours(i) == i * 168);
  assert(haven::camera_lifetime_hours(99) == 840);

  public_location = true; command(&planter, do_plantcamera, "phone"); assert(consumed == 0);
  public_location = false; school = true; command(&planter, do_plantcamera, "phone"); assert(consumed == 0);
  school = false; phone.value[0] = 0; command(&planter, do_plantcamera, "phone"); assert(consumed == 0);
  phone.value[0] = 1234; skill = 3;
  command(&planter, do_plantcamera, "phone"); assert(consumed == 1);
  const time_t expiry = current_time + 3 * 7 * 86400;
  assert(std::string(room.extra_descr->description) == "1234:" + std::to_string(expiry) + ":Planter");
  assert(IS_SET(area.area_flags, AREA_CHANGED));
  command(&planter, do_plantcamera, "phone"); assert(consumed == 1);
  assert(haven::camera_linked(room.extra_descr, 1234) && !haven::camera_linked(room.extra_descr, 123));
  assign(room.extra_descr->description, std::string(room.extra_descr->description) + " 5678:" + std::to_string(expiry + 1000) + ":Other");
  for (int i = 0; i < 1000; ++i) {
    assign(phone.material, ""); assign(second.material, "");
    spymessage(&room, (char *)"Movement.");
    assert(strstr(phone.material, "Movement.") && strstr(second.material, "Movement."));
    assert(prefix.material == nullptr && bugged_room(&room));
  }
  puts("PASS: skill lifetimes, exact numbers, duplicate/invalid placement, stable multiple feeds");

  phone.carried_by = nullptr; phone.in_obj = &inner; inner.in_obj = &bag; bag.carried_by = &planter;
  assign(phone.material, ""); spymessage(&room, (char *)"Nested."); assert(strstr(phone.material, "Nested."));
  SET_BIT(bag.extra_flags, ITEM_WARDROBE); assign(phone.material, "");
  spymessage(&room, (char *)"Hidden."); assert(!*phone.material); REMOVE_BIT(bag.extra_flags, ITEM_WARDROBE);
  SET_BIT(phone.extra_flags, ITEM_OFF); spymessage(&room, (char *)"Off."); assert(!*phone.material);
  REMOVE_BIT(phone.extra_flags, ITEM_OFF);
  for (bool *blocked : {&dark, &mist, &public_location, &school}) {
    *blocked = true; spymessage(&room, (char *)"Blocked.");
    emotespy(&planter, nullptr, 0, (char *)"gestures.", false, false);
    assert(!*phone.material); *blocked = false;
  }
  signal = false; spymessage(&room, (char *)"No signal."); assert(!*phone.material); signal = true;
  spymessage(&room, (char *)"Restored."); assert(strstr(phone.material, "Restored."));
  assign(phone.material, std::string(15999, 'x')); spymessage(&room, (char *)"Full."); assert(strlen(phone.material) == 15999);
  assign(phone.material, ""); emotespy(&planter, nullptr, EMOTE_ATTEMPT, (char *)"secret", false, false); assert(!*phone.material);
  emotespy(&planter, nullptr, 0, (char *)"@me waves.", false, false); assert(strstr(phone.material, "Planter waves."));
  std::string huge_intro(1000, 'a'), expanded;
  for (int i = 0; i < 1000; ++i) expanded += "@me ";
  planter.name = huge_intro.data();
  char *rendered = spyware_message(&planter, nullptr, 0, expanded.data(), &receiver, false, false);
  assert(strlen(rendered) > MSL); free_string(rendered);
  assign(phone.material, ""); emotespy(&planter, nullptr, 0, expanded.data(), false, false); assert(!*phone.material);
  planter.name = (char *)"Planter";
  std::string long_mention = "@" + std::string(MAX_INPUT_LENGTH + 1, 'a');
  rendered = spyware_message(&planter, nullptr, 0, long_mention.data(), &receiver, false, false);
  assert(strstr(rendered, "someone")); free_string(rendered);
  puts("PASS: nested/off/wardrobe phones, signal recovery, room restrictions, full inbox and long emotes");

  // Stored timestamps survive reload and are independent of current skill.
  const std::string saved = room.extra_descr->description; skill = 5;
  assign(room.extra_descr->description, saved); current_time = expiry - 1;
  assert(bugged_room(&room) && haven::camera_linked(room.extra_descr, 1234));
  current_time = expiry; camera_update();
  assert(notices == 1 && notice_owner == "Planter" && owner_notice.find("has expired") != std::string::npos);
  assert(!haven::camera_linked(room.extra_descr, 1234) && haven::camera_linked(room.extra_descr, 5678));
  current_time += 61; camera_update(); assert(notices == 1);
  command(&planter, do_bugsweep, "");
  assert(notices == 2 && notice_owner == "Other" && owner_notice.find("found and destroyed") != std::string::npos);
  assert(!bugged_room(&room)); command(&planter, do_bugsweep, ""); assert(notices == 2);
  phone.carried_by = &planter; phone.in_obj = nullptr;
  command(&planter, do_plantcamera, "phone"); assert(consumed == 2 && bugged_room(&room));
  puts("PASS: saved expiry, empty-room timer, planter notices once, isolated removal, sweep and replant");

  assign(room.extra_descr->description, "1234 5678 bad 0 -123 1234:0 1234:999999999999999999999999 1234:123:../x");
  haven::camera_links(&room);
  std::string migrated = room.extra_descr->description;
  assert(migrated == "1234:" + std::to_string(current_time + 7 * 86400) + " 5678:" + std::to_string(current_time + 7 * 86400));
  ++current_time; haven::camera_links(&room); assert(migrated == room.extra_descr->description);
  assign(room.extra_descr->description, std::string(MSL - 4, '9') + ":" + std::to_string(current_time + 100));
  command(&planter, do_plantcamera, "phone"); assert(bugged_room(&room));
  spymessage(nullptr, nullptr); do_plantcamera(nullptr, (char *)""); do_bugsweep(nullptr, (char *)"");
  assert(!bugged_room(nullptr));
  free_string(phone.material); free_string(second.material); free_string(prefix.material);
  free_string(room.extra_descr->description); free_string(room.extra_descr->keyword); delete room.extra_descr;
  puts("PASS: legacy migration, corrupt metadata, null safety and allocation cleanup");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-camera-test-') as temporary:
    path = Path(temporary)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-fsanitize=address,undefined', '-no-pie',
                    '-I', str(ROOT / 'src'), str(path / 'test.cc'), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
