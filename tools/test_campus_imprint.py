#!/usr/bin/env python3
"""Exercise campus conditioning through the production imprint display in WSL/Linux."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
skills = (ROOT / 'src/skills.c').read_text()
start = skills.index('  bool is_campus_imprint(')
end = skills.index('  bool mindbroken(', start)
source = r'''
#include "merc.h"
#include <cassert>
#include <cstdarg>
#include <string>
time_t current_time = 1000000;
int event_cleanse = 0;
bool student = true, gm = false;
ROOM_INDEX_DATA campus = {}, street = {};
std::string output;
bool is_ill(CHAR_DATA *) { return false; }
bool is_deaf(CHAR_DATA *) { return false; }
bool is_gm(CHAR_DATA *) { return gm; }
bool college_student(CHAR_DATA *, bool countsuspended) {
  assert(countsuspended); return student;
}
bool institute_room(ROOM_INDEX_DATA *room) { return room == &campus; }
bool str_cmp(const char *a, const char *b) { return strcmp(a, b) != 0; }
void free_string(char *s) { free(s); }
char *str_dup(const char *s) { return strdup(s); }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
void send_to_char(const char *text, CHAR_DATA *) { output += text; }
void printf_to_char(CHAR_DATA *, char *format, ...) {
  char buf[MSL]; va_list args; va_start(args, format);
  vsnprintf(buf, sizeof(buf), format, args); va_end(args); output += buf;
}
'''
source += skills[start:end]
start = skills.index('  _DOFUN(do_satiate) {')
source += skills[start:skills.index('  void triggercheck(', start)]
source += r'''
int main() {
  CHAR_DATA ch = {}; PC_DATA pc = {}; ch.pcdata = &pc;
  pc.fixation_name = (char *)"";
  for (int i = 0; i < 25; ++i) {
    pc.imprint[i] = str_dup(i == 0 ? "help a friend" : "");
    pc.imprint_trigger[i] = str_dup("");
  }
  pc.imprint_type[0] = IMPRINT_INFLUENCE;
  auto check = [&](bool expected) {
    output.clear(); show_imprints(&ch);
    assert((output.find("You mildly want to serve Cortex.") != std::string::npos) == expected);
    if (!event_cleanse) assert(output.find("You want to help a friend.") != std::string::npos);
    assert(pc.imprint_type[0] == IMPRINT_INFLUENCE);
    int count = 0;
    for (int i = 1; i < 25; ++i) {
      if (is_campus_imprint(&ch, i)) {
        ++count;
        assert(!strcmp(pc.imprint[i], "serve Cortex"));
        assert(pc.imprint_pending[i] == 0);
      }
    }
    assert(count == (expected ? 1 : 0));
  };
  ch.in_room = &street; check(false);
  ch.in_room = &campus; check(true); check(true);
  output.clear(); do_satiate(&ch, (char *)"serve Cortex");
  assert(output.find("cannot satiate") != std::string::npos); check(true);
  ch.in_room = &street; check(false);
  ch.in_room = nullptr; check(false);
  ch.in_room = &campus; check(true);
  student = false; check(false); student = true;
  gm = true; check(false); gm = false;
  event_cleanse = 1; check(false); event_cleanse = 0;
  // A full imprint list must not lose an unrelated effect to make space.
  ch.in_room = &street; sync_campus_imprint(&ch);
  for (int i = 1; i < 25; ++i) pc.imprint_type[i] = IMPRINT_DRUGS;
  ch.in_room = &campus; sync_campus_imprint(&ch);
  for (int i = 1; i < 25; ++i) assert(pc.imprint_type[i] == IMPRINT_DRUGS);
  pc.imprint_type[24] = 0; sync_campus_imprint(&ch);
  assert(is_campus_imprint(&ch, 24));
  // Even another imprint with the same text belongs to its original source.
  free_string(pc.imprint[1]); pc.imprint[1] = str_dup("serve Cortex");
  pc.imprint_type[1] = IMPRINT_INFLUENCE;
  output.clear(); show_imprints(&ch);
  assert(pc.imprint_type[1] == IMPRINT_INFLUENCE && is_campus_imprint(&ch, 24));
  ch.in_room = &street; sync_campus_imprint(&ch);
  assert(pc.imprint_type[1] == IMPRINT_INFLUENCE && pc.imprint_type[24] == 0);
  for (int i = 1; i < 25; ++i) pc.imprint_type[i] = 0;
  student = false; sync_campus_imprint(&ch);
  SET_FLAG(ch.act, ACT_IS_NPC); check(false);
  for (int i = 0; i < 25; ++i) {
    free_string(pc.imprint[i]); free_string(pc.imprint_trigger[i]);
  }
  puts("PASS: campus entry, exit, re-entry, eligibility, reminders and unrelated imprints.");
}
'''
with tempfile.TemporaryDirectory(prefix='campus-imprint-') as tmp:
    path = Path(tmp)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-Wno-write-strings', '-Wno-deprecated',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-no-pie',
                    '-I', str(ROOT / 'src'), str(path / 'test.cc'), '-o', str(path / 'test')],
                   check=True)
    subprocess.run([str(path / 'test')], check=True)
