#!/usr/bin/env python3
"""Linux/WSL regression checks for dorm cleanup and offline load ownership."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
houses = (ROOT / 'src/houses.c').read_text()
start = houses.index('  static bool active_dorm_resident(')
cleanup = houses[start:houses.index('  void save_containers()', start)]

source = r'''
#include "merc.h"
#include "recycle.h"
#include <cassert>
#include <cstring>
#include <cstdlib>
#include <set>
#include <sys/stat.h>

time_t current_time = 2000000;
std::vector<INSTITUTE_TYPE *> InVect;
std::vector<WEEKLY_TYPE *> WeeklyVect;
char *enclave_room[2 * MAX_DORMROOMS] = {};
struct Person {
  CHAR_DATA ch = {};
  INSTITUTE_TYPE institute = {};
  WEEKLY_TYPE weekly = {};
  bool online = false, file = true, compressed = false, load_succeeds = true;
  time_t modified = current_time;
};
std::map<std::string, Person *> people;
std::set<CHAR_DATA *> loaded;
std::vector<std::string> saved;
int loads = 0, frees = 0, saves = 0;

char *str_dup(const char *s) { return strdup(s ? s : ""); }
void free_string(char *s) { free(s); }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
char *capitalize(const char *s) { return const_cast<char *>(s); }
CHAR_DATA *get_char_world_pc(char *name) {
  auto it = people.find(name);
  return it != people.end() && it->second->online ? &it->second->ch : nullptr;
}
bool college_student(CHAR_DATA *ch, bool countsuspended) {
  assert(countsuspended);
  return people.at(ch->name)->institute.college_prestige > 0;
}
bool load_char_obj(DESCRIPTOR_DATA *descriptor, char *name) {
  assert(descriptor->character == nullptr && descriptor->original == nullptr);
  Person *person = people.at(name);
  descriptor->character = new CHAR_DATA(person->ch);
  loaded.insert(descriptor->character);
  ++loads;
  return person->load_succeeds;
}
void free_char(CHAR_DATA *ch) {
  assert(loaded.erase(ch) == 1); // Never free a live resident.
  ++frees;
  delete ch;
}
void save_dorms() {
  ++saves;
  saved.clear();
  for (char *name : enclave_room) saved.emplace_back(name);
}
int dorm_test_stat(const char *path, struct stat *st) {
  for (auto entry : people) {
    Person *person = entry.second;
    std::string player_path = std::string(PLAYER_DIR) + entry.first;
    if (person->compressed) player_path += ".gz";
    if (person->file && player_path == path) {
      st->st_mtime = person->modified;
      return 0;
    }
  }
  return -1;
}
#define stat(path, sb) dorm_test_stat(path, sb)
'''
source += cleanup
source += r'''
void reset() {
  assert(loaded.empty());
  for (char *&name : enclave_room) { free_string(name); name = str_dup(""); }
  for (auto entry : people) { free_string(entry.second->ch.name); delete entry.second; }
  people.clear(); InVect.clear(); WeeklyVect.clear(); saved.clear();
  loads = frees = saves = 0;
}
Person *person(const char *name, bool cached = true) {
  Person *p = new Person;
  p->ch.name = str_dup(name);
  p->ch.activeat = current_time;
  p->institute.name = p->ch.name;
  p->institute.college_prestige = 1;
  p->weekly.charname = p->ch.name;
  p->weekly.valid = true;
  p->weekly.logon = current_time;
  people[name] = p;
  InVect.push_back(&p->institute);
  if (cached) WeeklyVect.push_back(&p->weekly);
  return p;
}
void assign(int slot, const char *name) {
  free_string(enclave_room[slot]); enclave_room[slot] = str_dup(name);
}
int main() {
  reset();
  Person *owner = person("Owner"), *roomie = person("Roommate");
  owner->weekly.logon = current_time - 8 * 86400;
  assign(0, "Owner"); assign(MAX_DORMROOMS, "Roommate");
  dorms_update();
  assert(!strcmp(enclave_room[0], "Roommate") && !*enclave_room[MAX_DORMROOMS]);
  assert(saved[0] == "Roommate" && saved[MAX_DORMROOMS].empty() && saves == 1);
  assert(loads == 0); // Cached activity does not load offline characters.
  dorms_update(); assert(saves == 1); // No disk write without a change.

  reset(); owner = person("Owner"); roomie = person("Roommate");
  assign(19, "Owner"); assign(39, "Roommate");
  owner->online = true; owner->file = false;
  owner->weekly.logon = current_time - 30 * 86400;
  owner->institute.inactivity = 900;
  roomie->institute.inactivity = 501;
  dorms_update();
  assert(!strcmp(enclave_room[19], "Owner") && !*enclave_room[39]);
  assert(loads == 0 && frees == 0);

  reset(); owner = person("Owner"); assign(0, "Owner");
  owner->weekly.logon = current_time - 7 * 86400;
  owner->institute.inactivity = 500;
  dorms_update(); assert(!strcmp(enclave_room[0], "Owner") && saves == 0);
  owner->file = false; // Stale weekly records do not keep deleted PCs housed.
  dorms_update(); assert(!*enclave_room[0] && saves == 1 && loads == 0);

  reset(); owner = person("Owner"); assign(0, "Owner");
  owner->online = true; owner->institute.college_prestige = 0;
  dorms_update(); assert(!*enclave_room[0]);
  assign(0, "Owner"); owner->institute.college_prestige = 1;
  SET_FLAG(owner->ch.act, PLR_DEAD);
  dorms_update(); assert(!*enclave_room[0]);

  reset(); owner = person("Owner", false); assign(0, "Owner");
  owner->compressed = true;
  dorms_update(); assert(!strcmp(enclave_room[0], "Owner") && loads == 1 && frees == 1);
  owner->ch.activeat = current_time - 8 * 86400;
  dorms_update(); assert(!*enclave_room[0] && loads == 2 && frees == 2);

  reset(); owner = person("Owner", false); assign(0, "Owner");
  owner->ch.activeat = 0; owner->modified = current_time - 8 * 86400;
  dorms_update(); assert(!*enclave_room[0] && loads == 1 && frees == 1);

  reset(); owner = person("Owner", false); assign(0, "Owner");
  owner->load_succeeds = false;
  dorms_update(); assert(!*enclave_room[0] && loads == 1 && frees == 1);

  reset(); owner = person("Owner", false); assign(0, "Owner");
  SET_FLAG(owner->ch.act, ACT_IS_NPC);
  dorms_update(); assert(!*enclave_room[0] && loads == 1 && frees == 1);

  reset(); assign(0, "(null)"); assign(39, "AB");
  dorms_update(); assert(!*enclave_room[0] && !*enclave_room[39] && saves == 1);
  reset();
  for (char *&name : enclave_room) { free_string(name); name = nullptr; }
  puts("PASS: dorm inactivity, both slots, promotion, persistence, cached activity and offline load cleanup");
}
'''

with tempfile.TemporaryDirectory(prefix='paroxysm-dorm-inactivity-') as directory:
    scratch = Path(directory)
    (scratch / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-fsanitize=address,undefined', '-no-pie',
                    '-I', str(ROOT / 'src'), str(scratch / 'test.cc'),
                    '-o', str(scratch / 'test')], check=True)
    subprocess.run([str(scratch / 'test')], check=True)
